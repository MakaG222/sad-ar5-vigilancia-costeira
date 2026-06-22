#!/usr/bin/env bash
# API FastAPI — porta 8080
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
API="$ROOT/api"

if [[ ! -d "$API/.venv" ]]; then
  echo "Venv não encontrado. Corra primeiro: $ROOT/setup-mac.sh"
  exit 1
fi

cd "$API"
# shellcheck disable=SC1091
source .venv/bin/activate

# Chave AIS opcional (ficheiro .env local, não versionado)
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi

echo "==> API SAD AR5 — http://127.0.0.1:8080"
echo "    Docs: http://127.0.0.1:8080/docs"
echo "    AIS: ${AISSTREAM_API_KEY:+aisstream}${AISSTREAM_API_KEY:-demo simulada}"
echo

exec uvicorn main:app --reload --host 127.0.0.1 --port 8080
