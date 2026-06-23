"""Exportação de plano de missão e produtos SAD (GeoJSON / JSON)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
VALIDACAO = os.path.join(ROOT, "resultados", "validacao.json")
AHp = os.path.join(ROOT, "resultados", "ahp_pesos.json")


def exportar_validacao() -> dict:
    if os.path.exists(VALIDACAO):
        with open(VALIDACAO, encoding="utf-8") as f:
            return json.load(f)
    return {}


def exportar_risco_geojson(limiar: float = 0.0) -> dict:
    from services.risco_mapa import carregar_celulas

    celulas = carregar_celulas(max(limiar, 0.0))
    features = []
    for c in celulas:
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [c["lon"], c["lat"]]},
            "properties": {
                "risco": c.get("risco"),
                "r_droga": c.get("r_droga"),
                "r_pesca": c.get("r_pesca"),
                "r_poluicao": c.get("r_poluicao"),
                "r_imigracao": c.get("r_imigracao"),
                "dist_costa_km": c.get("dist_costa_km"),
            },
        })
    return {
        "type": "FeatureCollection",
        "name": "SAD_AR5_risco_PT_continental",
        "metadata": {
            "gerado_em": datetime.now(timezone.utc).isoformat(),
            "ambito": "Portugal Continental (lon -11.0 a -7.38)",
            "limiar": limiar,
        },
        "features": features,
    }


def _geojson_rota(rota: dict) -> list[dict]:
    features = []
    wps = rota.get("waypoints") or []
    if len(wps) > 1:
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[w["lon"], w["lat"]] for w in wps],
            },
            "properties": {"tipo": "rota", "modo": rota.get("modo")},
        })
    for i, w in enumerate(wps):
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [w["lon"], w["lat"]]},
            "properties": {"ordem": i, "tipo": w.get("tipo"), "nome": w.get("nome")},
        })
    for rs in rota.get("rotas_sector") or []:
        sw = rs.get("waypoints") or []
        if len(sw) > 1:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[w["lon"], w["lat"]] for w in sw],
                },
                "properties": {
                    "tipo": "sector",
                    "sector": rs.get("sector"),
                    "janela_h": rs.get("janela_h"),
                },
            })
    return features


def exportar_plano_missao(rota: dict, meta: dict | None = None) -> dict:
    """Pacote JSON para briefing operacional (rota + metadados + validação)."""
    val = exportar_validacao()
    return {
        "tipo": "plano_missao_sad_ar5",
        "ambito": "Portugal Continental",
        "gerado_em": datetime.now(timezone.utc).isoformat(),
        "meta": meta or {},
        "rota": rota,
        "agenda_24h": rota.get("agenda_24h"),
        "frota_resumo": rota.get("frota_resumo"),
        "respostas_sad": val.get("resposta_objetivo", {}),
        "validacao": {
            "baseline_patrulha": val.get("baseline_patrulha", {}),
            "ganho_sad_vs_aleatorio": val.get("baseline_patrulha", {}).get("ganho_sad_vs_aleatorio"),
        },
        "geojson": {
            "type": "FeatureCollection",
            "features": _geojson_rota(rota),
        },
    }
