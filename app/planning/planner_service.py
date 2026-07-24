from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.capabilities.models import MultiStepExecutionPlan
from app.capabilities.registry import CapabilityRegistry, registry
from app.planning.goal_classifier import GoalClassifier
from app.planning.path_planner import PathPlanner
from app.planning.planner_models import (
    ExecutionPath,
    GoalType,
    PlannerResult,
    PlanningMode,
)
from app.schemas.chat import ValidationResult
from app.services.execution_service import build_execution_plan


ExecutionPlanBuilder = Callable[
    [str | None, dict[str, Any] | None, int | None, str, str | None],
    tuple[str, MultiStepExecutionPlan | None, ValidationResult],
]


class PlannerService:
    def __init__(
        self,
        classifier: GoalClassifier | None = None,
        path_planner: PathPlanner | None = None,
        capability_registry: CapabilityRegistry = registry,
        execution_plan_builder: ExecutionPlanBuilder = build_execution_plan,
    ) -> None:
        self._classifier = classifier or GoalClassifier()
        self._path_planner = path_planner or PathPlanner()
        self._capability_registry = capability_registry
        self._execution_plan_builder = execution_plan_builder

    def plan(
        self,
        request: str,
        payload: dict[str, Any] | None = None,
        account_id: int | None = None,
        tenant_id: str = "default",
        mode: PlanningMode = PlanningMode.DETERMINISTIC,
    ) -> PlannerResult:
        goal = self._classifier.classify(request)
        execution_path = self._path_planner.plan(goal)
        debug = self._build_debug(request, mode, execution_path)

        if goal is GoalType.UNKNOWN:
            return PlannerResult(
                goal=goal,
                execution_path=execution_path,
                validation_errors=["The request does not match a supported banking goal."],
                debug=debug,
            )

        unresolved = [
            invocation.capability_id.value
            for invocation in execution_path.capabilities
            if self._capability_registry.get(invocation.capability_id.value) is None
        ]
        if unresolved:
            return PlannerResult(
                goal=goal,
                execution_path=execution_path,
                validation_errors=[
                    f"Capability is not registered: {capability_id}."
                    for capability_id in unresolved
                ],
                debug={**debug, "unresolved_capabilities": unresolved},
            )

        if len(execution_path.capabilities) != 1:
            return PlannerResult(
                goal=goal,
                execution_path=execution_path,
                validation_errors=[
                    "The current execution-plan compiler requires one root capability."
                ],
                debug=debug,
            )

        capability_id = execution_path.capabilities[0].capability_id.value
        resolved_intent, execution_plan, validation = self._execution_plan_builder(
            request,
            payload,
            account_id,
            tenant_id,
            capability_id,
        )

        return PlannerResult(
            goal=goal,
            execution_path=execution_path,
            execution_plan=execution_plan,
            validation_errors=validation.errors,
            validation_warnings=validation.warnings,
            debug={**debug, "resolved_intent": resolved_intent},
        )

    def _build_debug(
        self,
        request: str,
        mode: PlanningMode,
        execution_path: ExecutionPath,
    ) -> dict[str, Any]:
        return {
            "planning_mode": mode.value,
            "classifier": type(self._classifier).__name__,
            "request": request,
            "selected_capabilities": [
                invocation.capability_id.value
                for invocation in execution_path.capabilities
            ],
            "registered_capabilities": self._capability_registry.list_intents(),
        }

