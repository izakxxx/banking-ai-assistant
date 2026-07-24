from __future__ import annotations

from typing import Any


SECTION_LABELS = {
    "evidence_summary": "EVIDENCE SUMMARY",
    "request_body": "REQUEST BODY / EXAMPLE PAYLOAD",
    "required_fields": "REQUIRED FIELDS",
    "endpoint": "ENDPOINT / COMMAND EVIDENCE",
    "field_descriptions": "FIELD DESCRIPTIONS",
    "primary_evidence": "PRIMARY EVIDENCE",
    "related_notes": "RELATED NOTES",
}

DEFAULT_SECTION_PRIORITY = [
    "request_body",
    "required_fields",
    "endpoint",
    "field_descriptions",
    "primary_evidence",
    "related_notes",
]


def detect_context_intent(results: list[dict[str, Any]]) -> str:
    joined = " ".join(str(r.get("snippet", "")).lower() for r in results)

    if "paycharge" in joined:
        return "pay_savings_charge"

    if "command=activate" in joined and "activate a savings account" in joined:
        return "activate_savings_account"

    if "monthly fee" in joined or "feeonmonthday" in joined:
        return "create_savings_monthly_fee"

    if "mandatory fields for savings account charges" in joined:
        return "savings_charge_fields"

    return "general"


def classify_evidence(item: dict[str, Any]) -> str:
    snippet = str(item.get("snippet", "")).lower()

    if "request body" in snippet:
        return "request_body"

    if "mandatory fields" in snippet or "required fields" in snippet:
        return "required_fields"

    if "field descriptions" in snippet:
        return "field_descriptions"

    if "?command=" in snippet or "post " in snippet or "https://" in snippet:
        return "endpoint"

    return "primary_evidence"


def section_priority_for_intent(intent: str) -> list[str]:
    if intent == "pay_savings_charge":
        return [
            "request_body",
            "endpoint",
            "required_fields",
            "field_descriptions",
            "primary_evidence",
            "related_notes",
        ]

    if intent == "activate_savings_account":
        return [
            "endpoint",
            "request_body",
            "required_fields",
            "field_descriptions",
            "primary_evidence",
            "related_notes",
        ]

    if intent == "create_savings_monthly_fee":
        return [
            "required_fields",
            "request_body",
            "endpoint",
            "field_descriptions",
            "primary_evidence",
            "related_notes",
        ]

    if intent == "savings_charge_fields":
        return [
            "required_fields",
            "field_descriptions",
            "request_body",
            "endpoint",
            "primary_evidence",
            "related_notes",
        ]

    return DEFAULT_SECTION_PRIORITY


def build_evidence_summary(intent: str, results: list[dict[str, Any]]) -> str:
    snippets = " ".join(str(r.get("snippet", "")) for r in results)
    normalized = snippets.lower()

    lines = [
        "## EVIDENCE SUMMARY",
        f"Detected intent: {intent}",
    ]

    if intent == "pay_savings_charge":
        lines.extend([
            "Relevant operation: Pay a Savings Account Charge.",
            "Relevant endpoint pattern: POST /api/v1/savingsaccounts/{accountId}/charges/{savingsAccountChargeId}?command=paycharge",
            "Relevant payload fields: dateFormat, locale, amount, transactionDate.",
            "Business note: The savings account charge must be active and the savings account should have sufficient balance.",
        ])

    elif intent == "activate_savings_account":
        lines.extend([
            "Relevant operation: Activate a Savings Account.",
            "Relevant endpoint pattern: POST /api/v1/savingsaccounts/{savingsId}?command=activate",
            "Relevant payload fields: locale, dateFormat, activatedOnDate.",
            "Business note: Activation converts an approved savings application into an active savings account.",
        ])

    elif intent == "create_savings_monthly_fee":
        lines.extend([
            "Relevant operation: Apply/Create a Monthly Fee charge for a Savings Account.",
            "Relevant endpoint pattern: POST /api/v1/savingsaccounts/{accountId}/charges",
            "Relevant payload fields: chargeId, amount, feeOnMonthDay, monthDayFormat, locale, feeInterval.",
            "Business note: Monthly Fee uses chargeTimeType Monthly Fee and recurring date fields.",
        ])

    elif intent == "savings_charge_fields":
        lines.extend([
            "Relevant operation: Identify required fields for Savings Account Charges.",
            "Base required fields: chargeId, amount.",
            "Due-date charge fields: chargeId, amount, dueDate, dateFormat, locale.",
            "Annual/monthly fee fields may include feeOnMonthDay, monthDayFormat, locale and feeInterval depending on charge type.",
        ])

    else:
        lines.append("Relevant operation: General Fineract documentation lookup.")

    if "paycharge" in normalized and intent != "pay_savings_charge":
        lines.append("Related note: paycharge command appears in retrieved evidence but may not be the primary operation.")

    return "\n".join(lines)


def group_results(results: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "request_body": [],
        "required_fields": [],
        "endpoint": [],
        "field_descriptions": [],
        "primary_evidence": [],
        "related_notes": [],
    }

    for item in results:
        evidence_type = classify_evidence(item)

        if evidence_type not in buckets:
            evidence_type = "related_notes"

        buckets[evidence_type].append(item)

    for items in buckets.values():
        items.sort(
            key=lambda x: float(x.get("rerank_score") or x.get("score") or 0),
            reverse=True,
        )

    return buckets


def render_context_item(item: dict[str, Any], index: int) -> str:
    return "\n".join([
        f"[{index}] Source: {item.get('doc_id')} / {item.get('chunk_id')}",
        str(item.get("snippet", "")).strip(),
    ])


def build_rag_context(results: list[dict[str, Any]]) -> str:
    intent = detect_context_intent(results)
    buckets = group_results(results)
    priority = section_priority_for_intent(intent)

    sections = [
        build_evidence_summary(intent=intent, results=results)
    ]

    for key in priority:
        items = buckets.get(key, [])

        if not items:
            continue

        label = SECTION_LABELS.get(key, key.upper())

        section_lines = [f"## {label}"]

        for index, item in enumerate(items, start=1):
            section_lines.append(render_context_item(item, index))

        sections.append("\n\n".join(section_lines))

    return "\n\n---\n\n".join(sections)


def build_context_debug(results: list[dict[str, Any]]) -> dict[str, Any]:
    intent = detect_context_intent(results)
    grouped = group_results(results)

    return {
        "detected_intent": intent,
        "section_priority": section_priority_for_intent(intent),
        "groups": {
            key: [
                {
                    "doc_id": item.get("doc_id"),
                    "chunk_id": item.get("chunk_id"),
                    "score": item.get("score"),
                    "rerank_score": item.get("rerank_score"),
                    "sources": item.get("sources"),
                    "evidence_type": classify_evidence(item),
                    "snippet": item.get("snippet"),
                }
                for item in items
            ]
            for key, items in grouped.items()
        },
    }