"""Modo demonstração determinístico — navios e meteo fixos para apresentações."""
from __future__ import annotations

import json
import os

_DEMO_JSON = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "resultados", "demo_navios.json"
)


def activo() -> bool:
    return os.environ.get("DEMO_DETERMINISTICO", "").lower() in ("1", "true", "yes")


def carregar_navios_fixos() -> dict[str, dict]:
    try:
        with open(_DEMO_JSON, encoding="utf-8") as f:
            data = json.load(f)
    except OSError:
        return {}
    return {n["mmsi"]: dict(n) for n in data.get("navios", []) if n.get("mmsi")}


def meteo_fallback_demo() -> list[dict]:
    """Meteo estável para demo em sala (vento 8 m/s em Porto e Portimão)."""
    return [
        {"base": "Porto (Sá Carneiro)", "vento_ms": 8.0, "condicao": "moderada", "erro": None},
        {"base": "Portimão", "vento_ms": 7.5, "condicao": "moderada", "erro": None},
        {"base": "Lisboa (Tires)", "vento_ms": 9.0, "condicao": "moderada", "erro": None},
    ]
