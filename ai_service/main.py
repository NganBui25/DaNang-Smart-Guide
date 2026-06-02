from __future__ import annotations

import json
import logging
import os

import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

try:
    from models.embedder import ensure_model_loaded, get_runtime_info
    from query_parser import parse_query_with_llm
    from sentiment import summarize_sentiment
    from vectorization import (
        compute_similarity_batch,
        encode_text,
        get_search_backend_name,
    )
except ImportError:  # pragma: no cover - supports package-style imports in tests/tools.
    from ai_service.models.embedder import ensure_model_loaded, get_runtime_info
    from ai_service.query_parser import parse_query_with_llm
    from ai_service.sentiment import summarize_sentiment
    from ai_service.vectorization import (
        compute_similarity_batch,
        encode_text,
        get_search_backend_name,
    )


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
CATEGORY_MATCH_THRESHOLD = float(os.getenv("CATEGORY_MATCH_THRESHOLD", "0.35"))

app = FastAPI(title="DaNang Local Gems - AI Engine")


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "danang_hidden_gems"),
    )


def _load_embedding_vector(raw_value):
    if raw_value is None:
        return None

    value = raw_value
    if isinstance(value, str):
        value = json.loads(value)
    if isinstance(value, str):
        value = json.loads(value)
    if not isinstance(value, list):
        return None
    return value


def _resolve_category_match(cursor, raw_category: str | None):
    category_text = (raw_category or "").strip()
    if not category_text:
        return None

    category_query_vec = encode_text(category_text)
    if category_query_vec is None:
        return None

    cursor.execute(
        """
        SELECT DISTINCT c.id, c.name
        FROM places_category c
        INNER JOIN places_place p ON p.category_id = c.id
        WHERE p.status = 'APPROVED'
        """.strip()
    )
    category_rows = cursor.fetchall()
    if not category_rows:
        return None

    category_vectors = {}
    category_meta = {}
    for row in category_rows:
        category_vec = encode_text(row["name"])
        if category_vec is None:
            continue
        row_id = str(row["id"])
        category_vectors[row_id] = category_vec
        category_meta[row_id] = row

    if not category_vectors:
        return None

    best_match = compute_similarity_batch(
        category_query_vec,
        category_vectors,
        top_k=1,
        search_backend="numpy",
    )
    if not best_match:
        return None

    category_id, score = best_match[0]
    if float(score) < CATEGORY_MATCH_THRESHOLD:
        logger.info(
            "Category semantic match below threshold | input=%r | score=%.4f | threshold=%.2f",
            category_text,
            float(score),
            CATEGORY_MATCH_THRESHOLD,
        )
        return None

    matched_row = category_meta[str(category_id)]
    return {
        "id": matched_row["id"],
        "name": matched_row["name"],
        "score": round(float(score), 4),
    }


class SearchRequest(BaseModel):
    text: str
    top_k: int = 5
    hidden_gem: bool = False
    user_lat: float | None = None
    user_lng: float | None = None


class VectorizeRequest(BaseModel):
    place_id: str
    text: str


class SentimentRequest(BaseModel):
    reviews: list[str]


@app.on_event("startup")
def startup_event():
    ensure_model_loaded()
    runtime = get_runtime_info()
    gpu_name = runtime.get("gpu_name")
    gpu_suffix = f" | gpu={gpu_name}" if gpu_name else ""
    logger.info(
        "AI runtime ready | torch=%s | device=%s | cuda_available=%s | model=%s | search_backend=%s%s",
        runtime["torch_version"],
        runtime["device"],
        runtime["cuda_available"],
        runtime["model_name"],
        get_search_backend_name(),
        gpu_suffix,
    )


@app.get("/healthz")
def healthz():
    runtime = get_runtime_info()
    return {
        "status": "ok",
        "device": runtime["device"],
        "model_name": runtime["model_name"],
        "torch_version": runtime["torch_version"],
        "cuda_available": runtime["cuda_available"],
        "search_backend": get_search_backend_name(),
    }


@app.post("/search")
def search(req: SearchRequest):
    logger.info(
        "Semantic search request | text=%r | top_k=%s | hidden_gem=%s",
        req.text,
        req.top_k,
        req.hidden_gem,
    )

    parsed_data = parse_query_with_llm(req.text)
    logger.info("Parsed query intent: %s", parsed_data)

    semantic_text = parsed_data.get("semantic_text")
    if not semantic_text or not semantic_text.strip():
        semantic_text = req.text

    query_vec = encode_text(semantic_text)
    if query_vec is None:
        raise HTTPException(status_code=400, detail="Could not encode semantic query")

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        select_fields = ["p.id", "p.name", "p.embedding_vector", "p.is_hidden_gem"]
        where_clauses = [
            "p.status = 'APPROVED'",
            "p.embedding_vector IS NOT NULL",
        ]
        params: list = []
        join_clause = "LEFT JOIN places_category c ON p.category_id = c.id"
        having_clauses: list[str] = []

        if req.hidden_gem:
            where_clauses.append("p.is_hidden_gem = 1")

        resolved_category = None
        if parsed_data.get("category"):
            resolved_category = _resolve_category_match(cursor, parsed_data.get("category"))
            if resolved_category:
                parsed_data["category"] = resolved_category["name"]
                where_clauses.append("c.id = %s")
                params.append(resolved_category["id"])
                logger.info(
                    "Resolved category by vector match | input=%r | matched=%r | score=%.4f",
                    parsed_data.get("category"),
                    resolved_category["name"],
                    resolved_category["score"],
                )
            else:
                parsed_data["category"] = None

        anchor_name_raw = parsed_data.get("location_anchor", "")
        anchor_name = anchor_name_raw.lower().strip() if anchor_name_raw else None

        target_lat = None
        target_lng = None
        use_like_search = False

        if anchor_name:
            cursor.execute(
                """
                SELECT lat, lng
                FROM places_place
                WHERE name LIKE %s AND lat IS NOT NULL
                LIMIT 1
                """.strip(),
                (f"%{anchor_name}%",),
            )
            anchor_result = cursor.fetchone()

            if anchor_result:
                target_lat = anchor_result["lat"]
                target_lng = anchor_result["lng"]
            else:
                use_like_search = True
        elif (
            parsed_data.get("distance_rule")
            and req.user_lat is not None
            and req.user_lng is not None
        ):
            target_lat = req.user_lat
            target_lng = req.user_lng

        if target_lat is not None and target_lng is not None:
            distance_expr = f"""
(6371 * acos(
    cos(radians({target_lat})) * cos(radians(p.lat)) *
    cos(radians(p.lng) - radians({target_lng})) +
    sin(radians({target_lat})) * sin(radians(p.lat))
))
            """.strip()

            select_fields.append(f"{distance_expr} AS distance")
            where_clauses.append("p.lat IS NOT NULL")
            where_clauses.append("p.lng IS NOT NULL")

            dist_rule = parsed_data.get("distance_rule")
            if dist_rule and dist_rule.get("operator") and dist_rule.get("value") is not None:
                operator = dist_rule["operator"]
                try:
                    distance_value = float(dist_rule["value"])
                except (TypeError, ValueError):
                    logger.warning("Invalid distance value in parsed query: %s", dist_rule)
                else:
                    if operator in {"<", ">", "=", "<=", ">="}:
                        having_clauses.append(f"distance {operator} %s")
                        params.append(distance_value)
            elif anchor_name and not dist_rule:
                having_clauses.append("distance < 5")

        if use_like_search and anchor_name:
            where_clauses.append("(p.address LIKE %s OR p.name LIKE %s)")
            params.extend([f"%{anchor_name}%", f"%{anchor_name}%"])

        select_str = ", ".join(select_fields)
        where_str = " AND ".join(where_clauses)

        query = f"""
            SELECT {select_str}
            FROM places_place p
            {join_clause}
            WHERE {where_str}
        """.strip()

        if having_clauses:
            query += f" HAVING {' AND '.join(having_clauses)}"

        logger.info("Executing semantic candidate query: %s | params=%s", query, params)
        if params:
            cursor.execute(query, tuple(params))
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
    except Exception as exc:
        logger.error("Database error during pre-filtering: %s", exc)
        raise HTTPException(status_code=500, detail="Database error during pre-filtering")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

    vectors_dict = {}
    for row in rows:
        try:
            vector = _load_embedding_vector(row["embedding_vector"])
        except Exception:
            continue
        if vector is not None:
            vectors_dict[str(row["id"])] = vector

    if not vectors_dict:
        return {"parsed_intent": parsed_data, "results": []}

    results_raw = compute_similarity_batch(query_vec, vectors_dict, top_k=req.top_k)

    top_results = []
    query_words = set(semantic_text.lower().split())
    for uid, score in results_raw:
        db_id = str(uid)
        if len(db_id) == 32 and "-" not in db_id:
            db_id = f"{db_id[:8]}-{db_id[8:12]}-{db_id[12:16]}-{db_id[16:20]}-{db_id[20:]}"

        match_keywords = [word for word in query_words if len(word) > 2]
        if score > 0.6:
            reason = "Phu hop ngu nghia tong the rat cao."
        elif match_keywords:
            reason = f"Trung khop {len(match_keywords)} tu khoa va ngu canh."
        else:
            reason = "Goi y dua tren do tuong dong cao."

        top_results.append(
            {
                "place_id": db_id,
                "score": round(float(score), 4),
                "match_reason": reason,
            }
        )

    return {
        "parsed_intent": parsed_data,
        "results": top_results,
    }


@app.post("/vectorize")
def vectorize(req: VectorizeRequest):
    logger.info("Vectorizing place: %s", req.place_id)
    vector = encode_text(req.text)
    return {"vector": vector.tolist() if vector is not None else None}


@app.post("/sentiment")
def sentiment(req: SentimentRequest):
    logger.info("Sentiment analysis for %s reviews", len(req.reviews))
    summary = summarize_sentiment(req.reviews)
    return {"summary": summary}
