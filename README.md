# DaNang Smart Guide

DaNang Smart Guide is a full-stack demo app for discovering places in Da Nang using semantic search.

## Stack
- Frontend: React + Vite + Nginx
- Backend: Django + DRF + Gunicorn
- AI service: FastAPI + FAISS
- Database: MySQL 8 (Docker)
- Orchestration: Docker Compose

## Project Structure
- `frontend/`: web UI
- `backend/`: Django API + admin
- `ai_service/`: AI search service
- `docker-compose.yml`: all services
- `.env.example`: base environment values

## Prerequisites
- Docker Desktop (running)
- Git

## Quick Start (Recommended: Docker)
1. Clone repo:
```bash
git clone https://github.com/NganBui25/DaNang-Smart-Guide.git
cd DaNang-Smart-Guide
```

2. Create env file:
```bash
cp .env.example .env
```
On Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

3. Build and start services:
```bash
docker compose build
docker compose up -d
```

4. Run migration + import data + static + vector sync:
```bash
docker compose run --rm backend sh -c "python manage.py migrate && python scripts/import_data.py && python scripts/backfill_embeddings.py && python manage.py collectstatic --noinput"
docker compose run --rm ai_service python scripts/sync_faiss.py
```

5. Open app:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8080/api/
- Django Admin: http://localhost:8080/admin/
- AI Service docs: http://localhost:8000/docs

## Create Admin Account
If no admin exists yet:
```bash
docker compose run --rm backend python manage.py createsuperuser
```

## Useful Commands
```bash
docker compose ps
docker compose logs -f --tail=200
docker compose restart backend
docker compose down
docker compose down -v
```

## Common Issues
### 1) Port 3306 conflict
If you have local MySQL running, keep Docker DB internal only (already configured in this repo).

### 2) Docker daemon error
If you see `Docker Desktop is unable to start`, restart Docker Desktop and verify:
```bash
docker version
docker run --rm hello-world
```

### 3) Search returns empty
Re-run:
```bash
docker compose run --rm backend python scripts/backfill_embeddings.py
docker compose run --rm ai_service python scripts/sync_faiss.py
docker compose restart backend
```

### 4) Images not showing
Make sure backend is up and media URLs are served from backend:
```bash
docker compose up -d backend frontend
```
Then hard refresh browser (`Ctrl + F5`).

## Non-Docker (Optional)
You can run services manually, but Docker is strongly recommended for demo stability.

## Notes
- Do not commit real secrets into `.env`.
- Use `.env.example` as template.
