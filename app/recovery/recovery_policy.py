from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.recovery.error_classifier import ClassifiedError


@dataclass(frozen=True)
class RecoveryDecision:
    can_retry: bool
    strategy: str
    message: str


def _body_text(response_body: Any) -> str:
    if response_body is None:
        return ""

    if isinstance(response_body, str):
        return response_body.lower()

    return str(response_body).lower()


def decide_recovery(
    action: str,
    classified_error: ClassifiedError,
    response_body: Any | None = None,
) -> RecoveryDecision:
    text = _body_text(response_body)

    if action == "create_client" and classified_error == ClassifiedError.DUPLICATE_RESOURCE:
        if (
            "externalid" in text
            or "document" in text
            or "mobileno" in text
            or "email" in text
            or "national" in text
            or "tax" in text
        ):
            return RecoveryDecision(
                can_retry=False,
                strategy="HUMAN_REVIEW_REQUIRED",
                message=(
                    "Duplicate business identity data detected. "
                    "Automatic mutation is not safe. Human review is required."
                ),
            )

        return RecoveryDecision(
            can_retry=False,
            strategy="DUPLICATE_RESOURCE_REVIEW",
            message="Duplicate resource detected. Human review is required before retrying.",
        )

    if classified_error == ClassifiedError.TEMPORARY_FAILURE:
        return RecoveryDecision(
            can_retry=True,
            strategy="RETRY_SAME_STEP",
            message="Temporary failure detected. This step can be retried safely.",
        )

    if classified_error == ClassifiedError.AUTH_FAILURE:
        return RecoveryDecision(
            can_retry=True,
            strategy="REAUTHENTICATE_AND_RETRY",
            message="Authentication failed. Refresh authentication and retry the step.",
        )

    return RecoveryDecision(
        can_retry=False,
        strategy="NO_SAFE_RECOVERY",
        message="No safe automatic recovery policy is available for this failure.",
    )