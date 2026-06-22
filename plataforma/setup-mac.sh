#!/usr/bin/env bash
# Instalação única da plataforma SAD AR5 no macOS.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
API="$ROOT/api"
WEB="$ROOT/web"

echo "==> SAD AR5 — setup macOS"
echo "    Pasta: $ROOT"
echo

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERRO: '$1' não encontrado."
    echo "      Instale com Homebrew, por exemplo:"
    echo "        brew install $2"
    exit 1
  fi
}

need_cmd python3 python
need_cmd node node
need_cmd npm node

PY="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"
echo "Python $PY · Node $(node -v) · npm $(npm -v)"
echo

# --- API ---
echo "==> API (venv + dependências Python)"
cd "$API"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip -q
pip install -r requirements.txt
echo "    OK: .venv pronto"
echo

# --- Frontend ---
echo "==> Frontend (npm)"
cd "$WEB"
npm install
echo "    OK: node_modules pronto"
echo

# --- .env opcional ---
ENV_EX="$ROOT/.env.example"
ENV="$ROOT/.env"
if [[ ! -f "$ENV" && -f "$ENV_EX" ]]; then
  cp "$ENV_EX" "$ENV"
  echo "==> Criado $ENV (edite AISSTREAM_API_KEY se tiver chave AIS)"
fi

echo "==> Setup concluído."
echo
echo "Arranque:"
echo "  cd \"$ROOT\""
echo "  ./start-mac.sh"
echo
