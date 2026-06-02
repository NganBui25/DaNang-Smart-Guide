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
    ("Quan an", ("nha hang", "quan an", "an vat", "am thuc", "restaurant", "food")),
    ("Vui choi", ("vui choi", "giai tri", "tre em", "kids", "kid", "play")),
)

LOCATION_RULES = (
    ("bien", ("gan bien", "ven bien", "sat bien", "bo bien"), {"operator": "<", "value": 5}),
    ("song han", ("gan song han", "ven song han", "sat song han", "song han"), {"operator": "<", "value": 3}),
    (None, ("gan toi", "gan day", "xung quanh toi", "quanh day"), {"operator": "<", "value": 3}),
)

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


def _infer_location(query: str) -> tuple[str | None, dict | None]:
    normalized_query = _normalize_text(query)
    for anchor, patterns, distance_rule in LOCATION_RULES:
        if any(pattern in normalized_query for pattern in patterns):
            return anchor, distance_rule.copy()
    return None, None


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
    inferred_anchor, inferred_distance = _infer_location(query)
    normalized_category = _normalize_category(parsed.get("category")) or inferred_category
    normalized_anchor = parsed.get("location_anchor")
    if normalized_anchor:
        normalized_anchor = _normalize_text(normalized_anchor)
    if not normalized_anchor:
        normalized_anchor = inferred_anchor

    cleaned_distance_rule = _clean_distance_rule(parsed.get("distance_rule")) or inferred_distance
    semantic_text = _build_semantic_text(parsed.get("semantic_text") or query)

    return {
        "category": normalized_category,
        "location_anchor": normalized_anchor,
        "distance_rule": cleaned_distance_rule,
        "semantic_text": semantic_text,
    }


def parse_query_with_llm(query: str) -> dict:
    if genai is None or not API_KEY:
        return _fallback_parser(query)

    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
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
