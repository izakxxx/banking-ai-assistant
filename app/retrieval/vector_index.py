# build_vectors.py
import json
from pathlib import Path
from typing import Any
from app.retrieval.embeddings import embed

INDEX_PATH = Path("data/index/chunks.json")
VECTOR_PATH = Path("data/index/vectors.json")


def build_vector_index() -> None:
    if not INDEX_PATH.exists():
        raise FileNotFoundError(f"No existe el índice de chunks: {INDEX_PATH}")

    chunks: list[dict[str, Any]] = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    vectors: list[dict[str, Any]] = []

    skipped_empty = 0
    skipped_missing = 0

    for chunk in chunks:
        doc_id = chunk.get("doc_id")
        chunk_id = chunk.get("chunk_id")
        text = chunk.get("text")

        if not doc_id or not chunk_id or text is None:
            skipped_missing += 1
            continue

        text = str(text).strip()
        if not text:
            skipped_empty += 1
            continue

        vec = embed(text)  # ✅ dict[str, float] serializable

        vectors.append({
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "vector": vec,
            "text": text,
        })

    VECTOR_PATH.parent.mkdir(parents=True, exist_ok=True)
    VECTOR_PATH.write_text(
        json.dumps(vectors, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"[OK] vectors.json generado: {VECTOR_PATH} | items={len(vectors)} | skipped_missing={skipped_missing} | skipped_empty={skipped_empty}")


if __name__ == "__main__":
    build_vector_index()
