from __future__ import annotations

from typing import Any


class RuntimeContext:
    def __init__(self) -> None:
        self._values: dict[str, Any] = {}

    def update(self, values: dict[str, Any]) -> None:
        self._values.update(values)

    def get_all(self) -> dict[str, Any]:
        return self._values.copy()

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)