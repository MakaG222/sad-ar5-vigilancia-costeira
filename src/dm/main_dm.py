"""
main_dm.py — Orquestrador do módulo de Data Mining e integração com o SAD.

Executa o pipeline CRISP-DM (preparação -> exploração -> modelação ->
avaliação) e integra os resultados no Sistema de Apoio à Decisão de drones:
  - EDA / visualização
  - Clustering (hotspots -> zonas de patrulha)
  - Classificação (deteção de apreensão marítima)
  - Lógica difusa (risco) e comparação com a média ponderada
  - Otimização de drones sobre o risco difuso vs. ponderado

Saídas: resultados/dm/*.png e resultados/dm/dm_resultados.json
"""
from __future__ import annotations
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# permitir importar os módulos do SAD de drones (pasta src/)
SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from dm import eda, clustering, classificacao, fuzzy_risco, projecao
from geo import gerar_procura, bases_proj, COSTA_LONLAT, _KX, _KY
from risco import calcular_risco
from otimizacao import (set_cover, raio_por_autonomia, dimensionar_persistencia)

OUT = os.path.join(os.path.dirname(__file__), "../../resultados/dm")
XLSX = os.path.join(os.path.dirname(__file__), "../../dados/fontes/apreensoes_droga_PT.xlsx")
os.makedirs(OUT, exist_ok=True)
LIMIAR = 0.5


def comparar_risco_fuzzy_ponderado():
    pts = gerar_procura()
    rp = calcular_risco(pts, XLSX)  # ponderado; guarda r_droga... nos pts
    fd = np.array([p["r_droga"] for p in pts])
    fp = np.array([p["r_pesca"] for p in pts])
    fo = np.array([p["r_poluicao"] for p in pts])
    fi = np.array([p["r_imigracao"] for p in pts])
    rf = fuzzy_risco.risco_fuzzy(fd, fp, fo, fi)

    lon = np.array([p["lon"] for p in pts]); lat = np.array([p["lat"] for p in pts])
    clon = [c[0] for c in COSTA_LONLAT]; clat = [c[1] for c in COSTA_LONLAT]

    fig, axes = plt.subplots(1, 3, figsize=(16, 7))
    for ax, val, tit in [(axes[0], rp, "Risco — média ponderada"),
                         (axes[1], rf, "Risco — inferência difusa (Mamdani)")]:
        sc = ax.scatter(lon, lat, c=val, cmap="YlOrRd", s=12, marker="s", vmin=0, vmax=1)
        ax.plot(clon, clat, color="#444", lw=1)
        ax.set_xlim(-11, -6.3); ax.set_ylim(36.4, 42.2)
        ax.set_aspect(1.0 / np.cos(np.radians(39.5)))
        ax.set_title(tit); plt.colorbar(sc, ax=ax, shrink=0.6)
    axes[2].scatter(rp, rf, s=6, alpha=0.4, color="#4575b4")
    axes[2].plot([0, 1], [0, 1], "k--", lw=1)
    axes[2].set_xlabel("Risco ponderado"); axes[2].set_ylabel("Risco difuso")
    axes[2].set_title(f"Correlação (r = {np.corrcoef(rp, rf)[0,1]:.2f})")
    axes[2].grid(alpha=0.3)
    fig.suptitle("Comparação do índice de risco: média ponderada vs. lógica difusa", fontsize=13)
    fig.tight_layout(); fig.savefig(f"{OUT}/fuzzy_vs_ponderado.png", dpi=140)
    plt.close(fig)

    # otimização sobre o risco difuso
    area_cel = (0.10 * _KX) * (0.10 * _KY)
    bases = bases_proj()
    for p, v in zip(pts, rf):
        p["risco"] = float(v)
    pts_alto = [p for p in pts if p["risco"] >= LIMIAR]
    R_long = raio_por_autonomia(6.0, 4.0)
    sc = set_cover(pts, bases, R_long, LIMIAR)
    fr = dimensionar_persistencia(pts_alto, bases, sc["bases_sel"], area_cel)
    return {"correlacao_fuzzy_ponderado": float(np.corrcoef(rp, rf)[0, 1]),
            "n_alto_risco_fuzzy": len(pts_alto),
            "frota_fuzzy": fr["frota_total"],
            "n_sim_fuzzy": fr["n_simultaneos"]}


def main():
    print(">> EDA ...")
    r_eda = eda.gerar()
    print(">> Clustering ...")
    r_clu = clustering.analisar()
    print(">> Projeção PCA ...")
    r_pca = projecao.gerar()
    print(">> Classificação (base vs. otimizado, SMOTE+GridSearch) + validação cruzada ...")
    res_clf, cols, _, cv, extra = classificacao.treinar_avaliar()
    print(">> Lógica difusa ...")
    fuzzy_risco.fig_pertencas()
    r_fz = comparar_risco_fuzzy_ponderado()

    clf_tab = {nome: {k: (round(float(r[k]), 3) if k not in ("cm", "proba") else
                          (r[k].tolist() if k == "cm" else None))
                      for k in ["accuracy", "precision", "recall", "f1", "auc",
                                "pr_auc", "cm"]}
               for nome, r in res_clf.items()}

    resultados = {"eda": r_eda, "clustering": r_clu, "pca": r_pca,
                  "classificacao": clf_tab, "validacao_cruzada": cv,
                  "modelo_recomendado": extra["nome_recomendado"],
                  "hiperparametros": {k: {kk: str(vv) for kk, vv in v.items()}
                                      for k, v in extra["hiperparametros"].items()},
                  "limiar": extra["limiar"], "fuzzy": r_fz}
    with open(f"{OUT}/dm_resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print("\n===== DATA MINING — RESUMO =====")
    print(f"Clustering geral: k={r_clu['kmeans_geral_k']} (silhueta {r_clu['silhueta_max']:.2f}); "
          f"DBSCAN {r_clu['dbscan_clusters']} clusters")
    print("Zonas de patrulha (marítimas):")
    for z in r_clu["zonas_patrulha"]:
        print(f"  ({z['centro_lat']:.2f},{z['centro_lon']:.2f})  n={z['n_apreensoes']}  peso={z['peso']:.2f}")
    print("\nClassificadores (teste):")
    print(f"{'Modelo':16s} {'Acc':>6}{'CPos':>7}{'Sens':>7}{'F1':>7}{'ROC':>7}{'PR':>7}")
    for nome, r in res_clf.items():
        print(f"{nome:16s} {r['accuracy']:6.3f}{r['precision']:7.3f}{r['recall']:7.3f}"
              f"{r['f1']:7.3f}{r['auc']:7.3f}{r['pr_auc']:7.3f}")
    print(f"Modelo recomendado: {extra['nome_recomendado']} (limiar F1-ótimo "
          f"{extra['limiar']['limiar_f1_otimo']:.2f})")
    print("\nValidação cruzada (5 folds, otimizados):")
    for nome, c in cv.items():
        print(f"  {nome:16s} F1={c['f1_media']:.3f}±{c['f1_desvio']:.3f}  "
              f"ROC={c['auc_media']:.3f}±{c['auc_desvio']:.3f}  "
              f"PR={c['pr_media']:.3f}±{c['pr_desvio']:.3f}")
    print(f"\nPCA: CP1={100*r_pca['var_cp1']:.1f}%, CP2={100*r_pca['var_cp2']:.1f}%; "
          f"{r_pca['n_componentes_80pct']} componentes p/ 80% var.")
    print(f"Fuzzy C-Means FPC={r_clu['fuzzy_cmeans_fpc']:.2f}")
    print(f"Risco difuso vs ponderado: r={r_fz['correlacao_fuzzy_ponderado']:.2f}; "
          f"frota (risco difuso)={r_fz['frota_fuzzy']} drones")
    print("\nFiguras em resultados/dm/. JSON: resultados/dm/dm_resultados.json")


if __name__ == "__main__":
    main()
