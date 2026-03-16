"""
Build FAISS index from crawled JSON place data.

Usage:
    python scripts/sync_faiss.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any

import faiss
import numpy as np


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.embedder import build_place_text, get_embedding  # noqa: E402


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "backend", "data"))
INDEX_FILE = os.getenv(
    "INDEX_FILE",
    os.path.join(os.path.dirname(__file__), "..", "faiss_index", "places.index"),
)
ID_MAP_FILE = os.getenv(
    "ID_MAP_FILE",
    os.path.join(os.path.dirname(__file__), "..", "faiss_index", "id_map.json"),
)
VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "768"))

DATA_FILES = {
    "coffee": "places_coffee.json",
    "food": "places_food.json",
    "play": "places_play.json",
}


def _safe_text(value: Any) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def _ensure_output_dirs() -> None:
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(ID_MAP_FILE), exist_ok=True)


def _iter_records() -> list[tuple[str, str, dict[str, Any]]]:
    records: list[tuple[str, str, dict[str, Any]]] = []

    for category, filename in DATA_FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[sync] missing file, skip: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            iterable = data.items()
        elif isinstance(data, list):
            iterable = ((str(i), item) for i, item in enumerate(data))
        else:
            print(f"[sync] unsupported structure in {filename}, skip")
            continue

        count = 0
        for json_key, place in iterable:
            if not isinstance(place, dict):
                continue
            records.append((category, str(json_key), place))
            count += 1

        print(f"[sync] loaded {count} records from {filename}")

    return records


def run_sync() -> None:
    _ensure_output_dirs()
    started_at = time.time()

    records = _iter_records()
    if not records:
        raise RuntimeError("No input records found. Nothing to index.")

    vectors: list[list[float]] = []
    ids: list[int] = []
    id_map: dict[str, dict[str, Any]] = {}

    for faiss_id, (category, json_key, place) in enumerate(records):
        name = (place.get("name") or "").strip()
        log_name = _safe_text(name)
        address = (place.get("address") or "").strip()

        reviews = place.get("reviews") or []
        review_text = " ".join(
            str(r.get("content", "")) for r in reviews if isinstance(r, dict)
        )

        full_text = build_place_text(
            name=name,
            address=address,
            description=review_text,
            category=category,
        )

        try:
            vector = get_embedding(full_text)
        except Exception as exc:  # noqa: BLE001
            print(f"[sync] embedding failed for '{log_name}': {_safe_text(exc)}")
            continue

        if not vector:
            print(f"[sync] empty vector for '{log_name}', skip")
            continue

        if len(vector) != VECTOR_DIMENSION:
            print(
                f"[sync] dimension mismatch for '{log_name}': "
                f"{len(vector)} != {VECTOR_DIMENSION}, skip"
            )
            continue

        vectors.append(vector)
        ids.append(faiss_id)
        id_map[str(faiss_id)] = {
            "json_key": json_key,
            "name": name,
            "category": category,
            "rating": place.get("rating", ""),
            "address": address,
            "coordinate": place.get("coordinate", []),
            "image_path": place.get("image_path", ""),
        }

        if len(vectors) % 20 == 0:
            print(f"[sync] embedded {len(vectors)} places...")

    if not vectors:
        raise RuntimeError("No vectors were generated. Index was not written.")

    matrix = np.asarray(vectors, dtype=np.float32)
    id_array = np.asarray(ids, dtype=np.int64)

    index = faiss.IndexIDMap(faiss.IndexFlatL2(VECTOR_DIMENSION))
    index.add_with_ids(matrix, id_array)

    faiss.write_index(index, INDEX_FILE)
    with open(ID_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - started_at
    print(f"[done] vectors: {index.ntotal} | time: {elapsed:.1f}s")
    print(f"[done] index file: {INDEX_FILE}")
    print(f"[done] id map: {ID_MAP_FILE}")


if __name__ == "__main__":
    run_sync()
