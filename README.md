# DaNang Smart Guide
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d

DaNang Smart Guide la du an full-stack tim kiem dia diem o Da Nang bang semantic search.

## Stack
- Frontend: React + Vite + Nginx
- Backend: Django + DRF + Gunicorn
- AI service: FastAPI + Sentence Transformers + FAISS
- Database: MySQL 8
- Orchestration: Docker Compose

## Cau truc chinh
- `frontend/`: giao dien web
- `backend/`: API Django + admin
- `ai_service/`: service tim kiem ngu nghia, vector hoa va backfill embedding
- `docker-compose.yml`: cau hinh mac dinh, chay duoc tren CPU
- `docker-compose.gpu.yml`: override de cap GPU NVIDIA cho `ai_service`
- `.env.example`: mau bien moi truong

## Chay CPU hay GPU
- CPU: `docker compose ...`
- GPU: `docker compose -f docker-compose.yml -f docker-compose.gpu.yml ...`

GPU mode duoc thiet ke cho Docker + NVIDIA runtime. `ai_service` se tu chon `cuda` khi:
- container co quyen truy cap GPU
- `AI_DEVICE=auto` hoac `AI_DEVICE=cuda`
- torch CUDA wheel da duoc cai

## Bat dau nhanh
### 1. Clone va tao `.env`
```powershell
git clone <repo-url>
cd DaNang-Smart-Guide
Copy-Item .env.example .env
```

### 2. Build va khoi dong
CPU:
```powershell
docker compose build
docker compose up -d
```

GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml build
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d
```

### 3. Khoi tao du lieu lan dau
Migrate + import data + collectstatic:
```powershell
docker compose run --rm backend sh -c "python manage.py migrate && python scripts/import_data.py && python manage.py collectstatic --noinput"
```

Backfill embedding trong `ai_service`:

CPU:
```powershell
docker compose run --rm ai_service python scripts/backfill_db_embeddings.py
```

GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm ai_service python scripts/backfill_db_embeddings.py
```

Dong bo file index FAISS offline:

CPU:
```powershell
docker compose run --rm ai_service python scripts/sync_faiss.py
```

GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm ai_service python scripts/sync_faiss.py
```

## Kiem tra runtime GPU
Kiem tra health:
```powershell
Invoke-RestMethod http://localhost:8000/healthz
```

Ban mong doi thay:
- `status = ok`
- `device = cuda` khi chay GPU dung
- `search_backend = faiss`

Kiem tra truc tiep trong container GPU:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml exec ai_service python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu')"
```

Neu lenh tren in `False` hoac `cpu`, `ai_service` van chua dung GPU that.

## Bien moi truong AI
Trong `.env` hoac `.env.example`:
- `SBERT_MODEL=keepitreal/vietnamese-sbert`
- `AI_DEVICE=auto`
- `SEARCH_BACKEND=faiss`
- `VECTOR_DIMENSION=768`

Gia tri `AI_DEVICE` ho tro:
- `auto`: uu tien `cuda`, fallback `cpu`
- `cpu`: bat buoc CPU
- `cuda`: bat buoc GPU, fail fast neu khong co CUDA

## Cac endpoint AI chinh
- `GET /healthz`: tra runtime state nhu `device`, `model_name`, `torch_version`, `cuda_available`, `search_backend`
- `POST /search`: semantic search, van giu request/response nhu cu
- `POST /vectorize`: vector hoa mot place
- `POST /sentiment`: tom tat cam xuc review

## Cac lenh thuong dung
Xem service:
```powershell
docker compose ps
```

Xem log AI:
```powershell
docker compose logs -f ai_service
```

Vao shell AI:
```powershell
docker compose exec ai_service sh
```

Neu dang chay GPU, them `-f docker-compose.yml -f docker-compose.gpu.yml` vao cac lenh tren.

## Rollout lai embedding sau khi doi runtime/model
1. Rebuild `ai_service`
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml build ai_service
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d ai_service
```

2. Xac nhan `/healthz` tra `device = cuda`

3. Reset vector trong DB:
```sql
UPDATE places_place SET embedding_vector = NULL;
```

4. Chay lai backfill:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm ai_service python scripts/backfill_db_embeddings.py
```

5. Neu van dung file index offline, sync lai:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml run --rm ai_service python scripts/sync_faiss.py
```

## Tinh huong thuong gap
### Search tra ve rong
Chay lai backfill va sync index:
```powershell
docker compose run --rm ai_service python scripts/backfill_db_embeddings.py
docker compose run --rm ai_service python scripts/sync_faiss.py
docker compose restart backend
```

### Chay nham script backfill o backend
`backend/scripts/backfill_embeddings.py` da la script deprecated. Script nay se dung lai va huong dan ban chay lenh moi trong `ai_service`.

### May chi co CPU
Van chay duoc bang `docker-compose.yml`. `ai_service` se tu chuyen sang `cpu` neu `AI_DEVICE=auto`.

### May co NVIDIA GPU
Dung:
```powershell
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --build
```

Sau do kiem tra:
```powershell
Invoke-RestMethod http://localhost:8000/healthz
```

## Dia chi mac dinh
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8080/api/`
- Django Admin: `http://localhost:8080/admin/`
- AI Service docs: `http://localhost:8000/docs`
