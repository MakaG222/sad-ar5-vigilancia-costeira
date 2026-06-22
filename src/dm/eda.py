"""
eda.py — Análise exploratória de dados e visualização (CRISP-DM: Data
Understanding). Produz os gráficos típicos ensinados na cadeira: séries
temporais, histogramas, boxplots e gráficos de barras.
"""
from __future__ import annotations
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from .preproc import carregar_e_limpar

OUT = os.path.join(os.path.dirname(__file__), "../../resultados/dm")
os.makedirs(OUT, exist_ok=True)
sns.set_theme(style="whitegrid")


def gerar():
    df = carregar_e_limpar(log=False)

    fig, axes = plt.subplots(2, 2, figsize=(13, 10))

    # (a) série temporal anual
    serie = df.groupby("ano").size()
    axes[0, 0].plot(serie.index, serie.values, "-o", color="#1f77b4")
    axes[0, 0].set_title("(a) Apreensões por ano")
    axes[0, 0].set_xlabel("Ano"); axes[0, 0].set_ylabel("Nº de apreensões")

    # (b) barras por grupo de droga
    g = df["grupo_droga"].value_counts()
    sns.barplot(x=g.values, y=g.index, ax=axes[0, 1], palette="viridis", hue=g.index, legend=False)
    axes[0, 1].set_title("(b) Apreensões por grupo de droga")
    axes[0, 1].set_xlabel("Nº de apreensões")

    # (c) histograma de log-quantidade (massa)
    m = df["log_qty_g"].dropna()
    axes[1, 0].hist(m, bins=40, color="#2ca02c", alpha=0.8)
    axes[1, 0].set_title("(c) Histograma de log(1+quantidade em g)")
    axes[1, 0].set_xlabel("log(1+g)"); axes[1, 0].set_ylabel("Frequência")

    # (d) % marítimo por grupo de droga
    mar = df.groupby("grupo_droga")["maritimo"].mean().sort_values(ascending=False) * 100
    sns.barplot(x=mar.values, y=mar.index, ax=axes[1, 1], palette="rocket", hue=mar.index, legend=False)
    axes[1, 1].set_title("(d) % de apreensões marítimas por grupo")
    axes[1, 1].set_xlabel("% marítimas")

    fig.suptitle("Análise exploratória — apreensões de droga em Portugal (2011–2024)",
                 fontsize=14)
    fig.tight_layout(); fig.savefig(f"{OUT}/eda_panorama.png", dpi=140)
    plt.close(fig)

    # boxplot log-quantidade por grupo + região
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    sns.boxplot(data=df, x="grupo_droga", y="log_qty_g", ax=axes[0],
                palette="Set2", hue="grupo_droga", legend=False)
    axes[0].set_title("Distribuição da quantidade por grupo de droga")
    axes[0].set_xlabel(""); axes[0].set_ylabel("log(1+g)")
    axes[0].tick_params(axis="x", rotation=30)
    cont = df[df["regiao"].notna()]
    sns.countplot(data=cont, x="regiao", hue="maritimo", ax=axes[1],
                  order=["N", "C", "S"])
    axes[1].set_title("Apreensões por região (N/C/S) e tipo")
    axes[1].set_xlabel("Região"); axes[1].legend(title="marítimo", labels=["não", "sim"])
    fig.tight_layout(); fig.savefig(f"{OUT}/eda_boxplot_regiao.png", dpi=140)
    plt.close(fig)

    resumo = {
        "n": int(len(df)),
        "intervalo": [int(df["ano"].min()), int(df["ano"].max())],
        "grupos": g.to_dict(),
        "pct_maritimo_por_grupo": {k: round(float(v), 2) for k, v in mar.items()},
    }
    return resumo


if __name__ == "__main__":
    import json
    print(json.dumps(gerar(), ensure_ascii=False, indent=2))
