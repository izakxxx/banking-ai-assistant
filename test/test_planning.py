from __future__ import annotations

import os
import unittest

os.environ.setdefault("OPENAI_API_KEY", "test-key")

from app.capabilities.models import ExecutionStep, MultiStepExecutionPlan
from app.planning.goal_classifier import GoalClassifier
from app.planning.path_planner import PathPlanner
from app.planning.planner_models import CapabilityId, GoalType
from app.planning.planner_service import PlannerService
from app.schemas.chat import ValidationResult


class GoalClassifierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.classifier = GoalClassifier()

    def test_classifies_supported_goals(self) -> None:
        cases = {
            "Pay a savings account charge": GoalType.PAY_SAVINGS_CHARGE,
            "Create monthly fee": GoalType.CREATE_SAVINGS_MONTHLY_FEE,
            "Create client with savings account": (
                GoalType.ONBOARD_CUSTOMER_WITH_SAVINGS_FEE
            ),
        }

        for request, expected_goal in cases.items():
            with self.subTest(request=request):
                self.assertEqual(self.classifier.classify(request), expected_goal)

    def test_returns_unknown_for_unsupported_request(self) -> None:
        self.assertEqual(
            self.classifier.classify("Show today's exchange rates"),
            GoalType.UNKNOWN,
        )


class PathPlannerTests(unittest.TestCase):
    def test_maps_onboarding_to_registered_composite_capability(self) -> None:
        path = PathPlanner().plan(GoalType.ONBOARD_CUSTOMER_WITH_SAVINGS_FEE)

        self.assertEqual(path.goal, GoalType.ONBOARD_CUSTOMER_WITH_SAVINGS_FEE)
        self.assertEqual(len(path.capabilities), 1)
        self.assertEqual(
            path.capabilities[0].capability_id,
            CapabilityId.ONBOARD_CLIENT_WITH_SAVINGS_FEE,
        )


class PlannerServiceTests(unittest.TestCase):
    def test_propagates_existing_capability_validation(self) -> None:
        result = PlannerService().plan(
            request="Create monthly fee",
            payload={},
            account_id=41,
        )

        self.assertIsNone(result.execution_plan)
        self.assertEqual(
            set(result.validation_errors),
            {"Missing chargeId.", "Missing amount."},
        )

    def test_reuses_execution_plan_builder_with_explicit_capability(self) -> None:
        calls: list[tuple[object, ...]] = []

        def fake_builder(
            question: str | None,
            payload: dict | None,
            account_id: int | None,
            tenant_id: str,
            intent: str | None,
        ) -> tuple[str, MultiStepExecutionPlan, ValidationResult]:
            calls.append((question, payload, account_id, tenant_id, intent))
            return (
                intent or "",
                MultiStepExecutionPlan(
                    intent=intent or "",
                    steps=[ExecutionStep(step=1, action="compiled_by_capability")],
                ),
                ValidationResult(is_valid=True),
            )

        service = PlannerService(execution_plan_builder=fake_builder)
        result = service.plan(
            request="Pay a savings account charge",
            payload={"amount": 25},
            account_id=41,
            tenant_id="lab",
        )

        self.assertEqual(result.goal, GoalType.PAY_SAVINGS_CHARGE)
        self.assertIsNotNone(result.execution_plan)
        self.assertEqual(result.validation_errors, [])
        self.assertEqual(
            calls,
            [
                (
                    "Pay a savings account charge",
                    {"amount": 25},
                    41,
                    "lab",
                    CapabilityId.PAY_SAVINGS_CHARGE.value,
                )
            ],
        )

    def test_unknown_goal_does_not_compile_a_plan(self) -> None:
        def unexpected_builder(*args, **kwargs):
            self.fail("Execution plan builder should not be called")

        result = PlannerService(execution_plan_builder=unexpected_builder).plan(
            "Generate a loan portfolio report"
        )

        self.assertEqual(result.goal, GoalType.UNKNOWN)
        self.assertIsNone(result.execution_plan)
        self.assertTrue(result.validation_errors)


if __name__ == "__main__":
    unittest.main()
