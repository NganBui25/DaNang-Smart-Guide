from __future__ import annotations

import json
import os
import re
import unicodedata

from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    genai = None


load_dotenv()

API_KEY = os.getenv("LLM_API_KEY")
if genai is None:
    print("WARNING: google-generativeai is not installed; query parser will use fallback mode.")
elif not API_KEY:
    print("WARNING: LLM_API_KEY was not found; query parser will use fallback mode.")
else:
    genai.configure(api_key=API_KEY)


SYSTEM_PROMPT = """
Ban la mot tro ly trich xuat du lieu tim kiem dia diem tai Da Nang.
Doc cau truy van va tra ve JSON chinh xac:
{
    "category": "Loai dia diem (vd: quan cafe, nha hang). Neu khong ro, tra ve null",
    "location_anchor": "Khu vuc hoac moc (vd: song Han). Neu khong co, tra ve null",
    "location_type": "Chi duoc chon 'point' neu moc la mot diem cu the, hoac 'area' neu moc la khu vuc rong/ten duong. Neu khong co location_anchor, tra ve null",
    "distance_rule": {
        "operator": "Chi chon 1 trong 3 dau: '<', '>', '='. Neu khong co, tra ve null",
        "value": "So Km dang so nguyen. Neu khong co, tra ve null"
    },
    "semantic_text": "Phan text mo ta khong gian, cam giac..."
}
Chi tra ve dung JSON, khong them giai thich.
"""

CATEGORY_PATTERNS = (
    ("Cafe", ("quan cafe", "ca phe", "ca phe", "cafe", "coffee", "quan ca phe")),
    ("Quan an", ("nha hang", "quan an", "an vat", "am thuc", "restaurant", "food", "nuong")),
    ("Vui choi", ("vui choi", "giai tri", "tre em", "kids", "kid", "play")),
)

LOCATION_RULES = (
    ("bien", "area", ("gan bien", "ven bien", "sat bien", "bo bien"), {"operator": "<", "value": 5}),
    ("song han", "point", ("gan song han", "ven song han", "sat song han", "song han"), {"operator": "<", "value": 3}),
    (None, None, ("gan toi", "gan day", "xung quanh toi", "quanh day"), {"operator": "<", "value": 3}),
)

AREA_HINTS = (
    "quan ",
    "phuong ",
    "duong ",
    "hem ",
    "khu ",
    "thanh pho ",
    "huyen ",
)

POINT_HINTS = (
    "cau ",
    "cho ",
    "ben xe",
    "san bay",
    "toa nha",
    "cong vien",
    "bao tang",
    "hai dang",
)
TRAILING_LOCATION_STOPWORDS = {"khong", "nao", "nhe", "a", "ha", "ay", "day"}

GENERIC_TOKENS = {
    "an",
    "cho",
    "choi",
    "coffee",
    "da",
    "dia",
    "diem",
    "gan",
    "hang",
    "khu",
    "nang",
    "nha",
    "noi",
    "phe",
    "quan",
    "song",
    "toi",
    "tra",
    "vui",
    "ven",
    "sat",
    "bien",
    "han",
    "ca",
    "cafe",
}
WORD_PATTERN = re.compile(r"\w+", re.UNICODE)
LOCATION_EXTRACTORS = (
    ("area", re.compile(r"\b(?:o|gan|xa|ven|sat|tai)\s+(quan\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,2})\b")),
    ("area", re.compile(r"\b(?:o|gan|xa|ven|sat|tai)\s+(phuong\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,2})\b")),
    ("area", re.compile(r"\b(?:o|gan|xa|ven|sat|tai)\s+(duong\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,3})\b")),
    ("area", re.compile(r"\b(?:o|gan|xa|ven|sat|tai)\s+(thanh pho\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,2})\b")),
    ("point", re.compile(r"\b(cau\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,2})\b")),
    ("point", re.compile(r"\b(ben xe\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,2})\b")),
    ("point", re.compile(r"\b(san bay\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,2})\b")),
    ("point", re.compile(r"\b(cong vien\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,2})\b")),
    ("point", re.compile(r"\b(bao tang\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,2})\b")),
    ("point", re.compile(r"\b(hai dang\s+[a-z0-9]+(?:\s+[a-z0-9]+){0,2})\b")),
)


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", value)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().strip()


def _normalize_tokens(value: str | None) -> list[str]:
    return [_normalize_text(token) for token in WORD_PATTERN.findall(value or "")]


def _normalize_category(category: str | None) -> str | None:
    category_norm = _normalize_text(category)
    if not category_norm:
        return None

    for canonical_name, patterns in CATEGORY_PATTERNS:
        if category_norm == _normalize_text(canonical_name):
            return canonical_name
        if any(pattern in category_norm for pattern in patterns):
            return canonical_name
    return category.strip() if category else None


def _infer_category(query: str) -> str | None:
    normalized_query = _normalize_text(query)
    for canonical_name, patterns in CATEGORY_PATTERNS:
        if any(pattern in normalized_query for pattern in patterns):
            return canonical_name
    return None


def _infer_location(query: str) -> tuple[str | None, str | None, dict | None]:
    normalized_query = _normalize_text(query)
    for anchor, location_type, patterns, distance_rule in LOCATION_RULES:
        if any(pattern in normalized_query for pattern in patterns):
            return anchor, location_type, distance_rule.copy()
    return None, None, None


def _extract_location_hint(query: str) -> tuple[str | None, str | None]:
    normalized_query = _normalize_text(query)
    for location_type, pattern in LOCATION_EXTRACTORS:
        match = pattern.search(normalized_query)
        if match:
            anchor = match.group(1).strip()
            anchor_tokens = anchor.split()
            while anchor_tokens and anchor_tokens[-1] in TRAILING_LOCATION_STOPWORDS:
                anchor_tokens.pop()
            cleaned_anchor = " ".join(anchor_tokens).strip()
            if cleaned_anchor:
                return cleaned_anchor, location_type
    return None, None


def _normalize_location_type(location_type: str | None, anchor: str | None) -> str | None:
    normalized_type = _normalize_text(location_type)
    if normalized_type in {"point", "area"}:
        return normalized_type

    anchor_norm = _normalize_text(anchor)
    if not anchor_norm:
        return None

    if any(anchor_norm.startswith(prefix) for prefix in AREA_HINTS):
        return "area"
    if any(token in anchor_norm for token in POINT_HINTS):
        return "point"
    if anchor_norm in {"bien"}:
        return "area"
    if anchor_norm in {"song han"}:
        return "point"
    return None


def _clean_distance_rule(distance_rule: dict | None) -> dict | None:
    if not isinstance(distance_rule, dict):
        return None

    operator = distance_rule.get("operator")
    value = distance_rule.get("value")
    if operator not in {"<", ">", "=", "<=", ">="}:
        return None
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return None
    return {"operator": operator, "value": int(numeric_value) if numeric_value.is_integer() else numeric_value}


def _build_semantic_text(query: str) -> str:
    kept_tokens: list[str] = []
    for token in WORD_PATTERN.findall(query or ""):
        normalized = _normalize_text(token)
        if len(normalized) < 2 or normalized in GENERIC_TOKENS:
            continue
        kept_tokens.append(token)

    semantic_text = " ".join(kept_tokens).strip()
    return semantic_text or (query or "").strip()


def _post_process_parsed_intent(query: str, parsed: dict | None) -> dict:
    parsed = parsed or {}

    inferred_category = _infer_category(query)
    inferred_anchor, inferred_location_type, inferred_distance = _infer_location(query)
    extracted_anchor, extracted_location_type = _extract_location_hint(query)
    normalized_category = _normalize_category(parsed.get("category")) or inferred_category
    normalized_anchor = parsed.get("location_anchor")
    if normalized_anchor:
        normalized_anchor = _normalize_text(normalized_anchor)
    if not normalized_anchor:
        normalized_anchor = inferred_anchor or extracted_anchor

    normalized_location_type = (
        _normalize_location_type(parsed.get("location_type"), normalized_anchor)
        or inferred_location_type
        or extracted_location_type
    )
    cleaned_distance_rule = _clean_distance_rule(parsed.get("distance_rule")) or inferred_distance
    semantic_text = _build_semantic_text(parsed.get("semantic_text") or query)

    return {
        "category": normalized_category,
        "location_anchor": normalized_anchor,
        "location_type": normalized_location_type,
        "distance_rule": cleaned_distance_rule,
        "semantic_text": semantic_text,
    }


def parse_query_with_llm(query: str) -> dict:
    if genai is None or not API_KEY:
        return _fallback_parser(query)

    try:
        model = genai.GenerativeModel(
            model_name="gemini-flash-lite-latest",
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(
            query,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.1,
            ),
        )
        return _post_process_parsed_intent(query, json.loads(response.text))
    except json.JSONDecodeError as exc:
        print(f"[-] Could not parse LLM JSON response: {exc}")
        return _fallback_parser(query)
    except Exception as exc:
        print(f"[-] Query parser LLM call failed: {exc}")
        return _fallback_parser(query)


def _fallback_parser(query: str) -> dict:
    return _post_process_parsed_intent(query, {})
