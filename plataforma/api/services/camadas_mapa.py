"""Camadas geográficas do relatório SAD (IOM, apreensões marítimas)."""
from __future__ import annotations
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from apreensoes_mapa import apreensoes_para_mapa
from geo import ponto_em_mar_mapa

CAMADAS_JSON = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "resultados", "camadas_mapa.json"
)

_cache: dict | None = None
_apr_cache: list[dict] | None = None
_apr_live_ready = False
_apr_lock = None  # compat; cache preenchido no arranque


def _carregar() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    try:
        with open(CAMADAS_JSON, encoding="utf-8") as f:
            _cache = json.load(f)
    except OSError:
        _cache = {"iom": [], "apreensoes": []}
    return _cache


def _apreensoes_json() -> list[dict]:
    return _carregar().get("apreensoes", [])


def _filtrar_mar(raw: list[dict]) -> list[dict]:
    """Garante que só pontos em células marítimas SAD chegam ao mapa."""
    out = []
    for p in raw:
        lon, lat = float(p["lon"]), float(p["lat"])
        if ponto_em_mar_mapa(lon, lat):
            out.append(p)
    return out


def aquecer_apreensoes() -> None:
    """Pré-calcula apreensões em mar (síncrono no arranque da API)."""
    global _apr_cache, _apr_live_ready
    from apreensoes_mapa import invalidar_cache
    invalidar_cache()
    _apr_cache = None
    try:
        live = apreensoes_para_mapa(ano_min=2020)
        _apr_cache = _filtrar_mar(live)
        _apr_live_ready = True
    except Exception:
        _apr_cache = _filtrar_mar(_apreensoes_json())
        _apr_live_ready = False


def _aquecer_apreensoes_live() -> None:
    aquecer_apreensoes()


def _apreensoes_raw() -> list[dict]:
    global _apr_cache
    if _apr_cache is not None:
        return _apr_cache
    return _filtrar_mar(_apreensoes_json())


def incidentes_iom() -> list[dict]:
    out = []
    for i, p in enumerate(_carregar().get("iom", [])):
        out.append({
            "id": f"iom-{i}",
            "lat": p["lat"],
            "lon": p["lon"],
            "vitimas": p.get("vitimas", 1),
            "data": p.get("data"),
            "rota": p.get("rota"),
            "fonte": "IOM Missing Migrants",
        })
    return out


def apreensoes_maritimas(agrupar: bool = True) -> list[dict]:
    """Apreensões marítimas recentes; agrupa por célula ~0.05° para o mapa."""
    raw = _apreensoes_raw()
    if not agrupar:
        return [
            {"lat": p["lat"], "lon": p["lon"], "ano": p.get("ano"), "n": 1, "fonte": "UNODC/IDS"}
            for p in raw
        ]
    grupos: dict[tuple, dict] = defaultdict(lambda: {"n": 0, "anos": set()})
    for p in raw:
        key = (round(p["lat"], 2), round(p["lon"], 2))
        g = grupos[key]
        g["lat"] = key[0]
        g["lon"] = key[1]
        g["n"] += 1
        if p.get("ano"):
            g["anos"].add(int(p["ano"]))
    out = []
    for i, g in enumerate(sorted(grupos.values(), key=lambda x: -x["n"])):
        anos = sorted(g["anos"])
        out.append({
            "id": f"apr-{i}",
            "lat": g["lat"],
            "lon": g["lon"],
            "n": g["n"],
            "ano_min": anos[0] if anos else None,
            "ano_max": anos[-1] if anos else None,
            "fonte": "Apreensões droga PT (marítimo · só em mar)",
        })
    return out


def desembarques_pt() -> list[dict]:
    out = []
    for i, p in enumerate(_carregar().get("desembarques_pt", [])):
        out.append({
            "id": f"des-{i}",
            "lat": p["lat"],
            "lon": p["lon"],
            "n_pessoas": p.get("n_pessoas", 1),
            "ano": p.get("ano"),
            "distrito": p.get("distrito"),
            "rota": p.get("rota"),
            "fonte": "SEF/ACM · Frontex · CP (PT continental)",
        })
    return out


def resumo_camadas() -> dict:
    iom = incidentes_iom()
    apr = apreensoes_maritimas()
    des = desembarques_pt()
    return {
        "n_iom": len(iom),
        "n_desembarques_pt": len(des),
        "n_apreensoes_pontos": len(apr),
        "n_apreensoes_registos": sum(a["n"] for a in apr),
        "apreensoes_live": _apr_live_ready,
    }
