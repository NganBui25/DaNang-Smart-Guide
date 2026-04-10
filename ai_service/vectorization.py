import numpy as np
from typing import Dict, List, Tuple
# Nhớ import đúng đường dẫn hàm get_embedding của bạn nhé
from models.embedder import get_embedding 

def encode_text(text: str) -> np.ndarray:
    """
    Chuyển đổi văn bản thành vector. Trả về NumPy Array.
    """
    return get_embedding(text)

def compute_similarity_batch(
    query_vec: np.ndarray, 
    vectors_dict: Dict[str, np.ndarray], 
    top_k: int = 5
) -> List[Tuple[str, float]]:
    """
    Tính Cosine Similarity giữa câu query và danh sách vector.
    Trả về Top K kết quả cao nhất.
    """
    if query_vec is None or not vectors_dict:
        return []

    ids = list(vectors_dict.keys())
    # Chuyển list các vector thành ma trận 2D
    matrix = np.asarray(list(vectors_dict.values()), dtype=np.float32)
    q = np.asarray(query_vec, dtype=np.float32)

    # Validate số chiều
    if matrix.ndim != 2 or q.ndim != 1 or matrix.shape[1] != q.shape[0]:
        print("[-] Lỗi: Kích thước vector không khớp!")
        return []

    # Tính toán Cosine Similarity
    matrix_norm = np.linalg.norm(matrix, axis=1)
    q_norm = np.linalg.norm(q)
    denom = matrix_norm * q_norm
    denom[denom == 0] = 1.0 # Tránh lỗi chia cho 0
    
    scores = (matrix @ q) / denom

    # Ghép ID và Điểm số, sau đó sort giảm dần
    results = [(ids[i], float(scores[i])) for i in range(len(ids))]
    results.sort(key=lambda x: x[1], reverse=True)
    
    # Trả về đúng số lượng Top K yêu cầu
    return results[:top_k]