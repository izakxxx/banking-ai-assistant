from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.retrieval.embeddings import embed_batch

INDEX_PATH = Path("data/index/chunks.json")
VECTOR_PATH = Path("data/index/vectors.json")

BATCH_SIZE = 100


def batch_items(items: list[dict[str, Any]], batch_size: int):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


def build_vector_index() -> None:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"No existe el índice de chunks: {INDEX_PATH}")

    chunks: list[dict[str, Any]] = json.loads(
        INDEX_PATH.read_text(encoding="utf-8")
    )

    vectors: list[dict[str, Any]] = []
    valid_chunks: list[dict[str, Any]] = []

    skipped_empty = 0
    skipped_missing = 0

    for chunk in chunks:
        doc_id = chunk.get("doc_id")
        chunk_id = chunk.get("chunk_id")
        text = chunk.get("text")

        if not doc_id or not chunk_id or text is None:
            skipped_missing += 1
            continue

        clean_text = str(text).strip()

        if not clean_text:
            skipped_empty += 1
            continue

        valid_chunks.append({
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "text": clean_text,
        })

    total = len(valid_chunks)

    print(
        f"[INFO] chunks={len(chunks)} | valid={total} | "
        f"skipped_missing={skipped_missing} | skipped_empty={skipped_empty}"
    )

    for batch_number, batch in enumerate(
        batch_items(valid_chunks, BATCH_SIZE),
        start=1,
    ):
        texts = [item["text"] for item in batch]

        embeddings = embed_batch(texts)

        if len(embeddings) != len(batch):
            raise RuntimeError(
                f"Embedding count mismatch. "
                f"batch={len(batch)} embeddings={len(embeddings)}"
            )

        for item, vector in zip(batch, embeddings):
            vectors.append({
                "doc_id": item["doc_id"],
                "chunk_id": item["chunk_id"],
                "vector": vector,
                "text": item["text"],
            })

        print(
            f"[OK] batch={batch_number} | "
            f"processed={len(vectors)}/{total}"
        )

    VECTOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    VECTOR_PATH.write_text(
        json.dumps(vectors, ensure_ascii=False),
        encoding="utf-8",
    )

    print(
        f"[OK] vectors.json generado: {VECTOR_PATH} | "
        f"items={len(vectors)}"
    )


if __name__ == "__main__":
    build_vector_index()