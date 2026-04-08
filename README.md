# DaNang Smart Guide

DaNang Smart Guide là dự án full-stack giúp tìm kiếm địa điểm ở Đà Nẵng bằng semantic search.

## Công nghệ dùng trong dự án
- Frontend: React + Vite + Nginx
- Backend: Django + DRF + Gunicorn
- AI service: FastAPI + FAISS
- Database: MySQL 8
- Orchestration: Docker Compose

## Cấu trúc chính
- `frontend/`: giao diện web
- `backend/`: API Django + admin
- `ai_service/`: service AI tìm kiếm và vector hóa
- `docker-compose.yml`: cấu hình mặc định, chạy được trên máy chỉ có CPU
- `docker-compose.gpu.yml`: cấu hình bổ sung nếu máy có NVIDIA GPU
- `.env.example`: file mẫu để tạo `.env`

## Trước khi bắt đầu

Bạn cần cài sẵn:
- Git
- Docker Desktop

Trước khi chạy lệnh, hãy mở Docker Desktop và chờ đến khi Docker Engine sẵn sàng.

## Chọn cách chạy: CPU hay GPU

Mặc định repo dùng `docker-compose.yml`, phù hợp với mọi máy, kể cả máy chỉ có CPU.

Nếu máy có NVIDIA GPU và Docker đã cấu hình GPU runtime, bạn có thể bật thêm file:
- `docker-compose.gpu.yml`

Quy ước trong tài liệu này:
- Máy CPU: dùng lệnh `docker compose ...`
- Máy GPU: thay bằng `docker compose -f docker-compose.yml -f docker-compose.gpu.yml ...`

Ví dụ:

CPU:
```powershell
docker compose up -d
```

GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

## Chạy dự án lần đầu sau khi clone

### 1. Clone code
```powershell
git clone <repo-url>
cd DaNang-Smart-Guide
```

Nếu bạn muốn lấy nhánh `develop`:
```powershell
git clone -b develop <repo-url>
cd DaNang-Smart-Guide
```

### 2. Tạo file môi trường

PowerShell:
```powershell
Copy-Item .env.example .env
```

Git Bash / Linux / macOS:
```bash
cp .env.example .env
```

Thông thường có thể dùng ngay giá trị mặc định trong `.env.example`.

### 3. Build và khởi động các service

Máy CPU:
```powershell
docker compose build
docker compose up -d
```

Máy GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml build
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

### 4. Khởi tạo dữ liệu lần đầu

Chạy migrate, import dữ liệu mẫu, backfill embedding và collectstatic:

Máy CPU:
```powershell
docker compose run --rm backend sh -c "python manage.py migrate && python scripts/import_data.py && python scripts/backfill_embeddings.py && python manage.py collectstatic --noinput"
```

Máy GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm backend sh -c "python manage.py migrate && python scripts/import_data.py && python scripts/backfill_embeddings.py && python manage.py collectstatic --noinput"
```

Đồng bộ FAISS index:

Máy CPU:
```powershell
docker compose run --rm ai_service python scripts/sync_faiss.py
```

Máy GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm ai_service python scripts/sync_faiss.py
```

### 5. Kiểm tra các service đã chạy
```powershell
docker compose ps
```

Nếu bạn đang dùng GPU variant thì thay bằng:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml ps
```

Khi chạy ổn, bạn có thể mở:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8080/api/`
- Django Admin: `http://localhost:8080/admin/`
- AI Service docs: `http://localhost:8000/docs`

## Tạo tài khoản admin

Nếu cần tài khoản admin để đăng nhập trang quản trị:

Máy CPU:
```powershell
docker compose run --rm backend python manage.py createsuperuser
```

Máy GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm backend python manage.py createsuperuser
```

## Những lần chạy sau

Sau lần đầu, thông thường chỉ cần:

Máy CPU:
```powershell
docker compose up -d
```

Máy GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

## Các lệnh thường dùng

Xem service đang chạy:
```powershell
docker compose ps
```

Xem log realtime của AI service:
```powershell
docker compose logs -f ai_service
```

Vào shell bên trong container AI:
```powershell
docker compose exec ai_service sh
```

Khởi động lại backend:
```powershell
docker compose restart backend
```

Dừng tất cả service:
```powershell
docker compose down
```

Xóa cả container và volume:
```powershell
docker compose down -v
```

Nếu dùng GPU, hãy thêm `-f docker-compose.yml -f docker-compose.gpu.yml` vào các lệnh trên.

## Các tình huống thường gặp

### 1. Docker Desktop đang mở nhưng lệnh Docker không chạy

Hãy kiểm tra:
```powershell
docker ps
docker compose ps
```

Nếu lỗi liên quan daemon, hãy đóng và mở lại Docker Desktop.

### 2. Search trả về rỗng

Chạy lại backfill và sync index:
```powershell
docker compose run --rm backend python scripts/backfill_embeddings.py
docker compose run --rm ai_service python scripts/sync_faiss.py
docker compose restart backend
```

Nếu bạn vừa đổi model embedding và muốn làm lại toàn bộ vector trong DB:
```sql
UPDATE places_place SET embedding_vector = NULL;
```
Sau đó chạy lại:
```powershell
docker compose run --rm backend python scripts/backfill_embeddings.py
```

### 3. Muốn reset toàn bộ dự án

Lệnh này sẽ xóa DB volume và dựng lại từ đầu:
```powershell
docker compose down -v
docker compose build
docker compose up -d
docker compose run --rm backend sh -c "python manage.py migrate && python scripts/import_data.py && python scripts/backfill_embeddings.py && python manage.py collectstatic --noinput"
docker compose run --rm ai_service python scripts/sync_faiss.py
```

### 4. Máy chỉ có CPU

Không sao, vẫn chạy được bằng `docker-compose.yml`.

Lưu ý:
- AI service sẽ chạy chậm hơn GPU
- không dùng `docker-compose.gpu.yml` trên máy không có NVIDIA GPU

### 5. Máy có NVIDIA GPU

Bạn có thể bật file override GPU để `ai_service` yêu cầu GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

## Lưu ý khi cộng tác

- Người khác chỉ nhận được những gì đã `commit` và `push`
- Thay đổi local chưa commit sẽ không xuất hiện khi người khác clone repo
- Không commit file `.env` thật chứa secret

## Tóm tắt siêu ngắn cho người mới

Nếu bạn chỉ cần chạy nhanh bản CPU:
```powershell
git clone -b develop <repo-url>
cd DaNang-Smart-Guide
Copy-Item .env.example .env
docker compose build
docker compose up -d
docker compose run --rm backend sh -c "python manage.py migrate && python scripts/import_data.py && python scripts/backfill_embeddings.py && python manage.py collectstatic --noinput"
docker compose run --rm ai_service python scripts/sync_faiss.py
```
