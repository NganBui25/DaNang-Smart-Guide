"""
Import seed place data from JSON files into Django models.

Usage:
    python scripts/import_data.py

Run this command from the backend/ directory or project root.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from typing import Iterable

import django


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
django.setup()

from places.models import Category, Place, PlaceImage  # noqa: E402
from reviews.models import Review  # noqa: E402
from users.models import User  # noqa: E402
from django.utils.text import slugify  # noqa: E402


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


def clean_text(value: object) -> str:
    return str(value or "").strip()


def build_description(place_data: dict) -> str:
    explicit_description = clean_text(place_data.get("description"))
    if explicit_description:
        return explicit_description

    snippets: list[str] = []
    seen = set()
    for review in place_data.get("reviews") or []:
        content = clean_text(review.get("content"))
        if len(content) < 20:
            continue
        canonical = re.sub(r"\s+", " ", content.casefold())
        if canonical in seen:
            continue
        seen.add(canonical)
        snippets.append(content)
        if len(snippets) == 2:
            break

    description = "\n\n".join(snippets)
    if len(description) > 1200:
        description = description[:1197].rstrip() + "..."
    return description


def parse_review_rating(raw_rating: object) -> int | None:
    match = re.search(r"(\d+)", clean_text(raw_rating))
    if not match:
        return None
    rating = int(match.group(1))
    if 1 <= rating <= 5:
        return rating
    return None


def build_seed_username(reviewer_name: str) -> str:
    base = slugify(reviewer_name).replace("-", "_") or "reviewer"
    digest = hashlib.sha1(reviewer_name.encode("utf-8")).hexdigest()[:8]
    return f"seed_{base[:40]}_{digest}"


def get_or_create_seed_user(reviewer_name: str) -> User:
    display_name = clean_text(reviewer_name) or "Nguoi dung seed"
    username = build_seed_username(display_name)
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": f"{username}@seed.local",
            "first_name": display_name,
            "role": "user",
            "is_active": True,
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    elif not user.first_name:
        user.first_name = display_name
        user.save(update_fields=["first_name"])
    return user


def sync_reviews(place: Place, raw_reviews: Iterable[dict]) -> int:
    imported_count = 0

    for raw_review in raw_reviews:
        comment = clean_text(raw_review.get("content"))
        rating = parse_review_rating(raw_review.get("rating"))
        if not comment or rating is None:
            continue

        user = get_or_create_seed_user(clean_text(raw_review.get("reviewer_name")))
        review, created = Review.objects.update_or_create(
            user=user,
            place=place,
            defaults={
                "rating": rating,
                "comment": comment,
            },
        )
        if created or review.comment == comment:
            imported_count += 1

    return imported_count


def run_import() -> None:
    total_new_places = 0
    total_synced_reviews = 0

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

            updated_fields: list[str] = []
            next_address = place_data.get("address", "") or ""
            description = build_description(place_data)

            if place.address != next_address:
                place.address = next_address
                updated_fields.append("address")
            if place.lat != lat:
                place.lat = lat
                updated_fields.append("lat")
            if place.lng != lng:
                place.lng = lng
                updated_fields.append("lng")
            if place.category_id != category.id:
                place.category = category
                updated_fields.append("category")
            if place.status != "APPROVED":
                place.status = "APPROVED"
                updated_fields.append("status")
            if description and place.description != description:
                place.description = description
                updated_fields.append("description")

            if updated_fields:
                place.save(update_fields=updated_fields + ["updated_at"])

            raw_image_path = place_data.get("image_path") or ""
            image_url = normalize_image_url(raw_image_path)
            if image_url:
                has_primary = PlaceImage.objects.filter(place=place, is_primary=True).exists()
                PlaceImage.objects.get_or_create(
                    place=place,
                    image_url=image_url,
                    defaults={"is_primary": not has_primary},
                )

            synced_reviews = sync_reviews(place, place_data.get("reviews") or [])
            total_synced_reviews += synced_reviews

            if created:
                total_new_places += 1
                print(f"  [+] {log_name}")
            else:
                print(f"  [sync] {log_name} updated")

    print(f"[done] imported {total_new_places} new places, synced {total_synced_reviews} reviews.")


if __name__ == "__main__":
    run_import()
