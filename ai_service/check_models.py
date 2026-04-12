import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load API Key
load_dotenv()
API_KEY = os.getenv("LLM_API_KEY")
genai.configure(api_key=API_KEY)

print("Đang truy vấn danh sách model từ Google...\n")
print("-" * 40)
print("Các model bạn có thể dùng để tạo văn bản (generateContent):")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Lỗi khi lấy danh sách: {e}")
    
print("-" * 40)