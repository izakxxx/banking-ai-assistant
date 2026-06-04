from __future__ import annotations

import json
from typing import Any

from app.capabilities.base import BaseCapability
from app.capabilities.models import ExecutionStep, MultiStepExecutionPlan
from app.schemas.chat import ValidationResult
from app.core.config import settings

_ALLOWED_FIELDS = {
    "amount",
    "dueDate",
    "dateFormat",
    "locale",
    "savingsAccountChargeId",
}


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        v = value.strip()
        if not v:
            return True
        if v in {"__REQUIRED_INT__", "__REQUIRED_AMOUNT__", "__REQUIRED_DATE__"}:
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


class PaySavingsChargeCapability(BaseCapability):
    intent = "pay_savings_charge"

    def sanitize(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload or {})

        if normalized.get("savingsAccountChargeId") is None:
            normalized["savingsAccountChargeId"] = "__REQUIRED_INT__"

        if normalized.get("amount") is None:
            normalized["amount"] = "__REQUIRED_AMOUNT__"

        if normalized.get("dueDate") is None:
            normalized["dueDate"] = "__REQUIRED_DATE__"

        normalized.setdefault("dateFormat", "dd MMMM yyyy")
        normalized.setdefault("locale", "en")

        normalized = {k: v for k, v in normalized.items() if k in _ALLOWED_FIELDS}
        return normalized

    def validate(self, payload: dict[str, Any]) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if _is_blank(payload.get("savingsAccountChargeId")):
            errors.append("Missing savingsAccountChargeId.")

        if _is_blank(payload.get("amount")):
            errors.append("Missing amount.")

        if _is_blank(payload.get("dueDate")):
            errors.append("Missing dueDate.")

        if _is_blank(payload.get("dateFormat")):
            errors.append("Missing dateFormat.")

        if _is_blank(payload.get("locale")):
            errors.append("Missing locale.")

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
        charge_id = payload.get("savingsAccountChargeId", "{savingsAccountChargeId}")
        endpoint = f"/api/v1/savingsaccounts/{account_segment}/charges/{charge_id}?command=paycharge"

        request_payload = {
            "amount": payload.get("amount"),
            "dueDate": payload.get("dueDate"),
            "dateFormat": payload.get("dateFormat"),
            "locale": payload.get("locale"),
        }

        step = ExecutionStep(
            step=1,
            action="pay_savings_charge",
            method="POST",
            endpoint=endpoint,
            payload=request_payload,
            description="Pay an existing savings account charge.",
            curl=_build_curl("POST", endpoint, request_payload, tenant_id=tenant_id),
        )

        return MultiStepExecutionPlan(
            intent=self.intent,
            steps=[step],
        )