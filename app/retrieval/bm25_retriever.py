from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi

from app.retrieval.util import looks_like_toc, tokenize_list

INDEX_PATH = Path("data/index/chunks.json")

_BM25_CACHE: dict[str, Any] | None = None


def _load_bm25_index() -> dict[str, Any]:
    global _BM25_CACHE

    if _BM25_CACHE is not None:
        return _BM25_CACHE

    if not INDEX_PATH.exists():
        _BM25_CACHE = {
            "chunks": [],
            "bm25": None,
        }
        return _BM25_CACHE

    raw_chunks = json.loads(INDEX_PATH.read_text(encoding="utf-8"))

    chunks: list[dict[str, Any]] = []
    corpus_tokens: list[list[str]] = []

    for chunk in raw_chunks:
        text = str(chunk.get("text", "")).strip()

        if not text or looks_like_toc(text):
            continue

        tokens = tokenize_list(text)

        if not tokens:
            continue

        chunks.append(chunk)
        corpus_tokens.append(tokens)

    bm25 = BM25Okapi(corpus_tokens) if corpus_tokens else None

    _BM25_CACHE = {
        "chunks": chunks,
        "bm25": bm25,
    }

    return _BM25_CACHE


def bm25_retrieve(query: str, top_k: int = 10) -> list[dict]:
    index = _load_bm25_index()
    bm25 = index["bm25"]
    chunks = index["chunks"]

    if bm25 is None or not chunks:
        return []

    query_tokens = tokenize_list(query)

    if not query_tokens:
        return []

    scores = bm25.get_scores(query_tokens)

    ranked = sorted(
        zip(scores, chunks),
        key=lambda item: item[0],
        reverse=True,
    )

    results = []

    for score, chunk in ranked[:top_k]:
        if score <= 0:
            continue

        text = str(chunk.get("text", ""))

        results.append({
            "doc_id": chunk.get("doc_id"),
            "chunk_id": chunk.get("chunk_id"),
            "score": round(float(score), 4),
            "snippet": text[:800].replace("\n", " ").strip(),
            "retriever": "bm25",
        })

    return results


def clear_bm25_cache() -> None:
    global _BM25_CACHE
    _BM25_CACHE = None