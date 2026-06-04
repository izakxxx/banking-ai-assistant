from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import json


DEFAULT_AUDIT_LOG_PATH = Path("data/execution/audit_log.jsonl")


def _load_audit_records(path: Path = DEFAULT_AUDIT_LOG_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return records


def _safe_get_result(record: dict[str, Any]) -> dict[str, Any]:
    result = record.get("result")

    if isinstance(result, dict):
        return result

    return {}


def _get_duration(result: dict[str, Any]) -> int | None:
    value = result.get("workflow_duration_ms")

    if isinstance(value, int):
        return value

    return None


def build_execution_analytics() -> dict[str, Any]:
    records = _load_audit_records()

    event_counter = Counter()
    status_counter = Counter()
    failed_action_counter = Counter()
    recovery_strategy_counter = Counter()
    tool_duration_totals = Counter()
    tool_duration_counts = Counter()

    durations: list[int] = []

    for record in records:
        event_type = record.get("event_type", "unknown")
        event_counter[event_type] += 1

        result = _safe_get_result(record)
        status = result.get("status", "unknown")
        status_counter[status] += 1

        duration = _get_duration(result)
        if duration is not None:
            durations.append(duration)

        failed_action = result.get("failed_action")
        if failed_action:
            failed_action_counter[failed_action] += 1

        recovery = result.get("recovery")
        if isinstance(recovery, dict):
            strategy = recovery.get("strategy")
            if strategy:
                recovery_strategy_counter[strategy] += 1

        steps = result.get("steps", [])
        if isinstance(steps, list):
            for step in steps:
                if not isinstance(step, dict):
                    continue

                tool = step.get("tool") or step.get("action")
                step_duration = step.get("step_duration_ms")

                if tool and isinstance(step_duration, int):
                    tool_duration_totals[tool] += step_duration
                    tool_duration_counts[tool] += 1

    successful_workflows = status_counter.get("executed", 0)
    failed_workflows = status_counter.get("failed", 0)
    total_workflows = successful_workflows + failed_workflows

    avg_duration_ms = int(sum(durations) / len(durations)) if durations else None
    max_duration_ms = max(durations) if durations else None
    min_duration_ms = min(durations) if durations else None

    avg_step_duration_by_tool = {}

    for tool, total_duration in tool_duration_totals.items():
        count = tool_duration_counts[tool]
        avg_step_duration_by_tool[tool] = int(total_duration / count)

    success_rate = (
        round((successful_workflows / total_workflows) * 100, 2)
        if total_workflows > 0
        else 0
    )

    return {
        "total_audit_records": len(records),
        "total_workflows": total_workflows,
        "successful_workflows": successful_workflows,
        "failed_workflows": failed_workflows,
        "success_rate": success_rate,
        "avg_workflow_duration_ms": avg_duration_ms,
        "min_workflow_duration_ms": min_duration_ms,
        "max_workflow_duration_ms": max_duration_ms,
        "events": dict(event_counter),
        "statuses": dict(status_counter),
        "top_failed_actions": failed_action_counter.most_common(10),
        "top_recovery_strategies": recovery_strategy_counter.most_common(10),
        "avg_step_duration_by_tool_ms": avg_step_duration_by_tool,
    }