from __future__ import annotations

def infer_intent(question: str) -> str:
    q = question.lower().strip()

    # Monthly fee (más tolerante)
    if (
        "monthly" in q
        and ("fee" in q or "charge" in q)
        and (
            "savings" in q
            or "account" in q
            or "maintenance" in q
        )
    ):
        return "create_savings_monthly_fee"

    # Pay charge
    if (
        "pay" in q
        and ("charge" in q or "fee" in q)
        and ("savings" in q or "account" in q)
    ):
        return "pay_savings_charge"

    # Due date charge
    if (
        "due date" in q
        and ("charge" in q or "fee" in q)
        and ("savings" in q or "account" in q)
    ):
        return "create_savings_due_date_charge"

    # Deposit
    if (
        "deposit" in q
        and ("savings" in q or "account" in q)
    ):
        return "make_savings_deposit"

    return "unknown"