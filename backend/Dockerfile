FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY backend/requirements.txt /app/backend-requirements.txt
RUN pip install --no-cache-dir -r /app/backend-requirements.txt

COPY . /app
WORKDIR /app/backend

RUN python manage.py collectstatic --noinput || true

EXPOSE 8080
CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "3"]
