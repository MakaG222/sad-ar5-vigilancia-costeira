#!/usr/bin/env bash
# Gera o relatório final limpo SIGAVI_FINAL (formato original do grupo, conteúdo actualizado).
set -euo pipefail

ORIG="$(cd "$(dirname "$0")/.." && pwd)"
DL="$(dirname "$ORIG")"
BASE_DOC="${1:-$DL/Trabalho Final SAD.docx}"
DEST="$DL/SIGAVI_FINAL"

if [[ ! -f "$BASE_DOC" ]]; then
  echo "ERRO: documento base não encontrado: $BASE_DOC"
  exit 1
fi

mkdir -p "$DEST"

echo "==> A gerar SIGAVI_FINAL.docx (sem realce amarelo) ..."
cd "$ORIG/src"
python3 gerar_docx_diff.py --entrega "$BASE_DOC" "$DEST/SIGAVI_FINAL.docx"

echo "==> A gerar SIGAVI_FINAL.pdf ..."
python3 gerar_pdf.py "$DEST/SIGAVI_FINAL.docx" "$DEST/SIGAVI_FINAL.pdf"

cp "$ORIG/NOTAS_ENTREGA.md" "$DEST/NOTAS_ENTREGA.md"
cp "$DEST/SIGAVI_FINAL.docx" "$ORIG/relatorio/SIGAVI_FINAL.docx"
cp "$DEST/SIGAVI_FINAL.pdf" "$ORIG/relatorio/SIGAVI_FINAL.pdf"
cp "$DEST/SIGAVI_FINAL.docx" "$DL/SIGAVI_FINAL.docx"
cp "$DEST/SIGAVI_FINAL.pdf" "$DL/SIGAVI_FINAL.pdf"

echo ""
echo "✓ Relatório final SIGAVI:"
echo "    $DEST/SIGAVI_FINAL.docx"
echo "    $DEST/SIGAVI_FINAL.pdf"
echo "    $DL/SIGAVI_FINAL.docx"
echo "    $ORIG/relatorio/SIGAVI_FINAL.docx"
