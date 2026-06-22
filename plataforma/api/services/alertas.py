"""Motor de alertas: meteo, risco, cobertura, incidentes."""
from __future__ import annotations
import os
import random
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from geo import zona_maritima_pt, ponto_em_mar, ponto_em_mar_mapa
from services.grelha_cache import pts_grelha, pts_mar, pts_mar_mapa
from store import estado

LIMIAR = 0.5
_ultima_cobertura: dict[str, datetime] = {}

# Ponto de demonstração: mar aberto a O de Sesimbra (~26 km da costa)
DEMO_LON = -9.50
DEMO_LAT = 38.45


def ponto_aleatorio_mar(seed: int | None = None) -> tuple[float, float, dict]:
    """Ponto marítimo aleatório ao longo de toda a costa PT (células ≥15 km da costa)."""
    cells = pts_mar_mapa()
    if not cells:
        cells = [p for p in pts_mar() if p.get("dist_costa_km", 0) >= 15]
    if not cells:
        return DEMO_LON, DEMO_LAT, {"fonte": "fallback_demo"}
    rng = random.Random(seed)
    p = rng.choice(cells)
    return p["lon"], p["lat"], {
        "lat": p["lat"],
        "lon": p["lon"],
        "risco": round(p.get("risco", 0), 2),
        "dist_costa_km": p.get("dist_costa_km"),
        "fonte": "grelha_mar_aleatorio",
    }


def snap_para_mar(lon: float, lat: float) -> tuple[float, float]:
    """Aproxima um ponto a mar aberto visível no mapa (fora de terra e estuários)."""
    if ponto_em_mar_mapa(lon, lat):
        return lon, lat
    cells = pts_mar_mapa()
    if not cells:
        cells = [p for p in pts_mar() if p.get("dist_costa_km", 0) >= 15]
    if not cells:
        cells = pts_mar()
    if not cells:
        return DEMO_LON, DEMO_LAT
    best = min(cells, key=lambda p: (p["lon"] - lon) ** 2 + (p["lat"] - lat) ** 2)
    return best["lon"], best["lat"]


def alertas_meteo(bases: list[dict]) -> list[dict]:
    out = []
    for b in bases:
        v = b.get("vento_ms")
        if v is None:
            continue
        if v > 15:
            out.append({
                "tipo": "meteo", "severidade": "media" if v <= 18 else "alta",
                "titulo": f"Vento elevado — {b['base']}",
                "detalhe": f"{v:.1f} m/s; raio efetivo {b.get('raio_operacional_km')} km.",
                "lat": b["lat"], "lon": b["lon"],
            })
        if b.get("operacional") is False:
            out.append({
                "tipo": "meteo", "severidade": "alta",
                "titulo": f"Condições limitantes — {b['base']}",
                "detalhe": "Visibilidade ou vento fora dos limites operacionais assumidos.",
                "lat": b["lat"], "lon": b["lon"],
            })
    return out


def alertas_risco_navios(navios: dict[str, dict]) -> list[dict]:
    pts = pts_grelha()
    # índice grosseiro por célula mais próxima
    out = []
    for mmsi, nav in navios.items():
        if not ponto_em_mar(nav["lon"], nav["lat"]):
            continue
        best = min(pts, key=lambda p: (p["lon"] - nav["lon"]) ** 2 + (p["lat"] - nav["lat"]) ** 2)
        if best["risco"] >= LIMIAR:
            out.append({
                "tipo": "risco_zona", "severidade": "media",
                "titulo": f"Embarcação em zona de alto risco — {nav.get('nome', mmsi)}",
                "detalhe": f"Risco local {best['risco']:.2f}; MMSI {mmsi}.",
                "lat": nav["lat"], "lon": nav["lon"],
                "meta": {"mmsi": mmsi, "risco": best["risco"]},
            })
    return out[:15]


def alertas_cobertura() -> list[dict]:
    """Sectores de alto risco sem 'visita' simulada há > TEMPO_REVISITA."""
    global _ultima_cobertura
    from config import TEMPO_REVISITA_H
    pts = pts_grelha()
    alto = sorted([p for p in pts if p["risco"] >= LIMIAR], key=lambda p: p["risco"], reverse=True)[:20]
    now = datetime.now(timezone.utc)
    out = []
    for p in alto:
        key = f"{p['lon']:.2f},{p['lat']:.2f}"
        ult = _ultima_cobertura.get(key, now - timedelta(hours=TEMPO_REVISITA_H + 1))
        if now - ult > timedelta(hours=TEMPO_REVISITA_H):
            out.append({
                "tipo": "cobertura", "severidade": "media",
                "titulo": "Revisita em atraso",
                "detalhe": f"Célula r={p['risco']:.2f} sem patrulha simulada há >{TEMPO_REVISITA_H} h.",
                "lat": p["lat"], "lon": p["lon"],
            })
        _ultima_cobertura[key] = now
    return out[:5]


def alertas_ipma(avisos: list[dict]) -> list[dict]:
    out = []
    for a in avisos:
        titulo = a.get("titulo", "")
        if titulo in ("Sem avisos IPMA activos", "Sem ligação IPMA", "IPMA indisponível"):
            continue
        if a.get("severidade") in ("alta", "media", "critica"):
            out.append({
                "tipo": "meteo", "severidade": a.get("severidade", "media"),
                "titulo": a["titulo"],
                "detalhe": a.get("detalhe", "")[:300],
                "lat": None, "lon": None,
                "meta": {"fonte": "ipma", "distrito": a.get("distrito")},
            })
    return out[:8]


def alertas_rss(noticias: list[dict]) -> list[dict]:
    out = []
    for n in noticias[:5]:
        out.append({
            "tipo": "incidente", "severidade": "media",
            "titulo": f"RSS: {n['titulo'][:80]}",
            "detalhe": f"{n.get('fonte')}: {n.get('resumo', '')[:200]}",
            "lat": None, "lon": None,
            "meta": {"link": n.get("link"), "fonte": n.get("fonte")},
        })
    return out[:3]


def registar_incidente_manual(titulo: str, detalhe: str, lat: float, lon: float,
                              severidade: str = "alta") -> dict:
    lon, lat = snap_para_mar(lon, lat)
    inc = {
        "id": f"INC-{len(estado.incidentes)+1:04d}",
        "titulo": titulo, "detalhe": detalhe,
        "lat": lat, "lon": lon, "severidade": severidade,
        "fonte": "manual", "criado_em": datetime.now(timezone.utc).isoformat(),
    }
    estado.incidentes.insert(0, inc)
    alerta = estado.add_alerta(
        "incidente", severidade, titulo, detalhe, lat, lon,
        {"incidente_id": inc["id"]}, dedupe_min=1)
    if alerta:
        inc["alerta_id"] = alerta["id"]
    return inc
