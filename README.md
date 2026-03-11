# 🏝️ Da Nang Smart Guide & Hidden Gems Recommendation

Dự án Hệ thống Gợi ý Điểm đến Bản địa tại Đà Nẵng, sử dụng công nghệ tìm kiếm ngữ nghĩa (Semantic Search) kết hợp với các mô hình ngôn ngữ lớn (NLP/PhoBERT) và nền tảng Web App.

Hệ thống được thiết kế theo kiến trúc Microservices gồm Backend Core (Django) xử lý CSDL và AI Service (FastAPI) chuyên dụng cho tính toán Vector FAISS.

## 📂 Cấu Trúc Thư Mục

```text
danang_hidden_gems/
├── backend/            # Chứa Backend API Core (Django + MySQL)
│   ├── apps/           # Chứa các app nghiệp vụ (places, reviews, users)
│   ├── data/           # Thư mục cào dữ liệu mồi JSON
│   ├── settings.py     # Config kết nối CSDL và App
│   └── requirements.txt
├── ai_service/         # Service độc lập chạy AI Model & FAISS Vector
│   ├── faiss_index/    # Chứa file bin index lưu trữ Vector
│   ├── scripts/        # Thư mục chạy background logic
│   ├── main.py         # Chạy FastAPI root cho tìm kiếm Vector
│   └── requirements.txt
└── frontend/           # (Sẽ có trong giai đoạn sau) Chứa ReactJS User App
```

## 🚀 Hướng Dẫn Cài Đặt và Chạy Project Local

Dưới đây là các bước để các thành viên trong nhóm clone về và chạy được trên máy tính cá nhân.

### 1. Yêu cầu trước khi bắt đầu (Prerequisites)
- Đã cài đặt Python 3.10 trở lên.
- Đã cài đặt và khởi chạy hệ quản trị CSDL MySQL (thông qua MySQL Workbench, XAMPP >= 10.4).
- Cài Git.

### 2. Thiết lập cơ sở dữ liệu (MySQL)
Mở một trình quản lý MySQL (VD: phpMyAdmin cục bộ hoặc DBeaver, tạo 1 câu lệnh Query mới và chạy):

```sql
CREATE DATABASE IF NOT EXISTS danang_hidden_gems CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

> **Lưu ý**: Config mặc định trong hệ thống đang cấu hình host MySQL là `127.0.0.1:3306`, user là `root`, password rỗng `''`. Nếu máy bạn có password, hãy vào file `backend/settings.py` để chỉnh lại trong biến `DATABASES`.

### 3. Cài đặt và Chạy Backend API (Django)
Mở terminal tại thư mục gốc của project (nơi chứa file này):

```bash
# 1. Di chuyển vào thư mục backend
cd backend

# 2. (Tùy chọn nhưng KHUYÊN DÙNG) Tạo môi trường ảo Virtual Environment để tránh xung đột thư viện với hệ điều hành:
python -m venv venv
# Active cho Windows:
.\venv\Scripts\activate
# Active cho MacOS/Linux:
source venv/bin/activate

# 3. Cài đặt các thư viện cần thiết cho Django
pip install -r requirements.txt

# 4. Tạo cấu trúc các bảng MySQL từ Models python (Migrate)
python manage.py migrate

# 5. Khởi chạy Server Backend tại cổng 8080 (hoặc cổng mặc định 8000 của django)
python manage.py runserver 8080
```
Server Backend sẽ chạy ở url: `http://localhost:8080`

### 4. Cài đặt và Chạy AI Service (FastAPI + FAISS)
FastAPI sẽ chạy độc lập để load file FAISS Index vào RAM. Hãy mở một **Terminal mới** từ thư mục gốc.

```bash
# 1. Di chuyển vào thư mục ai_service
cd ai_service

# 2. Cài đặt các thư viện cho AI Service
pip install -r requirements.txt

# 3. Khởi chạy server FastAPI (Nên chạy cổng mặc định 8000)
python -m uvicorn main:app --reload --port 8000
```
Server AI FastAPI sẽ chạy lúc này. Bạn có thể test API Docs xịn xò có sẵn của FastAPI tại: `http://localhost:8000/docs`

---

## 🤝 Hướng Dẫn Đóng Góp (Git Workflow)
Nhóm đang sử dụng nhánh **`feature/ai-api`** cho phần Backend và AI Vector. Khi clone về:
1. `git checkout feature/ai-api`
2. Cập nhật sửa lỗi nếu có.
3. Git add, commit và mở Pull Request báo cho Leader nếu code mới chạy ổn.
