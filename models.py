from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    TASK1 = "task1"
    TASK2 = "task2"
    TASK3 = "task3"


class SeverityLevel(str, Enum):
    SEV1 = "SEV1"
    SEV2 = "SEV2"
    SEV3 = "SEV3"


class RootCauseCategory(str, Enum):
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    APPLICATION = "APPLICATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    THIRD_PARTY = "THIRD_PARTY"
    UNKNOWN = "UNKNOWN"


class RecommendedAction(str, Enum):
    ROLLBACK = "ROLLBACK"
    SCALE_UP = "SCALE_UP"
    RESTART_SERVICE = "RESTART_SERVICE"
    FAILOVER = "FAILOVER"
    NOTIFY_VENDOR = "NOTIFY_VENDOR"
    INVESTIGATE = "INVESTIGATE"
    NO_ACTION = "NO_ACTION"


class IncidentObservation(BaseModel):
    incident_id: str
    task_type: TaskType
    difficulty: str
    task_description: str
    alert_text: str
    context: Dict[str, Any]
    expected_field: str
    allowed_values: List[str] = Field(default_factory=list)
    step_count: int = 0
    max_steps: int = 1
    last_action_summary: Optional[str] = None
    last_reward: float = Field(default=0.01, gt=0.0, lt=1.0)
    episode_status: str = "awaiting_action"


class IncidentAction(BaseModel):
    incident_id: str
    task_type: TaskType
    severity: Optional[SeverityLevel] = Field(None)
    root_cause: Optional[RootCauseCategory] = Field(None)
    action: Optional[RecommendedAction] = Field(None)

    def populated_fields(self) -> Dict[str, str]:
        fields: Dict[str, str] = {}
        if self.severity is not None:
            fields["severity"] = self.severity.value
        if self.root_cause is not None:
            fields["root_cause"] = self.root_cause.value
        if self.action is not None:
            fields["action"] = self.action.value
        return fields

    def selected_field(self) -> Optional[str]:
        populated = self.populated_fields()
        if len(populated) != 1:
            return None
        return next(iter(populated))

    def selected_value(self) -> Optional[str]:
        selected = self.selected_field()
        if selected is None:
            return None
        return self.populated_fields()[selected]


class IncidentReward(BaseModel):
    value: float = Field(..., gt=0.0, lt=1.0)
    reason: str


class StepResult(BaseModel):
    observation: IncidentObservation
    reward: IncidentReward
    done: bool
    info: Dict[str, Any] = Field(default_factory=dict)


class IncidentState(BaseModel):
    episode_id: str
    session_id: Optional[str] = None
    step_count: int
    max_steps: int
    total_reward: float = Field(default=0.01, gt=0.0, lt=1.0)
    done: bool
    incident_id: str
    task_type: TaskType
    difficulty: str
    status: str
    last_reward: float = Field(default=0.01, gt=0.0, lt=1.0)


class ResetRequest(BaseModel):
    task_type: Optional[TaskType] = None
    ticket_id: Optional[str] = None
    seed: Optional[int] = None
