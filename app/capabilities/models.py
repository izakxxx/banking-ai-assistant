from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel


class ExecutionStep(BaseModel):
    step: int
    action: str

    # Tool-based execution
    tool: Optional[str] = None

    # REST execution fallback / resolved execution
    method: Optional[str] = None
    endpoint: Optional[str] = None

    payload: dict[str, Any] = {}

    description: Optional[str] = None
    curl: Optional[str] = None

    depends_on: list[int] = []
    output_mapping: dict[str, str] = {}
    is_verification: bool = False


class MultiStepExecutionPlan(BaseModel):
    intent: str
    steps: list[ExecutionStep]


class CapabilityResult(BaseModel):
    intent: str
    plan: MultiStepExecutionPlan
    validation_errors: list[str] = []
    validation_warnings: list[str] = []