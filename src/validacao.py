"""
validacao.py — Fase C: validação do SAD por backtesting temporal e comparação
com baselines de patrulha.

  • Backtesting temporal (droga): treina o campo de risco com apreensões 2011–2022,
    avalia se as apreensões marítimas de 2023–2024 caem em zonas de alto risco.
  • Baseline de patrulha: compara a captura de risco do SAD (top-N células) face a
    patrulha aleatória e patrulha uniforme ao longo da costa.
  • Exporta figuras (21–22), JSON e artefactos para o painel interativo.

Uso: cd src && python validacao.py
"""
from __future__ import annotations
import json
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import PESOS_AMEACA
from geo import gerar_procura, proj, zona_maritima_pt, LON_MIN, LON_MAX, LAT_MIN, LAT_MAX
from risco import calcular_risco, _norm
from dm.construir_dados_reais import (
    kde, _norm as _norm_arr,
    DISTRITO_COSTA, IOM, campo_droga,
    campo_imigracao_iom, campo_imigracao_pt_costa,
)
from dm.coords_apreensao import geocodificar_dataframe
from dm.geocode import geocode

BASE = os.path.join(os.path.dirname(__file__), "..")
XLSX = os.path.join(BASE, "dados/fontes/apreensoes_droga_PT.xlsx")
INTERC = os.path.join(BASE, "dados/fontes/intercecoes_documentadas.csv")
CSV_REAIS = os.path.join(BASE, "dados/processados/intensidades_reais.csv")
FIGDIR = os.path.join(BASE, "resultados/figuras")
OUTDIR = os.path.join(BASE, "resultados")
LIMIAR = 0.5
ANO_CORTE = 2022


def _maritimo(df: pd.DataFrame) -> pd.DataFrame:
    mar = ["Territorial waters (seas, lakes, rivers, etc.)",
           "Seaport/Riverport station/Harbour", "International waters"]
    return df[df["Physical Seizure Location"].isin(mar) |
              (df["Trafficking Mode of Transportation"] == "Vessel/boat")].copy()


def apreensoes_geocodificadas(ano_min=None, ano_max=None) -> pd.DataFrame:
    df = pd.read_excel(XLSX)
    df = df.dropna(subset=["Seizure Date"])
    df["ano"] = pd.to_datetime(df["Seizure Date"]).dt.year
    df = _maritimo(df)
    if ano_min is not None:
        df = df[df["ano"] >= ano_min]
    if ano_max is not None:
        df = df[df["ano"] <= ano_max]
    return geocodificar_dataframe(df)


def _campo_droga_temporal(pts, ano_max: int):
    """Campo de droga só com apreensões até ano_max (KDE com peso temporal)."""
    fd, _, _ = campo_droga(pts, ano_max=ano_max, atlantico=False)
    return fd


def campo_imigracao_iom_ano(pts: list[dict], ano_max: int | None = None) -> np.ndarray:
    """KDE IOM em mar PT; opcionalmente só incidentes até ano_max."""
    if not os.path.exists(IOM):
        return np.zeros(len(pts))
    from geo import ponto_em_mar
    df = pd.read_csv(IOM)

    def parse(c):
        try:
            a, b = str(c).split(",")
            return float(a), float(b)
        except Exception:
            return np.nan, np.nan

    lat, lon = zip(*df["location_coodinates"].map(parse))
    df["lat"], df["lon"] = lat, lon
    df["ano"] = pd.to_datetime(df.get("reported_date", ""), errors="coerce").dt.year
    df = df.dropna(subset=["lat", "lon"])
    if ano_max is not None:
        df = df[df["ano"].fillna(0) <= ano_max]
    box = df[df.apply(
        lambda r: zona_maritima_pt(r["lon"], r["lat"]) and ponto_em_mar(r["lon"], r["lat"]), axis=1)]
    if box.empty:
        return np.zeros(len(pts))
    peso = pd.to_numeric(box["total_dead_and_missing"], errors="coerce").fillna(1.0).clip(lower=1.0).to_numpy()
    pts_xy = np.array([(p["x"], p["y"]) for p in pts])
    fontes_xy = [proj(lo, la) for lo, la in zip(box["lon"], box["lat"])]
    return _norm_arr(kde(pts_xy, fontes_xy, peso, sigma_km=70.0))


def risco_backtest_rigoroso(pts: list[dict], ano_max: int) -> tuple[np.ndarray, dict]:
    """Camadas temporais (droga, imigração) filtradas até ano_max; pesca/poluição estáticas (EMODnet)."""
    fd = _campo_droga_temporal(pts, ano_max)
    fi_pt = campo_imigracao_pt_ano(pts, ano_max)
    fi_iom = campo_imigracao_iom_ano(pts, ano_max)
    if fi_pt.max() > 0 and fi_iom.max() > 0:
        fi = _norm_arr(0.30 * fi_iom + 0.70 * fi_pt)
    elif fi_pt.max() > 0:
        fi = fi_pt
    else:
        fi = fi_iom
    if os.path.exists(CSV_REAIS):
        dfr = pd.read_csv(CSV_REAIS)
        fp = dfr["r_pesca"].to_numpy()
        fo = dfr["r_poluicao"].to_numpy()
    else:
        from risco import campo_pesca, campo_poluicao
        pts_xy = np.array([(p["x"], p["y"]) for p in pts])
        dist = np.array([p["dist_costa_km"] for p in pts])
        fp = campo_pesca(pts_xy, dist)
        fo = campo_poluicao(pts_xy)
    r = (PESOS_AMEACA["droga"] * fd + PESOS_AMEACA["pesca"] * fp +
         PESOS_AMEACA["poluicao"] * fo + PESOS_AMEACA["imigracao"] * fi)
    meta = {
        "ano_max": ano_max,
        "camadas_temporais": ["droga", "imigracao_pt", "imigracao_iom"],
        "camadas_estaticas": ["pesca (EMODnet)", "poluicao (EMODnet)"],
        "nota": (
            "Pesca e poluição não têm dimensão anual nas fontes abertas usadas; "
            "mantêm-se fixas enquanto droga e imigração são filtradas no treino."
        ),
    }
    return _norm(r), meta


def celula_mais_proxima(pts: list[dict], lon: float, lat: float) -> int:
    x, y = proj(lon, lat)
    d2 = [(p["x"] - x) ** 2 + (p["y"] - y) ** 2 for p in pts]
    return int(np.argmin(d2))


def _avaliar_holdout(risco_train: np.ndarray, holdout: pd.DataFrame, pts: list[dict]) -> dict:
    n_hold = len(holdout)
    if n_hold == 0:
        return {"n_holdout": 0}
    alto = risco_train >= LIMIAR
    n_alto = int(alto.sum())
    hits_limiar, hits_top20, riscos = 0, 0, []
    limiar20 = float(np.percentile(risco_train, 80))
    for _, row in holdout.iterrows():
        idx = celula_mais_proxima(pts, row["lon"], row["lat"])
        rv = float(risco_train[idx])
        riscos.append(rv)
        if rv >= LIMIAR:
            hits_limiar += 1
        if rv >= limiar20:
            hits_top20 += 1
    frac_alto = n_alto / len(pts)
    rng = np.random.default_rng(42)
    sims = [
        float((risco_train[rng.integers(0, len(pts), size=n_hold)] >= LIMIAR).mean())
        for _ in range(2000)
    ]
    baseline_rand = float(np.mean(sims))
    return {
        "n_holdout": n_hold,
        "n_celulas_alto_risco_train": n_alto,
        "frac_celulas_alto_risco": round(frac_alto, 4),
        "taxa_acerto_limiar": round(hits_limiar / n_hold, 4),
        "taxa_acerto_top20": round(hits_top20 / n_hold, 4),
        "baseline_aleatorio_limiar": round(baseline_rand, 4),
        "baseline_top20": 0.20,
        "ganho_relativo_limiar": round((hits_limiar / n_hold) / max(baseline_rand, 1e-6), 2),
        "risco_medio_holdout": round(float(np.mean(riscos)), 4),
        "risco_medio_global": round(float(risco_train.mean()), 4),
        "anos_holdout": sorted(holdout["ano"].unique().tolist()) if "ano" in holdout else [],
    }


def backtest_comparativo(pts: list[dict]) -> dict:
    """Compara três variantes de treino temporal no holdout 2023–2024."""
    holdout = apreensoes_geocodificadas(ano_min=ANO_CORTE + 1)
    r_estatico, _ = risco_com_droga_temporal(pts, ANO_CORTE)
    r_rigoroso, meta_rig = risco_backtest_rigoroso(pts, ANO_CORTE)
    res = {
        "ano_corte": ANO_CORTE,
        "meta_rigoroso": meta_rig,
        "modelo_droga_apenas": backtest_somente_droga(pts),
        "modelo_multi_ameaca_parcial": _avaliar_holdout(r_estatico, holdout, pts),
        "modelo_multi_ameaca_rigoroso": _avaliar_holdout(r_rigoroso, holdout, pts),
        "n_eventos_geocodificados_treino_droga": int(
            len(apreensoes_geocodificadas(ano_max=ANO_CORTE))
        ),
        "interpretacao": (
            "A variante rigorosa filtra droga e imigração até 2022; pesca/poluição "
            "permanecem estáticas por ausência de série temporal nas fontes EMODnet."
        ),
    }
    res["modelo_multi_ameaca_parcial"]["rotulo"] = (
        "Droga temporal + imigração estática (CSV produção)"
    )
    res["modelo_multi_ameaca_rigoroso"]["rotulo"] = (
        "Droga + imigração temporal + pesca/poluição estáticas"
    )
    return res


def risco_com_droga_temporal(pts, ano_max: int) -> tuple[np.ndarray, np.ndarray]:
    """Risco agregado com campo de droga temporal; restantes ameaças dos dados reais."""
    if os.path.exists(CSV_REAIS):
        dfr = pd.read_csv(CSV_REAIS)
        fp = dfr["r_pesca"].to_numpy()
        fo = dfr["r_poluicao"].to_numpy()
        fi = dfr["r_imigracao"].to_numpy()
    else:
        from risco import campo_pesca, campo_poluicao, campo_imigracao
        pts_xy = np.array([(p["x"], p["y"]) for p in pts])
        dist = np.array([p["dist_costa_km"] for p in pts])
        fp = campo_pesca(pts_xy, dist)
        fo = campo_poluicao(pts_xy)
        fi = campo_imigracao(pts_xy, dist)
    fd = _campo_droga_temporal(pts, ano_max)
    r = (PESOS_AMEACA["droga"] * fd + PESOS_AMEACA["pesca"] * fp +
         PESOS_AMEACA["poluicao"] * fo + PESOS_AMEACA["imigracao"] * fi)
    return _norm(r), fd


def backtest_temporal(pts: list[dict]) -> dict:
    """Treina com apreensões até 2022; testa holdout 2023–2024."""
    risco_train, _ = risco_com_droga_temporal(pts, ANO_CORTE)
    for i, p in enumerate(pts):
        p["risco_train"] = float(risco_train[i])

    holdout = apreensoes_geocodificadas(ano_min=ANO_CORTE + 1)
    n_hold = len(holdout)
    if n_hold == 0:
        return {"n_holdout": 0, "mensagem": "Sem apreensões marítimas no holdout"}

    alto = risco_train >= LIMIAR
    n_alto = int(alto.sum())
    hits_limiar, hits_top20, riscos = 0, 0, []
    limiar20 = float(np.percentile(risco_train, 80))

    for _, row in holdout.iterrows():
        idx = celula_mais_proxima(pts, row["lon"], row["lat"])
        rv = float(risco_train[idx])
        riscos.append(rv)
        if rv >= LIMIAR:
            hits_limiar += 1
        if rv >= limiar20:
            hits_top20 += 1

    # baseline aleatório: fração esperada de células alto risco
    frac_alto = n_alto / len(pts)
    rng = np.random.default_rng(42)
    sims = []
    for _ in range(2000):
        idxs = rng.integers(0, len(pts), size=n_hold)
        sims.append(float((risco_train[idxs] >= LIMIAR).mean()))
    baseline_rand = float(np.mean(sims))
    baseline_top20 = 0.20

    return {
        "ano_corte": ANO_CORTE,
        "n_holdout": n_hold,
        "n_celulas_alto_risco_train": n_alto,
        "frac_celulas_alto_risco": round(frac_alto, 4),
        "taxa_acerto_limiar": round(hits_limiar / n_hold, 4),
        "taxa_acerto_top20": round(hits_top20 / n_hold, 4),
        "baseline_aleatorio_limiar": round(baseline_rand, 4),
        "baseline_top20": baseline_top20,
        "ganho_relativo_limiar": round((hits_limiar / n_hold) / max(baseline_rand, 1e-6), 2),
        "risco_medio_holdout": round(float(np.mean(riscos)), 4),
        "risco_medio_global": round(float(risco_train.mean()), 4),
        "anos_holdout": sorted(holdout["ano"].unique().tolist()),
    }


def baseline_patrulha(pts: list[dict], n_patrulha: int | None = None) -> dict:
    """Compara captura de risco: SAD vs aleatório vs uniforme costeiro."""
    calcular_risco(pts, XLSX)
    risco = np.array([p["risco"] for p in pts])
    total = float(risco.sum())
    n = n_patrulha or int((risco >= LIMIAR).sum())
    n = max(1, min(n, len(pts)))

    # SAD: top-N por risco
    idx_sad = np.argsort(-risco)[:n]
    captura_sad = float(risco[idx_sad].sum() / total)

    # Aleatório: média de 500 simulações
    rng = np.random.default_rng(7)
    sims = []
    for _ in range(500):
        idx = rng.choice(len(pts), size=n, replace=False)
        sims.append(float(risco[idx].sum() / total))
    captura_rand = float(np.mean(sims))
    captura_rand_std = float(np.std(sims))

    # Uniforme costeiro: N células com menor dist_costa_km, espaçadas
    ordenado = sorted(range(len(pts)), key=lambda i: pts[i]["dist_costa_km"])
    step = max(1, len(ordenado) // n)
    idx_uni = ordenado[::step][:n]
    captura_uni = float(risco[idx_uni].sum() / total)

    # Bootstrap IC 95% do ganho SAD vs aleatório
    gains = []
    for _ in range(2000):
        idx = rng.choice(len(pts), size=n, replace=False)
        cap_r = float(risco[idx].sum() / total)
        gains.append(captura_sad / max(cap_r, 1e-6))
    gains = np.array(gains)
    ic95 = (float(np.percentile(gains, 2.5)), float(np.percentile(gains, 97.5)))

    return {
        "n_celulas_patrulha": n,
        "captura_sad": round(captura_sad, 4),
        "captura_aleatorio_media": round(captura_rand, 4),
        "captura_aleatorio_std": round(captura_rand_std, 4),
        "captura_uniforme_costeira": round(captura_uni, 4),
        "ganho_sad_vs_aleatorio": round(captura_sad / max(captura_rand, 1e-6), 2),
        "ganho_sad_vs_uniforme": round(captura_sad / max(captura_uni, 1e-6), 2),
        "ganho_ic95_bootstrap": [round(ic95[0], 2), round(ic95[1], 2)],
        "pct_risco_total_capturado_sad": round(100 * captura_sad, 1),
    }


def desembarques_pt_mapa() -> list[dict]:
    path = os.path.join(BASE, "dados/fontes/imigracao_pt_costa.csv")
    if not os.path.exists(path):
        return []
    df = pd.read_csv(path)
    out = []
    for _, r in df.iterrows():
        if not zona_maritima_pt(float(r["lon"]), float(r["lat"])):
            continue
        out.append({
            "lat": float(r["lat"]), "lon": float(r["lon"]),
            "n_pessoas": int(r.get("n_pessoas", 1)),
            "ano": int(r.get("ano", 0)),
            "distrito": str(r.get("distrito", "")),
            "rota": str(r.get("rota", "")),
        })
    return out


def validacao_imigracao(pts: list[dict]) -> dict:
    """Verifica se zonas de desembarque documentadas caem em células de risco imigração elevado."""
    calcular_risco(pts, XLSX)
    ev = desembarques_pt_mapa()
    if not ev:
        return {"n_eventos": 0}
    hits = 0
    r_im = []
    for e in ev:
        idx = celula_mais_proxima(pts, e["lon"], e["lat"])
        ri = float(pts[idx].get("r_imigracao", 0))
        r_im.append(ri)
        if ri >= LIMIAR:
            hits += 1
    return {
        "n_eventos": len(ev),
        "taxa_zona_alto_risco_imigracao": round(hits / len(ev), 3),
        "r_imigracao_medio_eventos": round(float(np.mean(r_im)), 3),
        "ambito": "Portugal Continental — desembarques marítimos SEF/Frontex/CP",
    }


def incidentes_iom_mapa() -> list[dict]:
    if not os.path.exists(IOM):
        return []
    from geo import ponto_em_mar
    df = pd.read_csv(IOM)

    def parse(c):
        try:
            a, b = str(c).split(",")
            return float(a), float(b)
        except Exception:
            return np.nan, np.nan

    lat, lon = zip(*df["location_coodinates"].map(parse))
    df["lat"], df["lon"] = lat, lon
    box = df[df.apply(
        lambda r: zona_maritima_pt(r["lon"], r["lat"]) and ponto_em_mar(r["lon"], r["lat"]), axis=1)]
    box = box.dropna(subset=["lat", "lon"])
    out = []
    for _, r in box.iterrows():
        out.append({
            "lat": float(r["lat"]), "lon": float(r["lon"]),
            "vitimas": int(pd.to_numeric(r.get("total_dead_and_missing"), errors="coerce") or 1),
            "data": str(r.get("reported_date", ""))[:10],
            "rota": str(r.get("migration_route", "")),
        })
    return out


def campo_imigracao_pt_ano(pts: list[dict], ano_max: int | None = None) -> np.ndarray:
    """KDE desembarques PT até ano_max (inclusive); vazio se sem eventos."""
    path = os.path.join(BASE, "dados/fontes/imigracao_pt_costa.csv")
    if not os.path.exists(path):
        return np.zeros(len(pts))
    df = pd.read_csv(path)
    df = df[df.apply(lambda r: zona_maritima_pt(float(r["lon"]), float(r["lat"])), axis=1)]
    if ano_max is not None:
        df = df[df["ano"] <= ano_max]
    if df.empty:
        return np.zeros(len(pts))
    peso = pd.to_numeric(df["n_pessoas"], errors="coerce").fillna(1.0).clip(lower=1.0).to_numpy()
    pts_xy = np.array([(p["x"], p["y"]) for p in pts])
    fontes_xy = [proj(lo, la) for lo, la in zip(df["lon"], df["lat"])]
    return _norm_arr(kde(pts_xy, fontes_xy, peso, sigma_km=55.0))


def backtest_somente_droga(pts: list[dict]) -> dict:
    """Holdout 2023–24: top 20 % de células por intensidade droga temporal (ranking fixo)."""
    fd = _campo_droga_temporal(pts, ANO_CORTE)
    holdout = apreensoes_geocodificadas(ano_min=ANO_CORTE + 1)
    n_hold = len(holdout)
    if n_hold == 0:
        return {"n_holdout": 0}
    n_top = max(1, int(np.ceil(0.2 * len(pts))))
    top_idx = set(int(i) for i in np.argsort(-fd)[:n_top])
    hits_top20 = sum(
        1 for _, row in holdout.iterrows()
        if celula_mais_proxima(pts, row["lon"], row["lat"]) in top_idx
    )
    hits_fixo = sum(
        1 for _, row in holdout.iterrows()
        if float(fd[celula_mais_proxima(pts, row["lon"], row["lat"])]) >= LIMIAR
    )
    rng = np.random.default_rng(42)
    sims_top = [
        float(np.mean([int(i) in top_idx for i in rng.integers(0, len(pts), size=n_hold)]))
        for _ in range(2000)
    ]
    baseline_top = float(np.mean(sims_top))
    return {
        "n_holdout": n_hold,
        "n_celulas_top20": n_top,
        "taxa_acerto_top20": round(hits_top20 / n_hold, 4),
        "taxa_acerto_limiar_05": round(hits_fixo / n_hold, 4),
        "baseline_top20": round(baseline_top, 4),
        "ganho_relativo_top20": round((hits_top20 / n_hold) / max(baseline_top, 1e-6), 2),
        "nota": "Ranking fixo das 231 células de maior intensidade droga (treino ≤2022).",
    }


def validacao_imigracao_holdout(pts: list[dict], ano_corte: int = 2022) -> dict:
    """KDE imigração treinado só com desembarques ≤ ano_corte; teste em eventos posteriores."""
    path = os.path.join(BASE, "dados/fontes/imigracao_pt_costa.csv")
    if not os.path.exists(path):
        return {"n_treino": 0, "n_teste": 0}
    df = pd.read_csv(path)
    df = df[df.apply(lambda r: zona_maritima_pt(float(r["lon"]), float(r["lat"])), axis=1)]
    treino = df[df["ano"] <= ano_corte]
    teste = df[df["ano"] > ano_corte]
    if teste.empty or treino.empty:
        return {"n_treino": len(treino), "n_teste": len(teste), "mensagem": "Amostra insuficiente"}
    fi = campo_imigracao_pt_ano(pts, ano_max=ano_corte)
    limiar_im = float(np.percentile(fi[fi > 0], 75)) if (fi > 0).sum() >= 4 else float(np.max(fi) * 0.5)
    hits = 0
    r_vals = []
    for _, row in teste.iterrows():
        idx = celula_mais_proxima(pts, float(row["lon"]), float(row["lat"]))
        rv = float(fi[idx])
        r_vals.append(rv)
        if rv >= limiar_im:
            hits += 1
    return {
        "ano_corte": ano_corte,
        "n_treino": int(len(treino)),
        "n_teste": int(len(teste)),
        "limiar_imigracao_treino": round(limiar_im, 3),
        "taxa_acerto_holdout": round(hits / len(teste), 3),
        "r_imigracao_medio_teste": round(float(np.mean(r_vals)), 3),
        "nota": "KDE só com desembarques ≤ ano_corte; limiar = percentil 75 do campo treinado.",
    }


def sensibilidade_limiar(pts: list[dict]) -> dict:
    """Robustez do mapa operacional e do ganho SAD a ±0,05 no limiar de alto risco."""
    calcular_risco(pts, XLSX)
    risco = np.array([p["risco"] for p in pts])
    total = float(risco.sum())
    rng = np.random.default_rng(7)
    linhas = []
    for lim in (0.45, 0.50, 0.55):
        n = int((risco >= lim).sum())
        n = max(1, min(n, len(pts)))
        idx_sad = np.argsort(-risco)[:n]
        cap_sad = float(risco[idx_sad].sum() / total)
        sims = []
        for _ in range(500):
            idx = rng.choice(len(pts), size=n, replace=False)
            sims.append(float(risco[idx].sum() / total))
        cap_rand = float(np.mean(sims))
        linhas.append({
            "limiar": lim,
            "n_celulas_alto_risco": n,
            "pct_grelha": round(100 * n / len(pts), 1),
            "captura_sad_pct": round(100 * cap_sad, 1),
            "captura_aleatorio_pct": round(100 * cap_rand, 1),
            "ganho_vs_aleatorio": round(cap_sad / max(cap_rand, 1e-6), 2),
        })
    return {"limiares": linhas, "referencia": 0.5}


def decomposicao_ganho(pts: list[dict]) -> dict:
    """Explica o ganho ~2×: concentração da massa de risco vs esforço de patrulha."""
    calcular_risco(pts, XLSX)
    risco = np.array([p["risco"] for p in pts])
    total = float(risco.sum())
    n = int((risco >= LIMIAR).sum())
    n = max(1, min(n, len(pts)))
    ordenado = np.sort(risco)[::-1]
    frac_celulas = n / len(pts)
    frac_risco_top_n = float(ordenado[:n].sum() / total)
    # Gini da distribuição de risco entre células
    x = np.sort(risco)
    n_c = len(x)
    gini = float((2 * np.arange(1, n_c + 1) - n_c - 1).dot(x) / (n_c * x.sum()))
    rng = np.random.default_rng(7)
    cap_rand = float(np.mean([
        float(risco[rng.choice(len(pts), size=n, replace=False)].sum() / total)
        for _ in range(500)
    ]))
    cap_sad = float(risco[np.argsort(-risco)[:n]].sum() / total)
    return {
        "n_celulas_patrulha": n,
        "frac_celulas_patrolhadas": round(frac_celulas, 4),
        "frac_risco_em_top_n": round(frac_risco_top_n, 4),
        "captura_sad": round(cap_sad, 4),
        "captura_aleatorio": round(cap_rand, 4),
        "ganho_observado": round(cap_sad / max(cap_rand, 1e-6), 2),
        "ganho_teorico_se_risco_uniforme": round(frac_risco_top_n / max(frac_celulas, 1e-6), 2),
        "indice_gini_risco": round(gini, 3),
        "interpretacao": (
            "O ganho reflecte sobretudo a concentração espacial do risco (Gini elevado): "
            "patrulhar as mesmas N células por ranking captura mais massa de risco que uma "
            "selecção aleatória com N células."
        ),
    }


def nota_mapas_risco(pts: list[dict]) -> dict:
    """Compara mapa operacional (todas as fontes) vs mapa de backtest (droga temporal ≤2022)."""
    calcular_risco(pts, XLSX)
    r_op = np.array([p["risco"] for p in pts])
    r_bt, _ = risco_com_droga_temporal(pts, ANO_CORTE)
    return {
        "n_alto_risco_operacional": int((r_op >= LIMIAR).sum()),
        "n_alto_risco_backtest_treino": int((r_bt >= LIMIAR).sum()),
        "limiar": LIMIAR,
        "nota": (
            "O mapa operacional usa todas as fontes e pesos AHP; o backtest treina droga "
            "e imigração até 2022 com pesca/poluição estáticas — daí diferença no n.º de "
            "células alto risco entre mapas operacional e de treino."
        ),
    }


def fig_sensibilidade_limiar(sens: dict):
    lims = sens["limiares"]
    fig, ax1 = plt.subplots(figsize=(7.2, 4.2))
    x = [f"{r['limiar']:.2f}".replace(".", ",") for r in lims]
    w = 0.35
    xpos = np.arange(len(lims))
    ax1.bar(xpos - w / 2, [r["n_celulas_alto_risco"] for r in lims], width=w,
            color="#8e44ad", label="Células alto risco", edgecolor="#333", linewidth=0.6)
    ax1.set_ylabel("N.º células alto risco")
    ax2 = ax1.twinx()
    ax2.plot(xpos, [r["ganho_vs_aleatorio"] for r in lims], "o-", color="#c0392b",
             linewidth=2, markersize=8, label="Ganho SAD vs aleatório")
    ax2.set_ylabel("Ganho vs patrulha aleatória (×)")
    ax1.set_xticks(xpos)
    ax1.set_xticklabels(x)
    ax1.set_xlabel("Limiar de alto risco")
    ax1.set_title("Sensibilidade do limiar de alto risco (±0,05)")
    lines1, lab1 = ax1.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, lab1 + lab2, loc="upper left", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "25_sensibilidade_limiar.png"), dpi=150)
    plt.close(fig)


def fig_backtest(bt: dict):
    if bt.get("n_holdout", 0) == 0:
        return
    fig, ax = plt.subplots(figsize=(7, 4.2))
    labels = ["SAD\n(top 20%)", "SAD\n(limiar 0,5)", "Aleatório\n(limiar)", "Referência\ntop 20%"]
    vals = [bt["taxa_acerto_top20"] * 100, bt["taxa_acerto_limiar"] * 100,
            bt["baseline_aleatorio_limiar"] * 100, bt["baseline_top20"] * 100]
    cores = ["#c0392b", "#e67e22", "#95a5a6", "#bdc3c7"]
    bars = ax.bar(labels, vals, color=cores, edgecolor="#333", linewidth=0.6)
    ax.set_ylabel("Taxa de acerto no holdout 2023–2024 (%)")
    ax.set_title("Backtesting temporal — apreensões marítimas previstas pelo SAD (treino ≤2022)")
    ax.set_ylim(0, max(vals) * 1.2 + 8)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1.5, f"{v:.1f}%",
                ha="center", fontsize=10, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "21_backtest_temporal.png"), dpi=150)
    plt.close(fig)


def fig_baseline(bl: dict):
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    labels = ["SAD\n(top-N risco)", "Aleatório\n(média 500×)", "Uniforme\ncosteiro"]
    vals = [bl["captura_sad"] * 100, bl["captura_aleatorio_media"] * 100,
            bl["captura_uniforme_costeira"] * 100]
    err = [0, bl["captura_aleatorio_std"] * 100, 0]
    cores = ["#2980b9", "#95a5a6", "#7f8c8d"]
    bars = ax.bar(labels, vals, yerr=err, capsize=4, color=cores, edgecolor="#333", linewidth=0.6)
    ax.set_ylabel("% do risco total capturado")
    ax.set_title(f"Baseline de patrulha — {bl['n_celulas_patrulha']} células patrulhadas")
    ax.set_ylim(0, max(vals) * 1.2 + 5)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 2, f"{v:.1f}%",
                ha="center", fontsize=10, fontweight="bold")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "22_baseline_patrulha.png"), dpi=150)
    plt.close(fig)


def validacao_intercecoes_documentadas(pts: list[dict]) -> dict:
    """Cruza eventos documentados (coordenadas reais) com o mapa de risco operacional."""
    if not os.path.exists(INTERC):
        return {"n_eventos": 0}
    calcular_risco(pts, XLSX)
    from geo import bases_proj
    bases = bases_proj()
    df = pd.read_csv(INTERC)
    linhas = []
    for _, row in df.iterrows():
        lon, lat = float(row["lon"]), float(row["lat"])
        idx = celula_mais_proxima(pts, lon, lat)
        p = pts[idx]
        # base mais próxima
        bx, by = proj(lon, lat)
        dist_b = [
            (b["nome"], ((b["x"] - bx) ** 2 + (b["y"] - by) ** 2) ** 0.5)
            for b in bases
        ]
        base_nom, _ = min(dist_b, key=lambda t: t[1])
        linhas.append({
            "ano": int(row["ano"]),
            "ameaca": str(row["ameaca"]),
            "lat": lat,
            "lon": lon,
            "fonte": str(row["fonte"]),
            "descricao": str(row["descricao"]),
            "risco_agregado": round(float(p["risco"]), 3),
            "r_droga": round(float(p.get("r_droga", 0)), 3),
            "r_imigracao": round(float(p.get("r_imigracao", 0)), 3),
            "alto_risco": bool(p["risco"] >= LIMIAR),
            "base_mais_proxima": base_nom,
        })
    n_alto = sum(1 for l in linhas if l["alto_risco"])
    return {
        "n_eventos": len(linhas),
        "taxa_zona_alto_risco": round(n_alto / len(linhas), 3) if linhas else 0.0,
        "eventos": linhas,
        "nota": "Coordenadas de fontes abertas ou relatórios oficiais; proxy marítimo quando aplicável.",
    }


def caixa_objetivo() -> dict:
    """Respostas explícitas às três questões operacionais."""
    res_path = os.path.join(OUTDIR, "resultados.json")
    if os.path.exists(res_path):
        with open(res_path, encoding="utf-8") as f:
            data = json.load(f)
        b = data.get("cenario_B") or data.get("cenarios", {}).get("B_alcance_AR5", {})
        fr_c = b.get("frota_persistencia_costeira", {})
        fr_t = b.get("frota_persistencia_total", {})
        mclp_k2 = next((r for r in data.get("frota_vs_k", []) if r.get("k") == 2), None)
        nomes_mclp = (mclp_k2 or {}).get("bases", ["Porto (Sá Carneiro)", "Portimão"])[:2]
        frac_mclp = round(float((mclp_k2 or {}).get("frac_risco", 1.0)), 4)
        frota_mclp_k2 = (mclp_k2 or {}).get("frota_total")
        sc90 = (data.get("cenarios", {}).get("A_conservador_vento", {})
                .get("calmo (4 m/s)", {}).get("set_cover", {}))
        bases_costeira = (data.get("cenarios", {}).get("A_conservador_vento", {})
                          .get("calmo (4 m/s)", {}).get("bases_nomes", []))
        bases_total = b.get("bases_recomendadas", [])
        return {
            "Q1_onde": {
                "resposta": "Sul/SW (Algarve), corredor Lisboa–Setúbal e NW/Peniche; "
                            "imigração reforçada no Algarve (desembarques PT); corredores AIS a O de Lisboa.",
                "zonas_patrulha": ["Algarve", "Setúbal–Lisboa", "NW/Peniche"],
            },
            "Q2_quantos": {
                "resposta": f"{fr_c.get('frota_total', 9)} AR5 faixa costeira (24 h); "
                            f"{fr_t.get('frota_total', 9)} AR5 área total de alto risco.",
                "frota_total": fr_t.get("frota_total", 9),
                "frota_costeira": fr_c.get("frota_total", 9),
                "n_simultaneos_costeira": fr_c.get("n_simultaneos", 3),
                "n_simultaneos_total": fr_t.get("n_simultaneos", 3),
                "bases_dimensionamento_costeira": bases_costeira,
                "bases_dimensionamento_total": bases_total,
                "nota": "A frota 9 AR5 assume bases distribuídas; com apenas Porto+Portimão (MCLP k=2) "
                        f"seriam necessários {frota_mclp_k2 or 10} AR5.",
            },
            "Q3_bases": {
                "resposta": f"MCLP (k=2): {', '.join(nomes_mclp)} — cobrem {frac_mclp*100:.0f} % "
                            f"do risco com o mínimo de instalações.",
                "bases_mclp": nomes_mclp,
                "frac_risco_mclp": frac_mclp,
                "frota_se_apenas_estas_bases": frota_mclp_k2,
                "nota": "Q3 responde à localização mínima (MCLP); Q2 usa rede costeira completa "
                        "para o dimensionamento de frota.",
            },
        }

    pts = gerar_procura()
    calcular_risco(pts, XLSX)
    from otimizacao import mclp, raio_por_autonomia, dimensionar_persistencia
    from config import CENARIOS_VENTO
    from geo import bases_proj

    bases = bases_proj()
    R = raio_por_autonomia(6.0, CENARIOS_VENTO["calmo"])
    rec = mclp(pts, bases, R, 2)
    pts_alto = [p for p in pts if p["risco"] >= LIMIAR]
    fr = dimensionar_persistencia(pts_alto, bases, rec["bases_sel"], 95.0)
    nomes = [bases[b]["nome"] for b in rec["bases_sel"]]

    return {
        "Q1_onde": {
            "resposta": "Sul/SW (Algarve, aproximações marítimas PT) e corredor Lisboa–Setúbal; "
                        "pesca no NW e ao largo de Peniche; tráfego AIS a O de Lisboa.",
            "zonas_patrulha": ["Algarve", "Setúbal–Lisboa", "NW/Peniche"],
        },
        "Q2_quantos": {
            "resposta": f"{fr['frota_total']} AR5 para vigilância persistente 24 h "
                        f"({fr['n_simultaneos']} simultâneos).",
            "frota_total": fr["frota_total"],
            "n_simultaneos": fr["n_simultaneos"],
        },
        "Q3_bases": {
            "resposta": f"{len(rec['bases_sel'])} bases: {', '.join(nomes)}.",
            "bases": nomes,
            "frac_risco": round(rec["frac_risco"], 4),
        },
    }


def main():
    os.makedirs(FIGDIR, exist_ok=True)
    os.makedirs(OUTDIR, exist_ok=True)
    print(">> Validação Fase C ...")
    pts = gerar_procura()

    print("   Backtesting temporal (droga 2011–2022 → teste 2023–2024) ...")
    bt = backtest_temporal(pts)
    print(f"      holdout n={bt.get('n_holdout')}  acerto limiar={bt.get('taxa_acerto_limiar',0)*100:.1f}%  "
          f"ganho vs aleatório={bt.get('ganho_relativo_limiar',0):.1f}×")

    print("   Baseline de patrulha (SAD vs aleatório vs uniforme) ...")
    bl = baseline_patrulha(pts)
    print(f"      SAD captura {bl['pct_risco_total_capturado_sad']:.1f}%  "
          f"ganho vs aleatório={bl['ganho_sad_vs_aleatorio']:.1f}×")

    obj = caixa_objetivo()
    iom = incidentes_iom_mapa()
    des = desembarques_pt_mapa()
    val_imig = validacao_imigracao(pts)
    val_imig_ho = validacao_imigracao_holdout(pts)
    bt_droga = backtest_somente_droga(pts)
    bt_comp = backtest_comparativo(pts)
    val_inter = validacao_intercecoes_documentadas(pts)
    sens = sensibilidade_limiar(pts)
    decomp = decomposicao_ganho(pts)
    nota_map = nota_mapas_risco(pts)
    apr = apreensoes_geocodificadas(ano_min=2020)
    apr_out = apr[["lat", "lon", "ano"]].to_dict(orient="records")

    out = {
        "backtest_temporal": bt,
        "backtest_comparativo": bt_comp,
        "backtest_somente_droga": bt_droga,
        "validacao_intercecoes_documentadas": val_inter,
        "baseline_patrulha": bl,
        "validacao_imigracao": val_imig,
        "validacao_imigracao_holdout": val_imig_ho,
        "sensibilidade_limiar": sens,
        "decomposicao_ganho": decomp,
        "nota_mapas_risco": nota_map,
        "resposta_objetivo": obj,
        "n_incidentes_iom": len(iom),
        "n_desembarques_pt": len(des),
        "n_apreensoes_maritimas_recentes": len(apr_out),
    }
    with open(os.path.join(OUTDIR, "validacao.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    with open(os.path.join(OUTDIR, "camadas_mapa.json"), "w", encoding="utf-8") as f:
        json.dump({"iom": iom, "desembarques_pt": des, "apreensoes": apr_out, "validacao": out}, f,
                  ensure_ascii=False, indent=2)

    fig_backtest(bt)
    fig_baseline(bl)
    fig_sensibilidade_limiar(sens)
    print(f"   Backtest rigoroso: acerto limiar="
          f"{bt_comp.get('modelo_multi_ameaca_rigoroso', {}).get('taxa_acerto_limiar', 0)*100:.1f}%")
    print(f"   Interceções documentadas: {val_inter.get('n_eventos')} eventos, "
          f"{val_inter.get('taxa_zona_alto_risco', 0)*100:.0f}% em alto risco")
    print(f"   Decomposição ganho: Gini={decomp['indice_gini_risco']:.3f}  "
          f"risco top-N={decomp['frac_risco_em_top_n']*100:.1f}%")
    print(f"   Imigração holdout: {val_imig_ho.get('taxa_acerto_holdout', 'N/A')} "
          f"(treino n={val_imig_ho.get('n_treino')}, teste n={val_imig_ho.get('n_teste')})")
    print(f"   Figuras: {FIGDIR}/21_backtest_temporal.png, 22_baseline_patrulha.png, "
          f"25_sensibilidade_limiar.png")
    print(f"   JSON: {OUTDIR}/validacao.json")
    return out


if __name__ == "__main__":
    main()
