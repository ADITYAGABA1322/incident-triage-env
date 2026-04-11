import uuid
from collections import Counter
from pathlib import Path
import sys
from threading import RLock
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from environment import IncidentEnv, TASK_SPECS
from incidents import TICKETS
from models import (
    IncidentAction,
    IncidentObservation,
    IncidentReward,
    IncidentState,
    ResetRequest,
    StepResult,
    TaskType,
)

app = FastAPI(title="Incident Triage Environment")
UI_DIR = Path(__file__).parent / "ui"
ASSETS_DIR = UI_DIR / "assets"

# Session store: session_id -> IncidentEnv instance
MAX_SESSIONS = 500
sessions: dict[str, IncidentEnv] = {}
completed_states: dict[str, IncidentState] = {}
session_lock = RLock()
task_counts = Counter(ticket["task_type"] for ticket in TICKETS)

app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")


def log_event(event: str, **fields: Any) -> None:
    details = " ".join(f"{key}={value}" for key, value in fields.items())
    print(f"[{event}] {details}", file=sys.stderr, flush=True)


def evict_oldest(mapping: dict[str, Any], max_size: int) -> None:
    while len(mapping) >= max_size:
        oldest_key = next(iter(mapping), None)
        if oldest_key is None:
            return
        mapping.pop(oldest_key, None)


@app.get("/", include_in_schema=False)
def home_page():
    return FileResponse(UI_DIR / "index.html")


@app.get("/status", include_in_schema=False)
def status_page():
    return FileResponse(UI_DIR / "status.html")


@app.get("/playground", include_in_schema=False)
def playground_page():
    return FileResponse(UI_DIR / "playground.html")


@app.get("/api", include_in_schema=False)
def api_page():
    return FileResponse(UI_DIR / "api.html")


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/metadata")
def metadata():
    return {
        "name": "incident-triage-env",
        "description": "Production incident triage environment for severity, root-cause, and remediation decisions.",
        "tasks": {
            task_type.value: {
                "name": spec["name"],
                "difficulty": spec["difficulty"],
                "expected_field": spec["expected_field"],
                "allowed_values": spec["allowed_values"],
                "ticket_count": task_counts[task_type.value],
            }
            for task_type, spec in TASK_SPECS.items()
        },
        "total_tickets": len(TICKETS),
    }


@app.get("/schema")
def schema():
    return {
        "action": IncidentAction.model_json_schema(),
        "observation": IncidentObservation.model_json_schema(),
        "reward": IncidentReward.model_json_schema(),
        "state": IncidentState.model_json_schema(),
        "step_result": StepResult.model_json_schema(),
    }


@app.get("/tasks")
def get_tasks():
    return {
        "tasks": {
            task_type.value: {
                "name": spec["name"],
                "difficulty": spec["difficulty"],
                "expected_field": spec["expected_field"],
                "allowed_values": spec["allowed_values"],
                "ticket_count": task_counts[task_type.value],
            }
            for task_type, spec in TASK_SPECS.items()
        }
    }


@app.get("/tickets")
def get_tickets():
    tickets = []
    for ticket in TICKETS:
        task_type = TaskType(ticket["task_type"])
        spec = TASK_SPECS[task_type]
        tickets.append(
            {
                "incident_id": ticket["incident_id"],
                "task_type": ticket["task_type"],
                "difficulty": spec["difficulty"],
                "task_name": spec["name"],
                "expected_field": spec["expected_field"],
                "alert_preview": ticket["alert_text"][:120],
            }
        )
    return {"tickets": tickets, "count": len(tickets)}


@app.post("/reset", response_model=StepResult)
def reset(reset_request: ResetRequest | None = None):
    request = reset_request or ResetRequest()
    session_id = str(uuid.uuid4())
    env = IncidentEnv()
    try:
        result = env.reset(
            task_type=request.task_type,
            ticket_id=request.ticket_id,
            seed=request.seed,
        )
    except ValueError as e:
        log_event(
            "RESET_ERROR",
            task_type=request.task_type.value if request.task_type else "any",
            ticket_id=request.ticket_id or "random",
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    with session_lock:
        evict_oldest(sessions, MAX_SESSIONS)
        evict_oldest(completed_states, MAX_SESSIONS)
        sessions[session_id] = env
    result.info["session_id"] = session_id
    result.info["state"] = env.state(session_id=session_id).model_dump()
    log_event(
        "RESET",
        session_id=session_id,
        incident_id=result.observation.incident_id,
        task_type=result.observation.task_type.value,
        expected_field=result.observation.expected_field,
    )
    return result


@app.post("/step", response_model=StepResult)
def step(action: IncidentAction, session_id: str):
    with session_lock:
        env = sessions.get(session_id)
        if not env:
            if session_id in completed_states:
                log_event("STEP_ERROR", session_id=session_id, error="episode_already_completed")
                raise HTTPException(status_code=400, detail="Episode already completed. Call reset() to start a new one.")
            log_event("STEP_ERROR", session_id=session_id, error="session_not_found")
            raise HTTPException(status_code=404, detail="Session not found. Call /reset first.")
        try:
            result = env.step(action)
        except (RuntimeError, ValueError) as e:
            log_event("STEP_ERROR", session_id=session_id, incident_id=action.incident_id, error=str(e))
            raise HTTPException(status_code=400, detail=str(e))
        result.info["session_id"] = session_id
        current_state = env.state(session_id=session_id)
        result.info["state"] = current_state.model_dump()
        if result.done:
            completed_states[session_id] = current_state
            sessions.pop(session_id, None)
    log_event(
        "STEP",
        session_id=session_id,
        incident_id=action.incident_id,
        task_type=action.task_type.value,
        answer=action.selected_value() or "NONE",
        reward=result.reward.value,
        done=str(result.done).lower(),
    )
    return result


@app.get("/state", response_model=IncidentState)
def state(session_id: str):
    with session_lock:
        env = sessions.get(session_id)
        if not env:
            completed_state = completed_states.get(session_id)
            if completed_state:
                log_event("STATE", session_id=session_id, incident_id=completed_state.incident_id, done=str(completed_state.done).lower())
                return completed_state
            log_event("STATE_ERROR", session_id=session_id, error="no_active_session")
            raise HTTPException(status_code=404, detail="No active session.")
        try:
            current_state = env.state(session_id=session_id)
            log_event("STATE", session_id=session_id, incident_id=current_state.incident_id, done=str(current_state.done).lower())
            return current_state
        except RuntimeError as e:
            log_event("STATE_ERROR", session_id=session_id, error=str(e))
            raise HTTPException(status_code=404, detail=str(e))


@app.get("/grader")
def get_grader_info():
    return {
        "grading": "deterministic",
        "scoring": "task1: adjacent-severity partial credit; task2/task3: exact match plus conservative near-miss partial credit",
        "tasks": {
            "task1": "exact=1.0, adjacent=0.5, far=0.0",
            "task2": "exact=1.0, related-domain=0.5, unknown=0.25, wrong=0.0",
            "task3": "exact=1.0, investigate fallback=0.4, related response=0.25, wrong=0.0",
        }
    }


@app.post("/mcp")
def mcp(payload: dict[str, Any] | None = None):
    request = payload or {}
    method = request.get("method")
    rpc_id = request.get("id")

    if method == "ping":
        result: dict[str, Any] = {"status": "ok"}
    elif method == "tools/list":
        result = {"tools": []}
    else:
        result = {
            "status": "ok",
            "message": "Incident triage environment does not expose MCP tools.",
        }

    return {"jsonrpc": "2.0", "id": rpc_id, "result": result}
