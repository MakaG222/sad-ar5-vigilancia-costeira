"""Camada de risco SAD para o mapa operacional."""
from __future__ import annotations

from services.grelha_cache import aquecer_grelha, pts_grelha, pts_mar

_celulas_cache: list[dict] | None = None


def carregar_celulas(limiar: float = 0.15, max_celulas: int = 800) -> list[dict]:
    global _celulas_cache
    if _celulas_cache is not None:
        return [c for c in _celulas_cache if c["risco"] >= limiar][:max_celulas]

    out = []
    for p in pts_mar():
        if p["risco"] < limiar:
            continue
        out.append({
            "lon": p["lon"], "lat": p["lat"],
            "risco": round(p["risco"], 3),
            "r_droga": round(p["r_droga"], 2),
            "r_pesca": round(p["r_pesca"], 2),
            "r_poluicao": round(p["r_poluicao"], 2),
            "r_imigracao": round(p["r_imigracao"], 2),
        })
    out.sort(key=lambda c: c["risco"], reverse=True)
    _celulas_cache = out
    return out[:max_celulas]


def get_celulas(limiar: float = 0.15) -> list[dict]:
    return carregar_celulas(limiar)


def resumo_risco() -> dict:
    pts = pts_grelha()
    alto = sum(1 for p in pts if p["risco"] >= 0.5)
    riscos = [p["risco"] for p in pts]
    return {
        "n_celulas_total": len(pts),
        "n_celulas_mapa": len(_celulas_cache) if _celulas_cache else 0,
        "n_alto_risco": alto,
        "risco_max": round(max(riscos, default=0), 3),
        "risco_medio": round(sum(riscos) / max(len(riscos), 1), 3),
    }


__all__ = ["carregar_celulas", "get_celulas", "resumo_risco", "aquecer_grelha"]
