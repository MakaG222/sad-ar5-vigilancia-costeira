"""Testes da camada de risco para o mapa."""
from __future__ import annotations

from services import risco_mapa


def test_carregar_celulas_respeita_limiar():
    risco_mapa._celulas_cache = None
    cel = risco_mapa.carregar_celulas(limiar=0.5, max_celulas=50)
    assert len(cel) <= 50
    assert all(c["risco"] >= 0.5 for c in cel)
    assert cel == sorted(cel, key=lambda c: c["risco"], reverse=True)


def test_resumo_risco_tem_contagens():
    risco_mapa._celulas_cache = None
    risco_mapa.carregar_celulas(limiar=0.15)
    res = risco_mapa.resumo_risco()
    assert res["n_celulas_total"] > 1000
    assert res["n_alto_risco"] >= 250
    assert 0 <= res["risco_medio"] <= 1
