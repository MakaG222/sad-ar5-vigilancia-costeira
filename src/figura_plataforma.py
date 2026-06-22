"""Figura 21 — esquema da plataforma operacional para o relatório."""
from __future__ import annotations
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BASE = os.path.join(os.path.dirname(__file__), "..")
OUT = os.path.join(BASE, "resultados/figuras/23_plataforma_operacional.png")


def gerar():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 6.5)
    ax.axis("off")
    ax.set_title("Plataforma operacional SAD AR5 — arquitectura e fluxo de decisão",
                 fontsize=11, pad=12)

    def box(x, y, w, h, text, color="#1a334d", fs=8):
        p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                           facecolor=color, edgecolor="#5dade2", linewidth=1)
        ax.add_patch(p)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color="white", wrap=True)

    # Fontes
    box(0.3, 4.8, 2.2, 1.2, "Fontes live\nOpen-Meteo · IPMA\nAIS · RSS", "#0f2037")
    box(0.3, 3.2, 2.2, 1.2, "Pipeline SAD\nrisco.json · validação\n camadas_mapa", "#0f2037")

    # API
    box(3.2, 3.5, 2.4, 2.2, "API FastAPI\nrotas OR-Tools\nmeteo → alcance\nWebSocket alertas", "#2980b9")

    # UI
    box(6.2, 2.8, 4.5, 3.2,
        "Interface web (React/Leaflet)\n"
        "· Mapa risco + k-means + incidentes\n"
        "· 7 cenários · validação rota (HUD)\n"
        "· Rotas sortie / 24 h / reactivo\n"
        "· Meteo live · WebSocket alertas\n"
        "· Modo apresentação + offline",
        "#152a45", fs=7.5)

    # Decisor
    box(6.2, 0.4, 4.5, 1.8,
        "Conclusões operacionais\n"
        "1. Priorizar sectores por ameaça (Q1)\n"
        "2. Ajustar frota ao vento (Q2)\n"
        "3. Lançar de Porto/Portimão ou base tática (Q3)",
        "#1e5631", fs=7.5)

    for x1, y1, x2, y2 in [(2.5, 5.4, 3.2, 4.8), (2.5, 3.8, 3.2, 4.2),
                           (5.6, 4.5, 6.2, 4.5), (8.45, 2.8, 8.45, 2.2)]:
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                     arrowstyle="->", color="#f39c12", lw=1.5,
                     connectionstyle="arc3,rad=0.1"))

    ax.text(5.5, 0.15, "http://localhost:5173  ·  protótipo quasi-tempo-real (demo CT302)",
            ha="center", fontsize=7, color="#566573")
    fig.tight_layout()
    fig.savefig(OUT, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return OUT


if __name__ == "__main__":
    print("Figura:", gerar())
