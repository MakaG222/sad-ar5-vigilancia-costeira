#!/usr/bin/env bash
# Arranque completo num único terminal (Mac)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

if [[ ! -d "$ROOT/api/.venv" ]] || [[ ! -d "$ROOT/web/node_modules" ]]; then
  echo "Instalação incompleta. A correr setup…"
  "$ROOT/setup.sh"
fi

cleanup() {
  echo
  echo "==> A parar serviços…"
  [[ -n "${API_PID:-}" ]] && kill "$API_PID" 2>/dev/null || true
  wait "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "==> A iniciar API (background)…"
"$ROOT/start-api.sh" &
API_PID=$!

echo "==> A aguardar API…"
for _ in $(seq 1 30); do
  if curl -sf "http://127.0.0.1:8080/api/estado" >/dev/null 2>&1; then
    echo "    API pronta."
    break
  fi
  sleep 1
done

echo "==> A iniciar frontend…"
exec "$ROOT/start-web.sh"
