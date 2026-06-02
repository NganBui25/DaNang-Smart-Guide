# Kế Hoạch Cải Thiện Chất Lượng Search

## Tóm tắt
- Mục tiêu là nâng chất lượng search sau khi merge phần cũ vào `develop`.
- Vấn đề hiện tại không phải GPU hay endpoint hỏng, mà là:
  - query chưa được hiểu thành `intent` rõ ràng
  - ranking chưa tận dụng tốt ràng buộc địa lý như `gần biển`
  - dữ liệu embedding của place còn nghèo nên semantic score chưa đủ sát nhu cầu thật
- Chia việc:
  - **Người A**: AI query understanding + ranking
  - **Người B**: backend/data pipeline cho embedding

## Sơ đồ hiện tại
```text
Người dùng gõ query
    |
    v
Frontend gửi POST /api/search/
    |
    v
Backend nhận query và gọi AI /search
    |
    v
AI parse query
    |
    +--> parsed_intent hiện thường:
    |    - category = null
    |    - location_anchor = null
    |    - distance_rule = null
    |    - semantic_text = nguyên câu query
    |
    v
AI vector hóa toàn bộ câu query
    |
    v
Lấy place + embedding từ DB
    |
    v
Tính semantic similarity
    |
    v
Trả place_id + score về backend
    |
    v
Backend map dữ liệu Place đầy đủ
    |
    v
Frontend hiển thị kết quả
```

### Chỗ đang thiếu
```text
[NLP parse intent tốt]
    |
    +--> hiểu "quán cafe" là category
    +--> hiểu "yên tĩnh" là semantic preference
    +--> hiểu "gần biển" là location/distance constraint
```

## Sơ đồ mục tiêu sau khi sửa
```text
Người dùng gõ query
    |
    v
Frontend gửi POST /api/search/
    |
    v
Backend gọi AI /search
    |
    v
AI parse intent
    |
    +--> category = cafe
    +--> semantic_text = yên tĩnh
    +--> location_anchor = biển
    +--> distance_rule = gần / < 5km
    |
    v
Pre-filter từ DB
    |
    +--> lọc theo category nếu có
    +--> lọc theo khoảng cách nếu có
    |
    v
Semantic embedding + similarity
    |
    v
Geo rerank / blended score
    |
    v
Top results đúng ngữ nghĩa + đúng vị trí
    |
    v
Backend trả dữ liệu place đầy đủ cho frontend
```

### Phân lớp trách nhiệm
```text
AI chịu trách nhiệm:
- hiểu người dùng muốn gì
- biến query thành intent có cấu trúc
- tính semantic score
- rerank theo logic địa lý

Backend chịu trách nhiệm:
- chuẩn bị text đầu vào cho embedding
- đảm bảo place có dữ liệu đủ giàu để AI hiểu
- backfill lại vector cho dữ liệu cũ
- giữ đúng thứ tự score AI trả về
```

## Giao việc A — AI Search Quality
- Tạo nhánh: `feature/ai-search-intent-ranking`
- Giữ nguyên contract `/search` và `/vectorize`
- Sửa parser để query phổ biến không cần `LLM_API_KEY` vẫn hiểu được:
  - `gần biển`, `ven biển`, `sát biển` -> `location_anchor="biển"`, `distance_rule={"operator":"<","value":5}`
  - `gần sông hàn` -> `location_anchor="sông hàn"`, `distance_rule={"operator":"<","value":3}`
  - `gần tôi` -> dùng `user_lat/user_lng`, `distance_rule={"operator":"<","value":3}`
  - `quán cafe`, `nhà hàng`, `vui chơi`, `trẻ em` -> map ra category hợp lý
  - `yên tĩnh`, `chill`, `lãng mạn`, `thoáng`, `view đẹp` -> giữ trong `semantic_text`
- Bổ sung anchor resolver:
  - `biển` -> dùng tập anchor ven biển mặc định
  - `sông hàn` -> dùng anchor sông Hàn mặc định
  - `gần tôi` -> dùng vị trí user
- Sửa ranking:
  - lọc trước theo category nếu parse được
  - thêm filter khoảng cách nếu có location/distance constraint
  - tính semantic similarity như hiện tại
  - nếu có ràng buộc địa lý, dùng blended score:
    - `final_score = 0.7 * semantic_score + 0.3 * proximity_score`
- Sửa `match_reason` để nói đúng lý do:
  - semantic match
  - category match
  - location/distance match
- Kết quả mục tiêu:
  - `quán cafe yên tĩnh gần biển` phải ưu tiên cafe ven biển/Sơn Trà/An Hải/Phạm Văn Đồng
  - `nhà hàng gần sông hàn` phải ưu tiên nhà hàng khu sông Hàn
  - `parsed_intent` không còn toàn `null`

## Giao việc B — Backend Embedding Enrichment
- Tạo nhánh: `feature/backend-embedding-enrichment`
- Giữ nguyên contract `/api/search/`
- Sửa pipeline seed/import:
  - lưu `description` nếu nguồn có
  - nếu seed không có `description`, tổng hợp mô tả ngắn từ 1-2 review seed đầu tiên rồi lưu vào `Place.description`
  - tuyệt đối không lưu chuỗi rác hay `"None"`
- Chuẩn hóa text build cho embedding:
  - `name + category + address + description + tags`
  - dùng cùng một công thức cho signal approve và backfill
- Sau khi sửa pipeline:
  - reset `embedding_vector`
  - backfill lại toàn bộ `APPROVED` places
- Kết quả mục tiêu:
  - vector của place giàu ngữ nghĩa hơn hiện tại
  - các query kiểu `yên tĩnh`, `chill`, `ấm cúng`, `phù hợp trẻ em` bám tốt hơn
  - place thiếu vài field vẫn vectorize ổn

## API / Interface
- Không thêm endpoint mới
- Giữ nguyên:
  - `POST /api/search/`
  - `POST /search`
  - `POST /vectorize`
- `parsed_intent` vẫn giữ shape hiện có:
  - `category`
  - `location_anchor`
  - `distance_rule`
  - `semantic_text`

## Test và nghiệm thu
- Query parsing:
  - `quán cafe yên tĩnh gần biển`
  - `nhà hàng gần sông hàn`
  - `địa điểm vui chơi cho trẻ em gần tôi`
  - xác nhận `parsed_intent` đúng ý, không rơi hết về `null`
- Ranking:
  - top 5 của query `gần biển` phải ưu tiên place ven biển hơn place nội thành nếu semantic gần nhau
  - kết quả vẫn sắp theo `ai_score` giảm dần
- Data enrichment:
  - import lại seed xong, phần lớn place có `description` hữu ích
  - backfill xong, toàn bộ `APPROVED` place có `embedding_vector`
- Web smoke test:
  - frontend `/search` không 500
  - query `quán cafe yên tĩnh gần biển` cho kết quả hợp lý hơn trước
  - detail/admin vẫn hoạt động bình thường

## Giả định và mặc định
- Công việc này thuộc **GĐ2** là chính:
  - A = mở rộng `ai-nlp-pipeline`
  - B = mở rộng `backend-vectorize-payload`
- Bước reset/backfill toàn bộ dữ liệu cũ là phần vận hành nối sang **GĐ4**
- Không chỉnh frontend trong plan này
- Thứ tự thực hiện mặc định:
  1. merge phần cũ hiện có vào `develop`
  2. A làm intent parsing + geo-aware ranking
  3. B làm data enrichment + backfill
  4. chạy lại import/backfill trên Docker GPU
  5. nghiệm thu lại trên web
