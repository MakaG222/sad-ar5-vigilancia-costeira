#!/usr/bin/env bash
# Frontend Vite — porta 5173 (proxy /api → 8080)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
WEB="$ROOT/web"

if [[ ! -d "$WEB/node_modules" ]]; then
  echo "node_modules não encontrado. Corra primeiro: $ROOT/setup-mac.sh"
  exit 1
fi

cd "$WEB"

echo "==> Web SAD AR5 — http://localhost:5173"
echo "    (requer API em http://127.0.0.1:8080)"
echo

# Abrir browser no Mac após arranque do servidor
(sleep 2 && open "http://localhost:5173" 2>/dev/null) &

exec npm run dev -- --host 127.0.0.1 --port 5173
