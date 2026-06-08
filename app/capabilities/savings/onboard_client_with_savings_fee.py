from __future__ import annotations

from typing import Any

from app.capabilities.base import BaseCapability
from app.capabilities.models import ExecutionStep, MultiStepExecutionPlan
from app.schemas.chat import ValidationResult


_REQUIRED_FIELDS = {
    "officeId",
    "firstname",
    "lastname",
    "externalId",
    "mobileNo",
    "dateOfBirth",
    "submittedOnDate",
    "activationDate",
    "legalFormId",
    "savingsProductId",
    "chargeId",
    "amount",
}


def _is_blank(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, str):
        return not value.strip()

    return False


class OnboardClientWithSavingsFeeCapability(BaseCapability):
    intent = "onboard_client_with_savings_fee"

    def sanitize(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw = dict(payload or {})

        if "payload" in raw and isinstance(raw["payload"], dict):
            raw = raw["payload"]

        normalized = dict(raw)

        alias_map = {
            "firstname": ["firstName", "clientFirstName"],
            "lastname": ["lastName", "clientLastName"],
            "mobileNo": ["mobileNumber", "phone", "phoneNumber"],
            "chargeId": ["savingsChargeId", "feeChargeId"],
            "amount": ["chargeAmount", "feeAmount"],
            "submittedOnDate": ["submissionDate", "submittedDate"],
            "activationDate": ["activationDate", "submissionDate", "submittedOnDate"],
            "savingsProductId": ["productId", "savingsProduct"],
        }

        for canonical, aliases in alias_map.items():
            if normalized.get(canonical) is None:
                for alias in aliases:
                    if raw.get(alias) is not None:
                        normalized[canonical] = raw[alias]
                        break

        client_name = raw.get("clientName")
        if client_name and not normalized.get("firstname"):
            parts = str(client_name).strip().split(" ", 1)
            normalized["firstname"] = parts[0]
            normalized["lastname"] = parts[1] if len(parts) > 1 else None

        normalized.setdefault("locale", "en")
        normalized.setdefault("dateFormat", "yyyy-MM-dd")
        normalized.setdefault("active", True)
        normalized.setdefault("activationDate", normalized.get("submittedOnDate"))
        normalized.setdefault("legalFormId", 1)

        normalized.setdefault("feeOnMonthDay", "May-13")
        normalized.setdefault("monthDayFormat", "MMMM-dd")
        normalized.setdefault("feeInterval", 1)

        return normalized

    def validate(self, payload: dict[str, Any]) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        for field in _REQUIRED_FIELDS:
            if _is_blank(payload.get(field)):
                errors.append(f"Missing {field}.")

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
        steps = [
            ExecutionStep(
                step=1,
                action="create_client",
                tool="create_client",
                payload={
                    "officeId": payload["officeId"],
                    "firstname": payload["firstname"],
                    "lastname": payload["lastname"],
                    "externalId": payload["externalId"],
                    "mobileNo": payload["mobileNo"],
                    "dateOfBirth": payload["dateOfBirth"],
                    "active": payload["active"],
                    "submittedOnDate": payload["submittedOnDate"],
                    "activationDate": payload["activationDate"],
                    "legalFormId": payload["legalFormId"],
                    "dateFormat": payload["dateFormat"],
                    "locale": payload["locale"],
                },
                description="Create a new client.",
                output_mapping={
                    "clientId": "body.clientId",
                    "resourceId": "body.resourceId",
                },
            ),
            ExecutionStep(
                step=2,
                action="create_savings_account",
                tool="create_savings_account",
                payload={
                    "clientId": "{{clientId}}",
                    "productId": payload["savingsProductId"],
                    "locale": payload["locale"],
                    "dateFormat": payload["dateFormat"],
                    "submittedOnDate": payload["submittedOnDate"],
                },
                description="Create a savings account for the new client.",
                depends_on=[1],
                output_mapping={
                    "savingsId": "body.savingsId",
                    "savingsResourceId": "body.resourceId",
                },
            ),
            ExecutionStep(
                step=3,
                action="apply_monthly_fee_to_savings_account",
                tool="apply_savings_monthly_fee",
                payload={
                    "chargeId": payload["chargeId"],
                    "amount": payload["amount"],
                    "feeOnMonthDay": payload["feeOnMonthDay"],
                    "monthDayFormat": payload["monthDayFormat"],
                    "feeInterval": payload["feeInterval"],
                    "locale": payload["locale"],
                },
                description="Apply a monthly fee charge to the created savings account.",
                depends_on=[2],
                output_mapping={
                    "savingsChargeResourceId": "body.resourceId",
                },
            ),
            ExecutionStep(
                step=4,
                action="verify_client",
                tool="verify_client",
                payload={},
                description="Verify that the client was created successfully.",
                depends_on=[1],
                is_verification=True,
            ),
            ExecutionStep(
                step=5,
                action="verify_savings_account",
                tool="verify_savings_account",
                payload={},
                description="Verify that the savings account was created successfully.",
                depends_on=[2],
                is_verification=True,
            ),
            ExecutionStep(
                step=6,
                action="verify_savings_charge",
                tool="verify_savings_charge",
                payload={},
                description="Verify that the monthly fee charge was assigned successfully.",
                depends_on=[3],
                is_verification=True,
            ),
        ]

        return MultiStepExecutionPlan(
            intent=self.intent,
            steps=steps,
        )