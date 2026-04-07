# inference.py

import os
import json
import re
import requests
from openai import OpenAI
from incidents import TICKETS
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://localhost:8000"
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

SYSTEM_PROMPT = """You are an expert SRE (Site Reliability Engineer) triaging production incidents.
You will receive an incident alert and context.
You must respond with ONLY a valid JSON object. No explanation. No markdown. No extra text. No code blocks.

Rules:
- For task1: classify severity. Choose ONLY from: SEV1, SEV2, SEV3
- For task2: classify root cause. Choose ONLY from: DATABASE, NETWORK, APPLICATION, INFRASTRUCTURE, THIRD_PARTY, UNKNOWN
- For task3: recommend action. Choose ONLY from: ROLLBACK, SCALE_UP, RESTART_SERVICE, FAILOVER, NOTIFY_VENDOR, INVESTIGATE, NO_ACTION

Response format (return this exact structure):
{"incident_id": "<incident_id>", "task_type": "<task_type>", "severity": "<value or null>", "root_cause": "<value or null>", "action": "<value or null>"}

Only populate the field relevant to the task_type. Set others to null.
"""


def build_user_prompt(observation: dict) -> str:
    return f"""Incident ID: {observation['incident_id']}
Task Type: {observation['task_type']}

Alert:
{observation['alert_text']}

Context:
{json.dumps(observation['context'], indent=2)}

Respond with JSON only. No markdown. No explanation."""


# 🔥 Robust JSON extractor
def extract_json(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON found in response")

    return json.loads(match.group(0))

def normalize_action(action: dict, task_type: str) -> dict:
    return {
        "incident_id": action.get("incident_id"),
        "task_type": task_type,
        "severity": action.get("severity") if task_type == "task1" else None,
        "root_cause": action.get("root_cause") if task_type == "task2" else None,
        "action": action.get("action") if task_type == "task3" else None,
    }


def call_llm(observation: dict) -> str:
    full_response = ""
    try:
        completion = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct-v0.3",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_prompt(observation)}
            ],
            temperature=0.1,
            top_p=0.9,
            max_tokens=200,
            seed=42,
            stream=True
        )

        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content is not None:
                full_response += chunk.choices[0].delta.content
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return ""

    return full_response.strip()


def run_episode(task_type: str = None) -> dict:
    # Step 1 — Reset environment
    params = {"task_type": task_type} if task_type else {}
    reset_response = requests.post(f"{BASE_URL}/reset", params=params)
    reset_response.raise_for_status()
    
    reset_data = reset_response.json()
    session_id = reset_data["session_id"]  
    observation = reset_data

    print(f"\n{'='*60}")
    print(f"Incident : {observation['incident_id']}")
    print(f"Task     : {observation['task_type']}")
    print(f"Alert    : {observation['alert_text'][:80]}...")

    # Step 2 — LLM with retry
    action = None
    raw = ""
    
    for attempt in range(3):
        raw = call_llm(observation)
        print(f"LLM Raw (attempt {attempt+1}): {raw}")

        try:
            parsed = extract_json(raw)
            action = normalize_action(parsed, observation["task_type"])
            break
        except Exception as e:
            print(f"Parse failed: {e}")
            
    if not action:
        return {"error": "invalid_json", "raw": raw}
    
        # Step 3 — Validate schema
    required_keys = {"incident_id", "task_type", "severity", "root_cause", "action"}
    if not required_keys.issubset(action.keys()):
        print("Invalid schema from LLM")
        return {"error": "invalid_schema", "raw": raw}
   

    # Step 4 — Submit to /step
    step_response = requests.post(f"{BASE_URL}/step", json=action, params={"session_id": session_id})
    step_response.raise_for_status()
    result = step_response.json()

    print(f"Answer   : {result['agent_answer']}")
    print(f"Expected : {result['ground_truth']}")
    print(f"Correct  : {result['correct']}  |  Reward: {result['reward']}")

    # 🔥 Logging
    with open("logs.jsonl", "a") as f:
        f.write(json.dumps({
            "observation": observation,
            "response": action,
            "result": result
        }) + "\n")
        
    return result


def run_full_eval():
    task_types = ["task1", "task2", "task3"]
    
    rounds = len(TICKETS) * 3  # 🔥 FIXED
    scores = []
    errors = 0

    task_scores = {
        "task1": [],
        "task2": [],
        "task3": []
    }
    
    for i in range(rounds):
        task = task_types[i % 3]
        result = run_episode(task_type=task)

        if "reward" in result:
            scores.append(result["reward"])
            task_scores[task].append(result["reward"])
        else:
            errors += 1

    print(f"\n{'='*60}")
    print(f"Total Episodes : {rounds}")
    print(f"Graded         : {len(scores)}")
    print(f"JSON Errors    : {errors}")
    if scores:
        print(f"Total Reward : {sum(scores)}")
        print(f"Average Reward : {sum(scores)/len(scores):.2f}")
        print(f"Overall Accuracy : {sum(scores)/len(scores)*100:.2f}%")

        for task in task_scores:
            if task_scores[task]:
                acc = sum(task_scores[task]) / len(task_scores[task]) * 100
                print(f"{task} Accuracy : {acc:.2f}%")


if __name__ == "__main__":
    run_full_eval()