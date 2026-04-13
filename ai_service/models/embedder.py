"""SentenceTransformer embedder with automatic CPU/GPU fallback."""

from __future__ import annotations

import logging
import os

import torch
from sentence_transformers import SentenceTransformer


logger = logging.getLogger(__name__)
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "768"))
MODEL_NAME = os.getenv("SBERT_MODEL", "keepitreal/vietnamese-sbert")
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer(MODEL_NAME, device=DEVICE)

logger.info("Loaded embedding model '%s' on device=%s", MODEL_NAME, DEVICE)


def is_model_loaded() -> bool:
    return model is not None


def get_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        return [0.0] * VECTOR_DIMENSION

    vector = model.encode(
        text,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
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
