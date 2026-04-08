# 🚨 Production Incident Triage Environment

An OpenEnv-compatible backend evaluation system where an AI agent triages production incidents like a real SRE (Site Reliability Engineer). Built for deterministic, RL-style evaluation — no UI, no chatbot, pure backend.

---

## 📌 What This Is

This is **not** a chatbot. It is a structured evaluation environment where:

1. Environment returns a production incident (alert + context)
2. AI agent reads the incident
3. Agent returns a structured JSON action
4. Environment sends action to a deterministic grader
5. Grader compares against ground truth
6. Returns a score between `0.0` and `1.0`

---

## 🗂️ Project Structure

```
Incident_Triage/
│
├── models.py               # Pydantic schemas — source of truth for all types
├── incidents.py            # Dataset of 15 production incidents
├── inference.py            # LLM agent (Mistral via NVIDIA API)
├── openenv.yaml            # OpenEnv submission config
├── pyproject.toml          # Project metadata
├── requirements.txt        # Dependencies
├── README.md
│
└── server/
    ├── __init__.py         # Empty — do not add imports here
    ├── app.py              # FastAPI server
    ├── environment.py      # Core RL-style logic (reset / step)
    ├── graders.py          # Deterministic scoring functions
    ├── Dockerfile
    └── requirements.txt
```

---

## ⚙️ Setup

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd Incident_Triage
pip install -r requirements.txt
```

### 2. Set your NVIDIA / Mistral API key

```bash
# Windows
set NVIDIA_API_KEY=your_nvidia_api_key_here

# Mac / Linux
export NVIDIA_API_KEY=your_nvidia_api_key_here
```

### 3. Start the server

```bash
uvicorn server.app:app --reload
```

Server runs at: `http://localhost:8000`

### 4. Run the agent

```bash
python inference.py
```

---

## 🔗 API Endpoints

### `GET /tasks`
Returns available task types and their descriptions.

**Response:**
```json
{
  "tasks": {
    "task1": "Severity Classification  → SeverityLevel enum",
    "task2": "Root Cause Category     → RootCauseCategory enum",
    "task3": "Recommended Action      → RecommendedAction enum"
  }
}
```

---

### `POST /reset`
Resets the environment and returns a new incident for the agent to triage.

**Query Params:**

| Param | Type | Required | Description |
|---|---|---|---|
| `task_type` | string | No | Filter by `task1`, `task2`, or `task3`. If omitted, picks any incident randomly. |

**Example:**
```bash
curl -X POST "http://localhost:8000/reset?task_type=task1"
```

**Response:**
```json
{
  "incident_id": "INC-001",
  "task_type": "task1",
  "alert_text": "[CRITICAL] Payment service returning HTTP 503. Error rate: 94%.",
  "context": {
    "service": "payment-service",
    "error_rate_pct": 94,
    "affected_users": 120000,
    "region": "us-east-1"
  }
}
```

---

### `POST /step`
Submits the agent's action and returns a graded result.

**Request Body:**
```json
{
  "incident_id": "INC-001",
  "task_type": "task1",
  "severity": "SEV1",
  "root_cause": null,
  "action": null
}
```

> Only populate the field relevant to the `task_type`. Set others to `null`.

**Response:**
```json
{
  "incident_id": "INC-001",
  "task_type": "task1",
  "reward": 1.0,
  "correct": true,
  "ground_truth": "SEV1",
  "agent_answer": "SEV1"
}
```

| Field | Type | Description |
|---|---|---|
| `reward` | float | `1.0` = correct, `0.0` = wrong |
| `correct` | bool | True if reward == 1.0 |
| `ground_truth` | string | Expected answer |
| `agent_answer` | string | What agent returned |

---

### `GET /grader`
Returns grader configuration for transparency.

**Response:**
```json
{
  "grading": "deterministic",
  "scoring": "binary (0.0 or 1.0)",
  "tasks": {
    "task1": "action.severity   == ground_truth.severity",
    "task2": "action.root_cause == ground_truth.root_cause",
    "task3": "action.action     == ground_truth.action"
  }
}
```

---

## 📋 Enum Reference

All agent outputs must use **exactly** these enum values (case-sensitive):

### Task 1 — Severity Classification (`severity` field)

| Value | Meaning |
|---|---|
| `SEV1` | Total outage / confirmed revenue impact |
| `SEV2` | Partial outage / degraded performance |
| `SEV3` | Minor / cosmetic / internal only |

### Task 2 — Root Cause Category (`root_cause` field)

| Value | Meaning |
|---|---|
| `DATABASE` | DB lag, connection pool, replica issues |
| `NETWORK` | Packet loss, BGP flap, cross-region failures |
| `APPLICATION` | Code bug, exception, bad deploy |
| `INFRASTRUCTURE` | Kubernetes, EC2, spot interruption |
| `THIRD_PARTY` | Stripe, SendGrid, external vendor |
| `UNKNOWN` | Cannot determine root cause |

### Task 3 — Recommended Action (`action` field)

| Value | Meaning |
|---|---|
| `ROLLBACK` | Revert to last stable deploy |
| `SCALE_UP` | Increase replicas / resources |
| `RESTART_SERVICE` | Restart stuck / deadlocked process |
| `FAILOVER` | Switch to replica / standby |
| `NOTIFY_VENDOR` | Escalate to third-party vendor |
| `INVESTIGATE` | Need more info before acting |
| `NO_ACTION` | Monitor only, no action needed |

---

## 🤖 Agent JSON Format

The agent must return **strict JSON only** — no markdown, no explanation, no extra text.

```json
{
  "incident_id": "INC-006",
  "task_type": "task2",
  "severity": null,
  "root_cause": "DATABASE",
  "action": null
}
```

Rules:
- `incident_id` must match the one returned by `/reset`
- `task_type` must match the one returned by `/reset`
- Only one field (`severity`, `root_cause`, or `action`) should be non-null
- The non-null field must use a valid enum value

---

## 🧠 How Grading Works

Grading is **fully deterministic** — no LLM is used inside the grader.

```
agent_answer == ground_truth  →  reward: 1.0  (correct)
agent_answer != ground_truth  →  reward: 0.0  (wrong)
missing field (null)          →  reward: 0.0  (wrong)
```

Scoring is binary because incident triage is a classification task. A wrong severity leads to a wrong on-call response — partial credit would mask bad agent behavior.

---

## 🧪 Quick Test (curl)

```bash
# 1. Check available tasks
curl http://localhost:8000/tasks

# 2. Get a task1 incident
curl -X POST "http://localhost:8000/reset?task_type=task1"

# 3. Submit agent action (replace incident_id with one from step 2)
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"incident_id": "INC-001", "task_type": "task1", "severity": "SEV1", "root_cause": null, "action": null}'

# 4. Check grader config
curl http://localhost:8000/grader
```

---

## 📊 Dataset Overview

15 production incidents across 3 task types (5 per task):

| Task | Incidents | What agent classifies |
|---|---|---|
| `task1` | INC-001 to INC-005 | Severity level |
| `task2` | INC-006 to INC-010 | Root cause category |
| `task3` | INC-011 to INC-015 | Recommended action |

Incident types include: payment outages, DB replica lag, Kubernetes node failures, BGP flapping, bad deploys, vendor degradations, memory deadlocks, and more.

---

## 🔧 Inference Script (Mistral via NVIDIA API)

`inference.py` uses the Mistral model via NVIDIA's OpenAI-compatible API endpoint.

Update the client in `inference.py`:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.environ["NVIDIA_API_KEY"]
)

response = client.chat.completions.create(
    model="mistralai/mistral-7b-instruct-v0.3",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(observation)}
    ],
    max_tokens=256,
    temperature=0.0
)

raw = response.choices[0].message.content.strip()
```

> `temperature=0.0` is critical — keeps outputs deterministic across runs.

---

## 📦 Requirements

```
fastapi
uvicorn
pydantic
openai
requests
```

Install:
```bash
pip install fastapi uvicorn pydantic openai requests
```

---

## 🚀 Run Full Evaluation

```bash
# Terminal 1
uvicorn server.app:app --reload

# Terminal 2
python inference.py
```

Expected output:
```
==================================================
Incident : INC-003
Task     : task1
Alert    : [INFO] Admin dashboard CSS assets returning 404...

LLM Raw  : {"incident_id": "INC-003", "task_type": "task1", "severity": "SEV3", "root_cause": null, "action": null}
Answer   : SEV3
Expected : SEV3
Correct  : True  |  Reward: 1.0

==================================================
Total Episodes : 15
Total Correct  : 13
Accuracy       : 86.7%
```

---

## 📝 Important Rules

- Never modify enum values in `models.py` — graders depend on exact string matching
- Never add LLM calls inside `graders.py` — grading must be deterministic
- Always call `/reset` before `/step` — environment maintains current incident state
- `server/__init__.py` must stay empty — do not add imports there
- Always run uvicorn from the project root: `uvicorn server.app:app --reload`