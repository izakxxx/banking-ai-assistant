import os

from langsmith import Client


def is_langsmith_enabled() -> bool:
    return bool(os.getenv("LANGSMITH_API_KEY"))


def get_langsmith_client() -> Client | None:
    if not is_langsmith_enabled():
        return None

    return Client()