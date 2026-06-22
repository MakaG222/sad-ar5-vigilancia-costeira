#!/usr/bin/env bash
# Cria venv local e instala dependências (macOS / Linux)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "$SCRIPT_DIR/requirements.txt" ]]; then
  ROOT="$SCRIPT_DIR"
elif [[ -f "$SCRIPT_DIR/../requirements.txt" ]]; then
  ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
else
  echo "Erro: requirements.txt não encontrado (script em $SCRIPT_DIR)."
  exit 1
fi

VENV="$ROOT/.venv"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Erro: python3 não encontrado. Instale Python 3 (ex.: brew install python)."
  exit 1
fi

if [[ ! -d "$VENV" ]]; then
  echo "==> A criar .venv em $ROOT"
  python3 -m venv "$VENV"
fi

# shellcheck disable=SC1091
source "$VENV/bin/activate"
pip install -q --upgrade pip
pip install -q -r "$ROOT/requirements.txt"
echo "==> Pronto. Active com: source $VENV/bin/activate"
echo "    Depois: cd src && python sincronizar_relatorio.py && python validacao.py && python gerar_docx.py"
