import re

def looks_like_toc(text: str) -> bool:
    # Marcadores típicos de menús / índices de docs técnicas
    markers = ["RESOURCES", "List ", "Retrieve", "template", "POST", "GET", "PUT", "DELETE"]
    hits = sum(1 for m in markers if m.lower() in text.lower())
    if hits >= 4:
        return True

    # Heurística adicional: muchas líneas cortas suele ser índice/menú
    lines = text.splitlines()
    if len(lines) >= 20:
        short = sum(1 for ln in lines if 1 <= len(ln.strip()) <= 45)
        if short / len(lines) > 0.65:
            return True

    return False


def tokenize_list(text: str) -> list[str]:
    text = text.lower()
    # Permitimos underscore para tokens técnicos: external_id, chunk_id, feeOnMonthDay, etc.
    text = re.sub(r"[^a-z0-9_\s]", " ", text)
    return [t for t in text.split() if len(t) > 2]


def tokenize_set(text: str) -> set[str]:
    return set(tokenize_list(text))
