"""
construir_dados_reais.py — Constrói as intensidades de risco por ameaça a partir de
FONTES DE DADOS REAIS e abertas, substituindo os priors gaussianos "calibrados à mão"
do modelo original.

Fontes (todas abertas e citáveis):
  • Pesca ilegal (INN)  → EMODnet vessel density (tipo 02) + anomalia pesca/AIS
    (esforço de pesca desproporcionado face ao tráfego geral na célula).
  • Poluição/derrames   → EMODnet *vessel density* de CARGA (10) + TANQUE (11): os
    corredores de tráfego mercante são o proxy físico do risco de derrame de
    hidrocarbonetos (EMSA CleanSeaNet aponta a mesma concentração).
  • Imigração irregular → IOM Missing Migrants Project (HDX, CC-BY 4.0): incidentes
    georreferenciados filtrados por `geo.zona_maritima_pt` (águas de Portugal Continental
    apenas, sem Espanha); KDE ponderado pelo n.º de vítimas.
  • Tráfico de droga    → 9 725 apreensões reais (UNODC/IDS), geocodificadas por
    distrito costeiro; KDE com peso temporal por evento (λ=0,15).

Saída: dados/processados/intensidades_reais.csv, com uma linha por célula da grelha de
procura (mesma ordem de geo.gerar_procura) e as colunas lon, lat, dist_costa_km,
r_droga, r_pesca, r_poluicao, r_imigracao (cada uma normalizada a [0, 1]).

Requer rasterio e pandas (apenas em tempo de construção). Execução:
    cd src && python -m dm.construir_dados_reais
"""
from __future__ import annotations
import os
import sys
import math
import numpy as np
import pandas as pd

from geo import gerar_procura, proj

BASE = os.path.join(os.path.dirname(__file__), "..", "..")
EMOD = os.path.join(BASE, "dados/fontes/emodnet")
IOM = os.path.join(BASE, "dados/fontes/iom_missing_migrants.csv")
IMIG_PT = os.path.join(BASE, "dados/fontes/imigracao_pt_costa.csv")
XLSX = os.path.join(BASE, "dados/fontes/apreensoes_droga_PT.xlsx")
OUTDIR = os.path.join(BASE, "dados/processados")
OUT = os.path.join(OUTDIR, "intensidades_reais.csv")

# distritos costeiros para geocodificar as apreensões de droga (lon, lat)
DISTRITO_COSTA = {
    "Faro": (-7.93, 36.97), "Setúbal": (-8.90, 38.47), "Lisboa": (-9.30, 38.70),
    "Porto": (-8.74, 41.20), "Leiria": (-9.05, 39.75), "Aveiro": (-8.75, 40.64),
    "Viana Do Castelo": (-8.80, 41.70), "Braga": (-8.78, 41.50),
}


def _norm(v: np.ndarray) -> np.ndarray:
    m = float(v.max())
    return v / m if m > 0 else v


def _norm_p(v: np.ndarray, p: float = 97.5) -> np.ndarray:
    """Normalização robusta por percentil: a densidade de tráfego tem alcance dinâmico
    enorme (o máximo é um único pixel de porto/rota). Escala pelo percentil p das células
    com sinal e satura em 1, preservando um gradiente informativo em toda a grelha."""
    pos = v[v > 0]
    ref = float(np.percentile(pos, p)) if pos.size else 0.0
    return np.clip(v / ref, 0.0, 1.0) if ref > 0 else v


def _lonlat_para_3857(lon, lat):
    R = 6378137.0
    x = np.radians(lon) * R
    y = np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)) * R
    return x, y


# ---------------------------------------------------------------------------
def amostrar_emodnet(pts, ficheiro):
    """Amostra o valor de densidade de embarcações (horas) em cada célula da grelha."""
    import rasterio
    ds = rasterio.open(os.path.join(EMOD, ficheiro))
    nod = ds.nodata
    xs, ys = _lonlat_para_3857(np.array([p["lon"] for p in pts]),
                               np.array([p["lat"] for p in pts]))
    vals = np.array([v[0] for v in ds.sample(list(zip(xs, ys)))], dtype=float)
    vals[~np.isfinite(vals)] = 0.0
    if nod is not None:
        vals[vals == nod] = 0.0
    vals[vals < 0] = 0.0
    return vals


def suavizar(pts, valores, sigma_km):
    """Suavização gaussiana sobre a grelha: um pesqueiro/corredor é uma ÁREA, não um
    pixel. Redistribui o sinal de cada célula pela vizinhança, convertendo bancos
    pontuais em zonas operacionalmente coerentes."""
    xy = np.array([(p["x"], p["y"]) for p in pts])
    out = np.zeros(len(pts))
    s2 = 2.0 * sigma_km ** 2
    for i in range(len(pts)):
        dx = xy[:, 0] - xy[i, 0]
        dy = xy[:, 1] - xy[i, 1]
        w = np.exp(-(dx * dx + dy * dy) / s2)
        out[i] = float(np.dot(w, valores) / w.sum())
    return out


def kde(pts_xy, fontes_xy, pesos, sigma_km):
    """Densidade gaussiana (KDE) das fontes pontuais avaliada nas células da grelha."""
    f = np.zeros(len(pts_xy))
    s2 = 2.0 * sigma_km ** 2
    for (fx, fy), w in zip(fontes_xy, pesos):
        dx = pts_xy[:, 0] - fx
        dy = pts_xy[:, 1] - fy
        f += w * np.exp(-(dx * dx + dy * dy) / s2)
    return f


# ---------------------------------------------------------------------------
def campo_imigracao_iom(pts):
    """KDE dos incidentes IOM em águas marítimas operacionais de PT continental."""
    if not os.path.exists(IOM):
        return np.zeros(len(pts)), 0
    df = pd.read_csv(IOM)

    def parse(c):
        try:
            a, b = str(c).split(",")
            return float(a), float(b)
        except Exception:
            return np.nan, np.nan

    lat, lon = zip(*df["location_coodinates"].map(parse))
    df["lat"], df["lon"] = lat, lon
    df = df.dropna(subset=["lat", "lon"])
    from geo import zona_maritima_pt, ponto_em_mar
    # Apenas incidentes em águas (exclui centros de detenção em terra, ex. Lisboa)
    box = df[df.apply(lambda r: zona_maritima_pt(r["lon"], r["lat"]) and ponto_em_mar(r["lon"], r["lat"]), axis=1)].copy()
    if box.empty:
        return np.zeros(len(pts)), 0
    peso = pd.to_numeric(box["total_dead_and_missing"], errors="coerce").fillna(1.0).clip(lower=1.0).to_numpy()
    fontes_xy = [proj(lo, la) for lo, la in zip(box["lon"], box["lat"])]
    pts_xy = np.array([(p["x"], p["y"]) for p in pts])
    f = kde(pts_xy, fontes_xy, peso, sigma_km=70.0)
    return _norm(f), len(box)


def campo_imigracao_pt_costa(pts):
    """KDE de desembarques marítimos documentados (SEF/ACM, Frontex, CP) — PT continental."""
    if not os.path.exists(IMIG_PT):
        return np.zeros(len(pts)), 0
    df = pd.read_csv(IMIG_PT)
    from geo import zona_maritima_pt
    df = df[df.apply(lambda r: zona_maritima_pt(r["lon"], r["lat"]), axis=1)]
    if df.empty:
        return np.zeros(len(pts)), 0
    peso = pd.to_numeric(df["n_pessoas"], errors="coerce").fillna(1.0).clip(lower=1.0).to_numpy()
    fontes_xy = [proj(lo, la) for lo, la in zip(df["lon"], df["lat"])]
    pts_xy = np.array([(p["x"], p["y"]) for p in pts])
    f = kde(pts_xy, fontes_xy, peso, sigma_km=55.0)
    return _norm(f), len(df)


def campo_imigracao_combinado(pts):
    """IOM marítimo + desembarques PT costa (70/30) — âmbito Portugal continental."""
    f_iom, n_iom = campo_imigracao_iom(pts)
    f_pt, n_pt = campo_imigracao_pt_costa(pts)
    if n_iom == 0 and n_pt == 0:
        return np.zeros(len(pts)), 0, 0
    if n_iom == 0:
        return f_pt, 0, n_pt
    if n_pt == 0:
        return f_iom, n_iom, 0
    comb = _norm(0.30 * f_iom + 0.70 * f_pt)
    return comb, n_iom, n_pt


DECAY_DROGA = 0.15   # peso temporal exp(-λ·anos) — reforça apreensões recentes
ANO_REF_DROGA = 2024


def _apreensoes_maritimas(df: pd.DataFrame) -> pd.DataFrame:
    mar = ["Territorial waters (seas, lakes, rivers, etc.)",
           "Seaport/Riverport station/Harbour", "International waters"]
    return df[df["Physical Seizure Location"].isin(mar) |
              (df["Trafficking Mode of Transportation"] == "Vessel/boat")].copy()


def campo_droga(pts, ano_max: int | None = None, atlantico: bool = True):
    """KDE das apreensões marítimas com peso temporal por evento (dados reais)."""
    df = pd.read_excel(XLSX)
    df = df.dropna(subset=["Seizure Date"])
    df["ano"] = pd.to_datetime(df["Seizure Date"]).dt.year.astype(int)
    dmar = _apreensoes_maritimas(df)
    if ano_max is not None:
        dmar = dmar[dmar["ano"] <= ano_max]
    dmar["Distrito"] = dmar["Administrative Region"].apply(
        lambda x: x.split("/")[0].strip() if isinstance(x, str) and "/" in x else None)
    ref = ano_max if ano_max is not None else ANO_REF_DROGA
    fontes_xy, pesos = [], []
    for _, row in dmar.iterrows():
        dist = row["Distrito"]
        if dist not in DISTRITO_COSTA:
            continue
        lon, lat = DISTRITO_COSTA[dist]
        w = math.exp(-DECAY_DROGA * (ref - int(row["ano"])))
        fontes_xy.append(proj(lon, lat))
        pesos.append(w)
    pts_xy = np.array([(p["x"], p["y"]) for p in pts])
    f = kde(pts_xy, fontes_xy, pesos, sigma_km=55.0) if pesos else np.zeros(len(pts))
    if atlantico:
        # aproximação atlântica SW (cocaína — MAOC-N), apenas em águas a oeste de Cabo de S. Vicente
        f += kde(pts_xy, [proj(-9.5, 36.6)], [f.max() * 0.9 if f.max() > 0 else 1.0], 130.0)
    return _norm(f), int(len(dmar))


# ---------------------------------------------------------------------------
def main():
    print(">> Grelha de procura ...")
    pts = gerar_procura()
    print(f"   {len(pts)} células")

    print(">> Pesca (EMODnet fishing + anomalia pesca/AIS — proxy INN) ...")
    fish_raw = amostrar_emodnet(pts, "vesseldensity_02_fishing.tif")
    all_raw = amostrar_emodnet(pts, "vesseldensity_all_ais.tif")
    fish_sm = suavizar(pts, np.log1p(fish_raw), sigma_km=22.0)
    all_sm = suavizar(pts, np.log1p(all_raw), sigma_km=18.0)
    anomalia = _norm_p(fish_sm / (all_sm + 1e-6), p=95.0)
    pesca_base = _norm_p(fish_sm, p=95.0)
    pesca = _norm(0.75 * pesca_base + 0.25 * anomalia)

    print(">> Poluição (EMODnet — cargo + tanker) ...")
    cargo = amostrar_emodnet(pts, "vesseldensity_10_cargo.tif")
    tanker = amostrar_emodnet(pts, "vesseldensity_11_tanker.tif")
    poluicao = suavizar(pts, np.log1p(cargo + tanker), sigma_km=15.0)
    poluicao = _norm_p(poluicao, p=97.0)

    print(">> Imigração (IOM marítimo + desembarques PT costa — KDE) ...")
    imig, n_iom, n_pt = campo_imigracao_combinado(pts)
    print(f"   {n_iom} incidentes IOM em mar + {n_pt} eventos SEF/Frontex/CP (PT continental)")

    print(">> Droga (apreensões marítimas reais — KDE) ...")
    droga, n_mar = campo_droga(pts)
    print(f"   {n_mar} apreensões marítimas")

    print(">> AIS — densidade global de embarcações (EMODnet) ...")
    ais_emb = amostrar_emodnet(pts, "vesseldensity_all_ais.tif")
    ais_emb = _norm_p(np.log1p(suavizar(pts, np.log1p(ais_emb), sigma_km=18.0)), p=97.0)

    print(">> AIS — densidade de rotas marítimas (EMODnet) ...")
    ais_rot = amostrar_emodnet(pts, "routedensity_all_ais.tif")
    ais_rot = _norm_p(np.log1p(suavizar(pts, np.log1p(ais_rot), sigma_km=20.0)), p=97.0)

    os.makedirs(OUTDIR, exist_ok=True)
    out = pd.DataFrame({
        "lon": [p["lon"] for p in pts], "lat": [p["lat"] for p in pts],
        "dist_costa_km": [p["dist_costa_km"] for p in pts],
        "r_droga": np.round(droga, 5), "r_pesca": np.round(pesca, 5),
        "r_poluicao": np.round(poluicao, 5), "r_imigracao": np.round(imig, 5),
        "ais_embarcacoes": np.round(ais_emb, 5), "ais_rotas": np.round(ais_rot, 5)})
    out.to_csv(OUT, index=False)
    print(f"\nGuardado: {os.path.abspath(OUT)}  ({len(out)} linhas)")
    for c in ["r_droga", "r_pesca", "r_poluicao", "r_imigracao", "ais_embarcacoes", "ais_rotas"]:
        print(f"   {c}: méd {out[c].mean():.3f}  máx {out[c].max():.3f}  "
              f">0.5: {(out[c] >= 0.5).sum()} células")


if __name__ == "__main__":
    main()
