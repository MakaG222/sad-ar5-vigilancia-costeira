"""Meteorologia: Open-Meteo (atual + previsão) nos aeródromos candidatos."""
from __future__ import annotations
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

import httpx
from config import AERODROMOS, fator_vento, RAIO_BASE_KM


async def fetch_meteo_bases() -> tuple[list[dict], dict]:
    """Vento atual e previsão 12 h por base."""
    bases_out = []
    previsao = {"horas": [], "por_base": {}}

    async with httpx.AsyncClient(timeout=20.0) as client:
        for nome, lon, lat, reg in AERODROMOS:
            url = (
                "https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                "&current=wind_speed_10m,wind_direction_10m,visibility,cloud_cover"
                "&hourly=wind_speed_10m,wind_direction_10m,visibility"
                "&forecast_hours=12&timezone=Europe%2FLisbon"
            )
            try:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                bases_out.append({
                    "base": nome, "regiao": reg, "lat": lat, "lon": lon,
                    "erro": str(e), "vento_ms": None,
                })
                continue

            cur = data.get("current", {})
            vento_ms = float(cur.get("wind_speed_10m") or 0) / 3.6  # km/h → m/s approx
            # Open-Meteo wind_speed_10m is km/h in some versions - check unit
            # API returns km/h for wind_speed_10m in default - actually it's km/h in v1
            # Documentation: wind_speed_10m unit is km/h by default
            vento_ms = float(cur.get("wind_speed_10m") or 0) / 3.6
            vis = cur.get("visibility")
            fator = fator_vento(vento_ms)
            raio_km = round(RAIO_BASE_KM * fator, 1)

            bases_out.append({
                "base": nome, "regiao": reg, "lat": lat, "lon": lon,
                "vento_ms": round(vento_ms, 1),
                "vento_direcao_gr": cur.get("wind_direction_10m"),
                "visibilidade_m": vis,
                "nuvens_pct": cur.get("cloud_cover"),
                "fator_vento": round(fator, 2),
                "raio_operacional_km": raio_km,
                "operacional": vento_ms <= 18 and (vis is None or vis >= 2000),
            })

            hourly = data.get("hourly", {})
            previsao["por_base"][nome] = {
                "time": hourly.get("time", [])[:12],
                "vento_ms": [round(v / 3.6, 1) for v in hourly.get("wind_speed_10m", [])[:12]],
            }

    if bases_out and bases_out[0].get("vento_ms") is not None:
        previsao["horas"] = previsao["por_base"].get(bases_out[0]["base"], {}).get("time", [])

    return bases_out, previsao
