#!/usr/bin/env bash
# Gera o relatório final limpo SIGAVI_FINAL (formato original do grupo, conteúdo actualizado).
# Cada execução arquiva uma cópia versionada em relatorio/versoes/.
set -euo pipefail

ORIG="$(cd "$(dirname "$0")/.." && pwd)"
DL="$(dirname "$ORIG")"
BASE_DOC="${1:-$DL/Trabalho Final SAD.docx}"
DEST="$DL/SIGAVI_FINAL"
VERS_DIR="$ORIG/relatorio/versoes"
VERS_LOG="$VERS_DIR/VERSOES.md"

if [[ ! -f "$BASE_DOC" ]]; then
  echo "ERRO: documento base não encontrado: $BASE_DOC"
  exit 1
fi

mkdir -p "$DEST" "$VERS_DIR" "$ORIG/relatorio"

echo "==> A gerar SIGAVI_FINAL.docx (sem realce amarelo) ..."
cd "$ORIG/src"
python3 gerar_docx_diff.py --entrega "$BASE_DOC" "$DEST/SIGAVI_FINAL.docx"

echo "==> A gerar SIGAVI_FINAL.pdf ..."
if [[ -f gerar_pdf.py ]]; then
  python3 gerar_pdf.py "$DEST/SIGAVI_FINAL.docx" "$DEST/SIGAVI_FINAL.pdf"
else
  echo "AVISO: gerar_pdf.py não encontrado — só DOCX gerado."
fi

STAMP=$(date +%Y%m%d_%H%M)
max_ver=0
for f in "$VERS_DIR"/SIGAVI_FINAL_v*.docx; do
  [[ -e "$f" ]] || continue
  n=$(basename "$f" | sed -n 's/SIGAVI_FINAL_v\([0-9]*\)_.*/\1/p')
  [[ -n "$n" && "$n" -gt "$max_ver" ]] && max_ver="$n"
done
next_ver=$((max_ver + 1))
ver_tag=$(printf 'v%03d' "$next_ver")
archived="$VERS_DIR/SIGAVI_FINAL_${ver_tag}_${STAMP}.docx"

cp "$DEST/SIGAVI_FINAL.docx" "$archived"
cp "$DEST/SIGAVI_FINAL.docx" "$ORIG/relatorio/SIGAVI_FINAL.docx"
cp "$DEST/SIGAVI_FINAL.docx" "$DL/SIGAVI_FINAL.docx"
cp "$ORIG/NOTAS_ENTREGA.md" "$DEST/NOTAS_ENTREGA.md"

if [[ ! -f "$VERS_LOG" ]]; then
  cat > "$VERS_LOG" <<'EOF'
# Versões do relatório SIGAVI_FINAL

Arquivo automático: cada `bash scripts/gerar_sigavi_final.sh` gera uma cópia em `relatorio/versoes/`.

| Versão | Ficheiro | Notas |
|--------|----------|-------|
EOF
fi
echo "| ${ver_tag} | \`SIGAVI_FINAL_${ver_tag}_${STAMP}.docx\` | $(date '+%Y-%m-%d %H:%M') |" >> "$VERS_LOG"

if [[ -f "$DEST/SIGAVI_FINAL.pdf" ]]; then
  cp "$DEST/SIGAVI_FINAL.pdf" "$ORIG/relatorio/SIGAVI_FINAL.pdf"
  cp "$DEST/SIGAVI_FINAL.pdf" "$DL/SIGAVI_FINAL.pdf"
fi

echo ""
echo "✓ Relatório final SIGAVI (${ver_tag}):"
echo "    $DEST/SIGAVI_FINAL.docx"
echo "    $DL/SIGAVI_FINAL.docx"
echo "    $ORIG/relatorio/SIGAVI_FINAL.docx"
echo "    $archived"
if [[ -f "$DEST/SIGAVI_FINAL.pdf" ]]; then
  echo "    $DEST/SIGAVI_FINAL.pdf"
fi
