FROM python:3.12-slim AS base

WORKDIR /app

# ── System dependencies ──────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ──────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Application code ─────────────────────────────────────
COPY . .

# ── Web process (FastAPI) ────────────────────────────────
FROM base AS web
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# ── Worker process (Celery) ──────────────────────────────
FROM base AS worker
CMD ["celery", "-A", "app.core.celery", "worker", "--loglevel=info", "--concurrency=2"]
