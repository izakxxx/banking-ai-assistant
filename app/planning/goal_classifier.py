from __future__ import annotations

import re
import unicodedata

from app.planning.planner_models import GoalType


_GOAL_PATTERNS: tuple[tuple[GoalType, tuple[re.Pattern[str], ...]], ...] = (
    (
        GoalType.ONBOARD_CUSTOMER_WITH_SAVINGS_FEE,
        (
            re.compile(r"\bonboard(?:ing)?\b.*\b(?:client|customer)\b"),
            re.compile(
                r"\b(?:create|open|register)\b.*\b(?:client|customer)\b"
                r".*\bsavings?\b"
            ),
            re.compile(
                r"\b(?:client|customer)\b.*\bsavings?\b"
                r".*\b(?:create|open|onboard)\b"
            ),
        ),
    ),
    (
        GoalType.PAY_SAVINGS_CHARGE,
        (
            re.compile(r"\b(?:pay|settle)\b.*\bsavings?\b.*\b(?:charge|fee)\b"),
            re.compile(r"\b(?:savings?\s+)?(?:charge|fee)\b.*\b(?:pay|settle)\b"),
        ),
    ),
    (
        GoalType.CREATE_SAVINGS_MONTHLY_FEE,
        (
            re.compile(
                r"\b(?:create|add|apply|assign)\b.*\bmonthly\b"
                r".*\b(?:charge|fee)\b"
            ),
            re.compile(
                r"\bmonthly\b.*\b(?:charge|fee)\b"
                r".*\b(?:create|add|apply|assign)\b"
            ),
        ),
    ),
)


def _normalize(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return " ".join(ascii_text.lower().split())


class GoalClassifier:
    def classify(self, request: str) -> GoalType:
        normalized_request = _normalize(request)

        for goal, patterns in _GOAL_PATTERNS:
            if any(pattern.search(normalized_request) for pattern in patterns):
                return goal

        return GoalType.UNKNOWN

