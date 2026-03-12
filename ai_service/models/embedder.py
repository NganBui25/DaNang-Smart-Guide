"""
Module sinh Vector Embedding từ văn bản tiếng Việt sử dụng PhoBERT.
Model: vinai/phobert-base (768 chiều)
"""
import torch
from transformers import AutoTokenizer, AutoModel

MODEL_NAME = "vinai/phobert-base"

# Lazy load - chỉ load model khi cần lần đầu tiên
_tokenizer = None
_model = None


def _load_model():
    """Nạp model PhoBERT vào bộ nhớ (chỉ chạy 1 lần)"""
    global _tokenizer, _model
    if _tokenizer is None:
        print(f"[Embedder] Loading PhoBERT model: {MODEL_NAME} ...")
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        _model = AutoModel.from_pretrained(MODEL_NAME)
        _model.eval()  # Chuyển sang chế độ inference (không tính gradient)
        print("[Embedder] Model loaded successfully!")


def get_embedding(text: str) -> list[float]:
    """
    Chuyển đổi một chuỗi văn bản thành vector 768 chiều.
    
    Args:
        text: Văn bản tiếng Việt cần nhúng (tên địa điểm, mô tả, review...)
    
    Returns:
        Danh sách 768 float đại diện cho ý nghĩa ngữ nghĩa của văn bản.
    """
    _load_model()
    
    # Tokenize, giới hạn độ dài tối đa 256 token (đủ cho 1 đoạn mô tả)
    inputs = _tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding=True
    )
    
    with torch.no_grad():
        outputs = _model(**inputs)
    
    # Dùng mean-pooling trên token embeddings (loại trừ padding):
    # Đây là phương pháp phổ biến để tạo sentence embedding từ token embeddings
    attention_mask = inputs["attention_mask"]
    token_embeddings = outputs.last_hidden_state
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    embeddings = torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    return embeddings[0].tolist()  # Trả về list Python thông thường


def build_place_text(name: str, address: str = "", description: str = "", category: str = "") -> str:
    """
    Ghép các thông tin của một địa điểm thành 1 chuỗi văn bản để nhúng.
    Chiến lược: Kết hợp tất cả thông tin để vector bao quát nhất.
    """
    parts = [name]
    if category:
        parts.append(category)
    if address:
        parts.append(address)
    if description:
        parts.append(description)
    return ". ".join(filter(None, parts))
