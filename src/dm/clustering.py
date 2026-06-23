"""
clustering.py — Aprendizagem não supervisionada (segmentação espacial).

Aplica os algoritmos de clustering ensinados na cadeira para identificar
HOTSPOTS geográficos de apreensões e derivar zonas de patrulha:
  - K-means (com escolha de k pelo método do cotovelo e da silhueta)
  - Clustering hierárquico aglomerativo (dendrograma, ligação 'ward')
  - DBSCAN (baseado em densidade) para comparação

Pré-requisito: normalização (z-score) das coordenadas antes do clustering.
"""
from __future__ import annotations
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.metrics import silhouette_score
from scipy.cluster.hierarchy import dendrogram, linkage

from .preproc import carregar_e_limpar

OUT = os.path.join(os.path.dirname(__file__), "../../resultados/dm")
os.makedirs(OUT, exist_ok=True)
RANDOM = 42


def _dados_continentais(df, so_maritimo=False):
    d = df[(df["lat"].notna()) & (~df["ilha"])].copy()
    if so_maritimo:
        d = d[d["maritimo"] == 1]
    # jitter para desempatar coordenadas coincidentes (sedes de concelho)
    rng = np.random.default_rng(RANDOM)
    d["lat_j"] = d["lat"] + rng.normal(0, 0.05, len(d))
    d["lon_j"] = d["lon"] + rng.normal(0, 0.05, len(d))
    return d


def escolher_k(Xs, kmax=10):
    inercias, sils, ks = [], [], list(range(2, kmax + 1))
    for k in ks:
        km = KMeans(n_clusters=k, n_init=10, random_state=RANDOM).fit(Xs)
        inercias.append(km.inertia_)
        sils.append(silhouette_score(Xs, km.labels_))
    return ks, inercias, sils


def fig_elbow_silhueta(ks, inercias, sils, k_esc):
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.plot(ks, inercias, "-o", color="#d73027", label="Inércia (cotovelo)")
    ax1.set_xlabel("Nº de clusters (k)"); ax1.set_ylabel("Inércia", color="#d73027")
    ax1.axvline(k_esc, color="green", ls="--", label=f"k escolhido = {k_esc}")
    ax2 = ax1.twinx()
    ax2.plot(ks, sils, "-s", color="#4575b4", label="Silhueta")
    ax2.set_ylabel("Coeficiente de silhueta", color="#4575b4")
    ax1.set_title("Escolha de k: método do cotovelo e da silhueta")
    ax1.legend(loc="upper right"); ax1.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(f"{OUT}/clu_elbow_silhueta.png", dpi=140)
    plt.close(fig)


def fig_mapa_clusters(d, labels, centros_lonlat, titulo, fich):
    fig, ax = plt.subplots(figsize=(7, 8.5))
    sc = ax.scatter(d["lon_j"], d["lat_j"], c=labels, cmap="tab10", s=10, alpha=0.5)
    for (clon, clat) in centros_lonlat:
        ax.plot(clon, clat, "k*", ms=18, mec="white")
    ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
    ax.set_xlim(-9.8, -6.0); ax.set_ylim(36.5, 42.3)
    ax.set_aspect(1.0 / np.cos(np.radians(39.5)))
    ax.set_title(titulo)
    fig.tight_layout(); fig.savefig(f"{OUT}/{fich}", dpi=140)
    plt.close(fig)


def fig_dendrograma(Xs, fich="clu_dendrograma.png", n=400):
    rng = np.random.default_rng(RANDOM)
    idx = rng.choice(len(Xs), size=min(n, len(Xs)), replace=False)
    Z = linkage(Xs[idx], method="ward")
    fig, ax = plt.subplots(figsize=(10, 5))
    dendrogram(Z, no_labels=True, color_threshold=0.7 * max(Z[:, 2]), ax=ax)
    ax.set_title("Dendrograma — clustering hierárquico aglomerativo (ligação de Ward)")
    ax.set_ylabel("Distância")
    fig.tight_layout(); fig.savefig(f"{OUT}/{fich}", dpi=140)
    plt.close(fig)


def analisar():
    df = carregar_e_limpar(log=False)

    # ---- (1) K-means sobre TODAS as apreensões continentais (estrutura espacial)
    d = _dados_continentais(df)
    X = d[["lat_j", "lon_j"]].values
    Xs = StandardScaler().fit_transform(X)
    ks, inercias, sils = escolher_k(Xs, kmax=10)
    k_esc = ks[int(np.argmax(sils))]
    fig_elbow_silhueta(ks, inercias, sils, k_esc)

    km = KMeans(n_clusters=k_esc, n_init=10, random_state=RANDOM).fit(Xs)
    d["cluster"] = km.labels_
    # centróides de volta a lon/lat (desfazer normalização)
    scaler = StandardScaler().fit(X)
    centros = scaler.inverse_transform(km.cluster_centers_)
    centros_lonlat = [(c[1], c[0]) for c in centros]
    fig_mapa_clusters(d, km.labels_, centros_lonlat,
                      f"K-means (k={k_esc}) — hotspots de apreensões (continental)",
                      "clu_kmeans_geral.png")
    fig_dendrograma(Xs)

    # DBSCAN (densidade)
    db = DBSCAN(eps=0.25, min_samples=30).fit(Xs)
    n_db = len(set(db.labels_)) - (1 if -1 in db.labels_ else 0)

    # ---- (2) K-means sobre apreensões MARÍTIMAS continentais -> zonas de patrulha
    dm = _dados_continentais(df, so_maritimo=True)
    Xm = dm[["lat_j", "lon_j"]].values
    Xms = StandardScaler().fit_transform(Xm)
    k_mar = 4
    kmm = KMeans(n_clusters=k_mar, n_init=10, random_state=RANDOM).fit(Xms)
    dm["cluster"] = kmm.labels_
    scm = StandardScaler().fit(Xm)
    centros_m = scm.inverse_transform(kmm.cluster_centers_)
    zonas = []
    for c in range(k_mar):
        sub = dm[dm["cluster"] == c]
        zonas.append({"centro_lat": float(centros_m[c][0]),
                      "centro_lon": float(centros_m[c][1]),
                      "n_apreensoes": int(len(sub)),
                      "peso": float(len(sub) / len(dm))})
    zonas.sort(key=lambda z: -z["n_apreensoes"])
    fig_mapa_clusters(dm, kmm.labels_, [(z["centro_lon"], z["centro_lat"]) for z in zonas],
                      f"K-means (k={k_mar}) — zonas de patrulha (apreensões marítimas)",
                      "clu_kmeans_maritimo.png")

    # ---- (3) Fuzzy C-Means sobre as apreensões marítimas (liga difusos+clustering)
    fcm = fuzzy_cmeans(dm, Xms, k_mar)

    resumo = {
        "kmeans_geral_k": k_esc, "silhueta_max": float(max(sils)),
        "dbscan_clusters": int(n_db),
        "zonas_patrulha": zonas,
        "centros_geral_lonlat": [(round(lo, 3), round(la, 3)) for lo, la in centros_lonlat],
        "fuzzy_cmeans_fpc": fcm["fpc"],
    }
    return resumo


def fuzzy_cmeans(dm, Xms, c):
    """Fuzzy C-Means (skfuzzy): alternativa 'fuzzificada' ao k-médias em que a
    pertença a cada cluster é proporcional à distância ao centróide (decks 5 e
    11B). Reporta o coeficiente de partição difusa (FPC) e mostra a incerteza de
    afetação (pertença máxima) de cada ponto."""
    from skfuzzy import cmeans
    scm = StandardScaler().fit(dm[["lat_j", "lon_j"]].values)
    # cmeans espera dados em formato (features, amostras)
    cntr, u, _, _, _, _, fpc = cmeans(Xms.T, c=c, m=2.0, error=1e-4,
                                      maxiter=1000, seed=RANDOM)
    pertenca_max = u.max(axis=0)        # grau de pertença ao cluster dominante
    afet = u.argmax(axis=0)
    centros = scm.inverse_transform(cntr)

    fig, ax = plt.subplots(figsize=(7, 8.5))
    sc = ax.scatter(dm["lon_j"], dm["lat_j"], c=pertenca_max, cmap="viridis",
                    s=14, vmin=0.25, vmax=1.0)
    for cc in centros:
        ax.plot(cc[1], cc[0], "r*", ms=18, mec="white")
    ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
    ax.set_xlim(-9.8, -6.0); ax.set_ylim(36.5, 42.3)
    ax.set_aspect(1.0 / np.cos(np.radians(39.5)))
    ax.set_title(f"Fuzzy C-Means (c={c}, FPC={fpc:.2f})\ncor = grau de pertença ao "
                 "cluster dominante (incerteza)")
    plt.colorbar(sc, ax=ax, shrink=0.6, label="pertença máxima")
    fig.tight_layout(); fig.savefig(f"{OUT}/clu_fuzzy_cmeans.png", dpi=140)
    plt.close(fig)
    return {"fpc": float(fpc), "pertenca_media": float(pertenca_max.mean())}


if __name__ == "__main__":
    import json
    r = analisar()
    print(json.dumps(r, ensure_ascii=False, indent=2))
