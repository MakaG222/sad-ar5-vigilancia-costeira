"""Testes do modo demo determinístico."""
from __future__ import annotations

import pytest

from services import demo_mode


def test_demo_navios_fixture():
    nav = demo_mode.carregar_navios_fixos()
    assert len(nav) >= 35
    assert "263999001" in nav
    assert nav["263999001"]["nome"] == "SUSPEITO DEMO"


def test_demo_activo_com_env(monkeypatch):
    monkeypatch.setenv("DEMO_DETERMINISTICO", "1")
    assert demo_mode.activo() is True
    monkeypatch.delenv("DEMO_DETERMINISTICO", raising=False)
    assert demo_mode.activo() is False
