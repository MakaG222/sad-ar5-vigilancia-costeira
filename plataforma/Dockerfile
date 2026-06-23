# SAD AR5 — imagem única: API FastAPI + frontend estático (Vite build)
# Build: docker compose build   (a partir de plataforma/)
# Contexto: raiz do repositório (..)

FROM node:20-alpine AS web
WORKDIR /build
COPY plataforma/web/package.json plataforma/web/package-lock.json ./
RUN npm ci
COPY plataforma/web/ ./
RUN npm run build

FROM python:3.12-slim AS api

# CBC — solver usado por PuLP (MCLP / set cover)
RUN apt-get update \
    && apt-get install -y --no-install-recommends coinor-cbc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY plataforma/api/requirements.txt /app/plataforma/api/requirements.txt
RUN pip install --no-cache-dir -r /app/plataforma/api/requirements.txt

COPY src/ /app/src/
COPY dados/ /app/dados/
COPY resultados/ /app/resultados/
COPY plataforma/api/ /app/plataforma/api/
COPY --from=web /build/dist /app/plataforma/web/dist

WORKDIR /app/plataforma/api
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=15s --start-period=150s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=10)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
