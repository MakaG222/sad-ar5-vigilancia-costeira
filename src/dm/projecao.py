"""
projecao.py — Redução de dimensionalidade e projeção para 2D (deck de
Visualização 4_2: "Projecções para 2 dimensões").

Aplica a Análise de Componentes Principais (PCA / ACP — Transformada de
Karhunen-Loève): mudança de eixos para as direções de maior variância, com
medida da "variância explicada" (o que NÃO estamos a ver). Projeta as apreensões
no plano das 2 primeiras componentes, colorindo por classe (marítima/não), e
mostra o escalonamento dos valores próprios.
"""
from __future__ import annotations
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

from .preproc import carregar_e_limpar, features_classificacao

OUT = os.path.join(os.path.dirname(__file__), "../../resultados/dm")
os.makedirs(OUT, exist_ok=True)


def gerar():
    df = carregar_e_limpar(log=False)
    X, y, _ = features_classificacao(df)
    cols = list(X.columns)
    Xs = StandardScaler().fit_transform(X.astype(float).values)

    pca = PCA(n_components=min(10, Xs.shape[1])).fit(Xs)
    var = pca.explained_variance_ratio_
    Z = pca.transform(Xs)[:, :2]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    # (a) projeção 2D colorida por classe
    nao = y == 0; mar = y == 1
    axes[0].scatter(Z[nao, 0], Z[nao, 1], s=6, alpha=0.25, color="#7f7f7f",
                    label="não-marítima")
    axes[0].scatter(Z[mar, 0], Z[mar, 1], s=14, alpha=0.8, color="#d73027",
                    label="marítima")
    axes[0].set_xlabel(f"CP1 ({100*var[0]:.1f}% var.)")
    axes[0].set_ylabel(f"CP2 ({100*var[1]:.1f}% var.)")
    axes[0].set_title("Projeção PCA (2 primeiras componentes)")
    axes[0].legend()
    # (b) variância explicada e acumulada
    k = len(var)
    axes[1].bar(range(1, k + 1), 100 * var, color="#4575b4", label="por componente")
    axes[1].plot(range(1, k + 1), 100 * np.cumsum(var), "-o", color="#d73027",
                 label="acumulada")
    axes[1].axhline(80, color="gray", ls="--", lw=1)
    axes[1].set_xlabel("Componente principal"); axes[1].set_ylabel("Variância explicada (%)")
    axes[1].set_title("Variância explicada (escalonamento dos valores próprios)")
    axes[1].legend(); axes[1].grid(alpha=0.3, axis="y")
    fig.suptitle("Redução de dimensionalidade — PCA / ACP", fontsize=13)
    fig.tight_layout(); fig.savefig(f"{OUT}/proj_pca.png", dpi=140)
    plt.close(fig)

    n80 = int(np.argmax(np.cumsum(var) >= 0.80) + 1)
    return {"var_cp1": float(var[0]), "var_cp2": float(var[1]),
            "n_componentes_80pct": n80,
            "var_explicada": [round(float(v), 4) for v in var]}


if __name__ == "__main__":
    import json
    print(json.dumps(gerar(), ensure_ascii=False, indent=2))
