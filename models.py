#----- Edited file--------------

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, Dict


# ── Enums ─────────────────────────────────────────────

class SeverityLevel(str, Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"


class RootCauseCategory(str, Enum):
    DATABASE       = "DATABASE"
    NETWORK        = "NETWORK"
    APPLICATION    = "APPLICATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    THIRD_PARTY    = "THIRD_PARTY"
    UNKNOWN        = "UNKNOWN"


class RecommendedAction(str, Enum):
    ROLLBACK        = "ROLLBACK"
    SCALE_UP        = "SCALE_UP"
    RESTART_SERVICE = "RESTART_SERVICE"
    FAILOVER        = "FAILOVER"
    NOTIFY_VENDOR   = "NOTIFY_VENDOR"
    INVESTIGATE     = "INVESTIGATE"
    NO_ACTION       = "NO_ACTION"


# ── Observation (Input to Agent) ──────────────────────

class IncidentObservation(BaseModel):
    incident_id: str
    task_type: str   # "task1" | "task2" | "task3"
    alert_text: str
    context: Dict


# ── Action (Output from Agent) ────────────────────────

class IncidentAction(BaseModel):
    incident_id: str
    task_type: str

    severity:   Optional[SeverityLevel]     = Field(None)
    root_cause: Optional[RootCauseCategory] = Field(None)
    action:     Optional[RecommendedAction] = Field(None)


# ── Step Result ───────────────────────────────────────

class StepResult(BaseModel):
    incident_id: str
    task_type: str
    reward: float
    correct: bool
    ground_truth: str
    agent_answer: str
    
    
