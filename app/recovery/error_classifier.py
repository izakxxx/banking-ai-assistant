from __future__ import annotations

from enum import Enum
from typing import Any


class ClassifiedError(str, Enum):
    DUPLICATE_RESOURCE = "DUPLICATE_RESOURCE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTH_FAILURE = "AUTH_FAILURE"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    TEMPORARY_FAILURE = "TEMPORARY_FAILURE"
    UNKNOWN = "UNKNOWN"


def _body_text(response_body: Any) -> str:
    if response_body is None:
        return ""

    if isinstance(response_body, str):
        return response_body.lower()

    return str(response_body).lower()


def classify_fineract_error(
    status_code: int | None,
    response_body: Any,
) -> ClassifiedError:
    text = _body_text(response_body)

    if status_code == 401:
        return ClassifiedError.AUTH_FAILURE

    if status_code == 403:
        if (
            "duplicate" in text
            or "already exists" in text
            or "externalid" in text
        ):
            return ClassifiedError.DUPLICATE_RESOURCE

        return ClassifiedError.FORBIDDEN

    if status_code == 404:
        return ClassifiedError.NOT_FOUND

    if status_code in {408, 429, 500, 502, 503, 504}:
        return ClassifiedError.TEMPORARY_FAILURE

    if status_code == 409:
        return ClassifiedError.DUPLICATE_RESOURCE

    if status_code == 400:
        if (
            "already exists" in text
            or "duplicate" in text
            or "externalid" in text and "already" in text
        ):
            return ClassifiedError.DUPLICATE_RESOURCE

        return ClassifiedError.VALIDATION_ERROR

    return ClassifiedError.UNKNOWN