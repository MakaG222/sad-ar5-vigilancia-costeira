"""Métricas canónicas do SAD — consistência entre JSON e API."""
from __future__ import annotations

import json
import os

from services.sad_respostas import carregar_respostas

ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")
VALIDACAO = os.path.join(ROOT, "resultados", "validacao.json")
CAMADAS = os.path.join(ROOT, "resultados", "camadas_mapa.json")

CANON = {
    "n_celulas_patrulha": 274,
    "ganho_sad_vs_aleatorio": 2.13,
    "frota_total": 9,
    "frota_costeira": 9,
}


def test_validacao_json_canonica():
    with open(VALIDACAO, encoding="utf-8") as f:
        val = json.load(f)
    bl = val["baseline_patrulha"]
    q2 = val["resposta_objetivo"]["Q2_quantos"]
    assert bl["n_celulas_patrulha"] == CANON["n_celulas_patrulha"]
    assert bl["ganho_sad_vs_aleatorio"] == CANON["ganho_sad_vs_aleatorio"]
    assert q2["frota_total"] == CANON["frota_total"]
    assert q2["frota_costeira"] == CANON["frota_costeira"]


def test_camadas_mapa_alinhado_com_validacao():
    with open(VALIDACAO, encoding="utf-8") as f:
        val = json.load(f)
    with open(CAMADAS, encoding="utf-8") as f:
        cam = json.load(f)
    bl_val = val["baseline_patrulha"]
    bl_cam = cam["validacao"]["baseline_patrulha"]
    assert bl_cam["n_celulas_patrulha"] == bl_val["n_celulas_patrulha"]
    assert bl_cam["ganho_sad_vs_aleatorio"] == bl_val["ganho_sad_vs_aleatorio"]


def test_sad_respostas_api():
    r = carregar_respostas()
    assert "erro" not in r
    v = r["validacao"]
    assert v["n_celulas_patrulha"] == CANON["n_celulas_patrulha"]
    assert v["ganho_sad_vs_aleatorio"] == CANON["ganho_sad_vs_aleatorio"]
    bases = r["Q3_bases"].get("bases_mclp") or []
    assert "Porto (Sá Carneiro)" in bases
    assert "Portimão" in bases
