"""
preproc.py — Pré-processamento de dados (CRISP-DM: Data Preparation).

Aplica, de forma documentada, as etapas ensinadas na cadeira:
  1. Limpeza de dados (correção de inconsistências e gralhas)
  2. Tratamento de valores em falta (missing values)
  3. Transformação (datas -> ano/mês/estação; quantidade -> gramas; log)
  4. Discretização / agrupamento (substância -> grupo de droga; região N/C/S)
  5. Codificação de variáveis categóricas (one-hot / ordinal)
  6. Normalização (z-score / min-max) — aplicada nos módulos que a exigem
  7. Definição do alvo supervisionado (apreensão marítima: sim/não)
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

from .geocode import geocode, is_ilha, is_costeiro

XLSX_DEFAULT = os.path.join(os.path.dirname(__file__),
                            "../../dados/fontes/apreensoes_droga_PT.xlsx")

LOC_MARITIMO = ["Territorial waters (seas, lakes, rivers, etc.)",
                "Seaport/Riverport station/Harbour", "International waters"]

# --- agrupamento de substâncias (discretização semântica) ---
GRUPO_DROGA = {
    "Cannabis": ["Cannabis resin (hashish)", "Cannabis herb (marijuana)",
                 "Cannabis plants", "Cannabis seeds", "Cannabis pollen (dust)",
                 "Cannabis oil",
                 "Other cannabis-type (excluding synthetic cannabinoids)",
                 "Non-specified cannabis-type (excluding synthetic cannabinoids)",
                 "Other synthetic cannabinoids (spice)"],
    "Cocaina": ["Cocaine hydrochloride (HCl, powder cocaine)",
                "Non-specified cocaine-type", "Crack cocaine", "Coca leaf"],
    "Opioides": ["Heroin", "Opium", "Methadone", "Subutex (buprenorphine)",
                 "Codeine", "Poppy plants"],
    "Estimulantes": ["MDMA", "MDA", "Amphetamine", "Methamphetamine",
                     "Non-specified ecstasy-type substances",
                     "Mephedrone (4-methylmethcathinone, 4-MMC)",
                     "2C-B (4-bromo-2,5-dimethoxyphenethylamine)",
                     "Non-specified Synthetic cathinones",
                     "4-Chloromethcathinone (4-CMC, Clephedrone)", "Other NPS"],
    "Alucinogenios": ["LSD", "Dimethyltryptamine (DMT)", "Psilocybin",
                      "Non-specified hallucinogens", "Other hallucinogens"],
    "Medicamentos": ["Clonazepam (Rivotril)",
                     "Alprazolam (Xanax, Pranax, Ksalol)", "Benzodiazepines",
                     "GHB", "Lorazepam (Ativan, Temesta)", "Diazepam"],
    "Outras": ["Khat", "Other-miscellaneous"],
}
_SUB2GRUPO = {s: g for g, subs in GRUPO_DROGA.items() for s in subs}

# correção de gralhas em tokens administrativos
FIX_TOKEN = {"Lisba": "Lisboa", "Portio": "Porto", "Setubal": "Setúbal",
             "Santarem": "Santarém", "Evora": "Évora", "Braganca": "Bragança",
             "Leira": "Leiria", "Ilha Do Madeira": "Ilha Da Madeira",
             "Ilha São Miguel": "Ilha De São Miguel"}

ESTACAO = {12: "Inverno", 1: "Inverno", 2: "Inverno", 3: "Primavera",
           4: "Primavera", 5: "Primavera", 6: "Verão", 7: "Verão",
           8: "Verão", 9: "Outono", 10: "Outono", 11: "Outono"}


def _token(x):
    if isinstance(x, str):
        t = x.split("/")[0].strip() if "/" in x else x.strip()
        return FIX_TOKEN.get(t, t)
    return None


def _regiao_por_lat(lat):
    if lat is None:
        return None
    if lat >= 40.0:
        return "N"
    if lat >= 38.0:
        return "C"
    return "S"


def carregar_e_limpar(xlsx_path: str = XLSX_DEFAULT, log: bool = True) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path)
    n0 = len(df)

    # (1) limpeza: remover linhas totalmente inválidas (sem data/substância)
    df = df.dropna(subset=["Seizure Date", "Drug/Substance", "Quantity Seized"]).copy()

    # normalizar variantes da Subregion (inconsistência textual)
    df["Subregion"] = df["Subregion"].replace(
        {"Western and Central Europe": "West and Central Europe"})

    # (2) datas -> ano / mês / estação
    df["Seizure Date"] = pd.to_datetime(df["Seizure Date"], errors="coerce")
    df = df.dropna(subset=["Seizure Date"])
    df["ano"] = df["Seizure Date"].dt.year
    df["mes"] = df["Seizure Date"].dt.month
    df["estacao"] = df["mes"].map(ESTACAO)

    # token administrativo + geocodificação
    df["token"] = df["Administrative Region"].apply(_token)
    coords = df["token"].apply(lambda t: geocode(t) if t else None)
    df["lat"] = coords.apply(lambda c: c[0] if c else np.nan)
    df["lon"] = coords.apply(lambda c: c[1] if c else np.nan)
    df["ilha"] = df["token"].apply(lambda t: is_ilha(t) if t else False)
    df["costeiro"] = df["token"].apply(lambda t: is_costeiro(t) if t else False)
    df["regiao"] = df["lat"].apply(_regiao_por_lat)

    # (3) quantidade -> gramas (apenas unidades de massa) + log
    unidade = df["Measurement Unit"].astype(str)
    qty = pd.to_numeric(df["Quantity Seized"], errors="coerce")
    qty_g = np.where(unidade == "kg", qty * 1000.0,
                     np.where(unidade == "g", qty, np.nan))
    df["qty_g"] = qty_g
    df["e_massa"] = (~np.isnan(qty_g)).astype(int)
    df["log_qty_g"] = np.log1p(df["qty_g"])

    # (4) agrupamento da substância
    df["grupo_droga"] = df["Drug/Substance"].map(_SUB2GRUPO).fillna("Outras")

    # (7) alvo supervisionado: apreensão marítima (sim/não)
    df["maritimo"] = ((df["Physical Seizure Location"].isin(LOC_MARITIMO)) |
                      (df["Trafficking Mode of Transportation"] == "Vessel/boat")
                      ).astype(int)

    if log:
        print(f"[preproc] linhas: {n0} -> {len(df)} "
              f"(removidas {n0 - len(df)} inválidas)")
        print(f"[preproc] geocodificadas: {df['lat'].notna().sum()} "
              f"({100*df['lat'].notna().mean():.1f}%)")
        print(f"[preproc] marítimas: {df['maritimo'].sum()} "
              f"({100*df['maritimo'].mean():.2f}%)")
    return df


def features_classificacao(df: pd.DataFrame):
    """Constrói X (features sem fuga de informação) e y (marítimo).

    Exclui as colunas usadas para construir o alvo (Physical Seizure Location,
    Trafficking Mode) para evitar data leakage.
    Features: grupo de droga, região, estação, mês, ano, log-quantidade, flag de
    massa, costeiro/ilha.
    """
    d = df.copy()
    # (2) imputação de valores em falta:
    #  - log_qty_g em falta (unidades não-massa) -> mediana
    med = d["log_qty_g"].median()
    d["log_qty_g"] = d["log_qty_g"].fillna(med)
    #  - região em falta (sem geocódigo) -> "Desconhecida"
    d["regiao"] = d["regiao"].fillna("Desc")

    num = ["log_qty_g", "e_massa", "ano", "mes"]
    cat = ["grupo_droga", "regiao", "estacao"]
    # (5) codificação one-hot das categóricas
    X = pd.get_dummies(d[num + cat], columns=cat, drop_first=False)
    y = d["maritimo"].values
    return X, y, d


if __name__ == "__main__":
    df = carregar_e_limpar()
    X, y, d = features_classificacao(df)
    print("X shape:", X.shape, "| features:", list(X.columns)[:8], "...")
    print("grupos:", df["grupo_droga"].value_counts().to_dict())
    print("regiao:", df["regiao"].value_counts().to_dict())
