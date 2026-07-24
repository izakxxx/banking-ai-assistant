from __future__ import annotations

from app.retrieval.util import tokenize_set


DOMAIN_TERMS = {
    "mandatory": 0.20,
    "fields": 0.15,
    "chargeid": 0.25,
    "amount": 0.20,
    "feeonmonthday": 0.25,
    "monthdayformat": 0.25,
    "locale": 0.15,
    "dateformat": 0.15,
    "post": 0.10,
    "command": 0.10,
    "paycharge": 0.20,
    "savingsaccountchargeid": 0.20,
}


NEGATIVE_CONTEXT_TERMS = {
    "paycharge": 0.70,
    "waive": 0.40,
    "inactivate": 0.40,
    "delete": 0.35,
}


def detect_query_context(query: str) -> str:
    q = query.lower()

    if "pay" in q and "charge" in q:
        return "pay_charge"

    if "activate" in q and "savings account" in q:
        return "activate_savings"

    if "fields" in q and "charge" in q:
        return "charge_fields"

    if "monthly fee" in q:
        return "monthly_fee"

    return "general"


def rerank_results(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
) -> list[dict]:
    q_terms = tokenize_set(query)

    if not q_terms:
        return candidates[:top_k]

    reranked = []

    for item in candidates:
        snippet = item.get("snippet", "")
        normalized_snippet = snippet.lower().replace("_", "").replace("-", "")

        t_terms = tokenize_set(snippet)

        overlap = q_terms & t_terms
        overlap_score = len(overlap) / max(len(q_terms), 1)

        base_score = float(item.get("score", 0.0))

        source_bonus = 0.0
        sources = item.get("sources", [])

        if "bm25" in sources:
            source_bonus += 0.15

        if "semantic" in sources:
            source_bonus += 0.25

        domain_bonus = 0.0
        matched_domain_terms = []

        for term, weight in DOMAIN_TERMS.items():
            if term in normalized_snippet:
                domain_bonus += weight
                matched_domain_terms.append(term)

        negative_penalty = 0.0
        matched_negative_terms = []

        for term, penalty in NEGATIVE_CONTEXT_TERMS.items():
            if term in normalized_snippet:
                negative_penalty += penalty
                matched_negative_terms.append(term)

        context_bonus = 0.0
        context_penalty = 0.0

        query_context = detect_query_context(query)

        if query_context == "pay_charge":
            if "paycharge" in normalized_snippet:
                context_bonus += 1.2
            if "delete" in normalized_snippet or "waive" in normalized_snippet or "inactivate" in normalized_snippet:
                context_penalty += 0.4

        if query_context == "activate_savings":
            if "activate a savings account" in normalized_snippet:
                context_bonus += 1.5
            if "gsim" in normalized_snippet:
                context_penalty += 1.0
            if "charge" in normalized_snippet:
                context_penalty += 1.0
            if "recurringdepositaccounts" in normalized_snippet:
                context_penalty += 0.8
            if "fixeddepositaccounts" in normalized_snippet:
                context_penalty += 0.8

        if query_context == "charge_fields":
            if "mandatory fields for savings account charges" in normalized_snippet:
                context_bonus += 1.5

        final_score = (
            base_score
            + overlap_score
            + source_bonus
            + domain_bonus
            + context_bonus
            - negative_penalty
            - context_penalty
        )

        reranked.append({
            **item,
            "rerank_score": round(final_score, 6),
            "matched_terms": sorted(list(overlap)),
            "matched_domain_terms": matched_domain_terms,
            "matched_negative_terms": matched_negative_terms,
        })

    reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

    return reranked[:top_k]