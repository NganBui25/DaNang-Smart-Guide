# File script sync vectors với CSDL Django -> FAISS Index
import sys
import os

# Thêm path tới ai_service để chạy import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def generate_mock_vector():
    """Tạm thời sinh mảng vector float 768 chiều giả để test"""
    import random
    return [random.random() for _ in range(768)]

if __name__ == "__main__":
    print("Test script generator...")
    # Sau này sẽ load Model Transformer PhoBERT ở đây
    # Gọi CSDL lấy danh sách Place -> map ID -> index.add_with_ids(...)
