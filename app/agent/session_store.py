from __future__ import annotations

from typing import Any


class SessionStore:
    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    def get(self, session_id: str) -> dict[str, Any]:
        return self._store.get(session_id, {})

    def set(self, session_id: str, data: dict[str, Any]) -> None:
        self._store[session_id] = data

    def update(self, session_id: str, data: dict[str, Any]) -> None:
        current = self.get(session_id)
        current.update(data)
        self.set(session_id, current)

    def clear(self, session_id: str) -> None:
        if session_id in self._store:
            del self._store[session_id]


session_store = SessionStore()