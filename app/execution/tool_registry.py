from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    method: str
    endpoint_template: str
    description: str


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {
            "create_client": ToolDefinition(
                name="create_client",
                method="POST",
                endpoint_template="/api/v1/clients",
                description="Create a client in Fineract.",
            ),
            "create_savings_account": ToolDefinition(
                name="create_savings_account",
                method="POST",
                endpoint_template="/api/v1/savingsaccounts",
                description="Create a savings account in Fineract.",
            ),
            "apply_savings_monthly_fee": ToolDefinition(
                name="apply_savings_monthly_fee",
                method="POST",
                endpoint_template="/api/v1/savingsaccounts/{{savingsId}}/charges",
                description="Apply a monthly fee charge to a savings account.",
            ),
            "verify_client": ToolDefinition(
                name="verify_client",
                method="GET",
                endpoint_template="/api/v1/clients/{{clientId}}",
                description="Verify that a client exists.",
            ),
            "verify_savings_account": ToolDefinition(
                name="verify_savings_account",
                method="GET",
                endpoint_template="/api/v1/savingsaccounts/{{savingsId}}",
                description="Verify that a savings account exists.",
            ),
            "verify_savings_charge": ToolDefinition(
                name="verify_savings_charge",
                method="GET",
                endpoint_template="/api/v1/savingsaccounts/{{savingsId}}/charges/{{savingsChargeResourceId}}",
                description="Verify that a savings account charge exists.",
            ),
            "approve_savings_account": ToolDefinition(
                name="approve_savings_account",
                method="POST",
                endpoint_template="/api/v1/savingsaccounts/{{savingsId}}?command=approve",
                description="Approve a savings account in Fineract.",
            ),
            "activate_savings_account": ToolDefinition(
                name="activate_savings_account",
                method="POST",
                endpoint_template="/api/v1/savingsaccounts/{{savingsId}}?command=activate",
                description="Activate a savings account in Fineract.",
            ),
        }

    def get(self, tool_name: str) -> ToolDefinition | None:
        return self._tools.get(tool_name)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())


tool_registry = ToolRegistry()