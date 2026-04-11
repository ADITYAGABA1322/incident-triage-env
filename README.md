---
title: Incident Triage Env
colorFrom: gray
colorTo: blue
sdk: docker
app_port: 7860
license: mit
short_description: OpenEnv-compatible incident triage evaluation environment.
---

# Production Incident Triage Environment

This project is an OpenEnv-compatible evaluation environment for production incident response. An agent receives a typed incident observation and must perform one of three real-world triage tasks: classify severity, identify the most likely root cause, or recommend the best immediate action.

The environment is built for the OpenEnv hackathon requirements:
- real-world utility
- three graded tasks with easy, medium, and hard difficulty
- typed observation, action, reward, and state models
- deterministic reward logic with partial credit
- root-level `inference.py`
- Docker-based deployment for Hugging Face Spaces

## Overview

The dataset contains 36 incidents across three task families:

| Task | Difficulty | Count | Objective |
|---|---|---:|---|
| `task1` | easy | 11 | Predict incident severity as `SEV1`, `SEV2`, or `SEV3` |
| `task2` | medium | 12 | Predict the most likely root cause domain |
| `task3` | hard | 13 | Predict the best immediate operational action |

The incidents cover realistic production scenarios such as payment failures, queue backlogs, regional network loss, failed deploys, infrastructure saturation, third-party degradation, and failover decisions.

## API

The FastAPI app exposes the following endpoints on port `7860`:

- `GET /health`
- `GET /metadata`
- `GET /tasks`
- `GET /grader`
- `GET /schema`
- `POST /reset`
- `POST /step`
- `GET /state`
- `POST /mcp`

### Reset

`POST /reset` starts a new single-step episode.

Optional request body:

```json
{
  "task_type": "task1",
  "ticket_id": "INC-001",
  "seed": 42
}
```

Response fields:
- `observation`
- `reward`
- `done`
- `info`

### Step

`POST /step?session_id=<id>` accepts an `IncidentAction` and returns a typed `StepResult`.

Example request:

```json
{
  "incident_id": "INC-001",
  "task_type": "task1",
  "severity": "SEV1"
}
```

### State

`GET /state?session_id=<id>` returns the current typed `IncidentState`.

## Web UI

The project also serves a browser-facing UI from the same FastAPI app:

- `/` shows the landing page with project overview and task summary
- `/status` shows live health, schema, and task readiness information
- `/playground` lets you manually reset a session and submit a step from the browser
- `/docs` provides the generated FastAPI API reference

## Models

The core models are defined in [models.py](/Users/adityagaba/Downloads/incident-triage-env/models.py):

- `IncidentObservation`
- `IncidentAction`
- `IncidentReward`
- `StepResult`
- `IncidentState`
- `ResetRequest`

Validation rules:
- `incident_id` must match the active ticket
- `task_type` must match the active ticket
- exactly one of `severity`, `root_cause`, or `action` must be populated
- the populated field must match the expected field for the task

## Reward Logic

Rewarding is deterministic and implemented in [graders.py](/Users/adityagaba/Downloads/incident-triage-env/graders.py).

- `task1`: `1.0` exact, `0.5` adjacent severity, `0.0` far miss
- `task2`: `1.0` exact, `0.5` related domain, `0.25` `UNKNOWN`, `0.0` wrong
- `task3`: `1.0` exact, `0.4` safe `INVESTIGATE` fallback, `0.25` related action, `0.0` wrong

This keeps grading reproducible while still giving partial-credit trajectory signal.

## Repository Layout

```text
incident-triage-env/
- app.py
- client.py
- environment.py
- graders.py
- incidents.py
- inference.py
- models.py
- openenv.yaml
- pyproject.toml
- requirements.txt
- Dockerfile
- README.md
- server/
- tests/
```

Runtime flow:
1. `incidents.py` stores the ticket dataset.
2. `environment.py` selects the episode and applies grading.
3. `app.py` exposes the API surface.
4. `inference.py` runs the baseline over the environment.
5. `graders.py` calculates deterministic reward and explanations.

## Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional OpenEnv CLI:

```bash
pip install openenv-core
```

Optional environment variables for `inference.py`:

```bash
export API_BASE_URL="https://your-openai-compatible-endpoint/v1"
export MODEL_NAME="your-model-name"
export HF_TOKEN="your-api-key"
export ENV_URL="http://localhost:7860"
```

If no external environment server is reachable, `inference.py` falls back to an in-process FastAPI client.

## Run Locally

Start the server:

```bash
uvicorn app:app --host 0.0.0.0 --port 7860
```

Run the baseline:

```bash
python inference.py
```

Run the smoke tests:

```bash
python -m unittest discover -s tests -v
```

## Docker

Build the image:

```bash
docker build -t incident-triage-env .
```

Run the container:

```bash
docker run --rm -p 7860:7860 incident-triage-env
```

Check health:

```bash
curl http://localhost:7860/health
```

## Baseline Logging

`inference.py` prints the required structured output:

```text
[START] task=INC-001 env=incident-triage-env model=deterministic-baseline
[STEP] step=1 action=SEV1 reward=1.00 done=true error=null
[END] success=true steps=1 score=1.00 rewards=1.00
```

## Baseline Scores

Latest local deterministic baseline:

| Metric | Value |
|---|---:|
| Episodes | 36 |
| Average score | 0.9861 |
| `task1` average | 1.0000 |
| `task2` average | 0.9583 |
| `task3` average | 1.0000 |

These results are written to `outputs/baseline_scores.json`.

## Quick API Example

Reset:

```bash
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_type":"task1","ticket_id":"INC-001"}'
```

Step:

```bash
curl -X POST "http://localhost:7860/step?session_id=<session-id>" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "INC-001",
    "task_type": "task1",
    "severity": "SEV1"
  }'
```

## Pre-Submission Checklist

- `openenv validate . --json` passes
- `openenv validate --url <space-url>` passes
- `POST /reset` returns `200`
- `POST /step` returns typed `reward`, `done`, and `info`
- `GET /state` works for active sessions
- `inference.py` runs from the repo root
- `Dockerfile` serves the app on port `7860`
- `openenv.yaml` matches the current API and dataset counts

## Notes

- `models.py` is the source of truth for valid enum labels.
- `graders.py` is the source of truth for scoring logic.
- The environment is intentionally single-step per episode and still exposes typed state for validation and debugging.
