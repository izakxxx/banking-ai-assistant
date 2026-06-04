from pydantic import BaseModel
from typing import Literal, Optional, Any

from app.capabilities.models import MultiStepExecutionPlan


class ChatRequest(BaseModel):
    message: str
    mode: Literal["explain", "sample", "execution"] = "explain"
    account_id: Optional[int] = None
    tenant_id: Optional[str] = "default"
    debug: bool = False
    session_id: Optional[str] = "default-session"


class SourceRef(BaseModel):
    doc_id: str
    chunk_id: str
    score: Optional[float] = None
    sources: list[str] = []
    excerpt: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str] = []
    warnings: list[str] = []


class ChatResponse(BaseModel):
    answer: str
    confidence: str
    sources: list[SourceRef] = []
    execution_plan: MultiStepExecutionPlan | None = None
    validation: ValidationResult | None = None
    debug: dict[str, Any] | None = None