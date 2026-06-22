#!/usr/bin/env bash
# Arranca API (8080) + frontend (5173) no macOS.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
API="$ROOT/api"
WEB="$ROOT/web"
RUN="$ROOT/.run"
API_PID="$RUN/api.pid"
WEB_PID="$RUN/web.pid"
API_LOG="$RUN/api.log"
WEB_LOG="$RUN/web.log"

API_PORT="${API_PORT:-8080}"
WEB_PORT="${WEB_PORT:-5173}"

mkdir -p "$RUN"

cleanup() {
  echo
  echo "==> A parar serviços..."
  "$ROOT/stop-mac.sh" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

need_ready() {
  if [[ ! -d "$API/.venv" || ! -d "$WEB/node_modules" ]]; then
    echo "Dependências em falta. A correr setup..."
    "$ROOT/setup-mac.sh"
  fi
}

free_port() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      echo "    Libertar porta $port"
      kill $pids 2>/dev/null || true
      sleep 0.5
      kill -9 $pids 2>/dev/null || true
    fi
  fi
}

wait_http() {
  local url="$1" label="$2" max="${3:-45}"
  local i=0
  while (( i < max )); do
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "    $label OK ($url)"
      return 0
    fi
    sleep 1
    (( i++ )) || true
  done
  echo "ERRO: $label não respondeu em ${max}s ($url)"
  echo "      Ver logs: $API_LOG / $WEB_LOG"
  exit 1
}

port_listening() {
  lsof -ti tcp:"$1" >/dev/null 2>&1
}

need_ready
"$ROOT/stop-mac.sh" 2>/dev/null || true
free_port "$API_PORT"
free_port "$WEB_PORT"

if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

echo "==> SAD AR5 — arranque macOS"
echo "    API  → http://127.0.0.1:$API_PORT"
echo "    Web  → http://localhost:$WEB_PORT"
echo

# --- API ---
cd "$API"
# shellcheck disable=SC1091
source .venv/bin/activate
: >"$API_LOG"
nohup uvicorn main:app --host 127.0.0.1 --port "$API_PORT" >>"$API_LOG" 2>&1 &
echo $! >"$API_PID"
echo "    API PID $(cat "$API_PID") · log $API_LOG"
wait_http "http://127.0.0.1:$API_PORT/api/estado" "API"

# --- Frontend (vite directamente — PID estável) ---
cd "$WEB"
: >"$WEB_LOG"
nohup ./node_modules/.bin/vite --host 127.0.0.1 --port "$WEB_PORT" >>"$WEB_LOG" 2>&1 &
echo $! >"$WEB_PID"
echo "    Web PID $(cat "$WEB_PID") · log $WEB_LOG"
wait_http "http://127.0.0.1:$WEB_PORT" "Web"

echo
echo "=========================================="
echo "  Plataforma pronta"
echo "  Abrir: http://localhost:$WEB_PORT"
echo "  Docs API: http://127.0.0.1:$API_PORT/docs"
echo
echo "  Parar:  ./stop-mac.sh"
echo "  Logs:   tail -f .run/api.log .run/web.log"
echo "=========================================="
echo

if command -v open >/dev/null 2>&1; then
  open "http://localhost:$WEB_PORT" 2>/dev/null || true
fi

echo "A correr. Ctrl+C para parar."
while true; do
  if ! port_listening "$API_PORT"; then
    echo "ERRO: API deixou de responder na porta $API_PORT. Ver $API_LOG"
    exit 1
  fi
  if ! port_listening "$WEB_PORT"; then
    echo "ERRO: Web deixou de responder na porta $WEB_PORT. Ver $WEB_LOG"
    exit 1
  fi
  sleep 5
done
