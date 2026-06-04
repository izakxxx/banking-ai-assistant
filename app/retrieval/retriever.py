import json
from pathlib import Path
from app.retrieval.util import looks_like_toc, tokenize_set

INDEX_PATH = Path("data/index/chunks.json")

def retrieve(query: str, top_k: int = 5) -> list[dict]:
    if not INDEX_PATH.exists():
        return []

    chunks = json.loads(INDEX_PATH.read_text(encoding="utf-8"))

    q_terms = tokenize_set(query)
    scored = []

    for chunk in chunks:
        text = chunk["text"]

        if looks_like_toc(text):
            continue

        t_terms = tokenize_set(text)
        overlap = q_terms & t_terms
        if not overlap:
            continue

        score = float(len(overlap))

        scored.append({
            "doc_id": chunk["doc_id"],
            "chunk_id": chunk["chunk_id"],
            "score": score,
            "snippet": text[:350].replace("\n", " ").strip(),
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]
