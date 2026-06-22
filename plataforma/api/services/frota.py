"""Dimensionamento dinâmico de frota com meteo actual/previsão + validação SAD."""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from config import (
    fator_vento, AR5, RESERVA_H, TEMPO_REVISITA_H, T_ON_SORTIE_H, SENSOR_SWATH_KM,
    T_ON_MIN_H, JANELA_SECTOR_H,
)
from geo import bases_lancamento
from otimizacao import raio_por_autonomia, dimensionar_persistencia, mclp
from services.grelha_cache import pts_grelha
VALIDACAO = os.path.join(os.path.dirname(__file__), "..", "..", "..", "resultados", "validacao.json")
LIMIAR = 0.5


def _validacao_frota() -> dict:
    try:
        with open(VALIDACAO, encoding="utf-8") as f:
            data = json.load(f)
    except OSError:
        return {}
    q2 = data.get("resposta_objetivo", {}).get("Q2_quantos", {})
    bl = data.get("baseline_patrulha", {})
    return {
        "frota_costeira_analise": q2.get("frota_costeira", 9),
        "frota_total_analise": q2.get("frota_total", 9),
        "n_simultaneos_analise": q2.get("n_simultaneos", 3),
        "ganho_sad_vs_aleatorio": bl.get("ganho_sad_vs_aleatorio"),
        "pct_risco_capturado": bl.get("pct_risco_total_capturado_sad"),
        "n_celulas_patrulha": bl.get("n_celulas_patrulha", 274),
        "revisita_h_analise": data.get("decomposicao_ganho", {}).get("frac_celulas_patrolhadas"),
    }


def dimensionar(vento_atual_ms: float, vento_previsto_ms: float | None = None) -> dict:
    pts = pts_grelha()
    bases = bases_lancamento()
    alto = [p for p in pts if p["risco"] >= LIMIAR]

    v_plan = vento_previsto_ms if vento_previsto_ms is not None else vento_atual_ms
    R = raio_por_autonomia(T_ON_SORTIE_H, v_plan)
    rec = mclp(pts, bases, R, 2)
    fr = dimensionar_persistencia(alto, bases, rec["bases_sel"], 95.0)

    autonomia_util = AR5["autonomia_h"] - RESERVA_H
    val = _validacao_frota()
    bl = {}
    try:
        with open(VALIDACAO, encoding="utf-8") as f:
            bl = json.load(f).get("baseline_patrulha", {})
    except OSError:
        pass

    return {
        "vento_atual_ms": vento_atual_ms,
        "vento_previsto_ms": v_plan,
        "fator_vento_atual": round(fator_vento(vento_atual_ms), 2),
        "fator_vento_previsto": round(fator_vento(v_plan), 2),
        "raio_operacional_km": round(R, 1),
        "bases": [bases[b]["nome"] for b in rec["bases_sel"]],
        "frac_risco_coberto": round(rec["frac_risco"], 4),
        "n_alto_risco": len(alto),
        "frota_recomendada": fr["frota_total"],
        "frota_total": fr["frota_total"],
        "n_simultaneos": fr["n_simultaneos"],
        "t_on_h": fr.get("t_on_h", T_ON_SORTIE_H),
        "revisita_h": fr.get("revisita_h", TEMPO_REVISITA_H),
        "swath_km": SENSOR_SWATH_KM,
        "autonomia_h": AR5["autonomia_h"],
        "autonomia_util_h": autonomia_util,
        "reserva_h": RESERVA_H,
        "t_on_limites": {
            "min_h": T_ON_MIN_H,
            "max_h": round(AR5["autonomia_h"] - RESERVA_H - 0.5, 1),
            "janela_sector_h": JANELA_SECTOR_H,
            "recomendado_h": T_ON_SORTIE_H,
        },
        "analise_sad": {
            "frota_costeira_24h": val.get("frota_costeira_analise", 9),
            "frota_total_alto_risco": val.get("frota_total_analise", 9),
            "n_simultaneos": val.get("n_simultaneos_analise", 3),
            "n_celulas_patrulha": bl.get("n_celulas_patrulha", 274),
            "ganho_vs_aleatorio": bl.get("ganho_sad_vs_aleatorio", 2.13),
            "pct_risco_capturado": bl.get("pct_risco_total_capturado_sad", 49.3),
            "revisita_h": TEMPO_REVISITA_H,
            "janela_sector_h": 4.0,
        },
        "nota_operacional": (
            "Usar vento previsto para planear; vento actual para despacho imediato."
            if vento_previsto_ms and abs(vento_previsto_ms - vento_atual_ms) > 3
            else None
        ),
    }
