#!/usr/bin/env bash
# Arranca a plataforma em Docker (API + interface num único contentor).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
PORT="${API_PORT:-8080}"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERRO: Docker não encontrado. Instale Docker Desktop: https://www.docker.com/products/docker-desktop/"
  exit 1
fi

cd "$ROOT"
echo "==> SAD AR5 — Docker"
echo "    A construir imagem (1.ª vez pode demorar alguns minutos)..."
docker compose up --build -d

echo
echo "A aguardar API (até 150 s no 1.º arranque)..."
for i in $(seq 1 150); do
  if curl -sf "http://127.0.0.1:${PORT}/api/health" >/dev/null 2>&1; then
    echo "    API OK"
    break
  fi
  sleep 1
  if [[ "$i" -eq 150 ]]; then
    echo "ERRO: API não respondeu. Ver: docker compose logs -f"
    exit 1
  fi
done

echo
echo "=========================================="
echo "  Plataforma pronta (Docker)"
echo "  Abrir: http://localhost:${PORT}"
echo "  Health: http://localhost:${PORT}/api/health"
echo
echo "  Parar:  ./stop-docker.sh"
echo "  Logs:   docker compose logs -f"
echo "=========================================="

if command -v open >/dev/null 2>&1; then
  open "http://localhost:${PORT}" 2>/dev/null || true
fi
