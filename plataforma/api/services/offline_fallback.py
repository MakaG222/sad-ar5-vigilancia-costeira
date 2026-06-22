"""Fallbacks locais para demo offline (sem rede externa)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from config import AERODROMOS, RAIO_BASE_KM, fator_vento

VENTO_DEMO_MS = 8.0


def meteo_fallback() -> list[dict]:
    """Meteo sintética nas bases do relatório (Open-Meteo indisponível)."""
    out = []
    fator = fator_vento(VENTO_DEMO_MS)
    for nome, lon, lat, reg in AERODROMOS:
        out.append({
            "base": nome,
            "regiao": reg,
            "lat": lat,
            "lon": lon,
            "vento_ms": VENTO_DEMO_MS,
            "fator_vento": round(fator, 2),
            "raio_operacional_km": round(RAIO_BASE_KM * fator, 1),
            "operacional": True,
            "fonte": "cache_local",
        })
    return out


def ipma_fallback() -> list[dict]:
    return [{
        "tipo": "ipma",
        "severidade": "baixa",
        "titulo": "IPMA — modo offline",
        "detalhe": (
            "Sem ligação à API IPMA. A demo continua com grelha SAD, frota, rotas "
            "e dados locais (validacao.json, camadas_mapa.json)."
        ),
        "distrito": None,
        "fonte": "cache_local",
    }]


def rss_fallback() -> list[dict]:
    return [{
        "id": "offline-sad",
        "fonte": "SAD local",
        "titulo": "Modo offline — pipeline local activo",
        "resumo": "Grelha, risco, clusters k-means e apreensões marítimas via ficheiros do projecto.",
        "link": "",
        "publicado": "",
        "fonte_dados": "cache_local",
    }]
