"""
zonas_cluster.py — Zonas operacionais por k-means nos hotspots SAD.

Agrupa células de alto risco em zonas contíguas para varrimento/patrulha.
Complementa os sectores costeiros fixos (latitude) com clusters orientados
pelo risco real (Algarve, Lisboa–Setúbal, NW, etc.).
"""
from __future__ import annotations

import os
import sys

import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from config import LIMIAR_RISCO_OPERACIONAL, N_SECTORES_COSTA
from geo import ponto_em_mar_mapa, proj
from services.grelha_cache import pts_mar

_CACHE: dict | None = None
RANDOM = 42


def invalidar_cache_clusters() -> None:
    global _CACHE
    _CACHE = None

NOMES_ZONA = [
    "Algarve / SW",
    "Setúbal–Lisboa",
    "Centro",
    "NW / Peniche",
    "Norte",
    "Ao largo",
]


def _nome_zona(centro_lat: float, centro_lon: float) -> str:
    if centro_lat < 37.6:
        return "Algarve / SW"
    if centro_lat < 38.8:
        return "Setúbal–Lisboa"
    if centro_lat < 40.2:
        return "Centro / NW"
    if centro_lon < -9.5:
        return "NW / Peniche"
    return "Norte / ao largo"


def _carregar_alto(limiar: float = LIMIAR_RISCO_OPERACIONAL) -> list[dict]:
    return [p for p in pts_mar() if p["risco"] >= limiar]


def clusters_risco(
    k: int | None = None,
    limiar: float = LIMIAR_RISCO_OPERACIONAL,
    tipo_campo: str = "risco",
) -> dict:
    """k-means espacial + risco sobre células de alto risco."""
    global _CACHE
    cache_key = (k, limiar, tipo_campo)
    if _CACHE and _CACHE.get("key") == cache_key:
        return _CACHE["data"]

    alto = _carregar_alto(limiar)
    if len(alto) < 4:
        return {"k": 1, "zonas": [], "n_alto_risco": len(alto), "metodo": "kmeans_sad"}

    k = k or min(N_SECTORES_COSTA, max(3, len(alto) // 40))
    k = min(k, len(alto))

    feats = []
    for p in alto:
        r_tipo = p.get(f"r_{tipo_campo}", p["risco"]) if tipo_campo not in ("risco", "geral") else p["risco"]
        feats.append([p["lon"], p["lat"], p["risco"], r_tipo])
    X = np.array(feats)
    Xs = StandardScaler().fit_transform(X)

    km = KMeans(n_clusters=k, n_init=12, random_state=RANDOM)
    labels = km.fit_predict(Xs)

    zonas = []
    for cid in range(k):
        membros = [alto[i] for i in range(len(alto)) if labels[i] == cid]
        if not membros:
            continue
        membros_mapa = [p for p in membros if ponto_em_mar_mapa(p["lon"], p["lat"])]
        if not membros_mapa:
            continue
        clat = float(np.mean([p["lat"] for p in membros_mapa]))
        clon = float(np.mean([p["lon"] for p in membros_mapa]))
        risco_med = float(np.mean([p["risco"] for p in membros_mapa]))
        risco_sum = float(sum(p["risco"] for p in membros_mapa))
        zonas.append({
            "id": cid + 1,
            "nome": _nome_zona(clat, clon),
            "centro_lat": round(clat, 3),
            "centro_lon": round(clon, 3),
            "n_celulas": len(membros_mapa),
            "risco_medio": round(risco_med, 3),
            "risco_total": round(risco_sum, 2),
            "lat_min": round(min(p["lat"] for p in membros_mapa), 2),
            "lat_max": round(max(p["lat"] for p in membros_mapa), 2),
            "lon_min": round(min(p["lon"] for p in membros_mapa), 2),
            "lon_max": round(max(p["lon"] for p in membros_mapa), 2),
            "celulas": [
                {
                    "lon": p["lon"], "lat": p["lat"],
                    "risco": round(p["risco"], 2),
                    "r_droga": round(p.get("r_droga", 0), 2),
                    "r_pesca": round(p.get("r_pesca", 0), 2),
                    "r_imigracao": round(p.get("r_imigracao", 0), 2),
                }
                for p in sorted(membros_mapa, key=lambda x: -x["risco"])[:60]
            ],
        })

    zonas.sort(key=lambda z: -z["risco_total"])
    for i, z in enumerate(zonas):
        z["rank"] = i + 1

    data = {
        "k": k,
        "limiar": limiar,
        "tipo_campo": tipo_campo,
        "n_alto_risco": len(alto),
        "metodo": "kmeans_sad",
        "zonas": zonas,
    }
    _CACHE = {"key": cache_key, "data": data}
    return data


def zona_mais_proxima(base: dict, tipo_campo: str = "risco") -> dict | None:
    """Zona de cluster mais próxima da base (para sortie)."""
    data = clusters_risco(tipo_campo=tipo_campo)
    zonas = data.get("zonas", [])
    if not zonas:
        return None
    bx = base.get("x") or proj(base["lon"], base["lat"])[0]
    by = base.get("y") or proj(base["lon"], base["lat"])[1]
    return min(
        zonas,
        key=lambda z: (proj(z["centro_lon"], z["centro_lat"])[0] - bx) ** 2
        + (proj(z["centro_lon"], z["centro_lat"])[1] - by) ** 2,
    )


def celulas_da_zona(zona_id: int, tipo_campo: str = "risco") -> list[dict]:
    data = clusters_risco(tipo_campo=tipo_campo)
    for z in data.get("zonas", []):
        if z["id"] == zona_id:
            return z.get("celulas", [])
    return []


def zona_por_regiao(regiao: dict | None, tipo_campo: str = "risco") -> dict | None:
    """Zona com maior risco dentro de uma região lat/lon."""
    if not regiao:
        return None
    data = clusters_risco(tipo_campo=tipo_campo)
    best, best_r = None, -1.0
    for z in data.get("zonas", []):
        if regiao.get("lat_min") is not None and z["lat_max"] < regiao["lat_min"]:
            continue
        if regiao.get("lat_max") is not None and z["lat_min"] > regiao["lat_max"]:
            continue
        if regiao.get("lon_min") is not None and z["lon_max"] < regiao["lon_min"]:
            continue
        if regiao.get("lon_max") is not None and z["lon_min"] > regiao["lon_max"]:
            continue
        if z["risco_total"] > best_r:
            best, best_r = z, z["risco_total"]
    return best
