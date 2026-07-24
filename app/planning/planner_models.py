from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from app.capabilities.models import MultiStepExecutionPlan


class GoalType(str, Enum):
    PAY_SAVINGS_CHARGE = "PAY_SAVINGS_CHARGE"
    CREATE_SAVINGS_MONTHLY_FEE = "CREATE_SAVINGS_MONTHLY_FEE"
    ONBOARD_CUSTOMER_WITH_SAVINGS_FEE = "ONBOARD_CUSTOMER_WITH_SAVINGS_FEE"
    UNKNOWN = "UNKNOWN"


class PlanningMode(str, Enum):
    DETERMINISTIC = "deterministic"


class CapabilityId(str, Enum):
    PAY_SAVINGS_CHARGE = "pay_savings_charge"
    CREATE_SAVINGS_MONTHLY_FEE = "create_savings_monthly_fee"
    ONBOARD_CLIENT_WITH_SAVINGS_FEE = "onboard_client_with_savings_fee"


class CapabilityInvocation(BaseModel):
    capability_id: CapabilityId


class ExecutionPath(BaseModel):
    goal: GoalType
    capabilities: list[CapabilityInvocation] = Field(default_factory=list)


class PlanningRequest(BaseModel):
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    account_id: int | None = None
    tenant_id: str = "default"
    mode: PlanningMode = PlanningMode.DETERMINISTIC


class PlannerResult(BaseModel):
    goal: GoalType
    execution_path: ExecutionPath
    execution_plan: MultiStepExecutionPlan | None = None
    validation_errors: list[str] = Field(default_factory=list)
    validation_warnings: list[str] = Field(default_factory=list)
    debug: dict[str, Any] = Field(default_factory=dict)

