from __future__ import annotations

from typing import Any

from app.capabilities.models import ExecutionStep


def build_business_followup_steps(
    action: str,
    business_status: str,
    context: dict[str, Any],
    next_step_number: int,
) -> list[ExecutionStep]:

    # ===== PENDING APPROVAL =====

    if (
        action == "verify_savings_account"
        and business_status == "SAVINGS_PENDING_APPROVAL"
    ):
        return [
            ExecutionStep(
                step=next_step_number,
                action="approve_savings_account",
                tool="approve_savings_account",
                payload={
                    "approvedOnDate": "13 May 2026",
                    "dateFormat": "dd MMMM yyyy",
                    "locale": "en",
                },
                description="Approve savings account.",
                depends_on=[5],
                output_mapping={},
                is_verification=False,
            ),
            ExecutionStep(
                step=next_step_number + 1,
                action="verify_savings_account_after_approval",
                tool="verify_savings_account",
                payload={},
                description="Verify after approval.",
                depends_on=[next_step_number],
                output_mapping={},
                is_verification=True,
            ),
        ]

    # ===== APPROVED BUT NOT ACTIVE =====

    if (
        action in {
            "verify_savings_account_after_approval",
            "verify_savings_account",
        }
        and business_status == "SAVINGS_NOT_ACTIVE"
    ):
        return [
            ExecutionStep(
                step=next_step_number,
                action="activate_savings_account",
                tool="activate_savings_account",
                payload={
                    "activatedOnDate": "13 May 2026",
                    "dateFormat": "dd MMMM yyyy",
                    "locale": "en",
                },
                description="Activate savings account.",
                depends_on=[next_step_number - 1],
                output_mapping={},
                is_verification=False,
            ),
            ExecutionStep(
                step=next_step_number + 1,
                action="verify_savings_account_after_activation",
                tool="verify_savings_account",
                payload={},
                description="Verify after activation.",
                depends_on=[next_step_number],
                output_mapping={},
                is_verification=True,
            ),
        ]

    return []