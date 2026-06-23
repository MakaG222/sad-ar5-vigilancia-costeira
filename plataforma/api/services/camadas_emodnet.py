"""Camada EMODnet / intensidade por ameaça (pipeline SAD)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from config import FONTES, PESOS_AMEACA
from services.risco_mapa import carregar_celulas

_CAMPO = {
    "droga": ("r_droga", "Apreensões marítimas (UNODC/IDS)"),
    "pesca": ("r_pesca", "EMODnet vessel density — pesca (tipo 02) + anomalia AIS"),
    "poluicao": ("r_poluicao", "EMODnet carga (10) + petroleiro (11)"),
    "imigracao": ("r_imigracao", "IOM + desembarques PT continental"),
    "geral": ("risco", "Índice multi-ameaça SAD (pesos AHP)"),
    "costeira": ("risco", "Corredor costeiro — risco global"),
}

_FONTE = {
    "droga": FONTES.get("droga_excel", "UNODC/IDS"),
    "pesca": FONTES.get("pesca", "EMODnet"),
    "poluicao": FONTES.get("poluicao", "EMODnet"),
    "imigracao": FONTES.get("imigracao", "IOM/SEF"),
    "geral": "Pipeline SAD — 4 ameaças",
    "costeira": "Pipeline SAD — corredor 8–45 km",
}


def celulas_emodnet(tipo: str = "geral", limiar: float = 0.35, max_celulas: int = 180) -> dict:
    campo, descricao = _CAMPO.get(tipo, _CAMPO["geral"])
    celulas = carregar_celulas(0.08, max_celulas=1200)
    filtradas = [c for c in celulas if c.get(campo, 0) >= limiar]
    filtradas.sort(key=lambda c: c.get(campo, 0), reverse=True)
    top = filtradas[:max_celulas]
    out = []
    for c in top:
        out.append({
            "lon": c["lon"],
            "lat": c["lat"],
            "intensidade": round(c.get(campo, 0), 3),
            "risco": c.get("risco"),
            "r_droga": c.get("r_droga"),
            "r_pesca": c.get("r_pesca"),
            "r_poluicao": c.get("r_poluicao"),
            "r_imigracao": c.get("r_imigracao"),
        })
    return {
        "tipo": tipo,
        "campo": campo,
        "descricao": descricao,
        "fonte": _FONTE.get(tipo, "EMODnet / SAD"),
        "limiar": limiar,
        "n_celulas": len(out),
        "pesos_ameaca": PESOS_AMEACA if tipo == "geral" else None,
        "celulas": out,
    }
