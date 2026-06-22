"""AIS: cache local + AISStream (se chave) ou embarcações simuladas em MAR."""
from __future__ import annotations
import asyncio
import json
import math
import os
import random
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from geo import (
    ponto_em_mar, gerar_procura, proj, LON_MIN, LON_MAX, LAT_MIN, LAT_MAX,
)
from store import estado

AISSTREAM_KEY = os.environ.get("AISSTREAM_API_KEY", "")


def modo_ais() -> dict:
    """Estado da fonte AIS: real (AISStream) ou demonstração offline."""
    key = bool(AISSTREAM_KEY)
    return {
        "modo_demo": not key,
        "fonte": "aisstream" if key else "demo",
        "mensagem": (
            "Modo demonstração — navios simulados em células marítimas SAD"
            if not key
            else "AIS real (AISStream) com fallback simulado se o stream falhar"
        ),
    }

# Posições marítimas reutilizáveis (células da grelha SAD)
_POS_MAR_CACHE: list[tuple[float, float]] | None = None


def _posicoes_mar(n: int = 60) -> list[tuple[float, float]]:
    global _POS_MAR_CACHE
    if _POS_MAR_CACHE is None:
        pts = gerar_procura(dist_min_km=10.0, dist_max_km=120.0)
        _POS_MAR_CACHE = [(p["lon"], p["lat"]) for p in pts]
    if not _POS_MAR_CACHE:
        return [(-9.0, 38.5)]
    if len(_POS_MAR_CACHE) >= n:
        return random.sample(_POS_MAR_CACHE, n)
    return _POS_MAR_CACHE


def _navio(mmsi: str, lon: float, lat: float, nome: str, sog: float, cog: float,
           tipo: str = "desconhecido") -> dict:
    return {
        "mmsi": mmsi, "nome": nome, "lon": lon, "lat": lat,
        "sog_nos": sog, "cog_gr": cog, "tipo": tipo,
        "atualizado_em": datetime.now(timezone.utc).isoformat(),
    }


def gerar_navios_demo(n: int = 45) -> dict[str, dict]:
    """Embarcações em células marítimas da grelha SAD (nunca em terra)."""
    random.seed(42)
    pos = _posicoes_mar(max(n + 5, 50))
    navios = {}
    nomes = ["LISBON EXPRESS", "ALGARVE STAR", "PORTO TRADER", "SINES TANKER",
             "PENICHE FISH", "SETUBAL CARGO", "VILAMOURA", "SAGRES PATROL"]
    for i in range(n):
        lon, lat = pos[i % len(pos)]
        lon += random.uniform(-0.04, 0.04)
        lat += random.uniform(-0.02, 0.02)
        if not ponto_em_mar(lon, lat):
            continue
        mmsi = f"263{100000 + i:06d}"
        navios[mmsi] = _navio(
            mmsi, lon, lat, random.choice(nomes) + f" {i}",
            round(random.uniform(2, 14), 1), round(random.uniform(0, 359), 0),
            random.choice(["cargo", "tanker", "pesca", "passageiros"]),
        )
    navios["263999001"] = _navio("263999001", -9.35, 38.62, "SUSPEITO DEMO", 42.0, 90.0, "cargo")
    return navios


async def poll_aisstream_once() -> int:
    if not AISSTREAM_KEY:
        return 0
    import websockets

    sub = {
        "APIKey": AISSTREAM_KEY,
        "BoundingBoxes": [[[LAT_MIN, LON_MIN], [LAT_MAX, LON_MAX]]],
    }
    n = 0
    try:
        async with websockets.connect(
            "wss://stream.aisstream.io/v0/stream", open_timeout=15
        ) as ws:
            await ws.send(json.dumps(sub))
            for _ in range(80):
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=3.0)
                except asyncio.TimeoutError:
                    break
                data = json.loads(msg)
                meta = data.get("MetaData") or data.get("Message", {}).get("MetaData")
                pos = data.get("Message", {}).get("PositionReport") or data.get("PositionReport")
                if not meta and not pos:
                    continue
                lon = float((meta or pos).get("longitude") or (meta or pos).get("Longitude") or 0)
                lat = float((meta or pos).get("latitude") or (meta or pos).get("Latitude") or 0)
                if not ponto_em_mar(lon, lat):
                    continue
                mmsi = str((meta or pos).get("MMSI") or (meta or pos).get("UserID") or "")
                if not mmsi:
                    continue
                nav = _navio(
                    mmsi, lon, lat,
                    str((meta or pos).get("ShipName") or mmsi).strip(),
                    float(pos.get("Sog") or pos.get("sog") or 0) if pos else 0.0,
                    float(pos.get("Cog") or pos.get("cog") or 0) if pos else 0.0,
                )
                estado.navios[mmsi] = nav
                n += 1
    except Exception:
        pass
    return n


def _mover_no_mar(lon: float, lat: float) -> tuple[float, float]:
    for _ in range(8):
        lon2 = max(LON_MIN, min(LON_MAX, lon + random.uniform(-0.03, 0.03)))
        lat2 = max(LAT_MIN, min(LAT_MAX, lat + random.uniform(-0.015, 0.015)))
        if ponto_em_mar(lon2, lat2):
            return lon2, lat2
    return lon, lat


async def atualizar_ais() -> dict:
    info = modo_ais()
    async with estado.lock:
        n_stream = await poll_aisstream_once() if AISSTREAM_KEY else 0
        if n_stream == 0:
            if not estado.navios:
                estado.navios = gerar_navios_demo()
            elif not AISSTREAM_KEY:
                for mmsi, nav in list(estado.navios.items()):
                    lon, lat = _mover_no_mar(nav["lon"], nav["lat"])
                    nav["lon"], nav["lat"] = lon, lat
                    nav["atualizado_em"] = datetime.now(timezone.utc).isoformat()
            estado.navios = {
                k: v for k, v in estado.navios.items()
                if ponto_em_mar(v["lon"], v["lat"])
            }
            if not estado.navios:
                estado.navios = gerar_navios_demo()
        estado.ultimo_ais = datetime.now(timezone.utc).isoformat()
        fonte = "aisstream" if n_stream else "demo"
        return {
            "navios": len(estado.navios),
            "fonte": fonte,
            "modo_demo": info["modo_demo"] or n_stream == 0,
            "mensagem": info["mensagem"] if n_stream == 0 else "AISStream activo",
        }
