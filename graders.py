from models import IncidentAction

_SEV_ORDER = {"SEV1": 0, "SEV2": 1, "SEV3": 2}
# Related-domain partial credit is intentionally conservative.
# DATABASE <-> APPLICATION captures incidents where app bugs manifest as
# database saturation and vice versa.
# NETWORK <-> INFRASTRUCTURE captures physical or platform-layer correlation.
# NETWORK <-> THIRD_PARTY captures dependency outages that resemble network loss.
# INFRASTRUCTURE <-> THIRD_PARTY captures external services failing through shared
# platform primitives.
# APPLICATION <-> THIRD_PARTY is intentionally not included because we treat
# product-code failures and vendor degradation as materially different diagnoses.
_TASK2_RELATED_GROUPS = [
    {"DATABASE", "APPLICATION"},
    {"NETWORK", "INFRASTRUCTURE"},
    {"NETWORK", "THIRD_PARTY"},
    {"INFRASTRUCTURE", "THIRD_PARTY"},
]
_TASK3_PARTIAL = {
    ("RESTART_SERVICE", "FAILOVER"): 0.25,
    ("FAILOVER", "RESTART_SERVICE"): 0.25,
    ("NOTIFY_VENDOR", "INVESTIGATE"): 0.25,
    ("SCALE_UP", "INVESTIGATE"): 0.25,
    ("RESTART_SERVICE", "INVESTIGATE"): 0.25,
}


def grade_task1(action: IncidentAction, ground_truth: dict) -> tuple[float, str]:
    if action.severity is None:
        return 0.0, "Missing severity classification."
    predicted = _SEV_ORDER.get(action.severity.value, -1)
    expected = _SEV_ORDER.get(ground_truth["severity"], -1)
    distance = abs(predicted - expected)
    score = {0: 1.0, 1: 0.5, 2: 0.0}[distance]
    if score == 1.0:
        return score, "Exact severity match."
    if score == 0.5:
        return score, "Adjacent severity band: partial credit for a close escalation call."
    return score, "Severity choice is too far from the ground truth."


def grade_task2(action: IncidentAction, ground_truth: dict) -> tuple[float, str]:
    if action.root_cause is None:
        return 0.0, "Missing root-cause classification."

    predicted = action.root_cause.value
    expected = ground_truth["root_cause"]

    if predicted == expected:
        return 1.0, "Exact root-cause match."
    if predicted == "UNKNOWN":
        return 0.25, "Conservative fallback: uncertainty recognized, but the failure domain was not isolated."
    if any({predicted, expected} == group for group in _TASK2_RELATED_GROUPS):
        return 0.5, "Related failure domain selected: partial credit for a near-miss diagnosis."
    return 0.0, "Root-cause classification does not match the expected failure domain."


def grade_task3(action: IncidentAction, ground_truth: dict) -> tuple[float, str]:
    if action.action is None:
        return 0.0, "Missing remediation recommendation."

    predicted = action.action.value
    expected = ground_truth["action"]

    if predicted == expected:
        return 1.0, "Exact remediation match."
    if predicted == "INVESTIGATE" and expected != "NO_ACTION":
        return 0.4, "Safe investigative fallback: the incident was recognized, but the optimal action was not taken."
    if predicted == "NO_ACTION" and expected == "INVESTIGATE":
        return 0.25, "Conservative response, but deeper investigation was expected."
    if (predicted, expected) in _TASK3_PARTIAL:
        return _TASK3_PARTIAL[(predicted, expected)], "Related remediation selected: partial credit for a close operational response."
    return 0.0, "Recommended action does not match the expected operator response."


GRADERS = {
    "task1": grade_task1,
    "task2": grade_task2,
    "task3": grade_task3,
}
