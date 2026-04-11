# Change Log and Runbook

This file explains what changed in the project and how to run or test each part.

Project path:

```bash
cd <repo-root>
```

## 1. What changed

### Backend and OpenEnv API

The backend is still a FastAPI app, but it now behaves like a stronger OpenEnv-style environment.

Main files:

- `app.py`
- `environment.py`
- `models.py`
- `graders.py`
- `incidents.py`
- `inference.py`
- `openenv.yaml`

Important backend changes:

- Added typed request and response models for observation, action, reward, state, and reset.
- Added proper `reset`, `step`, and `state` behavior.
- Added strict action validation.
- Added deterministic graders with partial credit.
- Added runtime-validator helper endpoints:
  - `GET /health`
  - `GET /metadata`
  - `GET /schema`
  - `POST /mcp`
- Updated `inference.py` to print strict `[START]`, `[STEP]`, and `[END]` logs.

### Frontend UI

A browser UI was added on top of the same FastAPI app.

Main files:

- `ui/index.html`
- `ui/status.html`
- `ui/playground.html`
- `ui/assets/styles.css`
- `ui/assets/app.js`

New UI routes:

- `/` shows the landing page.
- `/status` shows live health, schema, tasks, and grader status.
- `/playground` lets you reset an incident and submit an action from the browser.
- `/docs` still shows FastAPI API docs.

Latest UI improvements:

- The playground has quick presets for task1, task2, and task3.
- The playground loads the real ticket inventory from `/tickets`.
- Invalid ticket IDs such as `INC-105` are blocked in the UI before calling `/reset`.
- The playground now shows visible success and error messages.
- The summary strip shows incident id, expected field, reward, and episode status.
- Cards, form controls, and output panels have more spacing and padding.
- Reset and step buttons show loading states while requests are running.

The UI is served from `app.py` with:

- `app.mount("/assets", ...)`
- `GET /`
- `GET /status`
- `GET /playground`

### Docker and Space readiness

Main files:

- `Dockerfile`
- `.dockerignore`
- `README.md`
- `openenv.yaml`
- `server/app.py`

Important changes:

- Docker runs `uvicorn app:app` on port `7860`.
- `README.md` includes Hugging Face Docker Space metadata.
- `server/app.py` is present as a compatibility entrypoint.
- `openenv validate` passes locally.
- Runtime validation was made compatible by adding `/schema`, `/mcp`, and `{"status":"healthy"}` from `/health`.

### Tests

Main files:

- `tests/test_env.py`
- `tests/test_graders.py`

Test coverage includes:

- health, schema, and MCP helper endpoints
- UI routes and static assets
- reset, step, and state behavior
- wrong task-type rejection
- grader score range checks
- partial-credit checks
- non-constant grader behavior

### Terminal logs

The backend now prints useful logs when the UI or API is used:

```text
[RESET] session_id=... incident_id=INC-014 task_type=task3 expected_field=action
[STEP] session_id=... incident_id=INC-014 task_type=task3 answer=FAILOVER reward=1.0 done=true
[STATE] session_id=... incident_id=INC-014 done=true
[STEP_ERROR] session_id=... incident_id=INC-014 error=...
```

These logs appear in the same terminal where `uvicorn` is running.

## 2. Start the backend and UI locally

Use port `8000` locally if port `7860` is busy.

```bash
cd <repo-root>
source .venv/bin/activate
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Keep that terminal open.

Open these browser URLs:

```text
http://127.0.0.1:8000/
http://127.0.0.1:8000/status
http://127.0.0.1:8000/playground
http://127.0.0.1:8000/docs
```

If you already had the server running, stop it with `Ctrl+C` and start it again. Use hard refresh in the browser if the old UI is still visible.

Expected results:

- `/` shows the Incident Triage landing page.
- `/status` shows health and task cards.
- `/playground` lets you reset and step through an incident.
- `/docs` shows generated API documentation.

## 3. Test the UI manually

### Landing page

Open:

```text
http://127.0.0.1:8000/
```

Check:

- The page title says `Welcome to Incident Triage Environment`.
- Live snapshot cards load data.
- Task cards appear.
- Links to `/status`, `/playground`, and `/docs` work.

### Status page

Open:

```text
http://127.0.0.1:8000/status
```

Check:

- Health shows `healthy`.
- Total incidents shows `36`.
- Task cards show task1, task2, and task3.
- Schema coverage shows available runtime contracts.
- Grader summary loads.

### Playground page

Open:

```text
http://127.0.0.1:8000/playground
```

Run a correct hard-task case:

1. Click the `Action case` preset, or manually select `task3`.
2. Confirm ticket id is `INC-014`.
3. Click `Reset Environment`.
4. Confirm expected field is `action`.
5. Select `FAILOVER`.
6. Click `Submit Step`.

Expected result:

- `reward.value` is `1.0`.
- `done` is `true`.
- `info.correct` is `true`.
- `info.ground_truth` is `FAILOVER`.

Important ticket rule:

- Valid tickets are `INC-001` through `INC-036`.
- `INC-105` is not in this dataset, so reset should fail for that ticket.
- The updated UI loads valid tickets from `/tickets` and warns before sending an invalid ticket to the backend.

Expected terminal logs:

```text
[RESET] session_id=... incident_id=INC-014 task_type=task3 expected_field=action
[STEP] session_id=... incident_id=INC-014 task_type=task3 answer=FAILOVER reward=1.0 done=true
```

Run a task1 case:

1. Click the `Severity case` preset, or manually select `task1`.
2. Confirm ticket id is `INC-001`.
3. Click `Reset Environment`.
4. Confirm expected field is `severity`.
5. Select `SEV1`.
6. Click `Submit Step`.

Expected result:

- reward should be `1.0`.

Run a task2 case:

1. Click the `Root cause case` preset, or manually select `task2`.
2. Confirm ticket id is `INC-006`.
3. Click `Reset Environment`.
4. Confirm expected field is `root_cause`.
5. Select `DATABASE`.
6. Click `Submit Step`.

Expected result:

- reward should be `1.0`.

## 4. Test backend API with curl

Use a second terminal while the app is running on port `8000`.

Health:

```bash
curl -s http://127.0.0.1:8000/health | python3 -m json.tool
```

Expected:

```json
{
    "status": "healthy"
}
```

Metadata:

```bash
curl -s http://127.0.0.1:8000/metadata | python3 -m json.tool
```

Schema:

```bash
curl -s http://127.0.0.1:8000/schema | python3 -m json.tool
```

Reset a fixed incident:

```bash
curl -s -X POST http://127.0.0.1:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_type":"task3","ticket_id":"INC-014"}' > /tmp/reset.json
python3 -m json.tool /tmp/reset.json
```

Extract session id:

```bash
SESSION_ID=$(python3 -c 'import json; print(json.load(open("/tmp/reset.json"))["info"]["session_id"])')
echo $SESSION_ID
```

Submit a correct step:

```bash
curl -s -X POST "http://127.0.0.1:8000/step?session_id=$SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"incident_id":"INC-014","task_type":"task3","action":"FAILOVER"}' | python3 -m json.tool
```

Check state:

```bash
curl -s "http://127.0.0.1:8000/state?session_id=$SESSION_ID" | python3 -m json.tool
```

Expected state:

- `done` is `true`
- `status` is `completed`
- `last_reward` is `1.0`

## 5. Test backend edge cases

Bad session:

```bash
curl -s -X POST "http://127.0.0.1:8000/step?session_id=bad-session" \
  -H "Content-Type: application/json" \
  -d '{"incident_id":"INC-014","task_type":"task3","action":"FAILOVER"}' | python3 -m json.tool
```

Expected:

```json
{
    "detail": "Session not found. Call /reset first."
}
```

Bad ticket:

```bash
curl -s -X POST http://127.0.0.1:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_type":"task1","ticket_id":"INC-999"}' | python3 -m json.tool
```

Expected:

```json
{
    "detail": "No ticket found for ticket_id: INC-999"
}
```

Wrong field for task3:

```bash
curl -s -X POST http://127.0.0.1:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task_type":"task3","ticket_id":"INC-014"}' > /tmp/reset_wrong_field.json

SESSION_WRONG_FIELD=$(python3 -c 'import json; print(json.load(open("/tmp/reset_wrong_field.json"))["info"]["session_id"])')

curl -s -X POST "http://127.0.0.1:8000/step?session_id=$SESSION_WRONG_FIELD" \
  -H "Content-Type: application/json" \
  -d '{"incident_id":"INC-014","task_type":"task3","root_cause":"NETWORK"}' | python3 -m json.tool
```

Expected:

```json
{
    "detail": "Task 'task3' expects field 'action', but got 'root_cause'."
}
```

## 6. Run automated tests

```bash
cd <repo-root>
.venv/bin/python -m unittest discover -s tests -v
```

Expected:

```text
OK
```

## 7. Run OpenEnv local validation

```bash
cd <repo-root>
.venv/bin/openenv validate . --json
```

Expected:

```json
"passed": true
```

## 8. Run the baseline inference script

If the local app is running on port `8000`:

```bash
cd <repo-root>
ENV_URL=http://127.0.0.1:8000 .venv/bin/python inference.py
```

Expected log format:

```text
[START] task=INC-001 env=incident-triage-env model=...
[STEP] step=1 action=SEV1 reward=1.00 done=true error=null
[END] success=true steps=1 score=1.00 rewards=1.00
```

If no server is reachable, `inference.py` falls back to an in-process FastAPI client.

## 9. Docker commands

If `docker` is available on PATH:

```bash
docker build -t incident-triage-env .
docker run --rm -p 8001:7860 incident-triage-env
```

If using Docker Desktop on macOS and `docker` is not on PATH:

```bash
export PATH=/Applications/Docker.app/Contents/Resources/bin:$PATH
/Applications/Docker.app/Contents/Resources/bin/docker build -t incident-triage-env .
/Applications/Docker.app/Contents/Resources/bin/docker run --rm -p 8001:7860 incident-triage-env
```

Then test:

```bash
curl -s http://127.0.0.1:8001/health | python3 -m json.tool
curl -s -X POST http://127.0.0.1:8001/reset -H "Content-Type: application/json" -d '{}' | python3 -m json.tool
```

Open Docker UI routes:

```text
http://127.0.0.1:8001/
http://127.0.0.1:8001/status
http://127.0.0.1:8001/playground
http://127.0.0.1:8001/docs
```

Expected:

- `/health` returns `{"status": "healthy"}`
- `/reset` returns `observation`, `reward`, `done`, and `info`
- `/` shows the landing page
- `/status` shows the live dashboard
- `/playground` lets you test incidents from the browser

## 10. Live Hugging Face Space validation

Replace `<space-url>` with the actual public URL:

```bash
curl -s <space-url>/health | python3 -m json.tool
curl -s -X POST <space-url>/reset -H "Content-Type: application/json" -d '{}' | python3 -m json.tool
.venv/bin/openenv validate --url <space-url> --timeout 10
```

Expected:

- `/health` returns `{"status": "healthy"}`
- `/reset` returns `200` with a typed environment response
- `openenv validate --url` returns `"passed": true`

## 11. Common issues

### Port 7860 is busy

Use port `8000` locally:

```bash
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

### Root URL returns Not Found

This should no longer happen after the UI change. The root route `/` now serves the landing page.

### Playground says session not found

Click `Reset Environment` first, then submit a step.

### Wrong task errors happen after completion

Each episode is single-step. To test validation errors, reset a fresh session first.

### Docker credential helper error

Run:

```bash
export PATH=/Applications/Docker.app/Contents/Resources/bin:$PATH
```

Then retry the Docker command.
