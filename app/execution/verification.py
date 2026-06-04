from __future__ import annotations

from typing import Any

from app.capabilities.models import ExecutionStep


class VerificationTracker:
    def __init__(self) -> None:
        self._summary: dict[str, bool] = {}

    def mark_success(self, step: ExecutionStep) -> None:
        if step.is_verification:
            self._summary[step.action] = True

    def mark_failure(self, step: ExecutionStep) -> None:
        if step.is_verification:
            self._summary[step.action] = False

    def get_summary(self) -> dict[str, bool]:
        return self._summary.copy()