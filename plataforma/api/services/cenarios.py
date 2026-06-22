"""Cenários pré-definidos de patrulha (alinhados com relatório SAD)."""
from __future__ import annotations
from copy import deepcopy

# regiao: lat_min, lat_max, lon_min, lon_max (None = costa PT completa)
CENARIOS: list[dict] = [
    {
        "id": "rotina_24h",
        "nome": "Rotina 24 h — costa completa",
        "descricao": "6 sectores N→S; frota ~10 AR5; bases MCLP Porto + Portimão (Q2/Q3 relatório).",
        "modo": "plano24h",
        "tipo_patrulha": "costeira",
        "k_bases": 2,
        "base": None,
        "regiao": None,
        "ref_relatorio": "Q2_quantos + Q3_bases",
    },
    {
        "id": "anti_droga_algarve",
        "nome": "Anti-droga — Algarve",
        "descricao": "Patrulha sortie no SW; foco tráfico marítimo (Q1: Algarve).",
        "modo": "sortie",
        "tipo_patrulha": "droga",
        "k_bases": 1,
        "base": "Portimão",
        "regiao": {"lat_min": 36.85, "lat_max": 37.55, "lon_min": -9.3, "lon_max": -7.5},
        "ref_relatorio": "Q1_onde — Algarve",
    },
    {
        "id": "lisboa_setubal",
        "nome": "Corredor Lisboa–Setúbal",
        "descricao": "Alto tráfego AIS e risco integrado na RTM Lisboa.",
        "modo": "sortie",
        "tipo_patrulha": "geral",
        "k_bases": 1,
        "base": "Montijo (BA6 — FAP)",
        "regiao": {"lat_min": 38.35, "lat_max": 39.05, "lon_min": -9.6, "lon_max": -8.8},
        "ref_relatorio": "Q1_onde — Setúbal–Lisboa",
    },
    {
        "id": "pesca_inn_nw",
        "nome": "Pesca INN — NW / Peniche",
        "descricao": "Sortie ao largo do centro-oeste; foco pesca ilegal.",
        "modo": "sortie",
        "tipo_patrulha": "pesca",
        "k_bases": 1,
        "base": "Porto (Sá Carneiro)",
        "regiao": {"lat_min": 39.15, "lat_max": 41.45, "lon_min": -10.5, "lon_max": -8.7},
        "ref_relatorio": "Q1_onde — NW/Peniche",
    },
    {
        "id": "imigracao_atlantico",
        "nome": "Imigração — rota atlântica",
        "descricao": "Patrulha sul + foco imigração irregular (IOM/Frontex).",
        "modo": "sortie",
        "tipo_patrulha": "imigracao",
        "k_bases": 1,
        "base": "Faro",
        "regiao": {"lat_min": 36.85, "lat_max": 38.2, "lon_min": -10.0, "lon_max": -8.0},
        "ref_relatorio": "PESOS_AMEACA imigração 20%",
    },
    {
        "id": "poluicao_sul",
        "nome": "Poluição / derrames — Sul",
        "descricao": "EMSA CleanSeaNet: concentração de alertas na região Sul.",
        "modo": "sortie",
        "tipo_patrulha": "poluicao",
        "k_bases": 1,
        "base": "Sines",
        "regiao": {"lat_min": 37.5, "lat_max": 38.6, "lon_min": -9.5, "lon_max": -8.5},
        "ref_relatorio": "PESOS_AMEACA poluição 20%",
    },
    {
        "id": "norte_costeira",
        "nome": "Patrulha rotina — Norte",
        "descricao": "Sortie costeira Minho–Aveiro (região N).",
        "modo": "sortie",
        "tipo_patrulha": "costeira",
        "k_bases": 1,
        "base": "Porto (Sá Carneiro)",
        "regiao": {"lat_min": 40.5, "lat_max": 41.95, "lon_min": -10.5, "lon_max": -8.5},
        "ref_relatorio": "Cobertura sector N",
    },
]


def listar_cenarios() -> list[dict]:
    return deepcopy(CENARIOS)


def obter_cenario(cenario_id: str) -> dict | None:
    for c in CENARIOS:
        if c["id"] == cenario_id:
            return deepcopy(c)
    return None


def regiao_from_dict(d: dict | None) -> dict | None:
    if not d:
        return None
    keys = ("lat_min", "lat_max", "lon_min", "lon_max")
    if not any(d.get(k) is not None for k in keys):
        return None
    return {k: d.get(k) for k in keys if d.get(k) is not None}
