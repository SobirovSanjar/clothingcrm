FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends netcat-openbsd postgresql-client && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wait-for-db.sh .
RUN chmod +x wait-for-db.sh

COPY . .

EXPOSE 8000

# Wait for database, seed, then start the server.
CMD ["sh", "-c", "./wait-for-db.sh db 5432 && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
