import json
import os
import re
import sys
import random as _random
import httpx
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from openai import OpenAI

from incidents import TICKETS

load_dotenv(override=False)

API_BASE_URL = os.environ.get("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.environ.get("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"
API_KEY = (
    os.environ.get("HF_TOKEN")
    or os.environ.get("API_KEY")
    or os.environ.get("OPENAI_API_KEY")
    or ""
)
ENV_URL = os.environ.get("ENV_URL") or "http://localhost:7860"
BENCHMARK = "incident-triage-env"
MAX_TOKENS = 300
TEMPERATURE = 0.0
OUTPUT_PATH = Path(os.environ.get("OUTPUT_PATH") or "/tmp/outputs/baseline_scores.json")

SYSTEM_PROMPT = """You are an expert SRE triaging production incidents.
You will receive an incident alert, structured context, and the expected output field.
Return ONLY a valid JSON object with this exact shape:
{"incident_id":"<id>","task_type":"<task_type>","severity":null,"root_cause":null,"action":null}

Rules:
- Populate exactly one of severity, root_cause, or action based on task_type.
- Allowed severity values: SEV1, SEV2, SEV3
- Allowed root_cause values: DATABASE, NETWORK, APPLICATION, INFRASTRUCTURE, THIRD_PARTY, UNKNOWN
- Allowed action values: ROLLBACK, SCALE_UP, RESTART_SERVICE, FAILOVER, NOTIFY_VENDOR, INVESTIGATE, NO_ACTION
- Keep incident_id and task_type identical to the observation.
- Do not return markdown, prose, or any extra keys.
"""


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    action_clean = action.replace("\n", " ").replace("\r", "")[:100]
    print(
        f"[STEP] step={step} action={action_clean} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{reward:.2f}" for reward in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


class EnvironmentTransport:
    def reset(self, task_type: str, ticket_id: str) -> Dict[str, Any]:
        raise NotImplementedError

    def step(self, session_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    def close(self) -> None:
        return None


class HttpEnvironmentTransport(EnvironmentTransport):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def probe(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            return response.ok
        except requests.RequestException:
            return False

    def reset(self, task_type: str, ticket_id: str) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/reset",
            json={"task_type": task_type, "ticket_id": ticket_id},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def step(self, session_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/step",
            params={"session_id": session_id},
            json=action,
            timeout=30,
        )
        if not response.ok:
            error_body = ""
            try:
                error_body = response.json()
            except Exception:
                error_body = response.text[:500]
            raise requests.HTTPError(
                f"{response.status_code} {response.reason} — Body: {error_body}",
                response=response,
        )
        return response.json()

    def close(self) -> None:
        self.session.close()


class LocalEnvironmentTransport(EnvironmentTransport):
    def __init__(self):
        try:
            from fastapi.testclient import TestClient
        except ImportError as exc:
            raise RuntimeError(
                "LocalEnvironmentTransport requires 'httpx'. "
                "Install it with: pip install httpx"
            ) from exc

        try:
            import app as app_module
        except ImportError as exc:
            raise RuntimeError(
                "Could not import 'app' module. "
                "Make sure you are running inference.py from the project root."
            ) from exc

        self.session = TestClient(app_module.app)


    def reset(self, task_type: str, ticket_id: str) -> Dict[str, Any]:
        response = self.session.post(
            "/reset",
            json={"task_type": task_type, "ticket_id": ticket_id},
        )
        response.raise_for_status()
        return response.json()

    def step(self, session_id: str, action: Dict[str, Any]) -> Dict[str, Any]:
        response = self.session.post(
            "/step",
            params={"session_id": session_id},
            json=action,
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self.session.close()


def build_transport() -> EnvironmentTransport:
    http_transport = HttpEnvironmentTransport(ENV_URL)
    if http_transport.probe():
        print(f"[TRANSPORT] Using HTTP transport at {ENV_URL}", flush=True)
        return http_transport
    http_transport.close()
    print(
        f"[TRANSPORT] HTTP server at {ENV_URL} unreachable. "
        "Falling back to local in-process transport.",
        flush=True,
    )
    return LocalEnvironmentTransport()


def create_model_client() -> Optional[OpenAI]:
    if not (API_BASE_URL and API_KEY and MODEL_NAME):
        return None
    return OpenAI(
        base_url=API_BASE_URL,
        api_key=API_KEY,
        timeout=20.0,
        max_retries=0
    )


def build_user_prompt(observation: Dict[str, Any]) -> str:
    return (
        f"Incident ID: {observation['incident_id']}\n"
        f"Task Type: {observation['task_type']}\n"
        f"Difficulty: {observation['difficulty']}\n"
        f"Task Description: {observation['task_description']}\n"
        f"Expected Field: {observation['expected_field']}\n"
        f"Allowed Values: {', '.join(observation['allowed_values'])}\n\n"
        f"Alert:\n{observation['alert_text']}\n\n"
        f"Context:\n{json.dumps(observation['context'], indent=2, sort_keys=True)}\n"
    )


def extract_json(raw: str) -> Dict[str, Any]:
    fenced = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in model response.")
    return json.loads(match.group(0))


def normalize_action(raw_action: Dict[str, Any], observation: Dict[str, Any]) -> Dict[str, Any]:
    task_type = observation["task_type"]
    def upper_or_none(val):
        """Coerce to uppercase string or return None."""
        return str(val).upper().strip() if val is not None else None
    return {
        "incident_id": observation["incident_id"],
        "task_type": task_type,
        "severity": upper_or_none(raw_action.get("severity")) if task_type == "task1" else None,
        "root_cause": upper_or_none(raw_action.get("root_cause")) if task_type == "task2" else None,
        "action": upper_or_none(raw_action.get("action")) if task_type == "task3" else None,
    }


def _number(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"(\d+(?:\.\d+)?)", value)
        if match:
            return float(match.group(1))
    return None


def predict_severity(alert_text: str, context: Dict[str, Any]) -> str:
    error_rate = (
        _number(context.get("error_rate_pct"))
        or _number(context.get("failure_rate"))
        or _number(context.get("affected_users_pct"))
    )
    revenue_impact = (
        context.get("revenue_impact") is True
        or context.get("revenue_dependency") == "high"
        or "REVENUE IMPACT" in alert_text        # alert text is human-readable, spaces are correct here
        or "REVENUE_IMPACT" in alert_text.replace(" ", "_")  # cover both formats
    )
    region_global = context.get("region") == "global"
    if (
        "CRITICAL" in alert_text
        or "100%" in alert_text
        or revenue_impact
        or region_global
        or (error_rate is not None and error_rate >= 40)
    ):
        return "SEV1"

    if (
        "INTERNAL ONLY" in alert_text
        or "COSMETIC" in alert_text
        or "NO USER-FACING IMPACT" in alert_text
        or context.get("user_impact") in {"cosmetic", False}
        or context.get("impact") == "cosmetic"
    ):
        return "SEV3"

    return "SEV2"


def predict_root_cause(alert_text: str, context_text: str) -> str:
    if any(keyword in alert_text or keyword in context_text for keyword in ["STRIPE", "SENDGRID", "TWILIO", "VENDOR", "WEBHOOK", "EXTERNAL API"]):
        return "THIRD_PARTY"
    if any(keyword in alert_text or keyword in context_text for keyword in ["PACKET LOSS", "BGP", "TRACEROUTE", "ROUTE", "CROSS-REGION", "TRANSIT HOP"]):
        return "NETWORK"
    if any(keyword in alert_text or keyword in context_text for keyword in ["POSTGRES", "DB ", "DATABASE", "SLOW QUERY", "CONNECTION POOL", "REPLICA", "WRITE QUERIES", "DB_CPU"]):
        return "DATABASE"
    if any(keyword in alert_text or keyword in context_text for keyword in ["KUBERNETES", "NODE", "POD", "CLUSTER", "NOTREADY", "MEMORY PRESSURE", "EC2", "SPOT INTERRUPTION"]):
        return "INFRASTRUCTURE"
    if any(keyword in alert_text or keyword in context_text for keyword in ["EXCEPTION", "STACK TRACE", "DEPLOY", "CRASH", "NULLPOINTER", "TIMEOUTEXCEPTION", "CODE"]):
        return "APPLICATION"
    return "UNKNOWN"


def predict_action(alert_text: str, context_text: str) -> str:
    if any(keyword in alert_text or keyword in context_text for keyword in ["ROLLBACK", "IMMEDIATELY AFTER DEPLOY", "PREVIOUS_STABLE", "RECENT DEPLOY CAUSED"]):
        return "ROLLBACK"
    if any(keyword in alert_text or keyword in context_text for keyword in ["CPU", "QUEUE", "AUTOSCALER", "MAX_REPLICAS", "TRAFFIC SPIKE", "FLASH SALE"]):
        return "SCALE_UP"
    if any(keyword in alert_text or keyword in context_text for keyword in ["DEADLOCK", "HEALTH CHECK", "STUCK", "NO RESPONSE", "PROCESS NOT RESPONDING"]):
        return "RESTART_SERVICE"
    if any(keyword in alert_text or keyword in context_text for keyword in ["FAILOVER", "READ REPLICA", "PRIMARY DOWN", "PRIMARY RDS", "WRITES FAILING"]):
        return "FAILOVER"
    if any(keyword in alert_text or keyword in context_text for keyword in ["SENDGRID", "STRIPE", "TWILIO", "VENDOR"]):
        return "NOTIFY_VENDOR"
    if any(keyword in alert_text or keyword in context_text for keyword in ["COSMETIC", "MINOR UI GLITCH"]):
        return "NO_ACTION"
    return "INVESTIGATE"


def heuristic_action(observation: Dict[str, Any]) -> Dict[str, Any]:
    task_type = observation["task_type"]
    alert_text = observation["alert_text"].upper()
    
    # Normalize: replace underscores with spaces so "packet_loss_pct" matches "PACKET LOSS"
    raw_context = json.dumps(observation["context"])
    context_text = raw_context.upper().replace("_", " ")

    if task_type == "task1":
        return normalize_action({"severity": predict_severity(alert_text, observation["context"])}, observation)
    if task_type == "task2":
        return normalize_action({"root_cause": predict_root_cause(alert_text, context_text)}, observation)
    return normalize_action({"action": predict_action(alert_text, context_text)}, observation)


def get_action(model_client: Optional[OpenAI], observation: Dict[str, Any]) -> Dict[str, Any]:
    if model_client is None:
        return heuristic_action(observation)

    for attempt in range(2):
        try:
            completion = model_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_prompt(observation)},
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                timeout=15.0
            )
            content = (completion.choices[0].message.content or "").strip()
            return normalize_action(extract_json(content), observation)
        except httpx.TimeoutException:
            print(
                f"[WARN] LLM call timed out on attempt {attempt + 1}. "
                f"Incident: {observation['incident_id']}",
                flush=True,
            )
            continue
        except Exception as exc:
            print(f"[WARN] LLM error attempt {attempt + 1}: {exc}", flush=True)
            continue

    print(
        f"[FALLBACK] Using heuristic for {observation['incident_id']} after LLM failures.",
        flush=True,
    )
    return heuristic_action(observation)

def reward_value(step_data: Dict[str, Any]) -> float:
    reward = step_data.get("reward", {})
    if isinstance(reward, dict):
        return float(reward.get("value", 0.0))
    return float(reward or 0.0)


def active_model_name(model_client: Optional[OpenAI]) -> str:
    return MODEL_NAME if model_client is not None else "deterministic-baseline"


def summarize_action(action: Dict[str, Any]) -> str:
    for field in ("severity", "root_cause", "action"):
        value = action.get(field)
        if value is not None:
            return str(value)
    return "no_action"


def run_episode(
    transport: EnvironmentTransport,
    model_client: Optional[OpenAI],
    ticket: Dict[str, Any],
) -> Dict[str, Any]:
    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False
    episode_result: Dict[str, Any]

    log_start(task=ticket["incident_id"], env=BENCHMARK, model=active_model_name(model_client))

    try:
        reset_data = transport.reset(ticket["task_type"], ticket["incident_id"])
        observation = reset_data["observation"]
        session_id = reset_data.get("info", {}).get("session_id")
        if not session_id:
            raise RuntimeError("Environment reset did not return a session_id.")

        steps_taken = 1
        action = get_action(model_client, observation)
        step_data = transport.step(session_id=session_id, action=action)
        score = reward_value(step_data)
        rewards.append(score)
        success = bool(step_data.get("info", {}).get("correct", score >= 0.99))

        log_step(
            step=1,
            action=summarize_action(action),
            reward=score,
            done=bool(step_data.get("done", True)),
            error=None,
        )

        episode_result = {
            "incident_id": ticket["incident_id"],
            "task_type": ticket["task_type"],
            "difficulty": observation.get("difficulty"),
            "score": score,
            "success": success,
            "ground_truth": step_data.get("info", {}).get("ground_truth"),
            "agent_answer": step_data.get("info", {}).get("agent_answer"),
        }
    except Exception as exc:
        log_step(step=max(steps_taken, 1), action="error", reward=0.0, done=True, error=str(exc))
        score = 0.0
        success = False
        episode_result = {
            "incident_id": ticket["incident_id"],
            "task_type": ticket["task_type"],
            "score": 0.0,
            "success": False,
            "error": str(exc),
        }
    finally:
        log_end(success=success, steps=max(steps_taken, 1), score=score, rewards=rewards or [0.0])

    return episode_result


# def write_results(
#     results: List[Dict[str, Any]],
#     output_path: Path = OUTPUT_PATH,
# ) -> None:
#     grouped: Dict[str, List[float]] = {}
#     for result in results:
#         grouped.setdefault(result["task_type"], []).append(result.get("score", 0.0))

#     summary = {
#         "benchmark": BENCHMARK,
#         "model": MODEL_NAME,
#         "episodes": len(results),
#         "average_score": (sum(result.get("score", 0.0) for result in results) / len(results)) if results else 0.0,
#         "by_task": {
#             task_type: {
#                 "episodes": len(scores),
#                 "average_score": (sum(scores) / len(scores)) if scores else 0.0,
#             }
#             for task_type, scores in grouped.items()
#         },
#         "results": results,
#     }

#     try:
#         output_path.parent.mkdir(parents=True, exist_ok=True)
#         output_path.write_text(json.dumps(summary, indent=2))
#     except (PermissionError, OSError) as exc:
#         print(
#             f"[WARN] Could not write results file to {output_path}: {exc}. Scores were still emitted to stdout.",
#             file=sys.stderr,
#             flush=True,
#         )




def write_results(results, output_path=OUTPUT_PATH):
    # Build summary — handle serialization errors explicitly
    try:
        summary = {
            "benchmark": BENCHMARK,
            "model": MODEL_NAME,
            "episodes": len(results),
            "average_score": (
                sum(r.get("score", 0.0) for r in results) / len(results)
            ) if results else 0.0,
            "by_task": _group_by_task(results),
            "results": results,
        }
        serialized = json.dumps(summary, indent=2)
    except (TypeError, ValueError) as exc:
        print(
            f"[ERROR] Results serialization failed: {exc}. "
            "Raw results will be printed to stdout.",
            file=sys.stderr,
            flush=True,
        )
        # Emergency dump — at least something is preserved
        for result in results:
            print(f"[RESULT] {json.dumps(result, default=str)}", flush=True)
        return

    # Attempt primary write
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized)
        print(f"[RESULTS] Written to {output_path}", flush=True)
        return
    except (PermissionError, OSError) as exc:
        print(
            f"[WARN] Primary write failed ({output_path}): {exc}",
            file=sys.stderr, flush=True,
        )

    # Fallback: write to /tmp directly
    fallback_path = Path("/tmp/baseline_scores_fallback.json")
    try:
        fallback_path.write_text(serialized)
        print(f"[RESULTS] Fallback written to {fallback_path}", flush=True)
        return
    except OSError as exc2:
        print(f"[ERROR] Fallback write also failed: {exc2}", file=sys.stderr, flush=True)

    # Last resort: print to stdout as structured log
    print(f"[RESULTS_JSON] {serialized}", flush=True)
    # Signal failure to CI
    sys.exit(1)


def _group_by_task(results):
    grouped = {}
    for result in results:
        grouped.setdefault(result["task_type"], []).append(result.get("score", 0.0))
    return {
        task: {"episodes": len(scores), "average_score": sum(scores) / len(scores)}
        for task, scores in grouped.items()
    }

def stratified_shuffle(tickets):
    """Interleave task1/task2/task3 tickets so truncation hits all difficulties."""
    by_task = {}
    for ticket in tickets:
        by_task.setdefault(ticket["task_type"], []).append(ticket)

    # Shuffle within each task group
    for group in by_task.values():
        _random.shuffle(group)

    # Round-robin interleave across task types
    interleaved = []
    groups = list(by_task.values())
    max_len = max(len(g) for g in groups)
    for i in range(max_len):
        for group in groups:
            if i < len(group):
                interleaved.append(group[i])
    return interleaved

def main() -> None:
    transport = build_transport()
    results = []
    try:
        model_client = create_model_client()
        for ticket in stratified_shuffle(TICKETS):
            result = run_episode(transport, model_client, ticket)
            results.append(result)
            write_results(results)
    finally:
        transport.close()


if __name__ == "__main__":
    main()
