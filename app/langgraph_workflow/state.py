from __future__ import annotations

from typing import Any, TypedDict

from app.capabilities.models import MultiStepExecutionPlan


class FineractAgentState(TypedDict, total=False):
    session_id: str
    question: str
    initial_payload: dict[str, Any]
    account_id: int | None
    tenant_id: str

    intent: str | None
    execution_plan: MultiStepExecutionPlan | None
    validation: dict[str, Any] | None

    command: str | None

    approval_required: bool
    approved: bool

    execution_result: dict[str, Any] | None
    final_answer: str