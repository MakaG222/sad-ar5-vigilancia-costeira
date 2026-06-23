"""Testes dos endpoints de validação científica."""
from __future__ import annotations

from services.ciencia import (
    ahp_pesos, backtest_temporal, baseline_patrulha, sensibilidade_pesos,
)


def test_backtest_tem_holdout():
    bt = backtest_temporal()
    assert bt["n_holdout"] == 54
    assert bt["taxa_acerto_limiar"] > 0.8


def test_baseline_ganho_canonico():
    bl = baseline_patrulha()
    assert bl["n_celulas_patrulha"] == 274
    assert bl["ganho_sad_vs_aleatorio"] == 2.13
    assert len(bl["estrategias"]) == 3


def test_ahp_consistente():
    ah = ahp_pesos()
    assert ah["consistente"] is True
    assert abs(sum(ah["pesos_adotados"].values()) - 1.0) < 0.01


def test_sensibilidade_pesos_referencia():
    s = sensibilidade_pesos()
    assert s["delta_celulas"] == 0
    assert s["n_alto_risco"] >= 250


def test_sensibilidade_pesos_custom():
    s = sensibilidade_pesos(droga=0.85, pesca=0.05, poluicao=0.05, imigracao=0.05)
    ref = sensibilidade_pesos()
    assert s["pesos_referencia"] == ref["pesos_referencia"]
    assert isinstance(s["delta_celulas"], int)
