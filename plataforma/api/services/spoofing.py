"""Deteção heurística de AIS spoofing e comportamento anómalo."""
from __future__ import annotations
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))
from geo import proj
from store import estado


def _dist_km(nav_a: dict, nav_b: dict) -> float:
    x1, y1 = proj(nav_a["lon"], nav_a["lat"])
    x2, y2 = proj(nav_b["lon"], nav_b["lat"])
    return math.hypot(x1 - x2, y1 - y2)


def analisar_navio(mmsi: str, nav: dict, anterior: dict | None) -> list[dict]:
    alertas = []
    sog = float(nav.get("sog_nos") or 0)

    if sog > 35:
        alertas.append({
            "tipo": "spoofing", "severidade": "alta",
            "titulo": f"Velocidade AIS implausível — {nav.get('nome', mmsi)}",
            "detalhe": f"SOG={sog:.1f} nós (limiar 35 nós).",
            "lat": nav["lat"], "lon": nav["lon"],
            "meta": {"mmsi": mmsi, "sog": sog},
        })

    if anterior:
        dt_min = 2.0  # ciclo de poll ~2 min
        dist = _dist_km(anterior, nav)
        vel_kmh = dist / (dt_min / 60) if dt_min else 0
        if dist > 15 and vel_kmh > 200:
            alertas.append({
                "tipo": "spoofing", "severidade": "critica",
                "titulo": f"Salto de posição AIS — {nav.get('nome', mmsi)}",
                "detalhe": f"Deslocação {dist:.1f} km em ~{dt_min:.0f} min.",
                "lat": nav["lat"], "lon": nav["lon"],
                "meta": {"mmsi": mmsi, "dist_km": round(dist, 1)},
            })

    return alertas


def verificar_todos(navios_ant: dict[str, dict], navios_nov: dict[str, dict]) -> list[dict]:
    out = []
    pos_por_mmsi: dict[str, list] = {}
    for mmsi, nav in navios_nov.items():
        pos_por_mmsi.setdefault(mmsi, []).append(nav)
        out.extend(analisar_navio(mmsi, nav, navios_ant.get(mmsi)))

    # MMSI duplicado em posições distantes (mesmo instante)
    for mmsi, lista in pos_por_mmsi.items():
        if len(lista) > 1:
            for i in range(len(lista)):
                for j in range(i + 1, len(lista)):
                    if _dist_km(lista[i], lista[j]) > 5:
                        out.append({
                            "tipo": "spoofing", "severidade": "alta",
                            "titulo": f"MMSI duplicado — {mmsi}",
                            "detalhe": "Mesmo MMSI em duas posições distintas.",
                            "lat": lista[i]["lat"], "lon": lista[i]["lon"],
                            "meta": {"mmsi": mmsi},
                        })
    return out
