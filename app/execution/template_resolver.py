from __future__ import annotations

import re
from typing import Any


_TEMPLATE_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}")


def resolve_string_template(value: str, context: dict[str, Any]) -> Any:
    full_match = _TEMPLATE_PATTERN.fullmatch(value.strip())

    if full_match:
        key = full_match.group(1)
        return context.get(key, value)

    def replace(match: re.Match) -> str:
        key = match.group(1)
        return str(context.get(key, match.group(0)))

    return _TEMPLATE_PATTERN.sub(replace, value)


def resolve_templates(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return resolve_string_template(value, context)

    if isinstance(value, dict):
        return {
            k: resolve_templates(v, context)
            for k, v in value.items()
        }

    if isinstance(value, list):
        return [
            resolve_templates(item, context)
            for item in value
        ]

    return value


def get_path_value(data: dict[str, Any], path: str) -> Any:
    current: Any = data

    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None

    return current


def extract_outputs(
    response: dict[str, Any],
    output_mapping: dict[str, str] | None,
) -> dict[str, Any]:
    if not output_mapping:
        return {}

    extracted: dict[str, Any] = {}

    for key, path in output_mapping.items():
        value = get_path_value(response, path)

        if value is not None:
            extracted[key] = value

    return extracted