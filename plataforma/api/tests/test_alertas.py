"""Testes do motor de alertas."""
from __future__ import annotations

from services.alertas import ponto_aleatorio_mar, snap_para_mar


def test_ponto_aleatorio_em_mar():
    lon, lat, meta = ponto_aleatorio_mar(seed=7)
    assert -11 < lon < -7.5
    assert 36.8 < lat < 42.2
    assert meta.get("fonte")


def test_ponto_aleatorio_reproduzivel():
    a = ponto_aleatorio_mar(seed=99)
    b = ponto_aleatorio_mar(seed=99)
    assert a[0] == b[0] and a[1] == b[1]


def test_snap_para_mar():
    lon, lat = snap_para_mar(-9.0, 38.5)
    assert isinstance(lon, float) and isinstance(lat, float)


def test_alertas_meteo_vento_elevado():
    from services.alertas import alertas_meteo

    bases = [
        {
            "base": "Lisboa",
            "vento_ms": 20,
            "raio_operacional_km": 50,
            "lat": 38.7,
            "lon": -9.1,
            "operacional": True,
        }
    ]
    out = alertas_meteo(bases)
    assert any("Vento" in a["titulo"] for a in out)
