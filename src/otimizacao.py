"""
otimizacao.py — Núcleo de otimização do SAD.

Resolve dois problemas complementares de localização de instalações:

1. SET COVER (cobertura mínima): nº MÍNIMO de bases (aeródromos) necessárias
   para cobrir TODAS as células de alto risco dentro do raio efetivo do AR5.

2. MCLP (Maximal Covering Location Problem): para cada k = 1..N bases, qual a
   fração máxima de risco coberta — produz a curva de trade-off
   (nº de drones/bases vs. risco coberto).

Calcula ainda a frota necessária para sustentar a cobertura 24 h, a partir da
autonomia do AR5, do tempo de trânsito e da disponibilidade operacional.
"""
from __future__ import annotations
import math
import numpy as np
import pulp

from config import (AR5, RAIO_BASE_KM, RESERVA_H, DISPONIBILIDADE,
                    RESERVA_FROTA, fator_vento, SENSOR_SWATH_KM,
                    TEMPO_REVISITA_H, T_ON_MIN_H)


def matriz_cobertura(pts: list[dict], bases: list[dict], raio_km: float) -> np.ndarray:
    """a[b, i] = 1 se a célula i está dentro de `raio_km` da base b."""
    B = len(bases)
    P = len(pts)
    bx = np.array([b["x"] for b in bases]); by = np.array([b["y"] for b in bases])
    px = np.array([p["x"] for p in pts]);   py = np.array([p["y"] for p in pts])
    a = np.zeros((B, P), dtype=np.int8)
    for b in range(B):
        d = np.sqrt((px - bx[b]) ** 2 + (py - by[b]) ** 2)
        a[b] = (d <= raio_km).astype(np.int8)
    return a


def set_cover(pts, bases, raio_km, limiar_risco=0.5):
    """Nº mínimo de bases para cobrir todas as células com risco >= limiar.
    Células de alto risco não cobríveis por nenhuma base são ignoradas e
    reportadas separadamente."""
    a = matriz_cobertura(pts, bases, raio_km)
    alvo = [i for i, p in enumerate(pts) if p["risco"] >= limiar_risco]
    cobrivel = [i for i in alvo if a[:, i].sum() > 0]
    nao_cobrivel = [i for i in alvo if a[:, i].sum() == 0]

    prob = pulp.LpProblem("set_cover", pulp.LpMinimize)
    y = [pulp.LpVariable(f"y_{b}", cat="Binary") for b in range(len(bases))]
    prob += pulp.lpSum(y)
    for i in cobrivel:
        prob += pulp.lpSum(y[b] for b in range(len(bases)) if a[b, i]) >= 1
    prob.solve(pulp.PULP_CBC_CMD(msg=0))

    sel = [b for b in range(len(bases)) if y[b].value() and y[b].value() > 0.5]
    return {
        "bases_sel": sel,
        "n_bases": len(sel),
        "n_alvo": len(alvo),
        "n_cobrivel": len(cobrivel),
        "n_nao_cobrivel": len(nao_cobrivel),
        "limiar": limiar_risco,
    }


def mclp(pts, bases, raio_km, k):
    """Maximiza o risco coberto usando no máximo k bases."""
    a = matriz_cobertura(pts, bases, raio_km)
    risco = np.array([p["risco"] for p in pts])
    prob = pulp.LpProblem("mclp", pulp.LpMaximize)
    y = [pulp.LpVariable(f"y_{b}", cat="Binary") for b in range(len(bases))]
    z = [pulp.LpVariable(f"z_{i}", lowBound=0, upBound=1) for i in range(len(pts))]
    prob += pulp.lpSum(risco[i] * z[i] for i in range(len(pts)))
    prob += pulp.lpSum(y) <= k
    for i in range(len(pts)):
        prob += z[i] <= pulp.lpSum(y[b] for b in range(len(bases)) if a[b, i])
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    sel = [b for b in range(len(bases)) if y[b].value() and y[b].value() > 0.5]
    risco_coberto = sum(risco[i] * (z[i].value() or 0) for i in range(len(pts)))
    return {"k": k, "bases_sel": sel,
            "risco_coberto": risco_coberto,
            "frac_risco": risco_coberto / risco.sum()}


def curva_tradeoff(pts, bases, raio_km, kmax=None):
    kmax = kmax or len(bases)
    return [mclp(pts, bases, raio_km, k) for k in range(1, kmax + 1)]


# ---------------------------------------------------------------------------
# Dimensionamento da frota para cobertura 24 h
# ---------------------------------------------------------------------------
def dimensionar_frota(n_bases: int, raio_km: float) -> dict:
    """Modelo simples (1 órbita/drone por base, reachability). Usado no cenário
    conservador para comparação com o trabalho SIG original."""
    V = AR5["velocidade_cruzeiro_kmh"]
    E = AR5["autonomia_h"]
    transito_h = 2.0 * (raio_km / V)
    t_on = max(E - transito_h - RESERVA_H, 0.1)
    sorties_dia = 24.0 / t_on
    drones_por_base = math.ceil(sorties_dia / DISPONIBILIDADE)
    frota = math.ceil(n_bases * drones_por_base * (1.0 + RESERVA_FROTA))
    return {
        "n_bases": n_bases, "transito_h": round(transito_h, 2),
        "t_on_h": round(t_on, 2), "sorties_dia_por_base": round(sorties_dia, 2),
        "drones_por_base": drones_por_base, "drones_simultaneos": n_bases,
        "frota_total": frota,
    }


def dist_media_ao_base(pts_alto: list[dict], bases: list[dict],
                       bases_sel: list[int]) -> tuple[float, float]:
    """Distância média e máxima (km) das células de alto risco à base
    selecionada mais próxima."""
    if not bases_sel:
        return 0.0, 0.0
    bx = np.array([bases[b]["x"] for b in bases_sel])
    by = np.array([bases[b]["y"] for b in bases_sel])
    ds = []
    for p in pts_alto:
        d = np.sqrt((bx - p["x"]) ** 2 + (by - p["y"]) ** 2)
        ds.append(d.min())
    ds = np.array(ds)
    return float(ds.mean()), float(ds.max())


def dimensionar_persistencia(pts_alto, bases, bases_sel, area_celula_km2,
                             swath_km=SENSOR_SWATH_KM,
                             revisita_h=TEMPO_REVISITA_H,
                             disponibilidade=DISPONIBILIDADE):
    """Dimensiona a frota para VIGILÂNCIA PERSISTENTE 24 h da área de alto risco.

    Distingue alcance de cobertura sensorial:
      n_sim = área_alto_risco / (V * swath * revisita)   (drones em voo simultâneo)
      t_on  = autonomia - 2*dist_média/V - reserva
      M     = (24/t_on)/disponibilidade                  (multiplicador de rotação)
      frota = ceil( n_sim * M * (1 + reserva_frota) )
    """
    V = AR5["velocidade_cruzeiro_kmh"]
    E = AR5["autonomia_h"]
    area_hr = len(pts_alto) * area_celula_km2
    taxa_cobertura = V * swath_km * revisita_h          # km² varridos por ciclo/drone
    n_sim = max(1, math.ceil(area_hr / taxa_cobertura))

    d_med, d_max = dist_media_ao_base(pts_alto, bases, bases_sel)
    t_on = max(E - 2.0 * d_med / V - RESERVA_H, 0.5)
    M = (24.0 / t_on) / disponibilidade
    frota = math.ceil(n_sim * M * (1.0 + RESERVA_FROTA))
    return {
        "area_alto_risco_km2": round(area_hr, 0),
        "swath_km": swath_km, "revisita_h": revisita_h,
        "n_simultaneos": n_sim,
        "dist_media_km": round(d_med, 1), "dist_max_km": round(d_max, 1),
        "t_on_h": round(t_on, 2), "multiplicador_rotacao": round(M, 2),
        "disponibilidade": disponibilidade,
        "frota_total": frota,
    }


def raio_efetivo(vento_ms: float) -> float:
    return RAIO_BASE_KM * fator_vento(vento_ms)


def raio_por_autonomia(t_on_desejado_h: float, vento_ms: float = 4.0) -> float:
    """Raio de patrulha máximo limitado pela autonomia do AR5, para um tempo de
    permanência em estação desejado. r = V*(E - reserva - t_on)/2, com redução
    pelo vento."""
    V = AR5["velocidade_cruzeiro_kmh"]
    E = AR5["autonomia_h"]
    r = V * (E - RESERVA_H - t_on_desejado_h) / 2.0
    return max(r, 0.0) * fator_vento(vento_ms)


if __name__ == "__main__":
    from geo import gerar_procura, bases_proj
    from risco import calcular_risco
    pts = gerar_procura()
    bases = bases_proj()
    calcular_risco(pts, "../dados/fontes/apreensoes_droga_PT.xlsx")
    R = raio_efetivo(4.0)
    sc = set_cover(pts, bases, R, 0.5)
    print("SET COVER R=%.0f km:" % R, sc)
    print("FROTA:", dimensionar_frota(sc["n_bases"], R))
