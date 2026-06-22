"""Respostas SAD (Q1/Q2/Q3) do pipeline analítico."""
from __future__ import annotations
import json
import os

VALIDACAO = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "resultados", "validacao.json"
)


def carregar_respostas() -> dict:
    try:
        with open(VALIDACAO, encoding="utf-8") as f:
            data = json.load(f)
    except OSError:
        return {"erro": "validacao.json não encontrado"}
    obj = data.get("resposta_objetivo", {})
    bl = data.get("baseline_patrulha", {})
    return {
        "Q1_onde": obj.get("Q1_onde", {}),
        "Q2_quantos": obj.get("Q2_quantos", {}),
        "Q3_bases": obj.get("Q3_bases", {}),
        "validacao": {
            "ganho_sad_vs_aleatorio": bl.get("ganho_sad_vs_aleatorio"),
            "pct_risco_capturado": bl.get("pct_risco_total_capturado_sad"),
            "n_celulas_patrulha": bl.get("n_celulas_patrulha"),
            "n_incidentes_iom": data.get("n_incidentes_iom"),
            "n_desembarques_pt": data.get("n_desembarques_pt"),
            "revisita_h": 3.0,
            "janela_sector_h": 4.0,
        },
    }
