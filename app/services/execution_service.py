from __future__ import annotations

import json
from typing import Any

from app.capabilities.models import MultiStepExecutionPlan
from app.capabilities.registry import registry
from app.schemas.chat import ValidationResult
from app.retrieval.hybrid_retriever import hybrid_retrieve
from app.services.openai_service import ask_llm_execution_payload_with_context


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


def build_retrieval_context(question: str, top_k: int = 5) -> str:
    results = hybrid_retrieve(question, top_k=top_k)

    if not results:
        return ""

    return "\n\n---\n\n".join(
        f"doc_id={r.get('doc_id')} chunk_id={r.get('chunk_id')} score={r.get('score')}\n"
        f"{r.get('snippet')}"
        for r in results
    )


def build_retrieval_context(question: str, top_k: int = 5) -> str:
    results = hybrid_retrieve(question, top_k=top_k)

    if not results:
        return ""

    return "\n\n---\n\n".join(
        f"doc_id={r.get('doc_id')} chunk_id={r.get('chunk_id')} score={r.get('score')}\n"
        f"{r.get('snippet')}"
        for r in results
    )


def build_plan_with_llm_payload(
    question: str | None,
    payload: dict[str, Any] | None,
    account_id: int | None,
    tenant_id: str,
    explicit_intent: str | None,
) -> tuple[str, dict[str, Any]]:
    if explicit_intent:
        return explicit_intent, payload or {}

    if not question:
        return resolve_intent(question=None), payload or {}

    q = question.strip().lower()

    if q in {"execute", "run", "confirm", "approve"}:
        return resolve_intent(question=question), payload or {}

    context = build_retrieval_context(question)
    raw_answer = ask_llm_execution_payload_with_context(question, context)

    print("RAW LLM RESPONSE:")
    print(raw_answer)

    parsed = parse_llm_json(raw_answer)

    print("PARSED LLM JSON:")
    print(parsed)

    llm_intent = parsed.get("intent")
    llm_payload = parsed.get("payload")

    if not isinstance(llm_intent, str):
        llm_intent = resolve_intent(question)

    if not isinstance(llm_payload, dict):
        llm_payload = {}

    merged_payload = {
        **(payload or {}),
        **llm_payload,
    }

    return llm_intent, merged_payload



def build_execution_plan(
    question: str | None,
    payload: dict[str, Any] | None,
    account_id: int | None,
    tenant_id: str = "default",
    intent: str | None = None,
) -> tuple[str, MultiStepExecutionPlan | None, ValidationResult]:
    resolved_intent, effective_payload = build_plan_with_llm_payload(
        question=question,
        payload=payload,
        account_id=account_id,
        tenant_id=tenant_id,
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

    sanitized_payload = capability.sanitize(effective_payload or {})
    validation = capability.validate(sanitized_payload)

    if not validation.is_valid:
        return resolved_intent, None, validation

    plan = capability.build_plan(
        payload=sanitized_payload,
        account_id=account_id,
        tenant_id=tenant_id,
    )

    return resolved_intent, plan, validation