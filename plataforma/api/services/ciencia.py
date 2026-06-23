"""Endpoints de validação científica — backtest, baseline e sensibilidade AHP."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from config import LIMIAR_RISCO_OPERACIONAL, PESOS_AMEACA
from risco import aplicar_pesos
from services.grelha_cache import pts_grelha

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "resultados")
VALIDACAO = os.path.join(ROOT, "validacao.json")
AHP = os.path.join(ROOT, "ahp_pesos.json")


def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def backtest_temporal() -> dict:
    data = _load(VALIDACAO)
    bt = data.get("backtest_temporal", {})
    comp = data.get("backtest_comparativo", {})
    return {
        "ano_corte": bt.get("ano_corte", 2022),
        "n_holdout": bt.get("n_holdout"),
        "taxa_acerto_limiar": bt.get("taxa_acerto_limiar"),
        "taxa_acerto_percentil_20": bt.get("taxa_acerto_percentil_20", bt.get("taxa_acerto_top20")),
        "ganho_relativo_limiar": bt.get("ganho_relativo_limiar"),
        "baseline_aleatorio_limiar": bt.get("baseline_aleatorio_limiar"),
        "risco_medio_holdout": bt.get("risco_medio_holdout"),
        "meta_rigoroso": comp.get("meta_rigoroso"),
        "nota": (
            "Backtest temporal: treino até ao ano de corte; holdout em eventos posteriores. "
            "Camadas pesca/poluição estáticas (EMODnet)."
        ),
    }


def baseline_patrulha() -> dict:
    data = _load(VALIDACAO)
    bl = data.get("baseline_patrulha", {})
    decomp = data.get("decomposicao_ganho", {})
    sens = data.get("sensibilidade_limiar", {}).get("limiares", [])
    return {
        "n_celulas_patrulha": bl.get("n_celulas_patrulha"),
        "estrategias": [
            {
                "nome": "SAD (ranking)",
                "captura_pct": round(100 * bl.get("captura_sad", 0), 1),
                "descricao": "Patrulhar as N células de maior risco SAD",
            },
            {
                "nome": "Aleatório",
                "captura_pct": round(100 * bl.get("captura_aleatorio_media", 0), 1),
                "descricao": f"Média de 500 sorteios (σ={bl.get('captura_aleatorio_std', 0):.3f})",
            },
            {
                "nome": "Uniforme costeira",
                "captura_pct": round(100 * bl.get("captura_uniforme_costeira", 0), 1),
                "descricao": "N células espaçadas uniformemente na faixa costeira",
            },
        ],
        "ganho_sad_vs_aleatorio": bl.get("ganho_sad_vs_aleatorio"),
        "ganho_sad_vs_uniforme": bl.get("ganho_sad_vs_uniforme"),
        "ganho_ic95_bootstrap": bl.get("ganho_ic95_bootstrap"),
        "pct_risco_total_capturado_sad": bl.get("pct_risco_total_capturado_sad"),
        "indice_gini_risco": decomp.get("indice_gini_risco"),
        "sensibilidade_limiar": sens,
    }


def ahp_pesos() -> dict:
    data = _load(AHP)
    return {
        "metodo": data.get("metodo"),
        "pesos_ahp": data.get("pesos_ahp"),
        "pesos_adotados": data.get("pesos_adotados", PESOS_AMEACA),
        "consistency_ratio": data.get("consistency_ratio"),
        "consistente": data.get("consistente"),
        "sensibilidade_pm10pct": data.get("sensibilidade_pesos_pm10pct"),
        "nota": data.get("nota"),
    }


def sensibilidade_pesos(
    droga: float | None = None,
    pesca: float | None = None,
    poluicao: float | None = None,
    imigracao: float | None = None,
) -> dict:
    pesos = {
        "droga": droga if droga is not None else PESOS_AMEACA["droga"],
        "pesca": pesca if pesca is not None else PESOS_AMEACA["pesca"],
        "poluicao": poluicao if poluicao is not None else PESOS_AMEACA["poluicao"],
        "imigracao": imigracao if imigracao is not None else PESOS_AMEACA["imigracao"],
    }
    pts = pts_grelha()
    res = aplicar_pesos(pts, pesos, limiar=LIMIAR_RISCO_OPERACIONAL)
    ref = aplicar_pesos(pts, PESOS_AMEACA, limiar=LIMIAR_RISCO_OPERACIONAL)
    res["n_alto_referencia"] = ref["n_alto_risco"]
    res["delta_celulas"] = res["n_alto_risco"] - ref["n_alto_risco"]
    res["pesos_referencia"] = PESOS_AMEACA
    return res
