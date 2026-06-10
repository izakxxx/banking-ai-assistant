from __future__ import annotations

from typing import Any

from app.execution.fineract_client import fineract_client, FineractExecutionError
from app.validators.base import BasePreExecutionValidator
from app.validators.models import PreValidationResult, PreValidationStep


class PaySavingsChargePreExecutionValidator(BasePreExecutionValidator):
    intent = "pay_savings_charge"

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
                message="account_id is required before paying a savings charge.",
            ))
            return PreValidationResult(passed=False, steps=steps, errors=errors, warnings=warnings)

        charge_id = payload.get("savingsAccountChargeId")

        if charge_id in {None, "", "__REQUIRED_INT__"}:
            errors.append("Missing savingsAccountChargeId.")
            steps.append(PreValidationStep(
                name="charge_id_present",
                passed=False,
                message="savingsAccountChargeId is required.",
            ))
            return PreValidationResult(passed=False, steps=steps, errors=errors, warnings=warnings)

        try:
            response = fineract_client.request(
                method="GET",
                endpoint=f"/api/v1/savingsaccounts/{account_id}/charges",
                tenant_id=tenant_id,
            )
        except FineractExecutionError as exc:
            errors.append(str(exc))
            steps.append(PreValidationStep(
                name="fetch_savings_charges",
                passed=False,
                message="Could not fetch savings account charges from Fineract.",
                details={
                    "status_code": exc.status_code,
                    "response_body": exc.response_body,
                },
            ))
            return PreValidationResult(passed=False, steps=steps, errors=errors, warnings=warnings)

        body = response.get("body", {})
        charges = body if isinstance(body, list) else body.get("pageItems", body.get("charges", []))

        matched_charge = None
        for charge in charges:
            if int(charge.get("id", -1)) == int(charge_id):
                matched_charge = charge
                break

        if not matched_charge:
            errors.append(f"Savings charge {charge_id} was not found for account {account_id}.")
            steps.append(PreValidationStep(
                name="charge_exists",
                passed=False,
                message="Savings charge was not found in the account.",
                details={"account_id": account_id, "savingsAccountChargeId": charge_id},
            ))
            return PreValidationResult(passed=False, steps=steps, errors=errors, warnings=warnings)

        steps.append(PreValidationStep(
            name="charge_exists",
            passed=True,
            message="Savings charge exists.",
            details={"charge": matched_charge},
        ))

        outstanding = matched_charge.get("amountOutstanding")
        if outstanding is not None and float(outstanding) <= 0:
            errors.append(f"Savings charge {charge_id} is already fully paid.")
            steps.append(PreValidationStep(
                name="charge_has_outstanding_balance",
                passed=False,
                message="Charge has no outstanding amount.",
                details={"amountOutstanding": outstanding},
            ))
            return PreValidationResult(passed=False, steps=steps, errors=errors, warnings=warnings)

        steps.append(PreValidationStep(
            name="charge_has_outstanding_balance",
            passed=True,
            message="Charge has outstanding balance.",
            details={"amountOutstanding": outstanding},
        ))

        return PreValidationResult(
            passed=True,
            steps=steps,
            errors=errors,
            warnings=warnings,
        )