"""Testes de recálculo de risco com pesos AHP alternativos."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from config import PESOS_AMEACA
from geo import gerar_procura
from risco import aplicar_pesos, calcular_risco


def _pts():
    pts = gerar_procura()[:200]
    calcular_risco(pts, os.path.join(os.path.dirname(__file__), "..", "..", "..",
                                     "dados", "fontes", "apreensoes_droga_PT.xlsx"))
    return pts


def test_aplicar_pesos_referencia():
    pts = _pts()
    ref = aplicar_pesos(pts, PESOS_AMEACA)
    assert ref["n_alto_risco"] >= 1
    assert abs(sum(ref["pesos"].values()) - 1.0) < 0.001


def test_peso_droga_dominante():
    pts = _pts()
    dom = aplicar_pesos(pts, {"droga": 0.9, "pesca": 0.03, "poluicao": 0.04, "imigracao": 0.03})
    assert dom["n_alto_risco"] >= 1
