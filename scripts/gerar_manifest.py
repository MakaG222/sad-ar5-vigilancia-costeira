#!/usr/bin/env python3
"""Gera resultados/manifest.json com checksums SHA-256 dos JSON."""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "resultados/validacao.json",
    "resultados/resultados.json",
    "resultados/camadas_mapa.json",
    "resultados/demo_navios.json",
    "resultados/ahp_pesos.json",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    out = {rel: sha256(ROOT / rel) for rel in FILES if (ROOT / rel).is_file()}
    manifest = {
        "gerado_em": date.today().isoformat(),
        "nota": "Checksums SHA-256 dos JSON canónicos.",
        "sha256": out,
    }
    path = ROOT / "resultados" / "manifest.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"Escrito {path} ({len(out)} ficheiros)")


if __name__ == "__main__":
    main()
