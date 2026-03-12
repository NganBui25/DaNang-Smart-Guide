"""
Script đồng bộ dữ liệu từ file JSON crawl sang FAISS Index.

Luồng hoạt động:
1. Đọc file JSON cào được (places_coffee.json, places_food.json, places_play.json)
2. Với mỗi địa điểm, ghép text (name + address) → đưa qua PhoBERT → sinh vector
3. Nạp vector + place_id vào FAISS Index và lưu file .index
4. Đồng thời lưu map {faiss_internal_id: json_key} vào file JSON để tra cứu

Sử dụng: python scripts/sync_faiss.py
"""
import sys
import os
import json
import requests

# Thêm thư mục gốc của ai_service vào sys.path để import module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.embedder import get_embedding, build_place_text

import faiss
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "data")
INDEX_FILE = os.path.join(os.path.dirname(__file__), "..", "faiss_index", "places.index")
ID_MAP_FILE = os.path.join(os.path.dirname(__file__), "..", "faiss_index", "id_map.json")

DATA_FILES = {
    "coffee": "places_coffee.json",
    "food":   "places_food.json",
    "play":   "places_play.json"
}

VECTOR_DIMENSION = 768


def build_or_load_index():
    os.makedirs(os.path.dirname(INDEX_FILE), exist_ok=True)
    if os.path.exists(INDEX_FILE):
        print(f"[Sync] Đang load index cũ từ: {INDEX_FILE}")
        return faiss.read_index(INDEX_FILE)
    flat = faiss.IndexFlatL2(VECTOR_DIMENSION)
    return faiss.IndexIDMap(flat)


def run_sync():
    index = build_or_load_index()
    
    # Map: faiss_id (int) -> thông tin JSON gốc { key, name, category }
    id_map = {}
    faiss_id = index.ntotal  # Tiếp tục từ số lượng hiện tại (hỗ trợ sync tăng dần)

    for category, filename in DATA_FILES.items():
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"[Sync] Không tìm thấy file: {filepath}, bỏ qua.")
            continue
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"\n[Sync] Đang xử lý {len(data)} địa điểm từ '{filename}'...")
        
        for key, place in data.items():
            name = place.get("name", "")
            address = place.get("address", "")
            
            # Ghép các review lại để tạo description phong phú hơn
            reviews_text = " ".join([
                r.get("content", "") for r in place.get("reviews", [])
            ])
            
            # Ghép tất cả text thành một đoạn duy nhất
            full_text = build_place_text(
                name=name,
                address=address,
                description=reviews_text,
                category=category
            )
            
            print(f"  [{faiss_id}] Embedding: {name[:40]}...")
            
            try:
                vector = get_embedding(full_text)
                vec_array = np.array([vector], dtype=np.float32)
                ids = np.array([faiss_id], dtype=np.int64)
                index.add_with_ids(vec_array, ids)
                
                id_map[str(faiss_id)] = {
                    "json_key": key,
                    "name": name,
                    "category": category,
                    "rating": place.get("rating", ""),
                    "address": address,
                    "coordinate": place.get("coordinate", []),
                    "image_path": place.get("image_path", ""),
                }
                faiss_id += 1
            except Exception as e:
                print(f"  [LỖI] Không thể embed '{name}': {e}")
                continue

    # Lưu index và map
    faiss.write_index(index, INDEX_FILE)
    with open(ID_MAP_FILE, "w", encoding="utf-8") as f:
        json.dump(id_map, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Đồng bộ hoàn thành! Tổng số vector: {index.ntotal}")
    print(f"   Index lưu tại: {INDEX_FILE}")
    print(f"   ID Map lưu tại: {ID_MAP_FILE}")


if __name__ == "__main__":
    run_sync()
