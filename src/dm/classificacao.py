"""
classificacao.py — Aprendizagem supervisionada (modelação preditiva).

Tarefa: prever se uma apreensão é MARÍTIMA (sim/não) a partir de atributos sem
fuga de informação (grupo de droga, região, estação, mês, ano, quantidade).

Aplica as quatro famílias de algoritmos da cadeira, cada uma em configuração
BASE e OTIMIZADA (GridSearchCV):
  - Classificador de Bayes (Naive Bayes — Gaussiano)
  - Aprendizagem baseada em instâncias (k-vizinhos mais próximos)
  - Árvores de decisão (CART, Gini / entropia)
  - Redes neuronais (Perceptrão Multicamada, MLP)

Trata o forte desequilíbrio de classes (≈3,4 % marítimas) com SMOTE (oversampling
sintético) integrado no pipeline — garantindo que ocorre apenas nos folds de treino
— e com class_weight nas árvores. Avaliação: holdout estratificado 70/30 + validação
cruzada estratificada (5 folds); matriz de confusão; exatidão, confiança positiva
(precisão), sensibilidade (recall), F1, ROC-AUC e PR-AUC; e análise de ajuste do
limiar de decisão para o modelo recomendado.
"""
from __future__ import annotations
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import (train_test_split, StratifiedKFold,
                                     cross_val_score, GridSearchCV)
from sklearn.preprocessing import StandardScaler
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (confusion_matrix, classification_report,
                             roc_auc_score, roc_curve, f1_score,
                             precision_score, recall_score, accuracy_score,
                             average_precision_score, precision_recall_curve)

from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline

from .preproc import carregar_e_limpar, features_classificacao

OUT = os.path.join(os.path.dirname(__file__), "../../resultados/dm")
os.makedirs(OUT, exist_ok=True)
RANDOM = 42
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM)


def _smote_pipe(clf):
    """Pipeline com normalização + SMOTE + classificador. O SMOTE é aplicado
    apenas internamente (folds de treino), evitando fuga de informação."""
    return ImbPipeline([("sc", StandardScaler()),
                        ("sm", SMOTE(random_state=RANDOM)),
                        ("clf", clf)])


def _definicoes(k_neighbors_smote):
    """Configurações BASE e respetivas grelhas de OTIMIZAÇÃO por família.
    As árvores usam class_weight='balanced' (sem SMOTE, por não serem sensíveis
    a escala); as restantes famílias usam SMOTE no pipeline."""
    base = {
        "NB (base)": _smote_pipe(GaussianNB()),
        "k-NN (base)": _smote_pipe(KNeighborsClassifier(n_neighbors=7)),
        "Árvore (base)": DecisionTreeClassifier(max_depth=6, class_weight="balanced",
                                                random_state=RANDOM),
        "MLP (base)": _smote_pipe(MLPClassifier(hidden_layer_sizes=(10, 5),
                                                max_iter=600, random_state=RANDOM)),
    }
    grelhas = {
        "NB (otim.)": (_smote_pipe(GaussianNB()),
                       {"clf__var_smoothing": [1e-10, 1e-9, 1e-8, 1e-7]}),
        "k-NN (otim.)": (_smote_pipe(KNeighborsClassifier()),
                         {"clf__n_neighbors": [5, 7, 11, 15],
                          "clf__weights": ["uniform", "distance"]}),
        "Árvore (otim.)": (DecisionTreeClassifier(class_weight="balanced",
                                                  random_state=RANDOM),
                           {"criterion": ["gini", "entropy"],
                            "max_depth": [4, 6, 8, None],
                            "min_samples_leaf": [1, 5, 10]}),
        "MLP (otim.)": (_smote_pipe(MLPClassifier(max_iter=600, random_state=RANDOM)),
                        {"clf__hidden_layer_sizes": [(10, 5), (32,), (64,)],
                         "clf__alpha": [1e-4, 1e-3]}),
    }
    return base, grelhas


def _avaliar(clf, Xte, yte):
    yp = clf.predict(Xte)
    try:
        proba = clf.predict_proba(Xte)[:, 1]
    except Exception:
        proba = yp.astype(float)
    return {
        "accuracy": accuracy_score(yte, yp),
        "precision": precision_score(yte, yp, zero_division=0),
        "recall": recall_score(yte, yp, zero_division=0),
        "f1": f1_score(yte, yp, zero_division=0),
        "auc": roc_auc_score(yte, proba),
        "pr_auc": average_precision_score(yte, proba),
        "cm": confusion_matrix(yte, yp),
        "proba": proba,
    }


def treinar_avaliar():
    df = carregar_e_limpar(log=False)
    X, y, _ = features_classificacao(df)
    cols = list(X.columns)
    X = X.astype(float).values

    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=RANDOM)

    base, grelhas = _definicoes(k_neighbors_smote=7)

    resultados, rocs, prs, hiper = {}, {}, {}, {}

    # --- configurações BASE ---
    for nome, clf in base.items():
        clf.fit(Xtr, ytr)
        r = _avaliar(clf, Xte, yte)
        resultados[nome] = r
        rocs[nome] = roc_curve(yte, r["proba"])
        prs[nome] = precision_recall_curve(yte, r["proba"])

    # --- configurações OTIMIZADAS (GridSearchCV, scoring=F1) ---
    modelos_otim = {}
    for nome, (est, grid) in grelhas.items():
        gs = GridSearchCV(est, grid, scoring="f1", cv=CV, n_jobs=-1)
        gs.fit(Xtr, ytr)
        modelos_otim[nome] = gs.best_estimator_
        hiper[nome] = gs.best_params_
        r = _avaliar(gs.best_estimator_, Xte, yte)
        resultados[nome] = r
        rocs[nome] = roc_curve(yte, r["proba"])
        prs[nome] = precision_recall_curve(yte, r["proba"])

    # modelo recomendado: melhor PR-AUC entre os otimizados (métrica apropriada
    # a classes raras — Davis & Goadrich, 2006)
    nome_rec = max(grelhas.keys(), key=lambda n: resultados[n]["pr_auc"])
    modelo_rec = modelos_otim[nome_rec]

    # árvore otimizada para visualização (regras interpretáveis)
    arvore = modelos_otim["Árvore (otim.)"]

    _fig_confusao(resultados)
    _fig_comparacao(resultados)
    _fig_roc(rocs)
    _fig_pr(prs, y)
    _fig_arvore(arvore, cols)
    _fig_importancia(arvore, cols)
    lim = _fig_limiar(yte, resultados[nome_rec]["proba"], nome_rec)

    cv = validacao_cruzada(Xtr, ytr, base, grelhas, hiper)
    extra = {"nome_recomendado": nome_rec, "hiperparametros": hiper,
             "limiar": lim, "n_teste_pos": int(yte.sum()),
             "n_teste": int(len(yte))}
    return resultados, cols, modelos_otim, cv, extra


def validacao_cruzada(Xtr, ytr, base, grelhas, hiper):
    """Validação cruzada estratificada (5 folds) das configurações otimizadas,
    reportando média ± desvio de F1, ROC-AUC e PR-AUC. O SMOTE encontra-se dentro
    do pipeline, pelo que é reaplicado em cada fold de treino sem contaminar a
    validação (ImbPipeline)."""
    # reconstruir estimadores otimizados com os melhores hiperparâmetros
    _, grelhas2 = _definicoes(7)
    estim = {}
    for nome, (est, _grid) in grelhas2.items():
        est.set_params(**hiper[nome])
        estim[nome] = est
    out = {}
    for nome, est in estim.items():
        f1 = cross_val_score(est, Xtr, ytr, cv=CV, scoring="f1")
        auc = cross_val_score(est, Xtr, ytr, cv=CV, scoring="roc_auc")
        pr = cross_val_score(est, Xtr, ytr, cv=CV, scoring="average_precision")
        out[nome] = {"f1_media": float(f1.mean()), "f1_desvio": float(f1.std()),
                     "auc_media": float(auc.mean()), "auc_desvio": float(auc.std()),
                     "pr_media": float(pr.mean()), "pr_desvio": float(pr.std())}
    _fig_cv(out)
    return out


# ------------------------------- FIGURAS -------------------------------

def _fig_cv(cv):
    nomes = list(cv.keys())
    x = np.arange(len(nomes)); w = 0.27
    f1m = [cv[n]["f1_media"] for n in nomes]; f1s = [cv[n]["f1_desvio"] for n in nomes]
    aum = [cv[n]["auc_media"] for n in nomes]; aus = [cv[n]["auc_desvio"] for n in nomes]
    prm = [cv[n]["pr_media"] for n in nomes]; prs = [cv[n]["pr_desvio"] for n in nomes]
    fig, ax = plt.subplots(figsize=(9.5, 5))
    ax.bar(x - w, f1m, w, yerr=f1s, capsize=4, label="F1", color="#d73027")
    ax.bar(x, aum, w, yerr=aus, capsize=4, label="ROC-AUC", color="#4575b4")
    ax.bar(x + w, prm, w, yerr=prs, capsize=4, label="PR-AUC", color="#1a9850")
    ax.set_xticks(x); ax.set_xticklabels(nomes, rotation=12, fontsize=9)
    ax.set_ylim(0, 1.05); ax.set_ylabel("Valor (média ± desvio)")
    ax.set_title("Validação cruzada estratificada (5 folds) — modelos otimizados")
    ax.legend(); ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(f"{OUT}/clf_validacao_cruzada.png", dpi=140)
    plt.close(fig)


def _fig_confusao(res):
    nomes = list(res.keys()); n = len(nomes)
    ncol = 4; nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.1 * ncol, 3.2 * nrow))
    axes = np.atleast_1d(axes).ravel()
    for ax, nome in zip(axes, nomes):
        cm = res[nome]["cm"]
        ax.imshow(cm, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(cm[i, j]), ha="center", va="center",
                        color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=10)
        ax.set_title(nome, fontsize=9)
        ax.set_xticks([0, 1]); ax.set_yticks([0, 1])
        ax.set_xticklabels(["não", "marít."], fontsize=7)
        ax.set_yticklabels(["não", "marít."], fontsize=7)
        ax.set_xlabel("previsto", fontsize=7); ax.set_ylabel("real", fontsize=7)
    for ax in axes[n:]:
        ax.axis("off")
    fig.suptitle("Matrizes de confusão (conjunto de teste)", fontsize=12)
    fig.tight_layout(); fig.savefig(f"{OUT}/clf_confusao.png", dpi=140)
    plt.close(fig)


def _fig_comparacao(res):
    nomes = list(res.keys())
    metr = [("recall", "Sensibilidade"), ("precision", "Confiança positiva"),
            ("f1", "F1"), ("auc", "ROC-AUC"), ("pr_auc", "PR-AUC")]
    fig, ax = plt.subplots(figsize=(11, 5.2))
    x = np.arange(len(nomes)); w = 0.16
    for i, (m, lab) in enumerate(metr):
        ax.bar(x + (i - 2) * w, [res[n][m] for n in nomes], w, label=lab)
    ax.set_xticks(x); ax.set_xticklabels(nomes, rotation=18, fontsize=8.5)
    ax.set_ylim(0, 1.05); ax.set_ylabel("Valor")
    ax.set_title("Comparação de classificadores (base vs. otimizado) — apreensão marítima")
    ax.legend(ncol=5, fontsize=8); ax.grid(alpha=0.3, axis="y")
    fig.tight_layout(); fig.savefig(f"{OUT}/clf_comparacao.png", dpi=140)
    plt.close(fig)


def _fig_roc(rocs):
    fig, ax = plt.subplots(figsize=(7, 6.2))
    for nome, (fpr, tpr, _) in rocs.items():
        ax.plot(fpr, tpr, lw=1.3, label=nome)
    ax.plot([0, 1], [0, 1], "k--", lw=1)
    ax.set_xlabel("Taxa de falsos positivos"); ax.set_ylabel("Taxa de verdadeiros positivos")
    ax.set_title("Curvas ROC"); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(f"{OUT}/clf_roc.png", dpi=140)
    plt.close(fig)


def _fig_pr(prs, y):
    base_rate = float(np.mean(y))
    fig, ax = plt.subplots(figsize=(7, 6.2))
    for nome, (prec, rec, _) in prs.items():
        ax.plot(rec, prec, lw=1.3, label=nome)
    ax.axhline(base_rate, color="gray", ls="--", lw=1,
               label=f"acaso (prevalência = {base_rate:.3f})")
    ax.set_xlabel("Sensibilidade (recall)"); ax.set_ylabel("Confiança positiva (precisão)")
    ax.set_title("Curvas Precisão–Sensibilidade (informativas em classes raras)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(f"{OUT}/clf_pr.png", dpi=140)
    plt.close(fig)


def _fig_limiar(yte, proba, nome_rec):
    limiares = np.linspace(0.05, 0.95, 19)
    precs, recs, f1s = [], [], []
    for t in limiares:
        yp = (proba >= t).astype(int)
        precs.append(precision_score(yte, yp, zero_division=0))
        recs.append(recall_score(yte, yp, zero_division=0))
        f1s.append(f1_score(yte, yp, zero_division=0))
    t_opt = float(limiares[int(np.argmax(f1s))])
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.plot(limiares, precs, "-o", ms=4, label="Confiança positiva", color="#4575b4")
    ax.plot(limiares, recs, "-s", ms=4, label="Sensibilidade", color="#d73027")
    ax.plot(limiares, f1s, "-^", ms=4, label="F1", color="#1a9850")
    ax.axvline(0.5, color="gray", ls=":", lw=1, label="limiar nominal 0,5")
    ax.axvline(t_opt, color="black", ls="--", lw=1, label=f"F1 máx. em {t_opt:.2f}")
    ax.set_xlabel("Limiar de decisão"); ax.set_ylabel("Valor")
    ax.set_title(f"Ajuste do limiar — modelo recomendado [{nome_rec}]")
    ax.legend(fontsize=8.5); ax.grid(alpha=0.3); ax.set_ylim(0, 1.02)
    fig.tight_layout(); fig.savefig(f"{OUT}/clf_limiar.png", dpi=140)
    plt.close(fig)
    return {"limiar_f1_otimo": t_opt,
            "f1_no_otimo": float(max(f1s)),
            "recall_em_0.25": float(recs[int(np.argmin(np.abs(limiares - 0.25)))])}


def _fig_arvore(tree, cols):
    fig, ax = plt.subplots(figsize=(16, 8))
    plot_tree(tree, feature_names=cols, class_names=["não", "marít."],
              filled=True, max_depth=3, fontsize=7, ax=ax, impurity=True)
    ax.set_title("Árvore de decisão otimizada (CART) — primeiros níveis")
    fig.tight_layout(); fig.savefig(f"{OUT}/clf_arvore.png", dpi=130)
    plt.close(fig)


def _fig_importancia(tree, cols):
    imp = tree.feature_importances_
    ordem = np.argsort(imp)[::-1][:10]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh([cols[i] for i in ordem][::-1], imp[ordem][::-1], color="#4575b4")
    ax.set_title("Importância das variáveis (Árvore de decisão otimizada)")
    ax.set_xlabel("Importância")
    fig.tight_layout(); fig.savefig(f"{OUT}/clf_importancia.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    res, cols, _, cv, extra = treinar_avaliar()
    print(f"{'Modelo':16s} {'Acc':>6} {'CPos':>6} {'Sens':>6} {'F1':>6} {'ROC':>6} {'PR':>6}")
    for nome, r in res.items():
        print(f"{nome:16s} {r['accuracy']:6.3f} {r['precision']:6.3f} "
              f"{r['recall']:6.3f} {r['f1']:6.3f} {r['auc']:6.3f} {r['pr_auc']:6.3f}")
    print(f"\nModelo recomendado: {extra['nome_recomendado']}")
    print("Hiperparâmetros otimizados:")
    for n, h in extra["hiperparametros"].items():
        print(f"  {n}: {h}")
    print("\nValidação cruzada (5 folds, otimizados):")
    for nome, c in cv.items():
        print(f"  {nome:16s} F1={c['f1_media']:.3f}±{c['f1_desvio']:.3f}  "
              f"ROC={c['auc_media']:.3f}±{c['auc_desvio']:.3f}  "
              f"PR={c['pr_media']:.3f}±{c['pr_desvio']:.3f}")
    print(f"\nAjuste do limiar: F1 máx em {extra['limiar']['limiar_f1_otimo']:.2f} "
          f"(F1={extra['limiar']['f1_no_otimo']:.3f})")
