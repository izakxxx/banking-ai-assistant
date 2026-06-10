from __future__ import annotations

from typing import Any

from app.execution.fineract_client import fineract_client, FineractExecutionError
from app.validators.base import BasePreExecutionValidator
from app.validators.models import PreValidationResult, PreValidationStep


class CreateSavingsMonthlyFeePreExecutionValidator(BasePreExecutionValidator):
    intent = "create_savings_monthly_fee"

    def validate(
        self,
        payload: dict[str, Any],
        account_id: int | None,
        tenant_id: str = "default",
    ) -> PreValidationResult:
        steps: list[PreValidationStep] = []
        errors: list[str] = []
        warnings: list[str] = []

        if account_id is None:
            errors.append("Missing account_id.")
            steps.append(PreValidationStep(
                name="account_id_present",
                passed=False,
                message="account_id is required before applying a savings monthly fee.",
            ))
            return PreValidationResult(passed=False, steps=steps, errors=errors, warnings=warnings)

        try:
            response = fineract_client.request(
                method="GET",
                endpoint=f"/api/v1/savingsaccounts/{account_id}",
                tenant_id=tenant_id,
            )
        except FineractExecutionError as exc:
            errors.append(str(exc))
            steps.append(PreValidationStep(
                name="fetch_savings_account",
                passed=False,
                message="Could not fetch savings account from Fineract.",
                details={
                    "status_code": exc.status_code,
                    "response_body": exc.response_body,
                },
            ))
            return PreValidationResult(passed=False, steps=steps, errors=errors, warnings=warnings)

        account = response.get("body", {})
        status = account.get("status", {})
        active = status.get("active", False)

        if not active:
            errors.append(f"Savings account {account_id} is not active.")
            steps.append(PreValidationStep(
                name="account_is_active",
                passed=False,
                message="Savings account is not active.",
                details={"status": status},
            ))
            return PreValidationResult(passed=False, steps=steps, errors=errors, warnings=warnings)

        steps.append(PreValidationStep(
            name="account_is_active",
            passed=True,
            message="Savings account is active.",
            details={"account_id": account_id},
        ))

        return PreValidationResult(
            passed=True,
            steps=steps,
            errors=errors,
            warnings=warnings,
        )