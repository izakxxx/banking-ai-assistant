from __future__ import annotations

import json
from typing import Any

from app.capabilities.models import MultiStepExecutionPlan
from app.capabilities.registry import registry
from app.schemas.chat import ValidationResult


def parse_llm_json(raw_answer: str) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_answer)

        if isinstance(parsed, dict):
            return parsed

        return {}

    except Exception:
        return {}


def resolve_intent(
    question: str | None,
    explicit_intent: str | None = None,
) -> str:
    if explicit_intent:
        return explicit_intent

    q = (question or "").lower()

    if (
        "onboard" in q
        or "new client" in q
        or "create client" in q
        or ("savings account" in q and "client" in q and "charge" in q)
        or ("savings" in q and "client" in q and "fee" in q)
    ):
        return "onboard_client_with_savings_fee"

    if (
        "pay charge" in q
        or "pay savings charge" in q
        or "paycharge" in q
    ):
        return "pay_savings_charge"

    if (
        "monthly fee" in q
        or "maintenance fee" in q
        or "apply charge" in q
        or "savings charge" in q
    ):
        return "create_savings_monthly_fee"

    return "create_savings_monthly_fee"


def build_execution_plan(
    question: str | None,
    payload: dict[str, Any] | None,
    account_id: int | None,
    tenant_id: str = "default",
    intent: str | None = None,
) -> tuple[str, MultiStepExecutionPlan | None, ValidationResult]:
    resolved_intent = resolve_intent(
        question=question,
        explicit_intent=intent,
    )

    capability = registry.get(resolved_intent)

    if capability is None:
        return (
            resolved_intent,
            None,
            ValidationResult(
                is_valid=False,
                errors=[f"No capability registered for intent: {resolved_intent}."],
                warnings=[],
            ),
        )

    sanitized_payload = capability.sanitize(payload or {})
    validation = capability.validate(sanitized_payload)

    if not validation.is_valid:
        return resolved_intent, None, validation

    plan = capability.build_plan(
        payload=sanitized_payload,
        account_id=account_id,
        tenant_id=tenant_id,
    )

    return resolved_intent, plan, validation