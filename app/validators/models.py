from __future__ import annotations

from typing import Any
from pydantic import BaseModel


class PreValidationStep(BaseModel):
    name: str
    passed: bool
    message: str
    details: dict[str, Any] = {}


class PreValidationResult(BaseModel):
    passed: bool
    steps: list[PreValidationStep]
    errors: list[str] = []
    warnings: list[str] = []