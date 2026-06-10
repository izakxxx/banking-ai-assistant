from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.validators.models import PreValidationResult


class BasePreExecutionValidator(ABC):
    intent: str = "unknown"

    @abstractmethod
    def validate(
        self,
        payload: dict[str, Any],
        account_id: int | None,
        tenant_id: str = "default",
    ) -> PreValidationResult:
        raise NotImplementedError