"""
risco.py — Construção do índice de risco marítimo multi-ameaça por célula.

Cada ameaça é representada por um campo espacial de intensidade (0–1). Por defeito,
estas intensidades são derivadas de DADOS REAIS e abertos (ver
dm/construir_dados_reais.py): EMODnet vessel density para pesca e poluição, IOM
Missing Migrants para imigração e apreensões geocodificadas para droga. Caso o
ficheiro de intensidades reais não exista, recorre-se a campos-prior gaussianos
centrados em âncoras fundamentadas (fallback documentado). O risco final é a média
ponderada (PESOS_AMEACA) dos quatro campos, normalizada para [0, 1].
"""
from __future__ import annotations
import math
import os

import numpy as np
import pandas as pd

from config import PESOS_AMEACA
from geo import proj

# Caminho para as intensidades construídas a partir de dados reais (EMODnet + IOM +
# apreensões). Se existir, é usado em vez dos priors gaussianos.
_CSV_REAIS = os.path.join(os.path.dirname(__file__), "..", "dados",
                          "processados", "intensidades_reais.csv")


def _kernel(pts_xy: np.ndarray, ancora_xy: tuple[float, float],
            sigma_km: float, peso: float) -> np.ndarray:
    dx = pts_xy[:, 0] - ancora_xy[0]
    dy = pts_xy[:, 1] - ancora_xy[1]
    d2 = dx * dx + dy * dy
    return peso * np.exp(-d2 / (2.0 * sigma_km ** 2))


def _norm(v: np.ndarray) -> np.ndarray:
    m = v.max()
    return v / m if m > 0 else v


# ---------------------------------------------------------------------------
# Âncoras de droga a partir do Excel (apreensões marítimas por distrito costeiro)
# ---------------------------------------------------------------------------
# Localização costeira aproximada (lon, lat) de cada distrito litoral.
DISTRITO_COSTA = {
    "Faro": (-7.93, 36.97),
    "Setúbal": (-8.90, 38.47),
    "Lisboa": (-9.30, 38.70),
    "Porto": (-8.74, 41.20),
    "Leiria": (-9.05, 39.75),
    "Aveiro": (-8.75, 40.64),
    "Viana Do Castelo": (-8.80, 41.70),
    "Braga": (-8.78, 41.50),
}


def ancoras_droga(xlsx_path: str) -> list[tuple[tuple[float, float], float]]:
    """Devolve [(xy_proj, peso)] com base nas apreensões MARÍTIMAS por distrito."""
    df = pd.read_excel(xlsx_path)
    df["Distrito"] = df["Administrative Region"].apply(
        lambda x: x.split("/")[0].strip() if isinstance(x, str) and "/" in x else None)
    mar_loc = ["Territorial waters (seas, lakes, rivers, etc.)",
               "Seaport/Riverport station/Harbour", "International waters"]
    dmar = df[df["Physical Seizure Location"].isin(mar_loc) |
              (df["Trafficking Mode of Transportation"] == "Vessel/boat")]
    cont = dmar["Distrito"].value_counts()
    ancoras = []
    for distrito, (lon, lat) in DISTRITO_COSTA.items():
        n = int(cont.get(distrito, 0))
        if n > 0:
            ancoras.append((proj(lon, lat), float(n)))
    return ancoras


# ---------------------------------------------------------------------------
# Campos de intensidade por ameaça
# ---------------------------------------------------------------------------
def campo_droga(pts_xy: np.ndarray, xlsx_path: str) -> np.ndarray:
    f = np.zeros(len(pts_xy))
    # 1) focos costeiros (dados do Excel) — sigma curto (litoral)
    for xy, peso in ancoras_droga(xlsx_path):
        f += _kernel(pts_xy, xy, sigma_km=55.0, peso=peso)
    # 2) aproximações atlânticas da cocaína (S/SW) — MAOC-N, semissubmersíveis
    f += _kernel(pts_xy, proj(-9.5, 36.6), sigma_km=130.0, peso=80.0)   # SW atlântico (PT)
    return _norm(f)


def campo_pesca(pts_xy: np.ndarray, dist_costa: np.ndarray) -> np.ndarray:
    # Pesca INN: maior em pesqueiros ao largo (banda ~60–140 km) e viés a Norte.
    banda = np.exp(-((dist_costa - 95.0) ** 2) / (2.0 * 55.0 ** 2))
    f = np.zeros(len(pts_xy))
    f += _kernel(pts_xy, proj(-9.6, 41.0), sigma_km=160.0, peso=1.0)    # NW (pesqueiros)
    f += _kernel(pts_xy, proj(-9.3, 40.0), sigma_km=160.0, peso=0.8)
    f += _kernel(pts_xy, proj(-9.0, 37.2), sigma_km=150.0, peso=0.7)    # SW
    f = _norm(f) * (0.4 + 0.6 * banda)  # realça a banda ao largo
    return _norm(f)


def campo_poluicao(pts_xy: np.ndarray) -> np.ndarray:
    # Derrames: corredores de tráfego marítimo (TSS Cabo de São Vicente, sul PT,
    # aproximações a Lisboa/Sines). Concentração na região Sul (EMSA/MDPI).
    f = np.zeros(len(pts_xy))
    f += _kernel(pts_xy, proj(-9.3, 36.9), sigma_km=90.0, peso=1.0)   # TSS Cabo de São Vicente
    f += _kernel(pts_xy, proj(-8.5, 37.0), sigma_km=80.0, peso=0.9)   # aproximações Algarve (PT)
    f += _kernel(pts_xy, proj(-9.5, 38.6), sigma_km=70.0, peso=0.7)   # aprox. Lisboa
    f += _kernel(pts_xy, proj(-9.0, 37.95), sigma_km=60.0, peso=0.5)  # Sines
    return _norm(f)


def campo_imigracao(pts_xy: np.ndarray, dist_costa: np.ndarray) -> np.ndarray:
    # Imigração irregular: rota Atlântica/África Ocidental — aproximações a
    # Sul e Sudoeste, ao largo. Viés para sul e para offshore.
    f = np.zeros(len(pts_xy))
    f += _kernel(pts_xy, proj(-9.2, 36.6), sigma_km=140.0, peso=1.0)   # SW ao largo (PT)
    f += _kernel(pts_xy, proj(-8.3, 36.9), sigma_km=100.0, peso=0.8)   # sul Algarve ao largo (PT)
    offshore = np.clip(dist_costa / 200.0, 0, 1)
    f = _norm(f) * (0.5 + 0.5 * offshore)
    return _norm(f)


def _carregar_intensidades_reais(pts: list[dict]):
    """Carrega as intensidades por ameaça construídas a partir de dados reais (EMODnet
    vessel density para pesca e poluição, IOM Missing Migrants para imigração,
    apreensões geocodificadas para droga). Devolve None se o ficheiro não existir ou
    não corresponder à grelha atual."""
    if not os.path.exists(_CSV_REAIS):
        return None
    df = pd.read_csv(_CSV_REAIS)
    if len(df) != len(pts):
        return None
    # verificação de alinhamento da grelha (ordem determinística de gerar_procura)
    if (abs(df["lon"].iloc[0] - pts[0]["lon"]) > 1e-6 or
            abs(df["lat"].iloc[-1] - pts[-1]["lat"]) > 1e-6):
        return None
    return (df["r_droga"].to_numpy(), df["r_pesca"].to_numpy(),
            df["r_poluicao"].to_numpy(), df["r_imigracao"].to_numpy())


def calcular_risco(pts: list[dict], xlsx_path: str) -> np.ndarray:
    """Devolve vetor de risco [0,1] por ponto de procura e guarda os campos
    individuais em cada dict (chaves r_droga, r_pesca, r_poluicao, r_imigracao).

    Usa as intensidades de DADOS REAIS (dados/processados/intensidades_reais.csv) quando
    disponíveis; caso contrário, recorre aos campos-prior gaussianos (fallback)."""
    reais = _carregar_intensidades_reais(pts)
    if reais is not None:
        fd, fp, fo, fi = reais
    else:
        pts_xy = np.array([(p["x"], p["y"]) for p in pts])
        dist = np.array([p["dist_costa_km"] for p in pts])
        fd = campo_droga(pts_xy, xlsx_path)
        fp = campo_pesca(pts_xy, dist)
        fo = campo_poluicao(pts_xy)
        fi = campo_imigracao(pts_xy, dist)

    risco = (PESOS_AMEACA["droga"] * fd + PESOS_AMEACA["pesca"] * fp +
             PESOS_AMEACA["poluicao"] * fo + PESOS_AMEACA["imigracao"] * fi)
    risco = _norm(risco)

    for i, p in enumerate(pts):
        p["r_droga"] = float(fd[i])
        p["r_pesca"] = float(fp[i])
        p["r_poluicao"] = float(fo[i])
        p["r_imigracao"] = float(fi[i])
        p["risco"] = float(risco[i])
    return risco


if __name__ == "__main__":
    from geo import gerar_procura
    pts = gerar_procura()
    r = calcular_risco(pts, "../dados/fontes/apreensoes_droga_PT.xlsx")
    print("risco min/med/max:", r.min(), round(r.mean(), 3), r.max())
