"""
Validação de qualidade de rotas (Fase 2/4 do PLANO_PATRULHAS).

Avalia, de forma aditiva e sem alterar o planeador, se uma rota "faz sentido"
operacionalmente: coerência espacial (waypoints na zona/região), continuidade
do varrimento (sem saltos > swath), autonomia AR5 e cobertura estimada.

Devolve um bloco `validacao` com métricas, um score 0–100 e avisos, pronto a
mostrar no HUD e a citar na defesa.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from config import SENSOR_SWATH_KM
from rotas_maritimas import distancia_km


def _wps_patrulha(rota: dict) -> list[dict]:
    wps = rota.get("waypoints") or []
    return [w for w in wps if w.get("tipo") in ("patrulha", "alvo", "orbita")]


def _pct_na_zona(wps: list[dict], zona: dict | None, regiao: dict | None) -> float | None:
    """% de waypoints de patrulha dentro do cluster k-means ou da região."""
    caixa = None
    if zona and all(k in zona for k in ("lat_min", "lat_max", "lon_min", "lon_max")):
        caixa = zona
    elif regiao and any(regiao.get(k) is not None for k in ("lat_min", "lat_max", "lon_min", "lon_max")):
        caixa = regiao
    if not caixa or not wps:
        return None
    margem = 0.15  # ~15 km de tolerância nas bordas do cluster
    dentro = 0
    for w in wps:
        lat_ok = (caixa.get("lat_min", -90) - margem <= w["lat"] <= caixa.get("lat_max", 90) + margem)
        lon_ok = (caixa.get("lon_min", -180) - margem <= w["lon"] <= caixa.get("lon_max", 180) + margem)
        if lat_ok and lon_ok:
            dentro += 1
    return round(100.0 * dentro / len(wps), 1)


def _continuidade(wps: list[dict]) -> dict:
    """Distância entre waypoints consecutivos vs swath (detecção de saltos)."""
    if len(wps) < 2:
        return {"salto_max_km": 0.0, "salto_medio_km": 0.0, "n_saltos": 0, "limiar_km": SENSOR_SWATH_KM}
    limiar = SENSOR_SWATH_KM * 1.5
    dists = [distancia_km(wps[i], wps[i + 1]) for i in range(len(wps) - 1)]
    return {
        "salto_max_km": round(max(dists), 1),
        "salto_medio_km": round(sum(dists) / len(dists), 1),
        "n_saltos": sum(1 for d in dists if d > limiar),
        "limiar_km": round(limiar, 1),
    }


def avaliar_rota(rota: dict) -> dict:
    """Avalia uma rota e devolve bloco de validação (score 0–100 + avisos)."""
    if not isinstance(rota, dict) or rota.get("erro"):
        return {"score": None, "classe": "n/d", "avisos": ["Rota inválida"]}

    wps = _wps_patrulha(rota)
    zona = rota.get("zona_cluster") if isinstance(rota.get("zona_cluster"), dict) else None
    regiao = rota.get("regiao") if isinstance(rota.get("regiao"), dict) else None

    pct_zona = _pct_na_zona(wps, zona, regiao)
    cont = _continuidade(wps)
    dentro_aut = rota.get("dentro_autonomia", True)
    n_patrol = rota.get("n_pontos_patrol", len(wps))
    dist_km = rota.get("distancia_km", 0) or 0
    cobertura_km2 = round(n_patrol * SENSOR_SWATH_KM * SENSOR_SWATH_KM * 0.35, 0) if n_patrol else 0.0

    # Rota vazia/sem patrulha efectiva: falha clara (não "Coerente").
    if n_patrol < 1 or dist_km <= 0:
        return {
            "score": 25,
            "classe": "Rever",
            "pct_na_zona": pct_zona,
            "continuidade": cont,
            "dentro_autonomia": dentro_aut,
            "cobertura_estimada_km2": 0.0,
            "n_pontos_patrol": n_patrol,
            "regras": {
                "so_mar": "waypoints de patrulha em células de mar (planeador)",
                "uma_zona_por_sortie": True,
                "continuidade": True,
                "autonomia": dentro_aut is not False,
            },
            "avisos": [
                "Rota sem pontos de patrulha — zona de risco fora de alcance da base.",
                "Reduza t_on, escolha base mais próxima da zona, ou use uma zona/região mais perto.",
            ],
        }

    score = 100.0
    avisos: list[str] = []

    if dentro_aut is False:
        score -= 40
        avisos.append("Fora de autonomia AR5 (rever t_on/vento/base)")
    if pct_zona is not None and pct_zona < 80:
        score -= min(30, (80 - pct_zona) * 0.6)
        avisos.append(f"Só {pct_zona:.0f}% dos pontos na zona/região alvo")
    if cont["n_saltos"] > 0:
        score -= min(25, cont["n_saltos"] * 8)
        avisos.append(f"{cont['n_saltos']} salto(s) > {cont['limiar_km']:.0f} km no varrimento")
    if n_patrol < 4:
        score -= 10
        avisos.append("Poucos pontos de patrulha (< 4)")

    score = max(0, round(score))
    if score >= 85:
        classe = "Coerente"
    elif score >= 65:
        classe = "Aceitável"
    else:
        classe = "Rever"

    return {
        "score": score,
        "classe": classe,
        "pct_na_zona": pct_zona,
        "continuidade": cont,
        "dentro_autonomia": dentro_aut,
        "cobertura_estimada_km2": cobertura_km2,
        "n_pontos_patrol": n_patrol,
        "regras": {
            "so_mar": "waypoints de patrulha em células de mar (planeador)",
            "uma_zona_por_sortie": pct_zona is None or pct_zona >= 80,
            "continuidade": cont["n_saltos"] == 0,
            "autonomia": dentro_aut is not False,
        },
        "avisos": avisos or ["Rota coerente com as regras de patrulha SAD"],
    }


def avaliar_plano_24h(rota: dict) -> dict:
    """Validação agregada para o plano 24 h (média por sector)."""
    sectores = rota.get("rotas_sector") or []
    if not sectores:
        return avaliar_rota(rota)
    avals = []
    for s in sectores:
        sub = {
            "waypoints": s.get("waypoints", []),
            "n_pontos_patrol": s.get("n_pontos_patrol", 0),
            "distancia_km": s.get("dist_km", s.get("distancia_km", 0)),
            "dentro_autonomia": (s.get("meteo") or {}).get("dentro_autonomia", True),
            "zona_cluster": None,
            "regiao": {"lat_min": s.get("lat_min"), "lat_max": s.get("lat_max")},
        }
        avals.append(avaliar_rota(sub))
    scores = [a["score"] for a in avals if a.get("score") is not None]
    score = round(sum(scores) / len(scores)) if scores else None
    n_rever = sum(1 for a in avals if a.get("classe") == "Rever")
    classe = "Coerente" if (score or 0) >= 85 else "Aceitável" if (score or 0) >= 65 else "Rever"
    return {
        "score": score,
        "classe": classe,
        "n_sectores": len(sectores),
        "n_sectores_rever": n_rever,
        "por_sector": [{"sector": s["sector"], "score": a["score"], "classe": a["classe"]}
                       for s, a in zip(sectores, avals)],
        "avisos": ([f"{n_rever} sector(es) a rever"] if n_rever else
                   ["Plano 24 h coerente em todos os sectores"]),
    }
