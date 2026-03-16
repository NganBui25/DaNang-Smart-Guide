COMPOSE?=docker-compose

.PHONY: build up down logs data-sync migrate

build:
	$(COMPOSE) build

up: build
	$(COMPOSE) up -d

logs:
	$(COMPOSE) logs -f --tail=200

down:
	$(COMPOSE) down

migrate:
	$(COMPOSE) run --rm backend python manage.py migrate

collectstatic:
	$(COMPOSE) run --rm backend python manage.py collectstatic --noinput

data-sync:
	$(COMPOSE) run --rm backend sh -c "python manage.py migrate && python scripts/import_data.py && python scripts/backfill_embeddings.py && python manage.py collectstatic --noinput"
	$(COMPOSE) run --rm ai_service python scripts/sync_faiss.py
