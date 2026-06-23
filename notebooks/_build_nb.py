#!/usr/bin/env python3
"""Gera notebooks/analise_sad_ar5.ipynb no estilo de trabalho2.ipynb."""
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).parent / "analise_sad_ar5.ipynb"


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": text.splitlines(keepends=True)}


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "metadata": {},
        "source": text.splitlines(keepends=True),
        "outputs": [],
        "execution_count": None,
    }


cells: list[dict] = []

cells.append(md("""# Projeto Final — SAD AR5 Vigilância Costeira

**CT302 · Sistemas de Apoio à Decisão · Grupo VI · Escola Naval**

Pipeline analítico completo: apreensões UNODC → AHP → risco multi-ameaça → otimização (set cover / MCLP) → validação → respostas operacionais Q1–Q3.

| Secção | Conteúdo |
|--------|----------|
| 0 | Setup, imports e caminhos |
| 1 | Análise descritiva (EDA) das apreensões |
| 2 | Pesos AHP das ameaças |
| 3 | Grelha marítima e índice de risco |
| 4 | Otimização — cobertura, MCLP, frota 24 h |
| 5 | Validação — backtest temporal e baseline |
| 6 | Respostas SAD e exportação |

> **Colab:** faz upload da pasta `dados/` (ou do ZIP do repositório) e corre *Runtime → Run all*.
"""))

cells.append(md("## 0. Setup — instalação e imports"))
cells.append(code("""# Descomente no Colab ou na 1.ª execução local:
# !pip install -q numpy pandas matplotlib seaborn openpyxl pulp scikit-learn shapely

import csv
import json
import math
import os
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pulp
import seaborn as sns
from shapely.geometry import LineString, Point, Polygon

warnings.filterwarnings("ignore")
plt.rcParams["figure.figsize"] = (10, 5)
sns.set_style("whitegrid")
RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)

print("Setup concluído.")
"""))

cells.append(md("## 0.1 Caminhos dos dados"))
cells.append(code("""# --- Local vs Colab ---
try:
    from google.colab import files
    print("Modo Colab: faz upload de apreensoes_droga_PT.xlsx")
    uploaded = files.upload()
    XLSX_PATH = list(uploaded.keys())[0]
    REPO = Path.cwd()
    FIGDIR = REPO / "figuras"
    OUTDIR = REPO
except ImportError:
  XLSX_PATH = None
  REPO = Path.cwd()
  if (REPO / "src" / "config.py").exists():
      pass
  elif (REPO.parent / "src" / "config.py").exists():
      REPO = REPO.parent
  else:
      REPO = Path("/Users/miguelgaspar/Downloads/sad-ar5-vigilancia-costeira-clone")
  XLSX_PATH = XLSX_PATH or str(REPO / "dados/fontes/apreensoes_droga_PT.xlsx")
  CSV_INT = REPO / "dados/processados/intensidades_reais.csv"
  FIGDIR = REPO / "resultados/figuras"
  OUTDIR = REPO / "resultados"
  SRC = REPO / "src"
  sys.path.insert(0, str(SRC))
  os.chdir(SRC)

FIGDIR.mkdir(parents=True, exist_ok=True)
LIMIAR = 0.5
ANO_CORTE = 2022

if not Path(XLSX_PATH).exists():
    raise FileNotFoundError(f"Ficheiro não encontrado: {XLSX_PATH}")

print("XLSX:", XLSX_PATH)
print("FIGDIR:", FIGDIR)
"""))

# --- SECTION 1 EDA ---
cells.append(md("## 1. Análise descritiva (EDA)"))
cells.append(md("### 1.1 Carregamento e limpeza dos dados"))
cells.append(code("""# Geocodificação (tokens → coordenadas)
from dm.geocode import geocode, is_ilha, is_costeiro

LOC_MARITIMO = [
    "Territorial waters (seas, lakes, rivers, etc.)",
    "Seaport/Riverport station/Harbour", "International waters",
]
GRUPO_DROGA = {
    "Cannabis": ["Cannabis resin (hashish)", "Cannabis herb (marijuana)", "Cannabis plants",
                 "Cannabis seeds", "Cannabis oil", "Other cannabis-type (excluding synthetic cannabinoids)",
                 "Non-specified cannabis-type (excluding synthetic cannabinoids)", "Other synthetic cannabinoids (spice)"],
    "Cocaina": ["Cocaine hydrochloride (HCl, powder cocaine)", "Non-specified cocaine-type",
                "Crack cocaine", "Coca leaf"],
    "Opioides": ["Heroin", "Opium", "Methadone", "Subutex (buprenorphine)", "Codeine", "Poppy plants"],
    "Estimulantes": ["MDMA", "MDA", "Amphetamine", "Methamphetamine", "Non-specified ecstasy-type substances",
                     "Mephedrone (4-methylmethcathinone, 4-MMC)", "2C-B (4-bromo-2,5-dimethoxyphenethylamine)",
                     "Non-specified Synthetic cathinones", "4-Chloromethcathinone (4-CMC, Clephedrone)", "Other NPS"],
    "Alucinogenios": ["LSD", "Dimethyltryptamine (DMT)", "Psilocybin", "Non-specified hallucinogens", "Other hallucinogens"],
    "Medicamentos": ["Clonazepam (Rivotril)", "Alprazolam (Xanax, Pranax, Ksalol)", "Benzodiazepines",
                     "GHB", "Lorazepam (Ativan, Temesta)", "Diazepam"],
    "Outras": ["Khat", "Other-miscellaneous"],
}
_SUB2GRUPO = {s: g for g, subs in GRUPO_DROGA.items() for s in subs}
FIX_TOKEN = {"Lisba": "Lisboa", "Portio": "Porto", "Setubal": "Setúbal", "Leira": "Leiria"}
ESTACAO = {12:"Inverno",1:"Inverno",2:"Inverno",3:"Primavera",4:"Primavera",5:"Primavera",
           6:"Verão",7:"Verão",8:"Verão",9:"Outono",10:"Outono",11:"Outono"}

def _token(x):
    if isinstance(x, str):
        t = x.split("/")[0].strip() if "/" in x else x.strip()
        return FIX_TOKEN.get(t, t)
    return None

def _regiao_por_lat(lat):
    if lat is None: return None
    if lat >= 40.0: return "N"
    if lat >= 38.0: return "C"
    return "S"

df_raw = pd.read_excel(XLSX_PATH)
n0 = len(df_raw)
df = df_raw.dropna(subset=["Seizure Date", "Drug/Substance", "Quantity Seized"]).copy()
df["Seizure Date"] = pd.to_datetime(df["Seizure Date"], errors="coerce")
df = df.dropna(subset=["Seizure Date"])
df["ano"] = df["Seizure Date"].dt.year
df["mes"] = df["Seizure Date"].dt.month
df["estacao"] = df["mes"].map(ESTACAO)
df["token"] = df["Administrative Region"].apply(_token)
coords = df["token"].apply(lambda t: geocode(t) if t else None)
df["lat"] = coords.apply(lambda c: c[0] if c else np.nan)
df["lon"] = coords.apply(lambda c: c[1] if c else np.nan)
df["regiao"] = df["lat"].apply(_regiao_por_lat)
unidade = df["Measurement Unit"].astype(str)
qty = pd.to_numeric(df["Quantity Seized"], errors="coerce")
df["qty_g"] = np.where(unidade=="kg", qty*1000, np.where(unidade=="g", qty, np.nan))
df["log_qty_g"] = np.log1p(df["qty_g"])
df["grupo_droga"] = df["Drug/Substance"].map(_SUB2GRUPO).fillna("Outras")
df["maritimo"] = ((df["Physical Seizure Location"].isin(LOC_MARITIMO)) |
                  (df["Trafficking Mode of Transportation"]=="Vessel/boat")).astype(int)

print(f"Linhas: {n0} -> {len(df)} | Marítimas: {df['maritimo'].sum()} ({100*df['maritimo'].mean():.2f}%)")
df.head()
"""))

cells.append(md("### 1.2 Tipos de dados e estatísticas"))
cells.append(code("""print("Dimensões:", df.shape)
print("\\nTipos:")
print(df.dtypes)
print("\\nEstatísticas numéricas:")
display(df[["ano","mes","qty_g","log_qty_g","maritimo"]].describe())
print("\\nGrupos de droga:")
print(df["grupo_droga"].value_counts())
"""))

cells.append(md("### 1.3 Distribuição temporal e por grupo"))
cells.append(code("""fig, axes = plt.subplots(2, 2, figsize=(13, 10))
serie = df.groupby("ano").size()
axes[0,0].plot(serie.index, serie.values, "-o", color="#1f77b4")
axes[0,0].set_title("(a) Apreensões por ano")
axes[0,0].set_xlabel("Ano"); axes[0,0].set_ylabel("Nº apreensões")
g = df["grupo_droga"].value_counts()
sns.barplot(x=g.values, y=g.index, ax=axes[0,1], hue=g.index, legend=False, palette="viridis")
axes[0,1].set_title("(b) Por grupo de droga")
axes[1,0].hist(df["log_qty_g"].dropna(), bins=40, color="#2ca02c", alpha=0.8)
axes[1,0].set_title("(c) Histograma log(1+g)")
mar = df.groupby("grupo_droga")["maritimo"].mean().sort_values(ascending=False)*100
sns.barplot(x=mar.values, y=mar.index, ax=axes[1,1], hue=mar.index, legend=False, palette="rocket")
axes[1,1].set_title("(d) % marítimas por grupo")
fig.suptitle("EDA — apreensões Portugal 2011–2024", fontsize=14)
fig.tight_layout(); plt.show()
"""))

cells.append(md("### 1.4 Boxplots e região N/C/S"))
cells.append(code("""fig, axes = plt.subplots(1, 2, figsize=(14, 5))
sns.boxplot(data=df, x="grupo_droga", y="log_qty_g", ax=axes[0], hue="grupo_droga", legend=False, palette="Set2")
axes[0].set_title("Quantidade por grupo"); axes[0].tick_params(axis="x", rotation=30)
cont = df[df["regiao"].notna()]
sns.countplot(data=cont, x="regiao", hue="maritimo", ax=axes[1], order=["N","C","S"])
axes[1].set_title("Apreensões por região e tipo marítimo")
fig.tight_layout(); plt.show()
"""))

# --- SECTION 2 AHP ---
cells.append(md("## 2. Pesos AHP (Processo de Hierarquia Analítica)"))
cells.append(md("### 2.1 Matriz de comparação par a par (Saaty)"))
cells.append(code("""NOMES = ["droga", "pesca", "poluicao", "imigracao"]
LABELS = ["Tráfico droga", "Pesca INN", "Poluição", "Imigração"]
MATRIZ = np.array([
    [1,   3/2, 2,   2  ],
    [2/3, 1,   5/4, 5/4],
    [1/2, 4/5, 1,   1  ],
    [1/2, 4/5, 1,   1  ],
], dtype=float)
display(pd.DataFrame(MATRIZ, index=LABELS, columns=LABELS).round(3))
"""))

cells.append(md("### 2.2 Cálculo do autovetor e razão de consistência (CR)"))
cells.append(code("""n = MATRIZ.shape[0]
w_vals = np.linalg.eigvals(MATRIZ).real
lam_max = float(w_vals.max())
ci = (lam_max - n) / max(n - 1, 1)
ri = {1:0.0, 2:0.0, 3:0.58, 4:0.90, 5:1.12}.get(n, 1.12)
cr = ci / ri if ri > 0 else 0.0
vec = np.linalg.eig(MATRIZ)[1][:, np.argmax(w_vals)].real
vec = np.abs(vec) / vec.sum()
pesos_ahp = {n: round(float(v), 4) for n, v in zip(NOMES, vec)}
s = sum(pesos_ahp.values())
pesos_ahp = {k: round(v/s, 4) for k, v in pesos_ahp.items()}

PESOS_AMEACA = {"droga": 0.35, "pesca": 0.25, "poluicao": 0.20, "imigracao": 0.20}
print(f"λ_max={lam_max:.4f}  CI={ci:.4f}  CR={cr:.4f}  (<0.10 → consistente)")
pd.DataFrame({"Ameaça": NOMES, "Peso AHP": [pesos_ahp[k] for k in NOMES],
              "Peso adoptado": [PESOS_AMEACA[k] for k in NOMES]})
"""))

cells.append(md("### 2.3 Visualização dos pesos"))
cells.append(code("""fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
vals = [PESOS_AMEACA[k] for k in NOMES]
axes[0].barh(LABELS, vals, color=["#c0392b","#27ae60","#8e44ad","#2980b9"])
axes[0].set_xlim(0, 0.45); axes[0].set_xlabel("Peso"); axes[0].set_title(f"Pesos AHP — CR={cr:.3f}")
for i,v in enumerate(vals): axes[0].text(v+0.01, i, f"{v:.2f}", va="center")
im = axes[1].imshow(MATRIZ, cmap="Blues", vmin=0.5, vmax=3)
axes[1].set_xticks(range(4), LABELS, rotation=25, ha="right", fontsize=8)
axes[1].set_yticks(range(4), LABELS, fontsize=8)
axes[1].set_title("Matriz Saaty")
for i in range(4):
    for j in range(4):
        axes[1].text(j, i, f"{MATRIZ[i,j]:.2f}", ha="center", va="center", fontsize=7)
fig.tight_layout(); plt.show()
fig.savefig(FIGDIR/"24_ahp_pesos.png", dpi=150, bbox_inches="tight")
"""))

# --- SECTION 3 GRID + RISK ---
cells.append(md("## 3. Grelha marítima e índice de risco"))
cells.append(md("### 3.1 Parâmetros AR5 e projeção métrica"))
cells.append(code("""from config import AR5, AERODROMOS, CENARIOS_VENTO, RAIO_BASE_KM, RESERVA_H
from config import DISPONIBILIDADE, RESERVA_FROTA, SENSOR_SWATH_KM, TEMPO_REVISITA_H, T_ON_MIN_H, fator_vento

LAT0 = 39.5
_KX = 111.320 * math.cos(math.radians(LAT0))
_KY = 110.574
LON_MIN, LON_MAX = -11.0, -7.38
LAT_MIN, LAT_MAX = 36.85, 42.20
COSTA_LONLAT = [
    (-8.880,41.870),(-8.780,41.690),(-8.780,41.450),(-8.740,41.250),(-8.680,41.000),
    (-8.745,40.640),(-8.860,40.150),(-8.930,39.600),(-9.080,39.360),(-9.420,38.780),
    (-9.480,38.690),(-9.230,38.660),(-8.930,38.470),(-8.820,38.100),(-8.880,37.950),
    (-8.800,37.730),(-8.990,37.030),(-8.930,37.010),(-8.660,37.090),(-8.540,37.100),
    (-8.270,37.090),(-7.930,36.970),(-7.520,37.160),(-7.400,37.180),
]

def proj(lon, lat): return lon*_KX, lat*_KY
def inv_proj(x, y): return x/_KX, y/_KY

def costa_linestring():
    return LineString([proj(lon, lat) for lon, lat in COSTA_LONLAT])

def terra_polygon():
    pts = [proj(lon, lat) for lon, lat in COSTA_LONLAT]
    pts += [proj(COSTA_LONLAT[0][0],42.25), proj(-6.0,42.25), proj(-6.0,37.0), proj(COSTA_LONLAT[-1][0], COSTA_LONLAT[-1][1])]
    return Polygon(pts)

print("AR5 autonomia:", AR5["autonomia_h"], "h | velocidade:", AR5["velocidade_cruzeiro_kmh"], "km/h")
"""))

cells.append(md("### 3.2 Geração da grelha de procura (células marítimas)"))
cells.append(code("""costa = costa_linestring()
terra = terra_polygon()
passo = 0.10
pts = []
for lon in np.arange(LON_MIN, LON_MAX+passo/2, passo):
    for lat in np.arange(LAT_MIN, LAT_MAX+passo/2, passo):
        if not (LON_MIN <= lon <= LON_MAX and LAT_MIN <= lat <= LAT_MAX):
            continue
        x, y = proj(lon, lat)
        p = Point(x, y)
        if terra.contains(p):
            continue
        d = p.distance(costa)
        if 8.0 <= d <= 300.0:
            pts.append({"lon":float(lon),"lat":float(lat),"x":x,"y":y,"dist_costa_km":float(d)})

bases = []
for nome, lon, lat, reg in AERODROMOS:
    x, y = proj(lon, lat)
    bases.append({"nome":nome,"lon":lon,"lat":lat,"regiao":reg,"x":x,"y":y})

print(f"Células marítimas: {len(pts)} | Bases candidatas: {len(bases)}")
"""))

cells.append(md("### 3.3 Intensidades por ameaça e índice agregado"))
cells.append(code("""def _norm(v):
    m = v.max()
    return v / m if m > 0 else v

# Carregar intensidades reais (EMODnet + IOM + apreensões) se existirem
if Path(CSV_INT).exists():
    dfi = pd.read_csv(CSV_INT)
    assert len(dfi) == len(pts), "Regenerar intensidades_reais.csv"
    fd = dfi["r_droga"].to_numpy()
    fp = dfi["r_pesca"].to_numpy()
    fo = dfi["r_poluicao"].to_numpy()
    fi = dfi["r_imigracao"].to_numpy()
    print("Fonte: intensidades_reais.csv (dados reais)")
else:
    from risco import campo_droga, campo_pesca, campo_poluicao, campo_imigracao
    pts_xy = np.array([(p["x"], p["y"]) for p in pts])
    dist = np.array([p["dist_costa_km"] for p in pts])
    fd = campo_droga(pts_xy, XLSX_PATH)
    fp = campo_pesca(pts_xy, dist)
    fo = campo_poluicao(pts_xy)
    fi = campo_imigracao(pts_xy, dist)
    print("Fonte: campos gaussianos (fallback)")

risco = PESOS_AMEACA["droga"]*fd + PESOS_AMEACA["pesca"]*fp + PESOS_AMEACA["poluicao"]*fo + PESOS_AMEACA["imigracao"]*fi
risco = _norm(risco)
for i, p in enumerate(pts):
    p["r_droga"], p["r_pesca"] = float(fd[i]), float(fp[i])
    p["r_poluicao"], p["r_imigracao"] = float(fo[i]), float(fi[i])
    p["risco"] = float(risco[i])

r = np.array([p["risco"] for p in pts])
print(f"Risco médio={r.mean():.3f} | máx={r.max():.3f} | alto risco (≥{LIMIAR})={(r>=LIMIAR).sum()} células")
"""))

cells.append(md("### 3.4 Estatísticas por ameaça"))
cells.append(code("""rows = []
for a in NOMES:
    v = np.array([p[f"r_{a}"] for p in pts])
    rows.append({"ameaça":a,"peso":PESOS_AMEACA[a],"média":round(v.mean(),3),
                 "máx":round(v.max(),3),"p90":round(np.percentile(v,90),3)})
display(pd.DataFrame(rows))
"""))

cells.append(md("### 3.5 Mapa de risco agregado (Fig. 01)"))
cells.append(code("""COSTA_LON = [c[0] for c in COSTA_LONLAT]; COSTA_LAT = [c[1] for c in COSTA_LONLAT]
lon = [p["lon"] for p in pts]; lat = [p["lat"] for p in pts]; rv = [p["risco"] for p in pts]

fig, ax = plt.subplots(figsize=(7, 8))
sc = ax.scatter(lon, lat, c=rv, cmap="YlOrRd", s=14, marker="s", vmin=0, vmax=1)
for nome, blon, blat, reg in AERODROMOS:
    ax.plot(blon, blat, "^", color="navy", ms=8)
ax.plot(COSTA_LON, COSTA_LAT, color="#444", lw=1.5)
ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX)
ax.set_aspect(1.0/np.cos(np.radians(39.5)))
plt.colorbar(sc, ax=ax, label="Risco [0–1]", shrink=0.7)
ax.set_title("Fig. 01 — Índice de risco marítimo multi-ameaça")
fig.tight_layout(); plt.show()
fig.savefig(FIGDIR/"01_risco.png", dpi=140)
"""))

cells.append(md("### 3.6 Campos por ameaça (Fig. 02)"))
cells.append(code("""campos = [("r_droga","Tráfico droga","Reds"),("r_pesca","Pesca INN","Greens"),
          ("r_poluicao","Poluição","Purples"),("r_imigracao","Imigração","Blues")]
fig, axes = plt.subplots(2, 2, figsize=(11, 12))
for (ch, tit, cmap), ax in zip(campos, axes.ravel()):
    v = [p[ch] for p in pts]
    sc = ax.scatter(lon, lat, c=v, cmap=cmap, s=8, marker="s", vmin=0, vmax=1)
    ax.plot(COSTA_LON, COSTA_LAT, color="#444", lw=1)
    ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.set_aspect(1.0/np.cos(np.radians(39.5)))
    ax.set_title(f"{tit} (peso {PESOS_AMEACA[ch.split('_')[1]]:.2f})")
    plt.colorbar(sc, ax=ax, shrink=0.7)
fig.suptitle("Fig. 02 — Campos de intensidade por ameaça", fontsize=14)
fig.tight_layout(); plt.show()
fig.savefig(FIGDIR/"02_ameacas.png", dpi=140)
"""))

# --- SECTION 4 OPTIMIZATION ---
cells.append(md("## 4. Otimização — set cover, MCLP e frota"))
cells.append(md("### 4.1 Matriz de cobertura e set cover (PuLP)"))
cells.append(code("""def matriz_cobertura(pts, bases, raio_km):
    B, P = len(bases), len(pts)
    bx = np.array([b["x"] for b in bases]); by = np.array([b["y"] for b in bases])
    px = np.array([p["x"] for p in pts]); py = np.array([p["y"] for p in pts])
    a = np.zeros((B, P), dtype=np.int8)
    for b in range(B):
        d = np.sqrt((px-bx[b])**2 + (py-by[b])**2)
        a[b] = (d <= raio_km).astype(np.int8)
    return a

def set_cover(pts, bases, raio_km, limiar_risco=0.5):
    a = matriz_cobertura(pts, bases, raio_km)
    alvo = [i for i,p in enumerate(pts) if p["risco"] >= limiar_risco]
    cobrivel = [i for i in alvo if a[:,i].sum() > 0]
    prob = pulp.LpProblem("set_cover", pulp.LpMinimize)
    y = [pulp.LpVariable(f"y_{b}", cat="Binary") for b in range(len(bases))]
    prob += pulp.lpSum(y)
    for i in cobrivel:
        prob += pulp.lpSum(y[b] for b in range(len(bases)) if a[b,i]) >= 1
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    sel = [b for b in range(len(bases)) if y[b].value() and y[b].value() > 0.5]
    return {"bases_sel":sel,"n_bases":len(sel),"n_nao_cobrivel":len(alvo)-len(cobrivel)}

def raio_efetivo(vento_ms):
    return RAIO_BASE_KM * fator_vento(vento_ms)

R_calmo = raio_efetivo(CENARIOS_VENTO["calmo"])
sc_calmo = set_cover(pts, bases, R_calmo, LIMIAR)
print(f"Set cover R={R_calmo:.0f} km → {sc_calmo['n_bases']} bases | fora alcance: {sc_calmo['n_nao_cobrivel']}")
print("Bases:", ", ".join(bases[b]["nome"] for b in sc_calmo["bases_sel"]))
"""))

cells.append(md("### 4.2 MCLP — maximizar risco coberto com k bases"))
cells.append(code("""def mclp(pts, bases, raio_km, k):
    a = matriz_cobertura(pts, bases, raio_km)
    risco_v = np.array([p["risco"] for p in pts])
    prob = pulp.LpProblem("mclp", pulp.LpMaximize)
    y = [pulp.LpVariable(f"y_{b}", cat="Binary") for b in range(len(bases))]
    z = [pulp.LpVariable(f"z_{i}", lowBound=0, upBound=1) for i in range(len(pts))]
    prob += pulp.lpSum(risco_v[i]*z[i] for i in range(len(pts)))
    prob += pulp.lpSum(y) <= k
    for i in range(len(pts)):
        prob += z[i] <= pulp.lpSum(y[b] for b in range(len(bases)) if a[b,i])
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    sel = [b for b in range(len(bases)) if y[b].value() and y[b].value() > 0.5]
    risco_cob = sum(risco_v[i]*(z[i].value() or 0) for i in range(len(pts)))
    return {"k":k,"bases_sel":sel,"frac_risco":risco_cob/risco_v.sum(),
            "bases_nomes":[bases[b]["nome"] for b in sel]}

rec_k2 = mclp(pts, bases, R_calmo, 2)
print(f"MCLP k=2: {rec_k2['bases_nomes']} → cobre {100*rec_k2['frac_risco']:.1f}% do risco")
"""))

cells.append(md("### 4.3 Curva de trade-off e dimensionamento de frota"))
cells.append(code("""def raio_por_autonomia(t_on_h, vento_ms=4.0):
    V, E = AR5["velocidade_cruzeiro_kmh"], AR5["autonomia_h"]
    r = V*(E-RESERVA_H-t_on_h)/2.0
    return max(r,0.0)*fator_vento(vento_ms)

def dimensionar_frota(n_bases, raio_km):
    V, E = AR5["velocidade_cruzeiro_kmh"], AR5["autonomia_h"]
    transito = 2.0*(raio_km/V)
    t_on = max(E-transito-RESERVA_H, 0.1)
    sorties = 24.0/t_on
    dpb = math.ceil(sorties/DISPONIBILIDADE)
    return {"frota_total": math.ceil(n_bases*dpb*(1+RESERVA_FROTA)), "t_on_h": round(t_on,2)}

def dimensionar_persistencia(pts_alto, bases, bases_sel, area_celula):
    V, E = AR5["velocidade_cruzeiro_kmh"], AR5["autonomia_h"]
    area_hr = len(pts_alto)*area_celula
    n_sim = max(1, math.ceil(area_hr/(V*SENSOR_SWATH_KM*TEMPO_REVISITA_H)))
    bx = np.array([bases[b]["x"] for b in bases_sel])
    by = np.array([bases[b]["y"] for b in bases_sel])
    ds = [np.sqrt((bx-p["x"])**2+(by-p["y"])**2).min() for p in pts_alto]
    d_med = float(np.mean(ds))
    t_on = max(E-2*d_med/V-RESERVA_H, 0.5)
    M = (24/t_on)/DISPONIBILIDADE
    frota = math.ceil(n_sim*M*(1+RESERVA_FROTA))
    return {"n_simultaneos":n_sim,"frota_total":frota,"dist_media_km":round(d_med,1),"t_on_h":round(t_on,2)}

R_long = raio_por_autonomia(6.0, CENARIOS_VENTO["calmo"])
curva = [mclp(pts, bases, R_long, k) for k in range(1, len(bases)+1)]
area_celula = (0.10*_KX)*(0.10*_KY)
pts_alto = [p for p in pts if p["risco"] >= LIMIAR]

frota_vs_k = []
for c in curva:
    fp = dimensionar_persistencia(pts_alto, bases, c["bases_sel"], area_celula)
    frota_vs_k.append({"k":c["k"],"frac_risco":c["frac_risco"],"frota_total":fp["frota_total"],
                       "bases":c["bases_nomes"]})
eleg = [f for f in frota_vs_k if f["frac_risco"]>=0.95]
melhor = min(eleg, key=lambda f:f["frota_total"]) if eleg else frota_vs_k[-1]
k_rec = melhor["k"]
rec = mclp(pts, bases, R_long, k_rec)
fr_cost = dimensionar_persistencia(
    [p for i,p in enumerate(pts_alto) if matriz_cobertura(pts_alto,bases,R_calmo)[:,i].sum()>0],
    bases, sc_calmo["bases_sel"], area_celula)

print(f"Ótimo k={k_rec} | frota costeira={fr_cost['frota_total']} AR5 | frota total={melhor['frota_total']} AR5")
pd.DataFrame(frota_vs_k)
"""))

cells.append(md("### 4.4 Cenários de vento"))
cells.append(code("""rows_cen = []
for nome, vel in CENARIOS_VENTO.items():
    R = raio_efetivo(vel)
    sc = set_cover(pts, bases, R, LIMIAR)
    fr = dimensionar_frota(sc["n_bases"], R)
    rows_cen.append({"cenário":f"{nome} ({vel:.0f} m/s)","R km":R,"bases":sc["n_bases"],
                     "frota 24h":fr["frota_total"],"fora alcance":sc["n_nao_cobrivel"]})
df_cen = pd.DataFrame(rows_cen)
display(df_cen)
"""))

cells.append(md("### 4.5 Figuras de cobertura e trade-off (Fig. 03–05)"))
cells.append(code("""def circulo_lonlat(base, raio_km, n=120):
    ang = np.linspace(0, 2*np.pi, n)
    xs = base["x"]+raio_km*np.cos(ang); ys = base["y"]+raio_km*np.sin(ang)
    return [inv_proj(x,y)[0] for x,y in zip(xs,ys)], [inv_proj(x,y)[1] for x,y in zip(xs,ys)]

lon_a, lat_a = np.array(lon), np.array(lat)
r_a = np.array(rv); alto = r_a >= LIMIAR
a = matriz_cobertura(pts, bases, R_calmo); sel = sc_calmo["bases_sel"]
cob = a[sel].sum(axis=0)>0

fig, ax = plt.subplots(figsize=(7.5,8.5))
ax.scatter(lon_a[~alto], lat_a[~alto], c="#ddd", s=6, marker="s")
ax.scatter(lon_a[alto&cob], lat_a[alto&cob], c="#1a9850", s=12, marker="s", label="Coberto")
ax.scatter(lon_a[alto&~cob], lat_a[alto&~cob], c="#d73027", s=12, marker="s", label="Não coberto")
for b in sel:
    clon,clat = circulo_lonlat(bases[b], R_calmo)
    ax.plot(clon,clat,color="navy",lw=1.2,alpha=0.8)
    ax.plot(bases[b]["lon"],bases[b]["lat"],"^",color="navy",ms=10)
ax.plot(COSTA_LON,COSTA_LAT,color="#444",lw=1.5)
ax.set_xlim(LON_MIN,LON_MAX); ax.set_ylim(LAT_MIN,LAT_MAX)
ax.set_title(f"Fig. 03 — Cobertura conservadora R={R_calmo:.0f} km"); ax.legend(fontsize=8)
fig.tight_layout(); plt.show(); fig.savefig(FIGDIR/"03_cobertura_conservador.png",dpi=140)

# Fig 05
fig, ax = plt.subplots(figsize=(8,5.5))
ax.plot([c["k"] for c in curva], [100*c["frac_risco"] for c in curva], "-o", label=f"R={R_long:.0f} km")
ax.axhline(95,color="gray",ls="--"); ax.set_xlabel("Nº bases"); ax.set_ylabel("% risco coberto")
ax.set_title("Fig. 05 — Trade-off MCLP"); ax.legend(); ax.grid(alpha=0.3)
fig.tight_layout(); plt.show(); fig.savefig(FIGDIR/"05_tradeoff.png",dpi=140)
"""))

cells.append(md("### 4.6 Figuras de frota e sensibilidade (Fig. 06–08)"))
cells.append(code("""# Fig 06
fig, ax = plt.subplots(figsize=(8,5))
x = np.arange(len(df_cen)); w=0.38
ax.bar(x-w/2, df_cen["bases"], w, label="Bases", color="#4575b4")
ax.bar(x+w/2, df_cen["frota 24h"], w, label="Frota 24h", color="#d73027")
ax.set_xticks(x); ax.set_xticklabels(df_cen["cenário"], rotation=15, ha="right")
ax.set_title("Fig. 06 — Frota por vento"); ax.legend()
fig.tight_layout(); plt.show(); fig.savefig(FIGDIR/"06_frota.png",dpi=140)

# Fig 08
ks=[f["k"] for f in frota_vs_k]; ft=[f["frota_total"] for f in frota_vs_k]
frp=[100*f["frac_risco"] for f in frota_vs_k]
fig, ax1 = plt.subplots(figsize=(8.5,5.5))
ax1.plot(ks,ft,"-o",color="#d73027"); ax1.axvline(k_rec,color="green",ls="--")
ax2=ax1.twinx(); ax2.plot(ks,frp,"-s",color="#4575b4",alpha=0.7)
ax1.set_title("Fig. 08 — Frota vs nº bases"); fig.tight_layout()
plt.show(); fig.savefig(FIGDIR/"08_frota_vs_bases.png",dpi=140)
"""))

# --- SECTION 5 VALIDATION ---
cells.append(md("## 5. Validação científica"))
cells.append(md("### 5.1 Backtest temporal (treino ≤2022, teste 2023–2024)"))
cells.append(code("""from validacao import (risco_com_droga_temporal, apreensoes_geocodificadas, celula_mais_proxima)

risco_train, _ = risco_com_droga_temporal(pts, ANO_CORTE)
holdout = apreensoes_geocodificadas(ano_min=ANO_CORTE+1)
n_hold = len(holdout)
alto = risco_train >= LIMIAR
hits = 0; riscos_ho = []
for _, row in holdout.iterrows():
    idx = celula_mais_proxima(pts, row["lon"], row["lat"])
    rv = float(risco_train[idx])
    riscos_ho.append(rv)
    if rv >= LIMIAR: hits += 1

rng = np.random.default_rng(42)
sims = [float((risco_train[rng.integers(0,len(pts),n_hold)]>=LIMIAR).mean()) for _ in range(2000)]
baseline_rand = float(np.mean(sims))
taxa_acerto = hits/n_hold
ganho_bt = taxa_acerto/max(baseline_rand,1e-6)

print(f"Holdout n={n_hold} | acerto limiar={taxa_acerto:.1%} | baseline aleatório={baseline_rand:.1%} | ganho={ganho_bt:.2f}×")
"""))

cells.append(md("### 5.2 Baseline de patrulha (SAD vs aleatório vs uniforme)"))
cells.append(code("""risco_v = np.array([p["risco"] for p in pts])
total = float(risco_v.sum())
n_pat = int((risco_v >= LIMIAR).sum())

idx_sad = np.argsort(-risco_v)[:n_pat]
captura_sad = float(risco_v[idx_sad].sum()/total)

rng = np.random.default_rng(7)
sims = [float(risco_v[rng.choice(len(pts),n_pat,replace=False)].sum()/total) for _ in range(500)]
captura_rand = float(np.mean(sims)); captura_rand_std = float(np.std(sims))

ordenado = sorted(range(len(pts)), key=lambda i: pts[i]["dist_costa_km"])
idx_uni = ordenado[::max(1,len(ordenado)//n_pat)][:n_pat]
captura_uni = float(risco_v[idx_uni].sum()/total)
ganho_bl = captura_sad/max(captura_rand,1e-6)

print(f"N patrulha={n_pat}")
print(f"SAD: {100*captura_sad:.1f}% | Aleatório: {100*captura_rand:.1f}%±{100*captura_rand_std:.1f}% | Uniforme: {100*captura_uni:.1f}%")
print(f"Ganho SAD/aleatório: {ganho_bl:.2f}×")
"""))

cells.append(md("### 5.3 Figuras de validação (Fig. 21–22)"))
cells.append(code("""# Fig 21 backtest
fig, ax = plt.subplots(figsize=(7,4.2))
labels = ["SAD\\n(limiar 0,5)","Aleatório\\n(limiar)"]
vals = [taxa_acerto*100, baseline_rand*100]
bars = ax.bar(labels, vals, color=["#e67e22","#95a5a6"], edgecolor="#333")
ax.set_ylabel("Taxa acerto holdout (%)")
ax.set_title("Fig. 21 — Backtest temporal 2023–2024")
for b,v in zip(bars,vals): ax.text(b.get_x()+b.get_width()/2, v+1, f"{v:.1f}%", ha="center", fontweight="bold")
fig.tight_layout(); plt.show(); fig.savefig(FIGDIR/"21_backtest_temporal.png",dpi=150)

# Fig 22 baseline
fig, ax = plt.subplots(figsize=(6.5,4.2))
labels2 = ["SAD\\n(top-N)","Aleatório","Uniforme\\ncosteiro"]
vals2 = [captura_sad*100, captura_rand*100, captura_uni*100]
err = [0, captura_rand_std*100, 0]
bars = ax.bar(labels2, vals2, yerr=err, capsize=4, color=["#2980b9","#95a5a6","#7f8c8d"], edgecolor="#333")
ax.set_ylabel("% risco capturado"); ax.set_title(f"Fig. 22 — Baseline ({n_pat} células)")
for b,v in zip(bars,vals2): ax.text(b.get_x()+b.get_width()/2, v+2, f"{v:.1f}%", ha="center", fontweight="bold")
fig.tight_layout(); plt.show(); fig.savefig(FIGDIR/"22_baseline_patrulha.png",dpi=150)
"""))

cells.append(md("### 5.4 Métricas canónicas (plataforma / relatório)"))
cells.append(code("""val_path = OUTDIR / "validacao.json"
if val_path.exists():
    with open(val_path, encoding="utf-8") as f:
        val = json.load(f)
    bt_c = val["backtest_temporal"]
    bl_c = val["baseline_patrulha"]
    print("=== validacao.json (canónico para plataforma) ===")
    display(pd.DataFrame([
        {"métrica":"N holdout","notebook":n_hold,"canónico":bt_c["n_holdout"]},
        {"métrica":"Ganho backtest","notebook":round(ganho_bt,2),"canónico":bt_c.get("ganho_relativo_limiar")},
        {"métrica":"N células patrulha","notebook":n_pat,"canónico":bl_c["n_celulas_patrulha"]},
        {"métrica":"Ganho baseline","notebook":round(ganho_bl,2),"canónico":bl_c["ganho_sad_vs_aleatorio"]},
    ]))
else:
    val = {"resposta_objetivo":{}}
    print("(validacao.json não encontrado — usar valores calculados acima)")
"""))

# --- SECTION 6 RESPOSTAS ---
cells.append(md("## 6. Respostas SAD — Q1, Q2, Q3"))
cells.append(code("""if val_path.exists():
    resp = val["resposta_objetivo"]
    display(pd.DataFrame([
        ("Q1 — Onde patrulhar?", resp["Q1_onde"]["resposta"]),
        ("Q2 — Quantos AR5?", resp["Q2_quantos"]["resposta"]),
        ("Q3 — Onde colocar bases?", resp["Q3_bases"]["resposta"]),
    ], columns=["Pergunta","Resposta"]))
"""))

cells.append(md("## 7. Resumo final e exportação"))
cells.append(code("""# Tabelas comparativas (estilo trabalho2 — prontas para o relatório)

res_opt = pd.DataFrame(rows_cen)
res_val = pd.DataFrame([
    {"Métrica":"Backtest ganho vs aleatório","Valor":f"{ganho_bt:.2f}×"},
    {"Métrica":"Baseline ganho vs aleatório","Valor":f"{ganho_bl:.2f}×"},
    {"Métrica":"MCLP k=2 bases","Valor":", ".join(rec_k2["bases_nomes"])},
    {"Métrica":"Frota costeira 24h (AR5)","Valor":fr_cost["frota_total"]},
    {"Métrica":"Células alto risco","Valor":int((r>=LIMIAR).sum())},
])

print("="*70)
print("RESUMO FINAL — SAD AR5 VIGILÂNCIA COSTEIRA (Grupo VI)")
print("="*70)
print("\\n[OTIMIZAÇÃO] Cenários de vento")
print(res_opt.to_string(index=False))
print("\\n[VALIDAÇÃO]")
print(res_val.to_string(index=False))

res_opt.to_csv(OUTDIR/"resumo_cenarios_notebook.csv", index=False)
res_val.to_csv(OUTDIR/"resumo_validacao_notebook.csv", index=False)
pd.DataFrame(frota_vs_k).to_csv(OUTDIR/"frota_vs_k_notebook.csv", index=False)
print("\\nCSV guardados em", OUTDIR)
print("\\nFiguras em", FIGDIR)
"""))

cells.append(md("""## Notas para o relatório

- As figuras `01–08` e `21–25` correspondem às do relatório escrito.
- A **plataforma web** lê `resultados/validacao.json` e `resultados/resultados.json` em runtime.
- Para regenerar os JSON canónicos: `cd src && python main.py && python validacao.py`.
"""))

nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12.0"},
    },
    "cells": cells,
}

OUT.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
code_lines = sum(len("".join(c["source"]).splitlines()) for c in cells if c["cell_type"]=="code")
print(f"Gerado: {OUT} | {len(cells)} células | {code_lines} linhas de código")
