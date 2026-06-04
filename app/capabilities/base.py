from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
from app.capabilities.models import MultiStepExecutionPlan
from app.schemas.chat import ValidationResult

class BaseCapability(ABC):
    intent: str = "unknown"

    @abstractmethod
    def sanitize(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def validate(self, payload: dict[str, Any]) -> ValidationResult:
        raise NotImplementedError

    @abstractmethod
    def build_plan(
        self,
        payload: dict[str, Any],
        account_id: int | None,
        tenant_id: str = "default",
    ) -> MultiStepExecutionPlan:
        raise NotImplementedError