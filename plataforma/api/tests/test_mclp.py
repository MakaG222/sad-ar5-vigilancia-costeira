"""Testes MCLP e bases de lançamento."""
from __future__ import annotations

from config import BASES_MCLP_RECOMENDADAS
from otimizacao import mclp, raio_por_autonomia
from services.bases import listar_bases
from services.grelha_cache import pts_grelha


def test_mclp_recomendadas_canonicas():
    """Q3 do relatório: Porto + Portimão (config + endpoint /api/bases/lancamento)."""
    bl = listar_bases()
    assert bl["mclp_recomendadas"] == BASES_MCLP_RECOMENDADAS
    nomes = {b["nome"] for b in bl["bases"]}
    assert "Porto (Sá Carneiro)" in nomes
    assert any("portim" in n.lower() for n in nomes)


def test_mclp_k2_maximiza_cobertura():
    """MCLP k=2 devolve duas bases com cobertura de risco elevada."""
    pts = pts_grelha()
    bases = listar_bases()["bases"]
    raio = raio_por_autonomia(6.0, 8.0)
    rec = mclp(pts, bases, raio, 2)

    assert len(rec["bases_sel"]) == 2
    assert rec["frac_risco"] >= 0.85
    nomes = {bases[i]["nome"] for i in rec["bases_sel"]}
    assert len(nomes) == 2
