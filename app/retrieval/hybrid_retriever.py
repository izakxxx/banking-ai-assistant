from __future__ import annotations

from app.retrieval.bm25_retriever import bm25_retrieve
from app.retrieval.semantic_retriever import semantic_retrieve
from app.retrieval.reranker import rerank_results


def hybrid_retrieve(
    query: str,
    top_k: int = 5,
    bm25_k: int = 20,
    semantic_k: int = 40,
    use_reranker: bool = True,
) -> list[dict]:
    bm25_results = bm25_retrieve(query, top_k=bm25_k)
    semantic_results = semantic_retrieve(query, top_k=semantic_k, min_score=0.10)

    rrf_k = 30.0

    combined: dict[tuple, dict] = {}
    scores: dict[tuple, float] = {}

    def add_ranked(results: list[dict], source: str, weight: float) -> None:
        for rank, result in enumerate(results, start=1):
            key = (result["doc_id"], result["chunk_id"])

            if key not in combined:
                combined[key] = {
                    **result,
                    "sources": [source],
                }
            else:
                combined[key]["sources"].append(source)

            scores[key] = scores.get(key, 0.0) + weight * (1.0 / (rrf_k + rank))

    add_ranked(bm25_results, "bm25", weight=1.0)
    add_ranked(semantic_results, "semantic", weight=1.4)

    merged = []

    for key, item in combined.items():
        merged.append({
            **item,
            "score": round(scores[key], 6),
        })

    merged.sort(key=lambda x: x["score"], reverse=True)

    if not use_reranker:
        return merged[:top_k]

    return rerank_results(
        query=query,
        candidates=merged,
        top_k=top_k,
    )


def hybrid_retrieve_debug(query: str, top_k: int = 5) -> dict:
    bm25_results = bm25_retrieve(query, top_k=20)
    semantic_results = semantic_retrieve(query, top_k=40, min_score=0.10)

    final_results = hybrid_retrieve(
        query=query,
        top_k=top_k,
        bm25_k=20,
        semantic_k=40,
        use_reranker=True,
    )

    return {
        "query": query,
        "bm25_results": bm25_results,
        "semantic_results": semantic_results,
        "candidate_count": len({
            (item["doc_id"], item["chunk_id"])
            for item in bm25_results + semantic_results
        }),
        "reranked_results": final_results,
    }