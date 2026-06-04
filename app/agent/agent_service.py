from __future__ import annotations

from app.agent.session_store import session_store
from app.agent.input_parser import parse_user_inputs
from app.services.execution_service import build_execution_plan
from app.schemas.chat import ValidationResult


def extract_missing(validation: ValidationResult) -> list[str]:
    missing = []
    for e in validation.errors:
        if e.startswith("Missing "):
            missing.append(e.replace("Missing ", "").replace(".", ""))
    return missing


def run_agent(
    session_id: str,
    question: str,
    initial_payload: dict,
    account_id: int | None,
    tenant_id: str,
):
    session = session_store.get(session_id)

    # Caso 1: nueva conversación
    if not session:
        parsed = parse_user_inputs(question)
        merged_payload = {
            **(initial_payload or {}),
            **parsed,
        }

        intent, plan, validation = build_execution_plan(
            question=question,
            payload=merged_payload,
            account_id=account_id,
            tenant_id=tenant_id,
        )

        missing = extract_missing(validation)

        if missing:
            session_store.set(session_id, {
                "intent": intent,
                "payload": merged_payload,
                "missing": missing,
            })

            return {
                "status": "needs_input",
                "missing_inputs": missing,
            }

        if plan is None:
            return {
                "status": "error",
                "message": f"Could not build execution plan for intent: {intent}",
                "validation_errors": validation.errors,
            }

        session_store.set(session_id, {
            "intent": intent,
            "payload": merged_payload,
            "execution_plan": plan.model_dump(),
            "status": "confirm_required",
        })

        return {
            "status": "confirm_required",
            "message": "Execution plan is ready. Confirm if you want to run dry-run or execute.",
            "execution_plan": plan,
        }

    # Caso 2: ya hay sesión → completar datos
    parsed = parse_user_inputs(question)

    session["payload"].update(parsed)

    intent = session["intent"]

    _, plan, validation = build_execution_plan(
        question=None,
        payload=session["payload"],
        account_id=account_id,
        tenant_id=tenant_id,
        intent=intent,   # 🔥 IMPORTANTE
    )

    missing = extract_missing(validation)

    if missing:
        session["missing"] = missing
        session_store.set(session_id, session)

        return {
            "status": "needs_input",
            "missing_inputs": missing,
        }
    
    if plan is None:
        session_store.set(session_id, session)
        return {
            "status": "error",
            "message": f"Could not build execution plan for intent: {intent}",
            "validation_errors": validation.errors,
            "intent": intent,
        }

    session_store.set(session_id, {
        "intent": intent,
        "payload": session["payload"],
        "execution_plan": plan.model_dump(),
        "status": "confirm_required",
    })

    return {
        "status": "confirm_required",
        "message": "Execution plan is ready. Confirm if you want to run dry-run or execute.",
        "execution_plan": plan,
    }