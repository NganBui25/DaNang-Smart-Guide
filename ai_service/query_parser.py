import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

# Cấu hình API Key
API_KEY = os.getenv("LLM_API_KEY")
if not API_KEY:
    print("⚠️ CẢNH BÁO: Chưa tìm thấy LLM_API_KEY trong file .env")
else:
    genai.configure(api_key=API_KEY)

# Tách riêng System Prompt
SYSTEM_PROMPT = """
Bạn là một trợ lý trích xuất dữ liệu tìm kiếm địa điểm tại Đà Nẵng.
Nhiệm vụ của bạn là đọc câu truy vấn của người dùng và trả về MỘT CHUỖI JSON HỢP LỆ với cấu trúc sau:
{
    "category": "Loại địa điểm (vd: quán cafe, quán ăn, nhà hàng, khách sạn). Nếu không rõ, trả về null",
    "location_anchor": "Khu vực hoặc mốc vị trí (vd: sông Hàn, Hải Châu, biển Mỹ Khê). Nếu không có, trả về null",
    "distance_rule": "Quy tắc khoảng cách (vd: gần, xa, dưới 2km). Nếu không có, trả về null",
    "semantic_text": "Phần text còn lại miêu tả không gian, cảm giác, phong cách (vd: yên tĩnh, nhiều cây xanh, view đẹp). Phần này dùng để so sánh vector với SBERT."
}
Lưu ý: 
- CHỈ trả về đúng định dạng JSON, không thêm bất kỳ văn bản giải thích nào khác.
- Semantic_text rất quan trọng, hãy gom hết các từ chỉ tính chất, cảm giác vào đây.
"""

def parse_query_with_llm(query: str) -> dict:
    """
    Dùng Gemini 1.5 Flash để bóc tách câu truy vấn của người dùng thành các bộ lọc.
    """
    if not API_KEY:
        return _fallback_parser(query)

    try:
        # Khởi tạo model với system_instruction (Cách chuẩn xác để gán role cho LLM)
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=SYSTEM_PROMPT
        )
        
        # Gọi model chỉ với query của người dùng
        response = model.generate_content(
            query,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json", 
                temperature=0.1 
            )
        )
        
        # Parse chuỗi string trả về
        return json.loads(response.text)

    except json.JSONDecodeError as e:
        print(f"[-] Lỗi Parse JSON. Chuỗi model trả về:\n{response.text}\nChi tiết lỗi: {e}")
        return _fallback_parser(query)
    except Exception as e:
        print(f"[-] Lỗi khi gọi LLM: {e}")
        return _fallback_parser(query)

def _fallback_parser(query: str) -> dict:
    """Hàm dự phòng nếu API rớt mạng hoặc hết quota"""
    return {
        "category": None,
        "location_anchor": None,
        "distance_rule": None,
        "semantic_text": query
    }

if __name__ == "__main__":
    # Test case 1: Đầy đủ các yếu tố
    test_query_1 = "tìm cho mình một quán cf xa sông hàn nhưng không gian phải thật yên tĩnh và ngập tràn cây xanh"
    print(f"\n[Test 1] Câu hỏi: {test_query_1}")
    print("-" * 50)
    print(json.dumps(parse_query_with_llm(test_query_1), indent=4, ensure_ascii=False))

    # Test case 2: Thiếu vị trí cụ thể (chỉ có semantic)
    test_query_2 = "có nhà hàng nào đồ ăn ngon, view ngắm hoàng hôn lãng mạn không"
    print(f"\n[Test 2] Câu hỏi: {test_query_2}")
    print("-" * 50)
    print(json.dumps(parse_query_with_llm(test_query_2), indent=4, ensure_ascii=False))