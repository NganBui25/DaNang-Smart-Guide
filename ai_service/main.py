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
