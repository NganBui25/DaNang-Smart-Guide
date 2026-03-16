FROM python:3.11-slim
WORKDIR /app/ai_service
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY ai_service/requirements.txt /app/ai_service/requirements.txt
RUN pip install --no-cache-dir -r /app/ai_service/requirements.txt

COPY . /app

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
