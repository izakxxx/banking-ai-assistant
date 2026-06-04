from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


def new_execution_id() -> str:
    return f"exec-{uuid4().hex}"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(dt: datetime) -> str:
    return dt.isoformat()


def duration_ms(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() * 1000)