#!/usr/bin/env python3
"""Reestrutura (18→11 secções) e sincroniza Relatorio_SAD_AR5.md com o pipeline."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent


def main() -> None:
    rel = SRC.parent / "relatorio" / "Relatorio_SAD_AR5.md"
    text = rel.read_text(encoding="utf-8")
    # Já reestruturado (11 secções) — saltar merge 18→11
    ja_11 = "## 4. Pipeline de *data mining*" in text and "## 12. Validação quantitativa" not in text

    steps: list[list[str]] = []
    if not ja_11:
        steps.append([sys.executable, str(SRC / "restructurar_relatorio.py")])
    steps.extend([
        [sys.executable, str(SRC / "atualizar_relatorio_20.py")],
        [sys.executable, str(SRC / "fix_relatorio_pos_sync.py")],
    ])
    for cmd in steps:
        print(">>", " ".join(cmd))
        subprocess.run(cmd, check=True)
    print("OK — relatório sincronizado.")


if __name__ == "__main__":
    main()
