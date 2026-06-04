import re
import numpy as np
from collections import Counter
from typing import Mapping, Union
from sentence_transformers import SentenceTransformer

SparseVector = Union[Counter, Mapping[str, float]]
_model = SentenceTransformer("all-MiniLM-L6-v2")

def tokenize(text: str) -> list[str]:
    """
    Tokenizer simple para texto técnico.
    - lower
    - mantiene underscore (_) para identifiers tipo feeOnMonthDay, chunk_id, etc.
    - filtra tokens muy cortos
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9_\s]", " ", text)
    return [t for t in text.split() if len(t) > 2]


def embed(text: str) -> list[float]:
    return _model.encode(text).tolist()

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    v1 = np.array(v1)
    v2 = np.array(v2)

    if v1.size == 0 or v2.size == 0:
        return 0.0

    return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
