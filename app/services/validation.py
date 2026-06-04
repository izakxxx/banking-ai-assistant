from __future__ import annotations

from typing import Any

from app.schemas.chat import ValidationResult


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return True
        if v in {"__REQUIRED_INT__", "__REQUIRED_AMOUNT__"}:
            return True
    return False


def validate_savings_charge_payload(payload: dict[str, Any]) -> ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(payload, dict):
        return ValidationResult(
            is_valid=False,
            errors=["Payload must be a JSON object."],
            warnings=[],
        )

    if _is_blank(payload.get("chargeId")):
        errors.append("Missing chargeId.")

    if _is_blank(payload.get("amount")):
        errors.append("Missing amount.")

    if not _is_blank(payload.get("feeOnMonthDay")) and _is_blank(payload.get("monthDayFormat")):
        errors.append("feeOnMonthDay requires monthDayFormat.")

    if not _is_blank(payload.get("dueDate")):
        if _is_blank(payload.get("dateFormat")):
            errors.append("dueDate requires dateFormat.")
        if _is_blank(payload.get("locale")):
            errors.append("dueDate requires locale.")

    amount = payload.get("amount")
    if amount is not None and not isinstance(amount, (str, int, float)):
        errors.append("amount must be string, integer, or float.")

    charge_id = payload.get("chargeId")
    if charge_id not in {None, "__REQUIRED_INT__"} and not isinstance(charge_id, int):
        warnings.append("chargeId should be an integer.")

    fee_interval = payload.get("feeInterval")
    if fee_interval is not None and not isinstance(fee_interval, int):
        warnings.append("feeInterval should be an integer.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )