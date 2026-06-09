from __future__ import annotations

import numpy as np
from openai import OpenAI

from app.core.config import settings

EMBEDDING_MODEL = "text-embedding-3-small"

_client = OpenAI(api_key=settings.openai_api_key)


def embed(text: str) -> list[float]:
    vectors = embed_batch([text])
    return vectors[0] if vectors else []


def embed_batch(texts: list[str]) -> list[list[float]]:
    clean_texts = [str(text).strip() for text in texts if str(text).strip()]

    if not clean_texts:
        return []

    response = _client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=clean_texts,
    )

    return [item.embedding for item in response.data]


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    a = np.array(v1)
    b = np.array(v2)

    if a.size == 0 or b.size == 0:
        return 0.0

    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))