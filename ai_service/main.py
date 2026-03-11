from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import faiss
import numpy as np
import os

app = FastAPI(title="Danang Hidden Gems AI Service")

# Setup FAISS
VECTOR_DIMENSION = 768 # Kích thước vector của PhoBERT
INDEX_FILE = "faiss_index/places.index"

# Khởi tạo hoặc load index
if os.path.exists(INDEX_FILE):
    index = faiss.read_index(INDEX_FILE)
else:
    index = faiss.IndexFlatL2(VECTOR_DIMENSION)

class VectorData(BaseModel):
    place_id: int
    vector: list[float]

class SearchQuery(BaseModel):
    query_vector: list[float]
    top_k: int = 5

@app.get("/")
def read_root():
    return {"status": "AI Service is running", "vector_count": index.ntotal}

@app.post("/add_vector")
def add_vector(data: VectorData):
    if len(data.vector) != VECTOR_DIMENSION:
        raise HTTPException(status_code=400, detail=f"Vector must have {VECTOR_DIMENSION} dimensions")
    
    vec = np.array([data.vector], dtype=np.float32)
    # Trong thực tế, mình có thể dùng IndexIDMap để gán ID thực từ MySQL cho Index, hiện tại demo với FlatL2
    index.add(vec)
    faiss.write_index(index, INDEX_FILE)
    
    return {"status": "success", "message": f"Added vector for place {data.place_id}"}

@app.post("/search")
def search(query: SearchQuery):
    if len(query.query_vector) != VECTOR_DIMENSION:
        raise HTTPException(status_code=400, detail=f"Query vector must have {VECTOR_DIMENSION} dimensions")
    
    vec = np.array([query.query_vector], dtype=np.float32)
    distances, indices = index.search(vec, query.top_k)
    
    results = []
    for i in range(len(indices[0])):
        if indices[0][i] != -1: # Kiểm tra index hợp lệ
            results.append({
                "faiss_id": int(indices[0][i]),
                "distance": float(distances[0][i])
            })
            
    return {"status": "success", "results": results}
