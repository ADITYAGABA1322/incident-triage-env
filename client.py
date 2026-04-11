"""Lightweight HTTP client for the current FastAPI incident triage server."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

try:
    from .models import IncidentAction, IncidentState, StepResult
except ImportError:
    from models import IncidentAction, IncidentState, StepResult


class IncidentTriageClient:
    """Small helper for calling the local FastAPI endpoints from scripts or notebooks."""

    def __init__(self, base_url: str = "http://localhost:7860", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def __enter__(self) -> "IncidentTriageClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        self.session.close()

    def tasks(self) -> Dict[str, Any]:
        return self._request("GET", "/tasks")

    def grader_info(self) -> Dict[str, Any]:
        return self._request("GET", "/grader")

    def reset(
        self,
        task_type: Optional[str] = None,
        ticket_id: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> StepResult:
        return StepResult(
            **self._request(
                "POST",
                "/reset",
                json={
                    "task_type": task_type,
                    "ticket_id": ticket_id,
                    "seed": seed,
                },
            )
        )

    def state(self, session_id: str) -> IncidentState:
        return IncidentState(
            **self._request("GET", "/state", params={"session_id": session_id})
        )

    def step(self, session_id: str, action: IncidentAction | Dict[str, Any]) -> StepResult:
        payload = action.model_dump() if isinstance(action, IncidentAction) else action
        result = self._request(
            "POST",
            "/step",
            params={"session_id": session_id},
            json=payload,
        )
        return StepResult(**result)

    def _request(self, method: str, path: str, **kwargs: Any) -> Dict[str, Any]:
        response = self.session.request(
            method=method,
            url=f"{self.base_url}{path}",
            timeout=self.timeout,
            **kwargs,
        )
        response.raise_for_status()
        return response.json()
