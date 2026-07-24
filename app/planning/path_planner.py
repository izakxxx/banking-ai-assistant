from __future__ import annotations

from app.planning.planner_models import (
    CapabilityId,
    CapabilityInvocation,
    ExecutionPath,
    GoalType,
)


_GOAL_CAPABILITIES: dict[GoalType, tuple[CapabilityId, ...]] = {
    GoalType.PAY_SAVINGS_CHARGE: (CapabilityId.PAY_SAVINGS_CHARGE,),
    GoalType.CREATE_SAVINGS_MONTHLY_FEE: (
        CapabilityId.CREATE_SAVINGS_MONTHLY_FEE,
    ),
    GoalType.ONBOARD_CUSTOMER_WITH_SAVINGS_FEE: (
        CapabilityId.ONBOARD_CLIENT_WITH_SAVINGS_FEE,
    ),
}


class PathPlanner:
    def plan(self, goal: GoalType) -> ExecutionPath:
        capability_ids = _GOAL_CAPABILITIES.get(goal, ())
        return ExecutionPath(
            goal=goal,
            capabilities=[
                CapabilityInvocation(capability_id=capability_id)
                for capability_id in capability_ids
            ],
        )

