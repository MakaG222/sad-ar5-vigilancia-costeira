"""Cache partilhada da grelha SAD + risco (evita recalcular em cada endpoint)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from geo import gerar_procura, ponto_em_mar, ponto_em_mar_mapa
from risco import calcular_risco

XLSX = os.path.join(os.path.dirname(__file__), "..", "..", "..", "dados", "fontes",
                    "apreensoes_droga_PT.xlsx")

_pts: list[dict] | None = None
_pts_mar: list[dict] | None = None
_pts_mar_mapa: list[dict] | None = None


def pts_mar_mapa() -> list[dict]:
    """Células de mar aberto para marcadores no mapa (≥15 km costa, fora de estuários)."""
    global _pts_mar_mapa
    if _pts_mar_mapa is None:
        _pts_mar_mapa = [
            p for p in pts_mar()
            if ponto_em_mar_mapa(p["lon"], p["lat"])
        ]
    return _pts_mar_mapa


def pts_grelha() -> list[dict]:
    """Grelha completa com risco calculado (singleton em memória)."""
    global _pts
    if _pts is None:
        _pts = gerar_procura()
        calcular_risco(_pts, XLSX)
    return _pts


def pts_mar() -> list[dict]:
    """Células marítimas operacionais (subconjunto cacheado)."""
    global _pts_mar
    if _pts_mar is None:
        _pts_mar = [p for p in pts_grelha() if ponto_em_mar(p["lon"], p["lat"])]
    return _pts_mar


def aquecer_grelha() -> None:
    """Pré-aquece cache no arranque da API."""
    pts_grelha()
    pts_mar()
    pts_mar_mapa()


def invalidar() -> None:
    global _pts, _pts_mar, _pts_mar_mapa
    _pts = None
    _pts_mar = None
    _pts_mar_mapa = None
