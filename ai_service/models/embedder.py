"""
Lightweight deterministic text embedding helper.

This implementation avoids heavyweight ML model downloads so the demo stack can
run reliably in constrained environments. It uses hashed token features with
L2 normalization to produce fixed-size vectors.
"""

from __future__ import annotations

import hashlib
import os
import re
from math import sqrt
from sentence_transformers import SentenceTransformer

#VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "768"))
TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
VECTOR_DIMENSION = 768
MODEL_NAME = os.getenv("SBERT_MODEL", "keepitreal/vietnamese-sbert")
model = SentenceTransformer(MODEL_NAME)

def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall((text or "").lower())


def is_model_loaded() -> bool:
    # Kept for backward compatibility with existing health checks.
    return True


def get_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        return [0.0] * VECTOR_DIMENSION
    vector = model.encode(text)
    return vector.tolist()

def build_place_text(name: str, address: str = "", description: str = "", category: str = "") -> str:
    parts = [name]
    if category:
        parts.append(category)
    if address:
        parts.append(address)
    if description:
        parts.append(description)
    return ". ".join(filter(None, parts))
