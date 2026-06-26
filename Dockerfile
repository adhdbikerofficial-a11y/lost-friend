FROM python:3.12-slim

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

# Railway usa EXPOSE para detectar el puerto del proxy HTTP
EXPOSE 8000

# ── Note: Railway define el comando de inicio por servicio.
# ── Web:  uvicorn main:app --host 0.0.0.0 --port 8000
# ── Worker: celery -A app.core.celery worker --loglevel=info --concurrency=2
