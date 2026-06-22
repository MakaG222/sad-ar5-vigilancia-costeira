"""Testes unitários da validação de qualidade de rota (Fase 2).

Não dependem de rede nem do pipeline: exercitam a lógica pura de avaliação.

Uso:
    cd plataforma/api && source .venv/bin/activate
    python -m pytest tests/ -q        # se pytest disponível
    python tests/test_validacao_rota.py   # execução directa (sem pytest)
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from services.validacao_rota import avaliar_rota, avaliar_plano_24h


def _rota_coerente() -> dict:
    """Rota com waypoints contíguos dentro da zona alvo."""
    wps = [{"lon": -8.9, "lat": 37.0 + i * 0.05, "tipo": "patrulha"} for i in range(6)]
    return {
        "modo": "sortie",
        "n_pontos_patrol": 6,
        "distancia_km": 120.0,
        "dentro_autonomia": True,
        "zona_cluster": {"lat_min": 36.9, "lat_max": 37.4, "lon_min": -9.1, "lon_max": -8.7},
        "waypoints": [{"lon": -8.95, "lat": 36.95, "tipo": "entrada_mar"}, *wps],
    }


def test_rota_coerente_tem_score_alto():
    v = avaliar_rota(_rota_coerente())
    assert v["score"] >= 85
    assert v["classe"] == "Coerente"
    assert v["pct_na_zona"] == 100.0


def test_fora_de_autonomia_penaliza():
    r = _rota_coerente()
    r["dentro_autonomia"] = False
    v = avaliar_rota(r)
    assert v["score"] < 85
    assert any("autonomia" in a.lower() for a in v["avisos"])


def test_saltos_detetados():
    r = _rota_coerente()
    # injecta um waypoint muito distante -> salto > swath
    r["waypoints"].append({"lon": -7.0, "lat": 41.5, "tipo": "patrulha"})
    v = avaliar_rota(r)
    assert v["continuidade"]["n_saltos"] >= 1


def test_pontos_fora_da_zona_reduz_pct():
    r = _rota_coerente()
    r["waypoints"].append({"lon": -10.5, "lat": 41.0, "tipo": "patrulha"})  # fora da caixa
    v = avaliar_rota(r)
    assert v["pct_na_zona"] is not None and v["pct_na_zona"] < 100.0


def test_rota_invalida_nao_rebenta():
    assert avaliar_rota({"erro": "x"})["score"] is None
    assert avaliar_rota(None)["score"] is None


def test_rota_vazia_e_reprovada():
    """Rota sem pontos de patrulha / 0 km não pode ser 'Coerente'."""
    v = avaliar_rota({"modo": "sortie", "n_pontos_patrol": 0, "distancia_km": 0.0, "waypoints": []})
    assert v["classe"] == "Rever"
    assert v["score"] <= 40
    assert any("fora de alcance" in a.lower() or "sem pontos" in a.lower() for a in v["avisos"])


def test_plano_24h_ignora_base_unica_com_duas_bases():
    from services.patrulha_costeira import rota_plano_24h_costeira

    r = rota_plano_24h_costeira(8.0, k_bases=2, base_nome="Porto (Sá Carneiro)")
    bases = [rs["base"] for rs in r["rotas_sector"]]
    assert "Portimão" in bases
    assert bases.count("Portimão") >= 3
    assert bases[0].startswith("Porto")


def test_plano_24h_agrega_sectores():
    plano = {
        "modo": "plano_24h",
        "rotas_sector": [
            {"sector": 1, "n_pontos_patrol": 5, "dist_km": 90.0, "lat_min": 37.0, "lat_max": 37.5,
             "meteo": {"dentro_autonomia": True},
             "waypoints": [{"lon": -8.9, "lat": 37.0 + i * 0.05, "tipo": "patrulha"} for i in range(5)]},
            {"sector": 2, "n_pontos_patrol": 5, "dist_km": 95.0, "lat_min": 38.0, "lat_max": 38.5,
             "meteo": {"dentro_autonomia": True},
             "waypoints": [{"lon": -9.0, "lat": 38.0 + i * 0.05, "tipo": "patrulha"} for i in range(5)]},
        ],
    }
    v = avaliar_plano_24h(plano)
    assert v["n_sectores"] == 2
    assert v["score"] is not None
    assert len(v["por_sector"]) == 2


def _run_sem_pytest() -> int:
    testes = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    falhas = 0
    for t in testes:
        try:
            t()
            print(f"  ok  {t.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"  x   {t.__name__}: {e}")
    print()
    print("TODOS OK" if not falhas else f"FALHARAM {falhas}/{len(testes)}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(_run_sem_pytest())
