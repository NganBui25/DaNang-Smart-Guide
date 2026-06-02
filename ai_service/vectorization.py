from __future__ import annotations

import logging
import os
from typing import Dict, List, Tuple

import numpy as np

try:
    import faiss
except ImportError:  # pragma: no cover - runtime fallback is covered instead.
    faiss = None

try:
    from models.embedder import get_embedding
except ImportError:  # pragma: no cover - supports package-style imports in tests.
    from ai_service.models.embedder import get_embedding


logger = logging.getLogger(__name__)

FAISS_AVAILABLE = faiss is not None
SEARCH_BACKEND_DEFAULT = "faiss"


def encode_text(text: str) -> np.ndarray | None:
    vector = get_embedding(text)
    if vector is None:
        return None
    return np.asarray(vector, dtype=np.float32)


def normalize_vector(vector: np.ndarray) -> np.ndarray:
    result = np.asarray(vector, dtype=np.float32).reshape(-1)
    norm = np.linalg.norm(result)
    if norm == 0:
        return result
    return result / norm


def normalize_matrix(matrix: np.ndarray) -> np.ndarray:
    result = np.asarray(matrix, dtype=np.float32)
    if result.size == 0:
        return result
    norms = np.linalg.norm(result, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return result / norms


def get_search_backend_name(preferred: str | None = None) -> str:
    backend = (preferred or os.getenv("SEARCH_BACKEND", SEARCH_BACKEND_DEFAULT)).strip().lower()
    if backend not in {"faiss", "numpy"}:
        logger.warning(
            "Unsupported SEARCH_BACKEND='%s'; falling back to '%s'.",
            backend,
            SEARCH_BACKEND_DEFAULT,
        )
        backend = SEARCH_BACKEND_DEFAULT

    if backend == "faiss" and not FAISS_AVAILABLE:
        return "numpy"
    return backend


def _compute_similarity_numpy(
    ids: list[str],
    matrix: np.ndarray,
    query: np.ndarray,
    top_k: int,
) -> List[Tuple[str, float]]:
    scores = matrix @ query
    order = np.argsort(scores)[::-1][:top_k]
    return [(ids[int(idx)], float(scores[int(idx)])) for idx in order]


def _compute_similarity_faiss(
    ids: list[str],
    matrix: np.ndarray,
    query: np.ndarray,
    top_k: int,
) -> List[Tuple[str, float]]:
    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(np.ascontiguousarray(matrix, dtype=np.float32))
    scores, positions = index.search(
        np.ascontiguousarray(query.reshape(1, -1), dtype=np.float32),
        min(top_k, len(ids)),
    )

    results: list[tuple[str, float]] = []
    for position, score in zip(positions[0], scores[0]):
        if position == -1:
            continue
        results.append((ids[int(position)], float(score)))
    return results


def compute_similarity_batch(
    query_vec: np.ndarray,
    vectors_dict: Dict[str, np.ndarray],
    top_k: int = 5,
    search_backend: str | None = None,
) -> List[Tuple[str, float]]:
    if query_vec is None or not vectors_dict or top_k <= 0:
        return []

    ids = list(vectors_dict.keys())
    matrix = np.asarray(list(vectors_dict.values()), dtype=np.float32)
    query = np.asarray(query_vec, dtype=np.float32).reshape(-1)

    if matrix.ndim != 2 or query.ndim != 1 or matrix.shape[1] != query.shape[0]:
        logger.warning(
            "Vector dimension mismatch while searching: matrix=%s query=%s",
            matrix.shape,
            query.shape,
        )
        return []

    normalized_matrix = normalize_matrix(matrix)
    normalized_query = normalize_vector(query)
    backend_name = get_search_backend_name(search_backend)

    if backend_name == "faiss":
        try:
            return _compute_similarity_faiss(ids, normalized_matrix, normalized_query, top_k)
        except Exception as exc:  # pragma: no cover - exercised via fallback behavior.
            logger.warning("FAISS search failed, falling back to numpy: %s", exc)

    return _compute_similarity_numpy(ids, normalized_matrix, normalized_query, top_k)
