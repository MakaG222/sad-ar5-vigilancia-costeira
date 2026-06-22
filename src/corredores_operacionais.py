"""
corredores_operacionais.py — Corredores marítimos por ameaça (heurística operacional).

Complementa os clusters k-means com faixas alinhadas a rotas de tráfico conhecidas
(documentação UNODC, rotas atlânticas SW, corredor costeiro). Usado no scoring
e na selecção de células para varrimento.
"""
from __future__ import annotations

# (lat_min, lat_max, lon_min, lon_max, peso)
CORREDORES: dict[str, list[dict]] = {
    "droga": [
        {
            "nome": "Aproximação SW (Magreb → Algarve)",
            "lat_min": 36.65, "lat_max": 37.35,
            "lon_min": -9.5, "lon_max": -7.2,
            "peso": 1.35,
        },
        {
            "nome": "Ao largo Sagres / Cabo de São Vicente",
            "lat_min": 36.85, "lat_max": 37.25,
            "lon_min": -9.2, "lon_max": -8.4,
            "peso": 1.25,
        },
        {
            "nome": "Canal interior Algarve",
            "lat_min": 37.0, "lat_max": 37.55,
            "lon_min": -8.9, "lon_max": -7.6,
            "peso": 1.1,
        },
    ],
    "imigracao": [
        {
            "nome": "Rota atlântica ocidental",
            "lat_min": 36.8, "lat_max": 38.2,
            "lon_min": -10.5, "lon_max": -8.5,
            "peso": 1.3,
        },
    ],
    "pesca": [
        {
            "nome": "Banco e plataforma continental",
            "lat_min": 37.0, "lat_max": 41.5,
            "lon_min": -10.5, "lon_max": -8.0,
            "peso": 1.15,
        },
    ],
}


def bonus_corredor(lon: float, lat: float, tipo: str) -> float:
    """Multiplicador [1.0, ~1.35] se a célula cai num corredor da ameaça."""
    best = 1.0
    for c in CORREDORES.get(tipo, []):
        if (c["lat_min"] <= lat <= c["lat_max"]
                and c["lon_min"] <= lon <= c["lon_max"]):
            best = max(best, c["peso"])
    return best


def nome_corredor(lon: float, lat: float, tipo: str) -> str | None:
    for c in CORREDORES.get(tipo, []):
        if (c["lat_min"] <= lat <= c["lat_max"]
                and c["lon_min"] <= lon <= c["lon_max"]):
            return c["nome"]
    return None
