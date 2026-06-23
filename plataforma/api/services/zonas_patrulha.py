"""Zonas de patrulha por tipo de ameaça (alinhado com risco SAD)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from config import N_SECTORES_COSTA, PESOS_AMEACA
from geo import corredor_costeiro, ponto_em_mar_mapa, sectores_costa
from services.grelha_cache import pts_mar

TIPOS = {
    "geral": {"campo": "risco", "label": "Risco global (SAD)", "descricao": "Índice multi-ameaça do relatório"},
    "droga": {"campo": "r_droga", "label": "Tráfico de droga", "descricao": "Apreensões + rotas AIS"},
    "pesca": {"campo": "r_pesca", "label": "Pesca INN", "descricao": "SIFICAP / monitorização"},
    "poluicao": {"campo": "r_poluicao", "label": "Poluição / derrames", "descricao": "EMSA CleanSeaNet"},
    "imigracao": {"campo": "r_imigracao", "label": "Imigração irregular", "descricao": "Rota atlântica / IOM"},
    "costeira": {"campo": "dist_costa_km", "label": "Patrulha costeira uniforme", "descricao": "Toda a costa, faixa 8–45 km"},
}


def _carregar_pts():
    return pts_mar()


def zonas_por_tipo(tipo: str = "geral", limiar: float = 0.35) -> dict:
    meta = TIPOS.get(tipo, TIPOS["geral"])
    campo = meta["campo"]
    pts = _carregar_pts()
    corredor = corredor_costeiro(pts, dist_max_km=45.0)

    if tipo == "costeira":
        foco = corredor
    else:
        foco = sorted(
            [p for p in pts if p.get(campo, 0) >= limiar],
            key=lambda p: p.get(campo, 0),
            reverse=True,
        )[:120]

    sectores = sectores_costa(corredor, N_SECTORES_COSTA)
    zonas = []
    for i, sec in enumerate(sectores):
        if tipo == "costeira":
            zona_pts = sec
        else:
            lat0, lat1 = min(p["lat"] for p in sec), max(p["lat"] for p in sec)
            zona_pts = [p for p in foco if lat0 - 0.05 <= p["lat"] <= lat1 + 0.05]
        if not zona_pts and sec:
            zona_pts = sec[:3]
        zonas.append({
            "sector": i + 1,
            "n_pontos": len(zona_pts),
            "lat_min": round(min(p["lat"] for p in sec), 2),
            "lat_max": round(max(p["lat"] for p in sec), 2),
            "score_medio": round(
                sum(p.get(campo if campo != "dist_costa_km" else "risco", 0) for p in zona_pts)
                / max(len(zona_pts), 1), 3),
            "celulas": [{
                "lon": p["lon"], "lat": p["lat"],
                "risco": round(p.get("risco", 0), 2),
                "score": round(p.get(campo if campo != "dist_costa_km" else "risco", 0), 2),
            } for p in zona_pts if ponto_em_mar_mapa(p["lon"], p["lat"])][:40],
        })

    return {
        "tipo": tipo,
        "label": meta["label"],
        "descricao": meta["descricao"],
        "limiar": limiar,
        "pesos_ameaca": PESOS_AMEACA,
        "n_corredor": len(corredor),
        "n_foco": len(foco),
        "zonas": zonas,
        "corredor_costa": [{"lon": p["lon"], "lat": p["lat"]} for p in corredor],
    }


def listar_tipos() -> list[dict]:
    return [{"id": k, **v} for k, v in TIPOS.items()]
