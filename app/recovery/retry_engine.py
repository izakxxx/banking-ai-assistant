from __future__ import annotations

import uuid
from copy import deepcopy
from typing import Any


def generate_external_id(previous_value: str | None = None) -> str:
    suffix = uuid.uuid4().hex[:8].upper()

    if previous_value:
        return f"{previous_value}-{suffix}"

    return f"AUTO-{suffix}"


def mutate_payload_for_retry(
    action: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    mutated = deepcopy(payload)

    if action == "create_client":
        previous_external_id = mutated.get("externalId")

        mutated["externalId"] = generate_external_id(
            previous_external_id,
        )

    return mutated