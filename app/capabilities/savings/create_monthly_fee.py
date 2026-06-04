from __future__ import annotations

import json
from typing import Any

from app.capabilities.base import BaseCapability
from app.capabilities.models import ExecutionStep, MultiStepExecutionPlan
from app.schemas.chat import ValidationResult
from app.core.config import settings


_ALLOWED_FIELDS = {
    "chargeId",
    "amount",
    "feeOnMonthDay",
    "monthDayFormat",
    "feeInterval",
    "locale",
}


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


def _build_curl(
    method: str,
    endpoint: str,
    payload: dict[str, Any],
    tenant_id: str = "default",
    base_url: str = settings.fineract_base_url,
) -> str:
    body = json.dumps(payload, indent=2, ensure_ascii=False)
    return (
        f"curl -X {method} \"{base_url}{endpoint}\" \\\n"
        f"  -H \"Content-Type: application/json\" \\\n"
        f"  -H \"Accept: application/json\" \\\n"
        f"  -H \"Litecore-Platform-TenantId: {tenant_id}\" \\\n"
        f"  -H \"Authorization: Basic <base64EncodedAuthenticationKey>\" \\\n"
        f"  -d '{body}'"
    )


class CreateSavingsMonthlyFeeCapability(BaseCapability):
    intent = "create_savings_monthly_fee"

    def sanitize(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload or {})

        # Force critical defaults for this capability
        normalized["feeOnMonthDay"] = "May-13"
        normalized["monthDayFormat"] = "MMMM-dd"
        normalized["feeInterval"] = 1
        normalized["locale"] = "en"

        if normalized.get("chargeId") is None:
            normalized["chargeId"] = "__REQUIRED_INT__"

        if normalized.get("amount") is None:
            normalized["amount"] = "__REQUIRED_AMOUNT__"

        normalized = {k: v for k, v in normalized.items() if k in _ALLOWED_FIELDS}
        return normalized

    def validate(self, payload: dict[str, Any]) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if _is_blank(payload.get("chargeId")):
            errors.append("Missing chargeId.")

        if _is_blank(payload.get("amount")):
            errors.append("Missing amount.")

        if _is_blank(payload.get("feeOnMonthDay")):
            errors.append("Monthly Fee requires feeOnMonthDay.")

        if _is_blank(payload.get("monthDayFormat")):
            errors.append("Monthly Fee requires monthDayFormat.")

        if _is_blank(payload.get("feeInterval")):
            errors.append("Monthly Fee requires feeInterval.")

        if _is_blank(payload.get("locale")):
            warnings.append("Monthly Fee usually requires locale.")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def build_plan(
        self,
        payload: dict[str, Any],
        account_id: int | None,
        tenant_id: str = "default",
    ) -> MultiStepExecutionPlan:
        account_segment = "{accountId}" if account_id is None else str(account_id)
        endpoint = f"/api/v1/savingsaccounts/{account_segment}/charges"

        step = ExecutionStep(
            step=1,
            action="apply_monthly_fee_to_savings_account",
            method="POST",
            endpoint=endpoint,
            payload=payload,
            description="Apply a monthly fee charge to a savings account instance.",
            curl=_build_curl("POST", endpoint, payload, tenant_id=tenant_id),
        )

        return MultiStepExecutionPlan(
            intent=self.intent,
            steps=[step],
        )