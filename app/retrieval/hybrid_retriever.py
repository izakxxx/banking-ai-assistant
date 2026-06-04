from app.retrieval.retriever import retrieve as keyword_retrieve
from app.retrieval.semantic_retriever import semantic_retrieve

def hybrid_retrieve(query: str, top_k: int = 5) -> list[dict]:
    # Pedimos más para fusionar mejor
    kw_results = keyword_retrieve(query, top_k=10)
    sem_results = semantic_retrieve(query, top_k=40, min_score=0.10)

    # Reciprocal Rank Fusion (RRF)
    rrf_k = 30.0

    combined: dict[tuple, dict] = {}
    scores: dict[tuple, float] = {}

    def add_ranked(results: list[dict], source: str) -> None:
        for rank, r in enumerate(results, start=1):
            key = (r["doc_id"], r["chunk_id"])

            if key not in combined:
                combined[key] = {**r, "sources": [source]}
            else:
                combined[key]["sources"].append(source)

            weight = 1.0 if source == "keyword" else 1.4
            scores[key] = scores.get(key, 0.0) + weight * (1.0 / (rrf_k + rank))

    add_ranked(kw_results, "keyword")
    add_ranked(sem_results, "semantic")

    merged = []
    for key, item in combined.items():
        merged.append({**item, "score": round(scores[key], 6)})

    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged[:top_k]
