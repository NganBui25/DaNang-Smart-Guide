# Restart Guide (After Shutdown)

Use this every time you turn your machine on and want to run demo quickly.

## A) Start services
1. Open Docker Desktop and wait until it is ready.
2. Open terminal in project folder:
```powershell
cd D:\kiki\DUT\SEM6\sem6_hch\05_python\DaNang-Smart-Guide
```
3. Start all services:
```powershell
docker compose up -d
```

## B) Verify
```powershell
docker compose ps
```
You should see: `db`, `backend`, `ai_service`, `frontend` as running.

Open:
- http://localhost:3000
- http://localhost:8080/api/places/

## C) If search has no results
```powershell
docker compose run --rm backend python scripts/backfill_embeddings.py
docker compose run --rm ai_service python scripts/sync_faiss.py
docker compose restart backend
```

## D) If admin/login/css looks broken
```powershell
docker compose restart backend frontend
```
Then hard refresh browser: `Ctrl + F5`.

## E) Stop when done
```powershell
docker compose down
```

## F) Full reset (only when needed)
This will remove DB volume and rebuild from scratch:
```powershell
docker compose down -v
docker compose build
docker compose up -d
docker compose run --rm backend sh -c "python manage.py migrate && python scripts/import_data.py && python scripts/backfill_embeddings.py && python manage.py collectstatic --noinput"
docker compose run --rm ai_service python scripts/sync_faiss.py
```
