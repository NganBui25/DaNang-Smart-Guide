"""
Import seed place data from JSON files into Django models.

Usage:
    python scripts/import_data.py

Run this command from the backend/ directory or project root.
"""

from __future__ import annotations

import json
import os
import sys

import django


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from places.models import Category, Place, PlaceImage  # noqa: E402


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

FILES = {
    "Cafe": "places_coffee.json",
    "Quan an": "places_food.json",
    "Vui choi": "places_play.json",
}


def safe_text(value: object) -> str:
    return str(value).encode("ascii", "backslashreplace").decode("ascii")


def normalize_image_url(raw_path: str) -> str:
    if not raw_path:
        return ""

    path = raw_path.replace("\\", "/").strip()
    if path.startswith(("http://", "https://", "/media/")):
        return path
    if path.startswith("data/"):
        return "/media/" + path[len("data/") :]
    if path.startswith("image/"):
        return "/media/" + path
    return "/media/image/" + os.path.basename(path)


def run_import() -> None:
    total_new_places = 0

    for category_name, filename in FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[warn] missing file: {filepath}. skip.")
            continue

        category, _ = Category.objects.get_or_create(name=category_name)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"[import] {filename}: {len(data)} places")

        for _, place_data in data.items():
            name = (place_data.get("name") or "").strip()
            log_name = safe_text(name)
            if not name:
                continue

            coords = place_data.get("coordinate") or [None, None]
            try:
                lat = float(coords[0]) if coords and coords[0] else None
                lng = float(coords[1]) if len(coords) > 1 and coords[1] else None
            except (TypeError, ValueError):
                lat, lng = None, None

            place, created = Place.objects.get_or_create(
                name=name,
                defaults={
                    "address": place_data.get("address", "") or "",
                    "lat": lat,
                    "lng": lng,
                    "category": category,
                    "status": "APPROVED",
                    "is_hidden_gem": False,
                },
            )

            raw_image_path = place_data.get("image_path") or ""
            image_url = normalize_image_url(raw_image_path)
            if image_url:
                has_primary = PlaceImage.objects.filter(place=place, is_primary=True).exists()
                PlaceImage.objects.get_or_create(
                    place=place,
                    image_url=image_url,
                    defaults={"is_primary": not has_primary},
                )

            if created:
                total_new_places += 1
                print(f"  [+] {log_name}")
            else:
                print(f"  [skip] {log_name} already exists (image checked)")

    print(f"[done] imported {total_new_places} new places.")


if __name__ == "__main__":
    run_import()
