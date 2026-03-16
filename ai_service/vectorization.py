from __future__ import annotations

import numpy as np

from models.embedder import get_embedding


def encode_text(text: str) -> list[float]:
    return get_embedding(text)


def compute_similarity_batch(query_vec: list[float], vectors_dict: dict[str, list[float]]) -> list[tuple[str, float]]:
    if not query_vec or not vectors_dict:
        return []

    ids = list(vectors_dict.keys())
    matrix = np.asarray([vectors_dict[i] for i in ids], dtype=np.float32)
    q = np.asarray(query_vec, dtype=np.float32)

    if matrix.ndim != 2 or q.ndim != 1 or matrix.shape[1] != q.shape[0]:
        return []

    matrix_norm = np.linalg.norm(matrix, axis=1)
    q_norm = np.linalg.norm(q)
    denom = matrix_norm * q_norm
    denom[denom == 0] = 1.0
    scores = (matrix @ q) / denom

    results = [(ids[i], float(scores[i])) for i in range(len(ids))]
    return sorted(results, key=lambda x: x[1], reverse=True)
