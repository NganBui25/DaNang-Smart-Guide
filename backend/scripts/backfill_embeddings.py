"""
Backfill embedding_vector for approved places that don't have vectors yet.

Usage:
    python scripts/backfill_embeddings.py
"""

from __future__ import annotations

import os
import sys

import django


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
AI_SERVICE_DIR = os.path.join(PROJECT_ROOT, "ai_service")

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, AI_SERVICE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from places.models import Place  # noqa: E402
from models.embedder import build_place_text, get_embedding  # noqa: E402


def build_text(place: Place) -> str:
    tags_text = " ".join(place.tags.values_list("name", flat=True))
    category_name = place.category.name if place.category else ""
    return build_place_text(
        name=place.name or "",
        address=place.address or "",
        description=(place.description or "") + (" " + tags_text if tags_text else ""),
        category=category_name,
    )


def run() -> None:
    qs = (
        Place.objects.filter(status="APPROVED", embedding_vector__isnull=True)
        .select_related("category")
        .prefetch_related("tags")
    )
    total = qs.count()
    if total == 0:
        print("[done] no places need backfill.")
        return

    print(f"[backfill] places to process: {total}")
    updated = 0

    for idx, place in enumerate(qs, start=1):
        text = build_text(place)
        vector = get_embedding(text)
        if not vector:
            continue
        Place.objects.filter(pk=place.pk).update(embedding_vector=vector)
        updated += 1
        if updated % 20 == 0:
            print(f"[backfill] updated {updated}/{total}")

    print(f"[done] embedding backfill completed: {updated}/{total}")


if __name__ == "__main__":
    run()
