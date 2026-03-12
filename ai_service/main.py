from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import numpy as np
import os

from models.embedder import get_embedding, build_place_text

app = FastAPI(
    title="Danang Hidden Gems — AI Service",
    description="Vector Embedding (PhoBERT) và Semantic Search (FAISS) cho hệ thống gợi ý điểm đến Đà Nẵng",
    version="1.0.0"
)

# ------- FAISS Setup -------
VECTOR_DIMENSION = 768
INDEX_FILE = "faiss_index/places.index"
os.makedirs("faiss_index", exist_ok=True)

# Dùng IndexIDMap để ánh xạ chính xác place_id (từ MySQL) ↔ faiss_id
if os.path.exists(INDEX_FILE):
    index = faiss.read_index(INDEX_FILE)
else:
    flat_index = faiss.IndexFlatL2(VECTOR_DIMENSION)
    index = faiss.IndexIDMap(flat_index)


def _save_index():
    faiss.write_index(index, INDEX_FILE)


# ------- Pydantic Models -------
class PlaceTextInput(BaseModel):
    place_id: int
    name: str
    address: str = ""
    description: str = ""
    category: str = ""

class EmbedQueryRequest(BaseModel):
    text: str

class SearchQuery(BaseModel):
    query_vector: list[float]
    top_k: int = 10

class SearchByTextQuery(BaseModel):
    text: str
    top_k: int = 10


# ------- Endpoints -------
@app.get("/", summary="Health check")
def read_root():
    return {
        "status": "AI Service running",
        "vector_count": index.ntotal
    }


@app.post("/embed", summary="Chuyển đổi text thành vector PhoBERT")
def embed_text(req: EmbedQueryRequest):
    """Trả về vector embedding 768 chiều từ một đoạn văn bản."""
    vector = get_embedding(req.text)
    return {"vector": vector, "dimension": len(vector)}


@app.post("/add_place", summary="Thêm địa điểm vào FAISS index")
def add_place(data: PlaceTextInput):
    """
    Nhận thông tin text của địa điểm, tự động sinh vector PhoBERT
    và lưu vào FAISS Index với place_id là key ánh xạ.
    """
    combined_text = build_place_text(
        name=data.name,
        address=data.address,
        description=data.description,
        category=data.category
    )
    vector = get_embedding(combined_text)
    vec_array = np.array([vector], dtype=np.float32)
    ids = np.array([data.place_id], dtype=np.int64)
    index.add_with_ids(vec_array, ids)
    _save_index()
    return {
        "status": "success",
        "place_id": data.place_id,
        "text_used": combined_text[:100] + "..." if len(combined_text) > 100 else combined_text
    }


@app.post("/search_by_vector", summary="Tìm kiếm bằng vector có sẵn")
def search_by_vector(query: SearchQuery):
    """Nhận vector trực tiếp và trả về top-k place_id gần nhất."""
    if index.ntotal == 0:
        raise HTTPException(status_code=404, detail="FAISS index is empty. Please add places first.")
    if len(query.query_vector) != VECTOR_DIMENSION:
        raise HTTPException(status_code=400, detail=f"Vector must have {VECTOR_DIMENSION} dimensions")
    vec = np.array([query.query_vector], dtype=np.float32)
    distances, place_ids = index.search(vec, query.top_k)
    results = [
        {"place_id": int(place_ids[0][i]), "score": float(distances[0][i])}
        for i in range(len(place_ids[0])) if place_ids[0][i] != -1
    ]
    return {"status": "success", "results": results}


@app.post("/search", summary="Tìm kiếm bằng văn bản (end-to-end)")
def search_by_text(query: SearchByTextQuery):
    """
    Nhận câu hỏi text (VD: 'quán cà phê yên tĩnh gần biển'),
    tự động sinh vector qua PhoBERT rồi tìm kiếm ngữ nghĩa trong FAISS.
    Trả về danh sách place_id tương ứng với địa điểm phù hợp nhất.
    """
    if index.ntotal == 0:
        raise HTTPException(status_code=404, detail="FAISS index is empty. Please add places first.")
    vector = get_embedding(query.text)
    vec = np.array([vector], dtype=np.float32)
    distances, place_ids = index.search(vec, query.top_k)
    results = [
        {"place_id": int(place_ids[0][i]), "score": float(distances[0][i])}
        for i in range(len(place_ids[0])) if place_ids[0][i] != -1
    ]
    return {"status": "success", "query": query.text, "results": results}
