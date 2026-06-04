from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BusinessVerificationResult:
    passed: bool
    status: str
    message: str
    details: dict[str, Any]


def verify_business_state(
    action: str,
    response: dict[str, Any],
) -> BusinessVerificationResult:
    body = response.get("body", {})

    if action == "verify_client":
        active = body.get("active") is True

        return BusinessVerificationResult(
            passed=active,
            status="CLIENT_ACTIVE" if active else "CLIENT_NOT_ACTIVE",
            message="Client is active." if active else "Client is not active.",
            details={
                "clientId": body.get("id"),
                "active": body.get("active"),
                "status": body.get("status"),
            },
        )

    if action in {
        "verify_savings_account",
        "verify_savings_account_after_approval",
        "verify_savings_account_after_activation",
    }:
        status = body.get("status", {})

        if status.get("active") is True:
            return BusinessVerificationResult(
                passed=True,
                status="SAVINGS_ACTIVE",
                message="Savings account is active.",
                details={
                    "savingsId": body.get("id"),
                    "status": status,
                },
            )

        if status.get("submittedAndPendingApproval") is True:
            return BusinessVerificationResult(
                passed=False,
                status="SAVINGS_PENDING_APPROVAL",
                message=(
                    "Savings account was created but is still pending approval. "
                    "Workflow completed technically, but business activation is incomplete."
                ),
                details={
                    "savingsId": body.get("id"),
                    "status": status,
                },
            )

        return BusinessVerificationResult(
            passed=False,
            status="SAVINGS_NOT_ACTIVE",
            message="Savings account exists but is not active.",
            details={
                "savingsId": body.get("id"),
                "status": status,
            },
        )

    if action == "verify_savings_charge":
        is_active = body.get("isActive") is True
        amount = body.get("amount")
        outstanding = body.get("amountOutstanding")

        return BusinessVerificationResult(
            passed=is_active,
            status="CHARGE_ACTIVE" if is_active else "CHARGE_NOT_ACTIVE",
            message="Savings charge is active." if is_active else "Savings charge is not active.",
            details={
                "chargeId": body.get("id"),
                "isActive": is_active,
                "amount": amount,
                "amountOutstanding": outstanding,
            },
        )

    return BusinessVerificationResult(
        passed=True,
        status="NO_BUSINESS_RULE",
        message="No business verification rule was defined for this action.",
        details={},
    )