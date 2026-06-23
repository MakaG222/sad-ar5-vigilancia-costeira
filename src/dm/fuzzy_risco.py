"""
fuzzy_risco.py — Sistema de inferência difusa (Mamdani) para o risco marítimo.

Aplica a lógica difusa ensinada na cadeira: variáveis linguísticas com funções
de pertença, base de regras SE–ENTÃO, operadores mín/máx, inferência de Mamdani
e desfuzzificação pelo método do centróide.

Entradas (0–1): intensidade de droga, pesca, poluição, imigração.
Saída (0–1): risco.

Vantagem sobre a média ponderada: capta não-linearidades e reforço quando várias
ameaças são simultaneamente elevadas, de forma interpretável por regras.
"""
from __future__ import annotations
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import skfuzzy as fuzz
from skfuzzy import control as ctrl

OUT = os.path.join(os.path.dirname(__file__), "../../resultados/dm")
os.makedirs(OUT, exist_ok=True)

_u = np.arange(0, 1.01, 0.01)


def _construir_sistema():
    droga = ctrl.Antecedent(_u, "droga")
    pesca = ctrl.Antecedent(_u, "pesca")
    poluicao = ctrl.Antecedent(_u, "poluicao")
    imigracao = ctrl.Antecedent(_u, "imigracao")
    risco = ctrl.Consequent(_u, "risco")

    # funções de pertença triangulares: baixo / medio / alto
    for v in (droga, pesca, poluicao, imigracao):
        v["baixo"] = fuzz.trimf(_u, [0, 0, 0.4])
        v["medio"] = fuzz.trimf(_u, [0.2, 0.5, 0.8])
        v["alto"] = fuzz.trimf(_u, [0.6, 1, 1])

    risco["mt_baixo"] = fuzz.trimf(_u, [0, 0, 0.25])
    risco["baixo"] = fuzz.trimf(_u, [0.1, 0.3, 0.5])
    risco["medio"] = fuzz.trimf(_u, [0.35, 0.55, 0.75])
    risco["alto"] = fuzz.trimf(_u, [0.6, 0.8, 0.95])
    risco["mt_alto"] = fuzz.trimf(_u, [0.8, 1, 1])

    R = [
        ctrl.Rule(droga["alto"], risco["mt_alto"]),
        ctrl.Rule(droga["alto"] & imigracao["alto"], risco["mt_alto"]),
        ctrl.Rule(droga["medio"], risco["alto"]),
        ctrl.Rule(imigracao["alto"], risco["alto"]),
        ctrl.Rule(poluicao["alto"], risco["alto"]),
        ctrl.Rule(droga["medio"] & poluicao["medio"], risco["alto"]),
        ctrl.Rule(pesca["alto"], risco["medio"]),
        ctrl.Rule((poluicao["medio"] | imigracao["medio"]) & droga["baixo"], risco["medio"]),
        ctrl.Rule(pesca["medio"] & poluicao["baixo"] & droga["baixo"], risco["baixo"]),
        ctrl.Rule(droga["baixo"] & pesca["baixo"] & poluicao["baixo"] &
                  imigracao["baixo"], risco["mt_baixo"]),
    ]
    sistema = ctrl.ControlSystem(R)
    return sistema, (droga, pesca, poluicao, imigracao, risco)


def risco_fuzzy(fd, fp, fo, fi):
    """Aplica o sistema difuso a vetores de intensidade (0–1) e devolve risco."""
    sistema, _ = _construir_sistema()
    sim = ctrl.ControlSystemSimulation(sistema)
    fd, fp, fo, fi = map(np.asarray, (fd, fp, fo, fi))
    out = np.zeros(len(fd))
    for i in range(len(fd)):
        sim.input["droga"] = float(np.clip(fd[i], 0, 1))
        sim.input["pesca"] = float(np.clip(fp[i], 0, 1))
        sim.input["poluicao"] = float(np.clip(fo[i], 0, 1))
        sim.input["imigracao"] = float(np.clip(fi[i], 0, 1))
        try:
            sim.compute()
            out[i] = sim.output["risco"]
        except Exception:
            out[i] = 0.0
    m = out.max()
    return out / m if m > 0 else out


def fig_pertencas():
    _, vars_ = _construir_sistema()
    droga, pesca, poluicao, imigracao, risco = vars_
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for termo in ("baixo", "medio", "alto"):
        axes[0].plot(_u, droga[termo].mf, label=termo)
    axes[0].set_title("Funções de pertença — entrada (ex.: droga)")
    axes[0].set_xlabel("intensidade"); axes[0].set_ylabel("grau de pertença")
    axes[0].legend()
    for termo in ("mt_baixo", "baixo", "medio", "alto", "mt_alto"):
        axes[1].plot(_u, risco[termo].mf, label=termo)
    axes[1].set_title("Funções de pertença — saída (risco)")
    axes[1].set_xlabel("risco"); axes[1].legend()
    fig.tight_layout(); fig.savefig(f"{OUT}/fuzzy_pertencas.png", dpi=140)
    plt.close(fig)


if __name__ == "__main__":
    fig_pertencas()
    # teste rápido
    fd = np.array([0.9, 0.1, 0.5, 0.2])
    fp = np.array([0.1, 0.1, 0.5, 0.8])
    fo = np.array([0.2, 0.1, 0.6, 0.3])
    fi = np.array([0.8, 0.1, 0.4, 0.9])
    print("risco fuzzy:", np.round(risco_fuzzy(fd, fp, fo, fi), 3))
