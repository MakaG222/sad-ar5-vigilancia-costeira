"""Bases de lançamento AR5 (militares + aeródromos ≤20 km da costa)."""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from geo import bases_lancamento
from otimizacao import mclp, raio_por_autonomia
from config import BASES_MCLP_RECOMENDADAS, RAIO_LANCAMENTO_COSTA_KM, N_SECTORES_COSTA, AERODROMOS
from services.grelha_cache import pts_grelha


def _bases_mclp_para_mapa(bases: list[dict]) -> list[dict]:
    """Garante Porto + Portimão no mapa (aeródromos MCLP mesmo se filtrados em bases_lancamento)."""
    out = list(bases)
    nomes = {b["nome"] for b in out}
    for nome in BASES_MCLP_RECOMENDADAS:
        if nome in nomes:
            continue
        chave = nome.lower().split("(")[0].strip()
        parciais = [b for b in out if chave in b["nome"].lower()]
        if parciais:
            continue
        for an, lon, lat, regiao in AERODROMOS:
            if an == nome:
                from geo import proj
                x, y = proj(lon, lat)
                out.append({
                    "nome": an, "lon": lon, "lat": lat, "x": x, "y": y,
                    "forca": "Operacional", "tipo": "mclp",
                    "dist_costa_km": None, "regiao": regiao,
                })
                break
    return out


def listar_bases() -> dict:
    bases = _bases_mclp_para_mapa(bases_lancamento())
    pts = pts_grelha()
    rec = mclp(pts, bases, raio_por_autonomia(6.0, 8.0), 2)

    por_forca: dict[str, int] = {}
    for b in bases:
        por_forca[b["forca"]] = por_forca.get(b["forca"], 0) + 1

    return {
        "bases": bases,
        "n_bases": len(bases),
        "raio_costa_km": RAIO_LANCAMENTO_COSTA_KM,
        "mclp_recomendadas": BASES_MCLP_RECOMENDADAS,
        "bases_mclp_idx": rec.get("bases_sel", []),
        "frac_risco_mclp": round(rec.get("frac_risco", 0), 4),
        "n_sectores_costa": N_SECTORES_COSTA,
        "por_forca": por_forca,
    }
