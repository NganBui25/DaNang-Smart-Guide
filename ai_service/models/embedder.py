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


VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "768"))
TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall((text or "").lower())


def is_model_loaded() -> bool:
    # Kept for backward compatibility with existing health checks.
    return True


def get_embedding(text: str) -> list[float]:
    tokens = _tokenize(text)
    if not tokens:
        return [0.0] * VECTOR_DIMENSION

    vec = [0.0] * VECTOR_DIMENSION
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "big") % VECTOR_DIMENSION
        sign = 1.0 if (digest[4] & 1) == 0 else -1.0
        vec[idx] += sign

    norm = sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def build_place_text(name: str, address: str = "", description: str = "", category: str = "") -> str:
    parts = [name]
    if category:
        parts.append(category)
    if address:
        parts.append(address)
    if description:
        parts.append(description)
    return ". ".join(filter(None, parts))
