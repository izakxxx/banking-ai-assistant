from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class ExecutionStep(BaseModel):
    step: int
    action: str
    payload: dict[str, Any]

    method: Optional[str] = None
    endpoint: Optional[str] = None
    tool: Optional[str] = None

    description: Optional[str] = None
    curl: Optional[str] = None
    depends_on: Optional[list[int]] = None
    output_mapping: Optional[dict[str, str]] = None
    is_verification: bool = False


class MultiStepExecutionPlan(BaseModel):
    intent: str
    steps: list[ExecutionStep]


class CapabilityResult(BaseModel):
    intent: str
    plan: MultiStepExecutionPlan
    validation_errors: list[str] = []
    validation_warnings: list[str] = []