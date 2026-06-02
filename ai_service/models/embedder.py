from __future__ import annotations

import logging
import os
import re
from typing import Any

import numpy as np
from dotenv import load_dotenv

try:
    import torch
except ImportError:  # pragma: no cover - service requires torch at runtime.
    torch = None

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - service requires sentence-transformers at runtime.
    SentenceTransformer = None


logger = logging.getLogger(__name__)

load_dotenv()

TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "768"))
MODEL_NAME = os.getenv("SBERT_MODEL") or os.getenv("MODEL_NAME", "keepitreal/vietnamese-sbert")
REQUESTED_DEVICE = os.getenv("AI_DEVICE", "auto").strip().lower() or "auto"

_model: SentenceTransformer | None = None


def _cuda_available() -> bool:
    return bool(torch and torch.cuda.is_available())


def resolve_device(
    preferred: str | None = None,
    cuda_available: bool | None = None,
) -> str:
    requested = (preferred or REQUESTED_DEVICE).strip().lower()
    if requested not in {"auto", "cpu", "cuda"}:
        raise RuntimeError(
            f"Unsupported AI_DEVICE='{requested}'. Expected one of: auto, cpu, cuda."
        )

    has_cuda = _cuda_available() if cuda_available is None else cuda_available

    if requested == "auto":
        return "cuda" if has_cuda else "cpu"
    if requested == "cpu":
        return "cpu"
    if not has_cuda:
        raise RuntimeError("AI_DEVICE is set to 'cuda' but CUDA is not available.")
    return "cuda"


def get_runtime_info() -> dict[str, Any]:
    torch_version = getattr(torch, "__version__", "unavailable")
    cuda_available = _cuda_available()
    device = resolve_device(cuda_available=cuda_available)

    gpu_name = None
    if device == "cuda" and torch is not None:
        try:
            gpu_name = torch.cuda.get_device_name(0)
        except Exception:  # pragma: no cover - defensive logging only.
            gpu_name = None

    return {
        "requested_device": REQUESTED_DEVICE,
        "device": device,
        "model_name": MODEL_NAME,
        "vector_dimension": VECTOR_DIMENSION,
        "torch_version": torch_version,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
    }


def is_model_loaded() -> bool:
    return _model is not None


def ensure_model_loaded(force_reload: bool = False) -> SentenceTransformer:
    global _model

    if force_reload:
        _model = None

    if _model is not None:
        return _model

    if torch is None:
        raise RuntimeError("torch is not installed in ai_service runtime.")
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers is not installed in ai_service runtime.")

    runtime = get_runtime_info()
    _model = SentenceTransformer(MODEL_NAME, device=runtime["device"])
    return _model


def get_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        return [0.0] * VECTOR_DIMENSION

    model = ensure_model_loaded()
    vector = model.encode(text, convert_to_numpy=True)
    return np.asarray(vector, dtype=np.float32).tolist()


def build_place_text(
    name: str,
    address: str = "",
    description: str = "",
    category: str = "",
) -> str:
    parts = [name]
    if category:
        parts.append(category)
    if address:
        parts.append(address)
    if description:
        parts.append(description)
    return ". ".join(filter(None, parts))


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall((text or "").lower())
