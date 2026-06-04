import json
from pathlib import Path
from typing import Any

from app.retrieval.embeddings import embed, cosine_similarity
from app.retrieval.util import looks_like_toc

VECTOR_PATH = Path("data/index/vectors.json")

_VECTORS_CACHE: list[dict[str, Any]] | None = None


def _load_vectors() -> list[dict[str, Any]]:
    global _VECTORS_CACHE
    if _VECTORS_CACHE is None:
        _VECTORS_CACHE = json.loads(VECTOR_PATH.read_text(encoding="utf-8"))
    return _VECTORS_CACHE


def semantic_retrieve(query: str, top_k: int = 5, min_score: float | None = None) -> list[dict]:
    query_vec = embed(query)  # dict[str, float] (sparse)
    if not query_vec:
        return []

    vectors = _load_vectors()

    scored: list[tuple[float, dict[str, Any]]] = []

    for item in vectors:
        text = item.get("text", "")
        if not text or looks_like_toc(text):
            continue

        item_vec = item.get("vector")
        if not isinstance(item_vec, list) or not item_vec:
            continue

        score = cosine_similarity(query_vec, item_vec)

        if min_score is not None and score < min_score:
            continue

        scored.append((score, item))

    if not scored:
        return []

    scored.sort(reverse=True, key=lambda x: x[0])

    # 🎛️ Threshold dinámico opcional (recorta cola de ruido)
    # Solo lo aplico cuando el usuario pasó min_score, para que sea intencional.
    if min_score is not None:
        best_score = scored[0][0]
        threshold = max(min_score, best_score * 0.60)
        scored = [(s, it) for (s, it) in scored if s >= threshold]

    results = []
    for score, item in scored[:top_k]:
        results.append({
            "doc_id": item["doc_id"],
            "chunk_id": item["chunk_id"],
            "score": round(float(score), 4),
            "snippet": item["text"][:300].replace("\n", " "),
        })

    return results
