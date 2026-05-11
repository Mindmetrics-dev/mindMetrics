# ═══════════════════════════════════════════════════════════════════════════════
# MindMetrics — Dockerfile para servicio `web_ia` (Django + ETL)
# Base: python:3.13-slim (alineado con __pycache__ cpython-313 detectado)
# ═══════════════════════════════════════════════════════════════════════════════

FROM python:3.13-slim AS base

# Evita .pyc en contenedor y fuerza unbuffered stdout (logs en tiempo real)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Dependencias del sistema mínimas para psycopg[binary] y compilación opcional
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Capa de dependencias — se cachea si requirements.txt no cambia
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/backend/requirements.txt

# Copia diferida del código (la imagen final se construye en docker-compose con bind mount)
COPY . /app

# Puerto Django por defecto
EXPOSE 8000

# El comando real lo define docker-compose.yml (migrate + ETL + runserver)
CMD ["python", "/app/backend/manage.py", "runserver", "0.0.0.0:8000"]
