"""Meteorologia aplicada ao planeamento de rotas AR5."""
from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from config import fator_vento, CENARIOS_VENTO, ASSIMETRIA_DOWN, ASSIMETRIA_UP, T_ON_SORTIE_H
from otimizacao import raio_por_autonomia
from config import AR5, RESERVA_H, T_ON_MIN_H


def _dist_km(p1: dict, p2: dict) -> float:
    if "x" in p1 and "x" in p2:
        return math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])
    lat1, lon1 = p1.get("lat"), p1.get("lon")
    lat2, lon2 = p2.get("lat"), p2.get("lon")
    if None in (lat1, lon1, lat2, lon2):
        return 9999.0
    return math.hypot((lon1 - lon2) * 85, (lat1 - lat2) * 111)


def _match_meteo_base(nome: str | None, lat: float | None, lon: float | None,
                       meteo_bases: list[dict]) -> dict | None:
    if not meteo_bases:
        return None
    if nome:
        for m in meteo_bases:
            if m.get("base") == nome or nome.startswith(m.get("base", "")[:8]):
                return m
            if m.get("base", "") in nome:
                return m
    if lat is not None and lon is not None:
        alvo = {"lat": lat, "lon": lon}
        return min(meteo_bases, key=lambda m: _dist_km(alvo, m))
    return meteo_bases[0]


def _vento_mais_proximo(lat: float, lon: float, meteo_bases: list[dict]) -> dict | None:
    valid = [m for m in meteo_bases if m.get("lat") is not None and m.get("lon") is not None]
    if not valid:
        return None
    alvo = {"lat": lat, "lon": lon}
    return min(valid, key=lambda m: _dist_km(alvo, m))


def resolver_vento(
    base: dict,
    meteo_bases: list[dict] | None,
    vento_override_ms: float | None,
    usar_meteo_live: bool = True,
    lat_sector: float | None = None,
    lon_sector: float | None = None,
    t_on_h: float | None = None,
) -> dict:
    """
    Resolve vento efectivo para uma rota.
    Prioridade: override manual > meteo live (base ou sector) > cenário moderado.
    """
    fonte = "manual"
    vento_ms = vento_override_ms if vento_override_ms is not None else CENARIOS_VENTO["moderado"]
    vento_dir = None
    vis = None
    operacional = True
    estacao = None

    if usar_meteo_live and meteo_bases:
        m = None
        if lat_sector is not None and lon_sector is not None:
            m = _vento_mais_proximo(lat_sector, lon_sector, meteo_bases)
        if not m or m.get("vento_ms") is None:
            m = _match_meteo_base(base.get("nome"), base.get("lat"), base.get("lon"), meteo_bases)
        if m and m.get("vento_ms") is not None:
            vento_ms = float(m["vento_ms"])
            fonte = "open_meteo"
            vento_dir = m.get("vento_direcao_gr")
            vis = m.get("visibilidade_m")
            operacional = bool(m.get("operacional", True))
            estacao = m.get("base")
    elif vento_override_ms is not None:
        vento_ms = float(vento_override_ms)
        fonte = "manual"

    fator = fator_vento(vento_ms)
    ton = float(t_on_h) if t_on_h is not None else T_ON_SORTIE_H
    ton = max(T_ON_MIN_H, min(ton, AR5["autonomia_h"] - RESERVA_H - 0.5))
    alcance = raio_por_autonomia(ton, vento_ms)
    autonomia_util = AR5["autonomia_h"] - RESERVA_H

    # Classificação operacional AR5
    if vento_ms > 18:
        condicao = "critica"
        operacional = False
    elif vento_ms > 15:
        condicao = "limitada"
    elif vento_ms > 10:
        condicao = "moderada"
    else:
        condicao = "favoravel"

    return {
        "vento_ms": round(vento_ms, 1),
        "vento_direcao_gr": vento_dir,
        "visibilidade_m": vis,
        "fator_vento": round(fator, 2),
        "alcance_patrol_km": round(alcance, 1),
        "t_on_h": round(ton, 2),
        "autonomia_util_h": autonomia_util,
        "operacional": operacional,
        "condicao": condicao,
        "fonte": fonte,
        "estacao_meteo": estacao,
        "impacto": _texto_impacto(vento_ms, fator, alcance, condicao),
    }


def _texto_impacto(vento_ms: float, fator: float, alcance: float, condicao: str) -> str:
    pct = int((1 - fator) * 100)
    if condicao == "critica":
        return f"Vento {vento_ms:.0f} m/s — patrulha não recomendada; alcance −{pct}% ({alcance:.0f} km)."
    if condicao == "limitada":
        return f"Vento forte ({vento_ms:.0f} m/s): reduzir sector e priorizar costa próxima (−{pct}%, {alcance:.0f} km)."
    if condicao == "moderada":
        return f"Vento moderado ({vento_ms:.0f} m/s): rotas ajustadas; alcance operacional {alcance:.0f} km."
    return f"Condições favoráveis ({vento_ms:.0f} m/s); alcance máximo {alcance:.0f} km."


def custo_leg_com_vento(
    p1: dict, p2: dict,
    vento_dir_gr: float | None,
    vento_ms: float,
) -> float:
    """Distância efectiva km considerando componente de vento (AR5)."""
    d = math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])
    if vento_dir_gr is None or vento_ms <= 5 or d < 0.01:
        return d
    dx, dy = p2["x"] - p1["x"], p2["y"] - p1["y"]
    leg_bearing = math.degrees(math.atan2(dx, dy)) % 360
    diff = math.radians((leg_bearing - vento_dir_gr + 180) % 360 - 180)
    # Vento de direcao_gr vem DE onde sopra; voar na mesma direcao = tailwind
    cos_a = math.cos(diff)
    if cos_a > 0.3:
        return d / ASSIMETRIA_DOWN
    if cos_a < -0.3:
        return d / ASSIMETRIA_UP
    return d
