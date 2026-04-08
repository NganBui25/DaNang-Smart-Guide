# Restart Guide

Tài liệu này dành cho trường hợp bạn đã chạy dự án thành công ít nhất một lần và chỉ muốn mở máy lên rồi chạy lại thật nhanh.

## 1. Mở Docker Desktop

Mở Docker Desktop và chờ đến khi Docker Engine sẵn sàng.

## 2. Mở terminal tại thư mục dự án

PowerShell:
```powershell
cd D:\kiki\DUT\SEM6\sem6_hch\05_python\DaNang-Smart-Guide
```

## 3. Chạy lại các service

Máy CPU:
```powershell
docker compose up -d
```

Máy GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

## 4. Kiểm tra
```powershell
docker compose ps
```

Bạn nên thấy các service:
- `db`
- `backend`
- `ai_service`
- `frontend`

## 5. Mở ứng dụng

- Frontend: `http://localhost:3000`
- API: `http://localhost:8080/api/places/`
- Django Admin: `http://localhost:8080/admin/`

## 6. Nếu search trả về rỗng
```powershell
docker compose run --rm backend python scripts/backfill_embeddings.py
docker compose run --rm ai_service python scripts/sync_faiss.py
docker compose restart backend
```

Nếu bạn vừa đổi model embedding và cần làm lại toàn bộ vector:
```sql
UPDATE places_place SET embedding_vector = NULL;
```
```powershell
docker compose run --rm backend python scripts/backfill_embeddings.py
```

## 7. Nếu giao diện hoặc admin lỗi CSS / media
```powershell
docker compose restart backend frontend
```

Sau đó hard refresh trình duyệt bằng `Ctrl + F5`.

## 8. Khi dùng xong
```powershell
docker compose down
```

## 9. Full reset khi thật sự cần

Lệnh này sẽ xóa DB volume và dựng lại toàn bộ:
```powershell
docker compose down -v
docker compose build
docker compose up -d
docker compose run --rm backend sh -c "python manage.py migrate && python scripts/import_data.py && python scripts/backfill_embeddings.py && python manage.py collectstatic --noinput"
docker compose run --rm ai_service python scripts/sync_faiss.py
```
