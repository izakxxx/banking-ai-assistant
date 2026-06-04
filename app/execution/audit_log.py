from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json


LOG_PATH = Path("data/execution/audit_log.jsonl")


def write_audit_event(event: dict[str, Any]) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **event,
    }

    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")