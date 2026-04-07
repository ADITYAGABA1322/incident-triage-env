#----- Edited file--------------
# app.py

import uuid
from fastapi import FastAPI, HTTPException
from models import IncidentAction, StepResult
from server.environment import IncidentEnv
from server.graders import GRADERS

app = FastAPI(title="Incident Triage Environment")

# Session store: session_id -> IncidentEnv instance
sessions: dict[str, IncidentEnv] = {}


@app.get("/tasks")
def get_tasks():
    return {
        "tasks": {
            "task1": "Severity Classification  → SEV1, SEV2, SEV3",
            "task2": "Root Cause Category     → DATABASE, NETWORK, APPLICATION, INFRASTRUCTURE, THIRD_PARTY, UNKNOWN",
            "task3": "Recommended Action      → ROLLBACK, SCALE_UP, RESTART_SERVICE, FAILOVER, NOTIFY_VENDOR, INVESTIGATE, NO_ACTION",
        }
    }


@app.post("/reset")
def reset(task_type: str = None):
    session_id = str(uuid.uuid4())
    env = IncidentEnv()
    try:
        observation = env.reset(task_type=task_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    sessions[session_id] = env
    return {"session_id": session_id, **observation.model_dump()}


@app.post("/step", response_model=StepResult)
def step(action: IncidentAction, session_id: str):
    env = sessions.get(session_id)
    if not env:
        raise HTTPException(status_code=404, detail="Session not found. Call /reset first.")
    try:
        result = env.step(action)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    # Clean up session after step — one action per episode
    sessions.pop(session_id, None)
    return result


@app.get("/state")
def state(session_id: str):
    env = sessions.get(session_id)
    if not env or env.current_ticket is None:
        raise HTTPException(status_code=404, detail="No active session.")
    t = env.current_ticket
    return {
        "session_id": session_id,
        "incident_id": t["incident_id"],
        "task_type":   t["task_type"],
        "status":      "awaiting_action",
    }


@app.get("/grader")
def get_grader_info():
    return {
        "grading": "deterministic",
        "scoring": "task1: partial (1.0/0.5/0.0), task2/task3: binary (1.0/0.0)",
        "tasks": {
            "task1": "exact=1.0, adjacent=0.5, far=0.0",
            "task2": "action.root_cause == ground_truth.root_cause",
            "task3": "action.action     == ground_truth.action",
        }
    }