"""
main.py — Orquestra o Sistema de Apoio à Decisão (SAD) para vigilância costeira
com o TEKEVER AR5 e produz mapas, tabelas e resultados.

Pipeline:
  1. Gera grelha de células marítimas (Portugal Continental, até ~300 km da costa)
  2. Calcula o índice de risco multi-ameaça (droga, pesca, poluição, imigração)
  3. Otimiza a localização de bases (set cover) e a curva de trade-off (MCLP)
  4. Dimensiona a frota para cobertura 24 h em vários cenários de vento e de alcance
  5. Exporta figuras (resultados/figuras) e tabelas/JSON (resultados)
"""
from __future__ import annotations
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from config import (AERODROMOS, AR5, CENARIOS_VENTO, PESOS_AMEACA, RAIO_BASE_KM,
                    fator_vento, FONTES, SENSOR_SWATH_KM, TEMPO_REVISITA_H,
                    T_ON_MIN_H)
from geo import gerar_procura, bases_proj, COSTA_LONLAT, proj, inv_proj, _KX, _KY
from geo import LON_MIN, LON_MAX, LAT_MIN, LAT_MAX
from risco import calcular_risco
from otimizacao import (set_cover, curva_tradeoff, dimensionar_frota,
                        raio_efetivo, raio_por_autonomia, matriz_cobertura,
                        mclp, dimensionar_persistencia)

XLSX = "../dados/fontes/apreensoes_droga_PT.xlsx"
FIGDIR = "../resultados/figuras"
OUTDIR = "../resultados"
os.makedirs(FIGDIR, exist_ok=True)

LIMIAR = 0.5  # limiar de "alto risco"
COSTA_LON = [c[0] for c in COSTA_LONLAT]
COSTA_LAT = [c[1] for c in COSTA_LONLAT]


def circulo_lonlat(base, raio_km, n=120):
    ang = np.linspace(0, 2 * np.pi, n)
    xs = base["x"] + raio_km * np.cos(ang)
    ys = base["y"] + raio_km * np.sin(ang)
    lon = np.array([inv_proj(x, y)[0] for x, y in zip(xs, ys)])
    lat = np.array([inv_proj(x, y)[1] for x, y in zip(xs, ys)])
    return lon, lat


def _base_map(ax):
    ax.plot(COSTA_LON, COSTA_LAT, color="#444", lw=1.5, zorder=3)
    ax.set_xlabel("Longitude (°)"); ax.set_ylabel("Latitude (°)")
    ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX)
    ax.set_aspect(1.0 / np.cos(np.radians(39.5)))


# ---------------------------------------------------------------------------
def fig_risco(pts):
    lon = [p["lon"] for p in pts]; lat = [p["lat"] for p in pts]
    r = [p["risco"] for p in pts]
    fig, ax = plt.subplots(figsize=(7, 8))
    sc = ax.scatter(lon, lat, c=r, cmap="YlOrRd", s=14, marker="s",
                    vmin=0, vmax=1, zorder=2)
    for nome, blon, blat, reg in AERODROMOS:
        ax.plot(blon, blat, "^", color="navy", ms=8, zorder=4)
    _base_map(ax)
    plt.colorbar(sc, ax=ax, label="Índice de risco [0–1]", shrink=0.7)
    ax.set_title("Índice de risco marítimo multi-ameaça\n(Portugal Continental)")
    ax.legend([plt.Line2D([], [], marker="^", color="navy", ls="")],
              ["Aeródromos candidatos"], loc="lower left")
    fig.tight_layout(); fig.savefig(f"{FIGDIR}/01_risco.png", dpi=140)
    plt.close(fig)


def fig_ameacas(pts):
    lon = np.array([p["lon"] for p in pts]); lat = np.array([p["lat"] for p in pts])
    campos = [("r_droga", "Tráfico de droga", "Reds"),
              ("r_pesca", "Pesca ilegal (INN)", "Greens"),
              ("r_poluicao", "Poluição/derrames", "Purples"),
              ("r_imigracao", "Imigração irregular", "Blues")]
    fig, axes = plt.subplots(2, 2, figsize=(11, 12))
    for (chave, titulo, cmap), ax in zip(campos, axes.ravel()):
        v = [p[chave] for p in pts]
        sc = ax.scatter(lon, lat, c=v, cmap=cmap, s=8, marker="s", vmin=0, vmax=1)
        ax.plot(COSTA_LON, COSTA_LAT, color="#444", lw=1.0)
        ax.set_xlim(LON_MIN, LON_MAX); ax.set_ylim(LAT_MIN, LAT_MAX)
        ax.set_aspect(1.0 / np.cos(np.radians(39.5)))
        ax.set_title(f"{titulo}  (peso {PESOS_AMEACA[chave.split('_')[1]]:.2f})")
        plt.colorbar(sc, ax=ax, shrink=0.7)
    fig.suptitle("Campos de intensidade por ameaça", fontsize=14)
    fig.tight_layout(); fig.savefig(f"{FIGDIR}/02_ameacas.png", dpi=140)
    plt.close(fig)


def fig_cobertura(pts, bases, raio_km, sc, nome_fich, titulo):
    a = matriz_cobertura(pts, bases, raio_km)
    sel = sc["bases_sel"]
    cob = a[sel].sum(axis=0) > 0 if sel else np.zeros(len(pts), bool)
    fig, ax = plt.subplots(figsize=(7.5, 8.5))
    lon = np.array([p["lon"] for p in pts]); lat = np.array([p["lat"] for p in pts])
    risco = np.array([p["risco"] for p in pts])
    alto = risco >= LIMIAR
    ax.scatter(lon[~alto], lat[~alto], c="#dddddd", s=6, marker="s", zorder=1)
    ax.scatter(lon[alto & cob], lat[alto & cob], c="#1a9850", s=12, marker="s",
               zorder=2, label="Alto risco — COBERTO")
    ax.scatter(lon[alto & ~cob], lat[alto & ~cob], c="#d73027", s=12, marker="s",
               zorder=2, label="Alto risco — não coberto")
    for b in sel:
        clon, clat = circulo_lonlat(bases[b], raio_km)
        ax.plot(clon, clat, color="navy", lw=1.2, alpha=0.8, zorder=3)
        ax.plot(bases[b]["lon"], bases[b]["lat"], "^", color="navy", ms=10, zorder=5)
        ax.annotate(bases[b]["nome"], (bases[b]["lon"], bases[b]["lat"]),
                    fontsize=7, xytext=(3, 3), textcoords="offset points")
    _base_map(ax)
    ax.set_title(titulo)
    ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout(); fig.savefig(f"{FIGDIR}/{nome_fich}", dpi=140)
    plt.close(fig)


def fig_tradeoff(curvas, nomes):
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for (curva, nome) in zip(curvas, nomes):
        ks = [c["k"] for c in curva]
        fr = [100 * c["frac_risco"] for c in curva]
        ax.plot(ks, fr, "-o", label=nome)
    ax.axhline(95, color="gray", ls="--", lw=1)
    ax.set_xlabel("Nº de bases (drones simultâneos no ar)")
    ax.set_ylabel("Risco total coberto (%)")
    ax.set_title("Curva de trade-off — cobertura de risco vs. nº de bases (MCLP)")
    ax.grid(alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(f"{FIGDIR}/05_tradeoff.png", dpi=140)
    plt.close(fig)


def fig_frota_k(frota_vs_k, k_rec):
    ks = [f["k"] for f in frota_vs_k]
    ft = [f["frota_total"] for f in frota_vs_k]
    fr = [100 * f["frac_risco"] for f in frota_vs_k]
    fig, ax1 = plt.subplots(figsize=(8.5, 5.5))
    ax1.plot(ks, ft, "-o", color="#d73027", label="Frota total (24 h)")
    ax1.axvline(k_rec, color="green", ls="--", lw=1.2, label=f"Ótimo: {k_rec} bases")
    ax1.set_xlabel("Nº de bases utilizadas")
    ax1.set_ylabel("Frota total de AR5 (drones)", color="#d73027")
    for x, y in zip(ks, ft):
        ax1.text(x, y + 0.3, str(y), ha="center", fontsize=8, color="#d73027")
    ax2 = ax1.twinx()
    ax2.plot(ks, fr, "-s", color="#4575b4", alpha=0.7, label="Risco coberto (%)")
    ax2.set_ylabel("Risco total coberto (%)", color="#4575b4")
    ax2.axhline(95, color="#4575b4", ls=":", lw=1)
    ax1.set_title("Frota mínima vs. nº de bases (cobertura persistente 24 h)")
    ax1.grid(alpha=0.3); ax1.legend(loc="upper right")
    fig.tight_layout(); fig.savefig(f"{FIGDIR}/08_frota_vs_bases.png", dpi=140)
    plt.close(fig)


def fig_sensibilidade(sens):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for ax, (titulo, dados) in zip(axes, sens.items()):
        xs = [d["valor"] for d in dados]
        ys = [d["frota_total"] for d in dados]
        ax.plot(xs, ys, "-o", color="#d73027")
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.2, str(y), ha="center", fontsize=9)
        ax.set_title(titulo); ax.set_ylabel("Frota total (drones)")
        ax.grid(alpha=0.3)
    fig.suptitle("Análise de sensibilidade da frota (configuração recomendada)",
                 fontsize=13)
    fig.tight_layout(); fig.savefig(f"{FIGDIR}/07_sensibilidade.png", dpi=140)
    plt.close(fig)


def fig_frota(cenarios):
    nomes = list(cenarios.keys())
    nb = [cenarios[n]["set_cover"]["n_bases"] for n in nomes]
    ft = [cenarios[n]["frota"]["frota_total"] for n in nomes]
    x = np.arange(len(nomes)); w = 0.38
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(x - w/2, nb, w, label="Bases / drones simultâneos", color="#4575b4")
    ax.bar(x + w/2, ft, w, label="Frota total (24 h)", color="#d73027")
    for i, v in enumerate(nb): ax.text(i - w/2, v + 0.1, str(v), ha="center")
    for i, v in enumerate(ft): ax.text(i + w/2, v + 0.1, str(v), ha="center")
    ax.set_xticks(x); ax.set_xticklabels(nomes)
    ax.set_ylabel("Nº de drones")
    ax.set_title("Dimensionamento da frota AR5 por cenário de vento (R base 90 km)")
    ax.legend()
    fig.tight_layout(); fig.savefig(f"{FIGDIR}/06_frota.png", dpi=140)
    plt.close(fig)


# ---------------------------------------------------------------------------
def main():
    print(">> A gerar grelha de procura ...")
    pts = gerar_procura()
    bases = bases_proj()
    print(f"   {len(pts)} células, {len(bases)} bases candidatas")

    print(">> A calcular risco ...")
    calcular_risco(pts, XLSX)
    risco_total = sum(p["risco"] for p in pts)

    print(">> Figuras de risco ...")
    fig_risco(pts); fig_ameacas(pts)

    resultados = {"meta": {"n_celulas": len(pts), "limiar_alto_risco": LIMIAR,
                           "risco_total": risco_total, "AR5": AR5,
                           "pesos": PESOS_AMEACA}, "cenarios": {}}

    # ----- Cenário A: conservador (R base 90 km), 3 ventos -----
    print(">> Cenário A — conservador (R=90 km) por vento ...")
    cenarios_vento = {}
    for nome, vel in CENARIOS_VENTO.items():
        R = raio_efetivo(vel)
        sc = set_cover(pts, bases, R, LIMIAR)
        fr = dimensionar_frota(sc["n_bases"], R)
        cenarios_vento[f"{nome} ({vel:.0f} m/s)"] = {
            "vento_ms": vel, "fator": fator_vento(vel), "raio_km": R,
            "set_cover": sc, "frota": fr,
            "bases_nomes": [bases[b]["nome"] for b in sc["bases_sel"]]}
    resultados["cenarios"]["A_conservador_vento"] = cenarios_vento

    R_calmo = raio_efetivo(CENARIOS_VENTO["calmo"])
    sc_calmo = cenarios_vento[f"calmo ({CENARIOS_VENTO['calmo']:.0f} m/s)"]["set_cover"]
    fig_cobertura(pts, bases, R_calmo, sc_calmo, "03_cobertura_conservador.png",
                  f"Cenário A — Cobertura conservadora (R={R_calmo:.0f} km, vento calmo)\n"
                  f"{sc_calmo['n_bases']} bases | {sc_calmo['n_nao_cobrivel']} células de alto "
                  f"risco ao largo fora de alcance")
    fig_frota(cenarios_vento)

    # ----- Cenário B: alcance operacional real do AR5 -----
    print(">> Cenário B — alcance operacional AR5 (reachability) ...")
    area_celula = (0.10 * _KX) * (0.10 * _KY)  # km² por célula da grelha
    pts_alto = [p for p in pts if p["risco"] >= LIMIAR]

    # Raio de reachability (permanência mínima T_ON_MIN em estação)
    R_reach = raio_por_autonomia(T_ON_MIN_H, CENARIOS_VENTO["calmo"])
    sc_reach = set_cover(pts, bases, R_reach, LIMIAR)

    # Raio "alargado" (6 h em estação) para a curva de trade-off e mapas
    t_on_alvo = 6.0
    R_long = raio_por_autonomia(t_on_alvo, CENARIOS_VENTO["calmo"])

    # Curva de trade-off (MCLP) ao alcance alargado -> escolhe config recomendada
    print(">> Curvas de trade-off (MCLP) ...")
    c90 = curva_tradeoff(pts, bases, R_calmo)
    cL = curva_tradeoff(pts, bases, R_long)

    # Para cada k, calcula a frota persistente -> escolhe k que MINIMIZA a frota
    # (entre as configurações que cobrem >= 95% do risco). Mais bases reduzem o
    # trânsito (maior t_on, menor rotação), até um ótimo.
    print(">> A minimizar a frota (frota vs nº de bases) ...")
    frota_vs_k = []
    for c in cL:
        sel = c["bases_sel"]
        fp = dimensionar_persistencia(pts_alto, bases, sel, area_celula)
        frota_vs_k.append({"k": c["k"], "frac_risco": c["frac_risco"],
                           "frota_total": fp["frota_total"],
                           "n_sim": fp["n_simultaneos"],
                           "dist_media_km": fp["dist_media_km"],
                           "t_on_h": fp["t_on_h"],
                           "bases": [bases[b]["nome"] for b in sel]})
    elegiveis = [f for f in frota_vs_k if f["frac_risco"] >= 0.95]
    melhor = min(elegiveis, key=lambda f: f["frota_total"]) if elegiveis else frota_vs_k[-1]
    k_rec = melhor["k"]
    rec = mclp(pts, bases, R_long, k_rec)
    bases_rec = rec["bases_sel"]
    resultados["frota_vs_k"] = frota_vs_k

    # Frota por PERSISTÊNCIA sensorial (área total de alto risco), config recomendada
    fr_persist = dimensionar_persistencia(pts_alto, bases, bases_rec, area_celula)
    fig_frota_k(frota_vs_k, k_rec)

    # Frota por persistência só da faixa COSTEIRA (alto risco alcançável a 90 km)
    a90 = matriz_cobertura(pts_alto, bases, R_calmo)
    idx_cost = [i for i in range(len(pts_alto)) if a90[:, i].sum() > 0]
    pts_alto_cost = [pts_alto[i] for i in idx_cost]
    sc90 = set_cover(pts, bases, R_calmo, LIMIAR)
    fr_persist_cost = dimensionar_persistencia(pts_alto_cost, bases,
                                               sc90["bases_sel"], area_celula)

    resultados["cenarios"]["B_alcance_AR5"] = {
        "R_reach_km": R_reach, "reach_set_cover": sc_reach,
        "R_long_km": R_long, "k_recomendado": k_rec,
        "frac_risco_recomendado": rec["frac_risco"],
        "bases_recomendadas": [bases[b]["nome"] for b in bases_rec],
        "frota_persistencia_total": fr_persist,
        "frota_persistencia_costeira": fr_persist_cost,
        "n_alto_risco": len(pts_alto),
        "area_celula_km2": round(area_celula, 1)}

    sc_rec_like = {"bases_sel": bases_rec,
                   "n_nao_cobrivel": sum(1 for p in pts_alto
                                         if all(((bases[b]['x']-p['x'])**2 +
                                                 (bases[b]['y']-p['y'])**2) ** 0.5 > R_long
                                                for b in bases_rec))}
    fig_cobertura(pts, bases, R_long, sc_rec_like, "04_cobertura_alargado.png",
                  f"Cenário B — Configuração recomendada ({k_rec} bases, R={R_long:.0f} km)\n"
                  f"Cobre {100*rec['frac_risco']:.0f}% do risco total | frota persistente 24h: "
                  f"{fr_persist['frota_total']} drones")

    resultados["tradeoff"] = {"R90": c90, "R_long": cL,
                              "R90_km": R_calmo, "R_long_km": R_long}
    fig_tradeoff([c90, cL],
                 [f"R = {R_calmo:.0f} km (conservador)",
                  f"R = {R_long:.0f} km (alcance AR5)"])

    # ----- Análise de sensibilidade (frota persistente, config recomendada) -----
    print(">> Sensibilidade ...")
    sens = {"Largura útil do sensor (km)": [], "Tempo de revisita (h)": [],
            "Disponibilidade da frota": []}
    for w in [20, 30, 40, 50]:
        d = dimensionar_persistencia(pts_alto, bases, bases_rec, area_celula, swath_km=w)
        sens["Largura útil do sensor (km)"].append({"valor": w, "frota_total": d["frota_total"]})
    for t in [2, 3, 4, 6]:
        d = dimensionar_persistencia(pts_alto, bases, bases_rec, area_celula, revisita_h=t)
        sens["Tempo de revisita (h)"].append({"valor": t, "frota_total": d["frota_total"]})
    for a in [0.6, 0.7, 0.8, 0.9]:
        d = dimensionar_persistencia(pts_alto, bases, bases_rec, area_celula, disponibilidade=a)
        sens["Disponibilidade da frota"].append({"valor": a, "frota_total": d["frota_total"]})
    resultados["sensibilidade"] = sens
    fig_sensibilidade(sens)

    # ----- Exportar -----
    with open(f"{OUTDIR}/resultados.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2, default=float)

    # tabela resumo CSV
    import csv
    with open(f"{OUTDIR}/resumo_cenarios.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Cenario", "Vento_ms", "Raio_km", "N_bases",
                    "Drones_por_base", "Frota_total", "Bases"])
        for nome, c in cenarios_vento.items():
            w.writerow([f"A:{nome}", c["vento_ms"], f"{c['raio_km']:.0f}",
                        c["set_cover"]["n_bases"], c["frota"]["drones_por_base"],
                        c["frota"]["frota_total"], "; ".join(c["bases_nomes"])])
        w.writerow([f"B:persist. costeira", CENARIOS_VENTO["calmo"], f"{R_calmo:.0f}",
                    len(sc90["bases_sel"]), "-", fr_persist_cost["frota_total"],
                    "; ".join(bases[b]["nome"] for b in sc90["bases_sel"])])
        w.writerow([f"B:persist. total (recomendado)", CENARIOS_VENTO["calmo"],
                    f"{R_long:.0f}", k_rec, "-", fr_persist["frota_total"],
                    "; ".join(resultados["cenarios"]["B_alcance_AR5"]["bases_recomendadas"])])

    # ----- Validação Fase C (backtesting + baseline) -----
    print(">> Validação Fase C (backtesting + baseline) ...")
    try:
        import validacao
        validacao.main()
    except Exception as e:
        print(f"   (validação não gerada: {e})")

    # ----- Painel geoespacial interativo (Folium) -----
    print(">> Painel geoespacial interativo (Folium) ...")
    try:
        import mapa_interativo
        info_mapa = mapa_interativo.gerar(frota_total=fr_persist["frota_total"])
        print(f"   {info_mapa['ficheiro']}")
    except Exception as e:
        print(f"   (painel interativo não gerado: {e})")

    print("\n===== RESUMO =====")
    for nome, c in cenarios_vento.items():
        print(f"A {nome:18s} R={c['raio_km']:5.0f}km  bases={c['set_cover']['n_bases']}  "
              f"frota(simples)={c['frota']['frota_total']:3d}  fora_alcance={c['set_cover']['n_nao_cobrivel']}")
    print(f"\nB reachability      R={R_reach:5.0f}km  bases_min={sc_reach['n_bases']}  "
          f"(cobre todo o alto risco)")
    print(f"B recomendado       {k_rec} bases ({', '.join(resultados['cenarios']['B_alcance_AR5']['bases_recomendadas'])})  "
          f"cobre {100*rec['frac_risco']:.0f}% do risco")
    print(f"  -> Persistência COSTEIRA 24h: n_sim={fr_persist_cost['n_simultaneos']}  "
          f"frota={fr_persist_cost['frota_total']} drones")
    print(f"  -> Persistência TOTAL 24h:    n_sim={fr_persist['n_simultaneos']}  "
          f"frota={fr_persist['frota_total']} drones  (área {fr_persist['area_alto_risco_km2']:.0f} km²)")
    print("\nFiguras e tabelas em resultados/. JSON: resultados/resultados.json")


if __name__ == "__main__":
    main()
