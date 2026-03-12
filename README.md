# 🏝️ Da Nang Smart Guide — Hidden Gems Recommendation System

Hệ thống gợi ý điểm đến bản địa tại Đà Nẵng, sử dụng **Semantic Search** (PhoBERT + FAISS) tích hợp với **Django REST API** và **FastAPI AI Service**.

---

## 📂 Cấu Trúc Thư Mục

```text
DaNang-Smart-Guide/
├── backend/            # Django REST API (MySQL)
│   ├── places/         # App quản lý địa điểm & search
│   ├── reviews/        # App quản lý đánh giá
│   ├── users/          # App quản lý tài khoản
│   ├── data/           # Dữ liệu crawl JSON (coffee, food, play)
│   ├── scripts/        # import_data.py — nhập JSON vào MySQL
│   ├── settings.py
│   ├── urls.py
│   └── requirements.txt
├── ai_service/         # FastAPI AI Service (PhoBERT + FAISS)
│   ├── models/
│   │   └── embedder.py     # Module sinh vector PhoBERT 768 chiều
│   ├── scripts/
│   │   └── sync_faiss.py   # Đồng bộ JSON crawl → FAISS index
│   ├── faiss_index/
│   │   ├── places.index    # FAISS index (148 địa điểm)
│   │   └── id_map.json     # Map faiss_id → thông tin địa điểm
│   ├── main.py             # FastAPI endpoints
│   └── requirements.txt
└── frontend/           # (Giai đoạn 4) ReactJS SPA
```

---

## 🚀 Hướng Dẫn Cài Đặt & Chạy Local

### Yêu cầu
- Python 3.10+
- MySQL / MariaDB đang chạy (XAMPP, MySQL Workbench...)
- Git

---

### 1. Tạo Database MySQL
Mở MySQL và chạy:
```sql
CREATE DATABASE danang_hidden_gems
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

> ⚠️ Mặc định kết nối: `host=127.0.0.1`, `user=root`, `password=''`.  
> Nếu khác, sửa trong `backend/settings.py` mục `DATABASES`.

---

### 2. Chạy Backend Django (API Core)
```bash
cd backend

# (Khuyên dùng) Tạo môi trường ảo
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # Mac/Linux

# Cài thư viện
pip install -r requirements.txt

# Tạo bảng trong MySQL
python manage.py migrate

# Import dữ liệu mồi từ JSON vào MySQL
python scripts/import_data.py

# Khởi chạy server tại cổng 8080
python manage.py runserver 8080
```
✅ API sẵn sàng tại: `http://localhost:8080/api/`  
✅ Admin panel: `http://localhost:8080/admin/`

---

### 3. Chạy AI Service (FastAPI + FAISS + PhoBERT)
Mở **terminal mới** từ thư mục gốc:
```bash
cd ai_service

pip install -r requirements.txt

# Đồng bộ FAISS index từ dữ liệu JSON (chỉ cần chạy 1 lần)
# Lần đầu sẽ tự download model PhoBERT ~543MB từ HuggingFace
python scripts/sync_faiss.py

# Khởi chạy server tại cổng 8000
python -m uvicorn main:app --reload --port 8000
```
✅ AI Service tại: `http://localhost:8000`  
✅ API Docs (Swagger): `http://localhost:8000/docs`

---

## 📡 Danh Sách API Endpoints

| Method | URL | Chức năng |
|--------|-----|-----------|
| `GET` | `/api/places/` | Danh sách địa điểm (phân trang 12/trang) |
| `GET` | `/api/places/?category=Cafe` | Lọc theo danh mục |
| `GET` | `/api/places/?search=biển` | Tìm kiếm theo tên/địa chỉ |
| `GET` | `/api/places/?hidden_gem=1` | Lọc hidden gems |
| `GET` | `/api/places/{id}/` | Chi tiết địa điểm |
| `POST` | `/api/places/` | Crowdsourcing: submit địa điểm mới |
| `GET` | `/api/places/{id}/reviews/` | Danh sách reviews của địa điểm |
| `POST` | `/api/places/{id}/bookmark/` | Toggle bookmark |
| `POST` | `/api/search/` | **Tìm kiếm ngữ nghĩa AI** (PhoBERT + FAISS) |
| `GET` | `/api/categories/` | Danh sách danh mục |
| `POST` | `/api/reviews/` | Tạo review mới |

### Ví dụ Semantic Search
```bash
curl -X POST http://localhost:8080/api/search/ \
  -H "Content-Type: application/json" \
  -d '{"query": "quán cà phê chill gần biển", "top_k": 5}'
```

---

## 🛠️ Công Nghệ Sử Dụng

| Layer | Stack |
|-------|-------|
| Backend API | Python, Django 4.2 LTS, Django REST Framework |
| AI Service | FastAPI, PhoBERT (`vinai/phobert-base`), FAISS |
| Database | MySQL / MariaDB |
| Vector Search | FAISS IndexIDMap (L2 distance) |
| Frontend *(sắp ra)* | ReactJS, Google Maps API |

---

## 🤝 Git Workflow
Nhánh đang phát triển: **`feature/ai-api`**

```bash
git clone <repo-url>
git checkout feature/ai-api
```

Khi có thay đổi: `git add .` → `git commit -m "..."` → `git push origin feature/ai-api`
