"""Planificação de rotas: patrulha costeira completa (alinhada com SAD)."""
from __future__ import annotations

from services.patrulha_costeira import (
    rota_plano_24h_costeira,
    rota_reativa_costeira,
    rota_sortie_costeira,
)
from services.validacao_rota import avaliar_plano_24h, avaliar_rota


def _com_validacao(rota: dict, plano24h: bool = False) -> dict:
    if isinstance(rota, dict) and not rota.get("erro"):
        rota["validacao"] = avaliar_plano_24h(rota) if plano24h else avaliar_rota(rota)
    return rota


def _regiao(lat_min=None, lat_max=None, lon_min=None, lon_max=None, regiao=None):
    if regiao:
        return regiao
    if any(v is not None for v in (lat_min, lat_max, lon_min, lon_max)):
        return {"lat_min": lat_min, "lat_max": lat_max, "lon_min": lon_min, "lon_max": lon_max}
    return None


def rota_sortie(
    base_nome: str | None,
    vento_ms: float,
    n_alvos: int = 8,
    t_on_h: float | None = None,
    lon_lanc: float | None = None,
    lat_lanc: float | None = None,
    tipo_patrulha: str = "geral",
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    regiao: dict | None = None,
    cenario_id: str | None = None,
    meteo_bases: list[dict] | None = None,
    usar_meteo_live: bool = True,
) -> dict:
    return _com_validacao(rota_sortie_costeira(
        base_nome, vento_ms, n_alvos, t_on_h, lon_lanc, lat_lanc, tipo_patrulha,
        _regiao(lat_min, lat_max, lon_min, lon_max, regiao), cenario_id,
        meteo_bases, usar_meteo_live,
    ))


def rota_plano_24h(
    vento_ms: float,
    k_bases: int = 2,
    t_on_h: float | None = None,
    n_alvos: int = 8,
    base_nome: str | None = None,
    lon_lanc: float | None = None,
    lat_lanc: float | None = None,
    tipo_patrulha: str = "geral",
    lat_min: float | None = None,
    lat_max: float | None = None,
    lon_min: float | None = None,
    lon_max: float | None = None,
    regiao: dict | None = None,
    cenario_id: str | None = None,
    meteo_bases: list[dict] | None = None,
    usar_meteo_live: bool = True,
) -> dict:
    return _com_validacao(rota_plano_24h_costeira(
        vento_ms, k_bases, t_on_h, n_alvos, base_nome, lon_lanc, lat_lanc, tipo_patrulha,
        _regiao(lat_min, lat_max, lon_min, lon_max, regiao), cenario_id,
        meteo_bases, usar_meteo_live,
    ), plano24h=True)


def rota_reativa(
    lon: float,
    lat: float,
    vento_ms: float,
    base_nome: str | None = None,
    lon_lanc: float | None = None,
    lat_lanc: float | None = None,
    t_on_h: float | None = None,
    meteo_bases: list[dict] | None = None,
    usar_meteo_live: bool = True,
) -> dict:
    return _com_validacao(rota_reativa_costeira(
        lon, lat, vento_ms, base_nome, lon_lanc, lat_lanc, t_on_h,
        meteo_bases, usar_meteo_live,
    ))
