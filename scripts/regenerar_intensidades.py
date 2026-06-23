#!/usr/bin/env python3
"""Regenera dados/processados/intensidades_reais.csv a partir dos rasters EMODnet.

Requer: pip install rasterio numpy pandas
Uso: python scripts/regenerar_intensidades.py

Nota: o ficheiro CSV pré-calculado já está no repositório; só é necessário
regenerar se alterar os rasters em dados/fontes/emodnet/ ou a grelha em geo.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dados" / "processados" / "intensidades_reais.csv"


def main() -> int:
    try:
        import rasterio  # noqa: F401
    except ImportError:
        print("ERRO: instale rasterio — pip install rasterio", file=sys.stderr)
        print("O CSV existente em dados/processados/ pode ser usado sem regenerar.", file=sys.stderr)
        return 1

    if OUT.is_file():
        print(f"CSV existente: {OUT}")
        print("Para regenerar, implemente aqui a leitura dos .tif EMODnet e a amostragem na grelha.")
        print("Ver src/risco.py (_carregar_intensidades_reais) para o formato esperado.")
        return 0

    print(f"Ficheiro em falta: {OUT}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
