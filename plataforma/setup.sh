#!/usr/bin/env bash
# Instalação inicial — macOS (zsh/bash)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
API="$ROOT/api"
WEB="$ROOT/web"

echo "==> SAD AR5 — instalação (Mac)"
echo "    Raiz: $ROOT"
echo

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "ERRO: '$1' não encontrado."
    echo "      Instale com Homebrew: brew install $2"
    exit 1
  fi
}

need_cmd python3 python
need_cmd pip3 python
need_cmd node node
need_cmd npm node

echo "==> Python $(python3 --version)"
echo "==> Node $(node --version)"
echo

echo "==> API: venv + dependências"
cd "$API"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip -q
pip install -r requirements.txt

echo "==> Web: npm install"
cd "$WEB"
npm install

echo
echo "✓ Instalação concluída."
echo
echo "Arranque (dois terminais):"
echo "  Terminal 1:  $ROOT/start-api.sh"
echo "  Terminal 2:  $ROOT/start-web.sh"
echo
echo "Ou tudo num terminal:"
echo "  $ROOT/start.sh"
echo
echo "Opcional — AIS tempo real:"
echo "  export AISSTREAM_API_KEY=\"sua_chave\"   # https://aisstream.io"
