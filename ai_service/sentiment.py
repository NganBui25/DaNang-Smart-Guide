from pyvi import ViTokenizer
import logging

logger = logging.getLogger(__name__)

POSITIVE_WORDS = {
    "ngon", "rẻ", "đẹp", "tốt", "sạch_sẽ", "chu_đáo", "thân_thiện", "tuyệt", "thích", 
    "thoáng", "rộng", "đỉnh", "xuất_sắc", "xịn", "ok", "ổn", "thoải_mái", "lịch_sự",
    "yên_tĩnh", "chill", "chất_lượng", "tươi", "ngọt", "thơm"
}

NEGATIVE_WORDS = {
    "tệ", "tệ_hại", "đắt", "mắc", "bẩn", "dơ", "kém", "chậm", "thái_độ", "tồi", "ồn", 
    "nóng", "chán", "dở", "nguội", "khó_chịu", "mặn", "nhạt", "tanh", "hôi"
}

def summarize_sentiment(reviews: list[str]) -> str:
    """Tạo câu tóm tắt nhanh từ list các review của địa điểm."""
    if not reviews:
        return "Chưa có đánh giá nào cụ thể bằng chữ để phân tích."
        
    pos_count = 0
    neg_count = 0
    
    for r in reviews:
        tokens = ViTokenizer.tokenize(r).lower().split()
        for t in tokens:
            if t in POSITIVE_WORDS:
                pos_count += 1
            if t in NEGATIVE_WORDS:
                neg_count += 1
                
    total = pos_count + neg_count
    if total == 0:
        return "Đánh giá chung: Bình thường, mang tính thông tin tham khảo."
        
    pos_ratio = pos_count / total
    
    if pos_ratio > 0.75:
        summary = "Đa số khách hàng nhận xét rất tích cực với nhiều đánh giá khen ngợi cao."
    elif pos_ratio > 0.5:
        summary = "Đánh giá tổng quan là tích cực nhưng vẫn có một vài điểm trừ nhỏ."
    elif pos_ratio > 0.25:
        summary = "Nhiều đánh giá nhận xét trái chiều, cần chú ý đến một số phàn nàn."
    else:
        summary = "Phần lớn đánh giá không tốt, cần cân nhắc kỹ trước khi trải nghiệm."
        
    return summary
