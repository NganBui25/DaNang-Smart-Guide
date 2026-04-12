"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import mysql.connector
import json
import os
from dotenv import load_dotenv

from vectorization import encode_text, compute_similarity_batch
from sentiment import summarize_sentiment

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DaNang Smart Guide - AI Engine")

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "danang_hidden_gems")
    )

class SearchRequest(BaseModel):
    text: str
    top_k: int = 5
    hidden_gem: bool = False

class VectorizeRequest(BaseModel):
    place_id: str
    text: str

class SentimentRequest(BaseModel):
    reviews: list[str]

@app.post("/search")
def search(req: SearchRequest):
    logger.info(f"Searching for: {req.text} (top_k={req.top_k}, hidden_gem={req.hidden_gem})")
    query_vec = encode_text(req.text)
    if not query_vec:
        raise HTTPException(status_code=400, detail="Could not encode query")

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        q = "SELECT id, name, embedding_vector, is_hidden_gem FROM places_place WHERE status = 'APPROVED' AND embedding_vector IS NOT NULL"
        if req.hidden_gem:
            q += " AND is_hidden_gem = 1"
        cursor.execute(q)
        rows = cursor.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"DB connection error: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")

    vectors_dict = {}
    for r in rows:
        try:
            vec = json.loads(r["embedding_vector"])
            if isinstance(vec, str):
                vec = json.loads(vec)
            # Dùng trực tiếp ID dạng chuỗi (thường là char(32) trong DB MySQL)
            vectors_dict[str(r["id"])] = vec
        except Exception as e:
            continue
            
    if not vectors_dict:
        return {"results": []}

    results_raw = compute_similarity_batch(query_vec, vectors_dict)
    
    top_results = []
    query_words = set(req.text.lower().split())
    
    for uid, score in results_raw[:req.top_k]:
        db_id = str(uid)
        # Nối ID nếu là chuỗi 32 byte không có gạch ngang
        if len(db_id) == 32 and "-" not in db_id:
            db_id = f"{db_id[:8]}-{db_id[8:12]}-{db_id[12:16]}-{db_id[16:20]}-{db_id[20:]}"
            
        match_keywords = [w for w in query_words if len(w) > 2]
        if score > 0.6:
            reason = "Phù hợp ngữ nghĩa tổng thể rất cao."
        elif match_keywords:
            reason = f"Trùng khớp {len(match_keywords)} từ khóa tiềm năng."
        else:
            reason = "Gợi ý dựa trên ngữ cảnh tương đồng."
            
        top_results.append({
            "place_id": db_id,
            "score": score,
            "match_reason": reason
        })
        
    return {"results": top_results}

@app.post("/vectorize")
def vectorize(req: VectorizeRequest):
    logger.info(f"Vectorizing place: {req.place_id}")
    vec = encode_text(req.text)
    return {"vector": vec}

@app.post("/sentiment")
def sentiment(req: SentimentRequest):
    logger.info(f"Sentiment analysis for {len(req.reviews)} reviews")
    summary = summarize_sentiment(req.reviews)
    return {"summary": summary}

"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging
import mysql.connector
import json
import os
from dotenv import load_dotenv

from vectorization import encode_text, compute_similarity_batch
from sentiment import summarize_sentiment
from query_parser import parse_query_with_llm

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="DaNang Local Gems - AI Engine")


def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "danang_hidden_gems")
    )


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


@app.post("/search")
def search(req: SearchRequest):
    logger.info(f"[*] Raw Search Request: '{req.text}' (top_k={req.top_k}, hidden_gem={req.hidden_gem})")

    # ---------------------------------------------------------
    # BƯỚC 1: LLM BÓC TÁCH NGỮ CẢNH
    # ---------------------------------------------------------
    parsed_data = parse_query_with_llm(req.text)
    logger.info(f"[+] LLM Parsed Data: {parsed_data}")
    
    semantic_text = parsed_data.get("semantic_text")
    if not semantic_text or not semantic_text.strip():
        semantic_text = req.text

    # ---------------------------------------------------------
    # BƯỚC 2: VECTOR HÓA
    # ---------------------------------------------------------
    query_vec = encode_text(semantic_text)
    if query_vec is None:
        raise HTTPException(status_code=400, detail="Could not encode semantic query")

    # ---------------------------------------------------------
    # BƯỚC 3: XÂY DỰNG VÀ THỰC THI SQL (ĐÃ SỬA)
    # ---------------------------------------------------------
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # === XÂY DỰNG QUERY CÁCH AN TOÀN ===
        select_fields = ["p.id", "p.name", "p.embedding_vector", "p.is_hidden_gem"]
        where_clauses = [
            "p.status = 'APPROVED'",
            "p.embedding_vector IS NOT NULL"
        ]
        params: list = []
        join_clause = "LEFT JOIN places_category c ON p.category_id = c.id"
        having_clauses: list[str] = []

        # Hidden gem
        if req.hidden_gem:
            where_clauses.append("p.is_hidden_gem = 1")

        # Category filter
        if parsed_data.get("category"):
            where_clauses.append("c.name LIKE %s")
            params.append(f"%{parsed_data['category']}%")

        # === XỬ LÝ ĐỊA ĐIỂM + KHOẢNG CÁCH ===
        anchor_name_raw = parsed_data.get("location_anchor", "")
        anchor_name = anchor_name_raw.lower().strip() if anchor_name_raw else None

        target_lat = None
        target_lng = None
        use_like_search = False

        if anchor_name:
            # Tìm tọa độ mốc
            anchor_query = """
                SELECT lat, lng 
                FROM places_place 
                WHERE name LIKE %s AND lat IS NOT NULL 
                LIMIT 1
            """
            cursor.execute(anchor_query, (f"%{anchor_name}%",))
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

        # Nếu có tọa độ → thêm khoảng cách + filter null
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

            # Xử lý distance_rule từ LLM
            dist_rule = parsed_data.get("distance_rule")
            if dist_rule and dist_rule.get("operator") and dist_rule.get("value") is not None:
                op = dist_rule["operator"]
                try:
                    val = float(dist_rule["value"]) # Ép kiểu bảo vệ
                    if op in ["<", ">", "=", "<=", ">="]:
                        having_clauses.append(f"distance {op} %s")
                        params.append(val) # Đẩy vào params để MySQL tự escape
                except (ValueError, TypeError):
                    logger.warning("Invalid distance value")
            elif anchor_name and not dist_rule:
                having_clauses.append("distance < 5")

        # Fallback LIKE nếu không tìm được tọa độ mốc
        if use_like_search and anchor_name:
            where_clauses.append("(p.address LIKE %s OR p.name LIKE %s)")
            params.extend([f"%{anchor_name}%", f"%{anchor_name}%"])

        # === XÂY DỰNG CÂU SQL CUỐI CÙNG ===
        select_str = ", ".join(select_fields)
        where_str = " AND ".join(where_clauses)

        q = f"""
            SELECT {select_str}
            FROM places_place p
            {join_clause}
            WHERE {where_str}
        """.strip()

        if having_clauses:
            q += f" HAVING {' AND '.join(having_clauses)}"

        logger.info(f"[*] Executing SQL: {q} | params: {params}")

        cursor.execute(q, tuple(params) if params else None)
        rows = cursor.fetchall()
        conn.close()

    except Exception as e:
        logger.error(f"[-] DB error: {e}")
        raise HTTPException(status_code=500, detail="Database error during pre-filtering")

    # ---------------------------------------------------------
    # BƯỚC 4: VECTOR SIMILARITY
    # ---------------------------------------------------------
    vectors_dict = {}
    for r in rows:
        try:
            vec = json.loads(r["embedding_vector"])
            if isinstance(vec, str):
                vec = json.loads(vec)
            vectors_dict[str(r["id"])] = vec
        except Exception:
            continue

    if not vectors_dict:
        return {"parsed_intent": parsed_data, "results": []}

    results_raw = compute_similarity_batch(query_vec, vectors_dict, top_k=req.top_k)

    # ---------------------------------------------------------
    # BƯỚC 5: ĐỊNH DẠNG KẾT QUẢ
    # ---------------------------------------------------------
    top_results = []
    query_words = set(semantic_text.lower().split())

    for uid, score in results_raw:
        db_id = str(uid)
        if len(db_id) == 32 and "-" not in db_id:
            db_id = f"{db_id[:8]}-{db_id[8:12]}-{db_id[12:16]}-{db_id[16:20]}-{db_id[20:]}"

        match_keywords = [w for w in query_words if len(w) > 2]
        if score > 0.6:
            reason = "Phù hợp ngữ nghĩa tổng thể rất cao."
        elif match_keywords:
            reason = f"Trùng khớp {len(match_keywords)} từ khóa + ngữ cảnh."
        else:
            reason = "Gợi ý tương đồng cao."

        top_results.append({
            "place_id": db_id,
            "score": round(float(score), 4),
            "match_reason": reason
        })

    return {
        "parsed_intent": parsed_data,
        "results": top_results
    }


# Các endpoint còn lại giữ nguyên
@app.post("/vectorize")
def vectorize(req: VectorizeRequest):
    logger.info(f"Vectorizing place: {req.place_id}")
    vec = encode_text(req.text)
    if vec is not None:
        vec = vec.tolist()
    return {"vector": vec}


@app.post("/sentiment")
def sentiment(req: SentimentRequest):
    logger.info(f"Sentiment analysis for {len(req.reviews)} reviews")
    summary = summarize_sentiment(req.reviews)
    return {"summary": summary}