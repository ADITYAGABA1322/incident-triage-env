# heuristic_selftest.py  (new file — run once to validate)
from inference import heuristic_action
from incidents import TICKETS

correct = 0
for ticket in TICKETS:
    obs = {
        "incident_id": ticket["incident_id"],
        "task_type": ticket["task_type"],
        "alert_text": ticket["alert_text"],
        "context": ticket["context"],
    }
    prediction = heuristic_action(obs)
    gt = ticket["ground_truth"]
    field = list(gt.keys())[0]
    predicted_val = prediction.get(field)
    expected_val = gt[field]
    match = predicted_val == expected_val
    if not match:
        print(f"MISS {ticket['incident_id']}: predicted={predicted_val}, expected={expected_val}")
    else:
        correct += 1

print(f"\nHeuristic accuracy: {correct}/{len(TICKETS)} ({100*correct/len(TICKETS):.1f}%)")