from __future__ import annotations

import logging
import os

import requests


logger = logging.getLogger(__name__)
GEOCODING_TIMEOUT = float(os.getenv("GEOCODING_TIMEOUT", "5"))
DEFAULT_CITY_SUFFIX = os.getenv("GEOCODING_CITY_HINT", "Da Nang, Viet Nam")


def _build_search_text(query: str) -> str:
    cleaned = (query or "").strip()
    if not cleaned:
        return ""
    if DEFAULT_CITY_SUFFIX.lower() in cleaned.lower():
        return cleaned
    return f"{cleaned}, {DEFAULT_CITY_SUFFIX}"


def _google_maps_geocode(query: str) -> tuple[float | None, float | None]:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("MAPS_API_KEY")
    if not api_key:
        return None, None

    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "address": _build_search_text(query),
                "key": api_key,
                "language": "vi",
                "region": "vn",
            },
            timeout=GEOCODING_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logger.warning("Google Maps geocoding request failed for %r: %s", query, exc)
        return None, None

    if payload.get("status") != "OK":
        logger.info("Google Maps geocoding returned status=%s for %r", payload.get("status"), query)
        return None, None

    results = payload.get("results") or []
    if not results:
        return None, None

    location = (((results[0] or {}).get("geometry") or {}).get("location") or {})
    lat = location.get("lat")
    lng = location.get("lng")
    if lat is None or lng is None:
        return None, None
    return float(lat), float(lng)


def _nominatim_geocode(query: str) -> tuple[float | None, float | None]:
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": _build_search_text(query),
                "format": "jsonv2",
                "limit": 1,
            },
            headers={"User-Agent": "DaNangSmartGuide/1.0"},
            timeout=GEOCODING_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        logger.warning("Nominatim geocoding request failed for %r: %s", query, exc)
        return None, None

    if not payload:
        return None, None

    lat = payload[0].get("lat")
    lng = payload[0].get("lon")
    if lat is None or lng is None:
        return None, None
    return float(lat), float(lng)


def get_coordinates(query: str) -> tuple[float | None, float | None]:
    provider = (os.getenv("GEOCODING_PROVIDER") or "auto").strip().lower()
    if provider == "disabled":
        return None, None

    providers: list[str]
    if provider == "auto":
        providers = ["google_maps", "nominatim"]
    else:
        providers = [provider]

    for selected in providers:
        if selected == "google_maps":
            lat, lng = _google_maps_geocode(query)
        elif selected == "nominatim":
            lat, lng = _nominatim_geocode(query)
        else:
            logger.warning("Unsupported geocoding provider: %s", selected)
            continue

        if lat is not None and lng is not None:
            return lat, lng

    return None, None
