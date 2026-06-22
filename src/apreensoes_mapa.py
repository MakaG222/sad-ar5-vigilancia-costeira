"""
apreensoes_mapa.py — Apreensões marítimas para camadas de mapa.

Filtra na origem (UNODC: localização marítima no Excel) e exclui pontos que,
após geocodificação administrativa, caem em terra — apenas células marítimas
da grelha SAD são incluídas no mapa.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from geo import gerar_procura, ponto_em_mar, ponto_em_mar_mapa, proj
from dm.geocode import geocode
from risco import DISTRITO_COSTA

XLSX = os.path.join(os.path.dirname(__file__), "..", "dados", "fontes", "apreensoes_droga_PT.xlsx")

LOC_MARITIMO = [
    "Territorial waters (seas, lakes, rivers, etc.)",
    "Seaport/Riverport station/Harbour",
    "International waters",
]

_CACHE_RESULT: list[dict] | None = None
_XY_MAR: np.ndarray | None = None
_MAR_PTS: list[dict] | None = None


def invalidar_cache() -> None:
    global _CACHE_RESULT, _XY_MAR, _MAR_PTS
    _CACHE_RESULT = None
    _XY_MAR = None
    _MAR_PTS = None


def _maritimo_excel(df: pd.DataFrame) -> pd.DataFrame:
    """Só registos com localização marítima declarada no Excel UNODC."""
    return df[
        df["Physical Seizure Location"].isin(LOC_MARITIMO)
        | (df["Trafficking Mode of Transportation"] == "Vessel/boat")
    ].copy()


def _geocodificar(df: pd.DataFrame) -> pd.DataFrame:
    coords = []
    for _, row in df.iterrows():
        reg = row.get("Administrative Region")
        if not isinstance(reg, str):
            coords.append(None)
            continue
        token = reg.split("/")[0].strip()
        c = geocode(token)
        if c is None:
            dc = DISTRITO_COSTA.get(token)
            c = (dc[1], dc[0]) if dc else None
        if c is None and "/" in reg:
            c = geocode(reg.split("/")[-1].strip())
        coords.append(c)
    df = df.copy()
    df["lat"] = [c[0] if c else np.nan for c in coords]
    df["lon"] = [c[1] if c else np.nan for c in coords]
    return df.dropna(subset=["lat", "lon"])


def _celulas_mar_xy(pts: list[dict]) -> tuple[np.ndarray, list[dict]]:
    global _XY_MAR, _MAR_PTS
    if _XY_MAR is not None and _MAR_PTS is not None:
        return _XY_MAR, _MAR_PTS
    mar = [p for p in pts if ponto_em_mar_mapa(p["lon"], p["lat"])]
    _MAR_PTS = mar
    _XY_MAR = np.array([[p["x"], p["y"]] for p in mar], dtype=np.float64)
    return _XY_MAR, _MAR_PTS


def _snap_celula_mar(pts: list[dict], lon: float, lat: float) -> tuple[float, float] | None:
    """Projecta para a célula marítima SAD mais próxima (se o ponto original é terra)."""
    if ponto_em_mar(lon, lat):
        return lon, lat
    xy_mar, mar_pts = _celulas_mar_xy(pts)
    if len(mar_pts) == 0:
        return None
    x, y = proj(lon, lat)
    d2 = (xy_mar[:, 0] - x) ** 2 + (xy_mar[:, 1] - y) ** 2
    best = mar_pts[int(np.argmin(d2))]
    return best["lon"], best["lat"]


def apreensoes_para_mapa(ano_min: int | None = 2020, ano_max: int | None = None) -> list[dict]:
    """
    Apreensões marítimas (Excel) com coordenadas em água.
    Registos geocodificados em terra são projectados para a célula mar mais próxima
    apenas se a localização Excel for marítima confirmada.
    """
    global _CACHE_RESULT
    if _CACHE_RESULT is not None and ano_min == 2020 and ano_max is None:
        return _CACHE_RESULT
        return _CACHE_RESULT

    if not os.path.exists(XLSX):
        return []

    df = pd.read_excel(XLSX)
    df = df.dropna(subset=["Seizure Date"])
    df["ano"] = pd.to_datetime(df["Seizure Date"]).dt.year.astype(int)
    df = _maritimo_excel(df)
    if ano_min is not None:
        df = df[df["ano"] >= ano_min]
    if ano_max is not None:
        df = df[df["ano"] <= ano_max]
    df = _geocodificar(df)
    if df.empty:
        return []

    pts = gerar_procura()
    _celulas_mar_xy(pts)
    out: list[dict] = []
    for _, row in df.iterrows():
        lon, lat = float(row["lon"]), float(row["lat"])
        snapped = _snap_celula_mar(pts, lon, lat)
        if snapped is None:
            continue
        slon, slat = snapped
        if not ponto_em_mar_mapa(slon, slat):
            continue
        out.append({
            "lat": round(slat, 4),
            "lon": round(slon, 4),
            "ano": int(row["ano"]),
            "local_excel": str(row.get("Physical Seizure Location", ""))[:60],
            "em_mar": ponto_em_mar(lon, lat),
        })

    if ano_min == 2020 and ano_max is None:
        _CACHE_RESULT = out
    return out
