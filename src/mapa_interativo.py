"""
mapa_interativo.py — Painel geoespacial interativo (Folium) com camadas AIS,
incidentes reais e métricas de validação (Fase C).

Camadas:
  • Risco agregado e por ameaça (heatmap + detalhe por célula)
  • Tráfego AIS — densidade de embarcações e corredores de rotas (EMODnet)
  • Incidentes IOM Missing Migrants (marcadores agrupados)
  • Apreensões marítimas recentes (2020+)
  • Bases recomendadas, cobertura AR5 e setores de patrulha
  • Painel lateral com respostas ao objetivo e resultados de validação
"""
from __future__ import annotations
import json
import os
import numpy as np
import pandas as pd

import folium
from folium.plugins import HeatMap, MarkerCluster, MiniMap, Fullscreen, MeasureControl
from sklearn.cluster import KMeans

from config import AERODROMOS, CENARIOS_VENTO, PESOS_AMEACA, AR5
from geo import gerar_procura, bases_proj, inv_proj, LON_MIN, LON_MAX, LAT_MIN, LAT_MAX
from risco import calcular_risco
from otimizacao import mclp, raio_efetivo, raio_por_autonomia

BASE = os.path.join(os.path.dirname(__file__), "..")
XLSX = os.path.join(BASE, "dados/fontes/apreensoes_droga_PT.xlsx")
CSV_REAIS = os.path.join(BASE, "dados/processados/intensidades_reais.csv")
CAMADAS_JSON = os.path.join(BASE, "resultados/camadas_mapa.json")
VALIDACAO_JSON = os.path.join(BASE, "resultados/validacao.json")
OUT = os.path.join(BASE, "resultados/mapa_interativo.html")
LIMIAR = 0.5

CORES_AMEACA = {
    "r_droga": ("Tráfico de droga", "#c0392b"),
    "r_pesca": ("Pesca ilegal (INN)", "#27ae60"),
    "r_poluicao": ("Poluição/derrames", "#8e44ad"),
    "r_imigracao": ("Imigração irregular", "#2980b9"),
}


def _cor_risco(r: float) -> str:
    if r >= 0.80: return "#800026"
    if r >= 0.65: return "#bd0026"
    if r >= 0.50: return "#e31a1c"
    if r >= 0.35: return "#fc4e2a"
    if r >= 0.20: return "#fd8d3c"
    if r >= 0.10: return "#feb24c"
    return "#ffeda0"


def _circulo_latlon(base, raio_km, n=90):
    ang = np.linspace(0, 2 * np.pi, n)
    xs = base["x"] + raio_km * np.cos(ang)
    ys = base["y"] + raio_km * np.sin(ang)
    return [list(inv_proj(x, y)[::-1]) for x, y in zip(xs, ys)]


def zonas_patrulha(pts_alto, k):
    coords = np.array([(p["lat"], p["lon"]) for p in pts_alto])
    pesos = np.array([p["risco"] for p in pts_alto])
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    lab = km.fit_predict(coords, sample_weight=pesos)
    setores = []
    for c in range(k):
        m = lab == c
        if not m.any():
            continue
        sub, w = coords[m], pesos[m]
        setores.append({
            "centro": (float(np.average(sub[:, 0], weights=w)),
                       float(np.average(sub[:, 1], weights=w))),
            "n": int(m.sum()), "risco_medio": float(w.mean()),
            "risco_max": float(w.max())})
    setores.sort(key=lambda s: s["risco_medio"], reverse=True)
    return setores


def _carregar_ais(pts):
    """Carrega campos AIS da grelha processada."""
    if not os.path.exists(CSV_REAIS):
        return None, None
    df = pd.read_csv(CSV_REAIS)
    if len(df) != len(pts):
        return None, None
    emb = df["ais_embarcacoes"].to_numpy() if "ais_embarcacoes" in df.columns else None
    rot = df["ais_rotas"].to_numpy() if "ais_rotas" in df.columns else None
    return emb, rot


def _carregar_camadas():
    if os.path.exists(CAMADAS_JSON):
        with open(CAMADAS_JSON, encoding="utf-8") as f:
            return json.load(f)
    return {"iom": [], "apreensoes": [], "validacao": {}}


def _painel_html(n_celulas, k_rec, bases_rec, frac, frota, val: dict) -> str:
    obj = val.get("resposta_objetivo", {})
    bt = val.get("backtest_temporal", {})
    bl = val.get("baseline_patrulha", {})
    q2 = obj.get("Q2_quantos", {}).get("resposta", "—")
    q3 = obj.get("Q3_bases", {}).get("resposta", "—")
    bt_txt = ""
    if bt.get("n_holdout", 0) > 0:
        bt_txt = (f"<br><b>Validação temporal:</b> {100*bt['taxa_acerto_limiar']:.0f}% das "
                  f"apreensões 2023–24 em alto risco "
                  f"(ganho {bt.get('ganho_relativo_limiar',0):.1f}× vs aleatório)")
    bl_txt = ""
    if bl:
        bl_txt = (f"<br><b>Baseline:</b> SAD captura {bl.get('pct_risco_total_capturado_sad',0):.0f}% "
                  f"do risco ({bl.get('ganho_sad_vs_aleatorio',0):.1f}× vs patrulha aleatória)")
    return f"""
    <div id="sad-panel" style="position:fixed;top:12px;right:12px;z-index:9999;
        background:rgba(15,32,55,0.94);color:#fff;padding:12px 16px;border-radius:10px;
        box-shadow:0 2px 12px rgba(0,0,0,0.45);font:12px/1.5 Arial,sans-serif;
        max-width:340px;max-height:90vh;overflow-y:auto;">
      <b style="font-size:14px;color:#5dade2">SAD — Vigilância Costeira AR5 (PT)</b><br>
      <span style="opacity:.8">Costa portuguesa · dados AIS + incidentes reais</span>
      <hr style="border-color:#34495e;margin:8px 0">
      <b style="color:#f39c12">Resposta ao objetivo</b><br>
      <span style="font-size:11px">
        <b>Onde:</b> Sul/SW, Lisboa–Setúbal, NW<br>
        <b>Quantos:</b> {q2}<br>
        <b>Bases:</b> {q3}
      </span>
      <hr style="border-color:#34495e;margin:8px 0">
      <span style="font-size:11px">
        {n_celulas} células · <b>{k_rec} bases</b> ({bases_rec})<br>
        Cobertura: <b>{100*frac:.0f}%</b> do risco · Frota 24 h: <b>{frota} AR5</b>
        {bt_txt}{bl_txt}
      </span>
      <hr style="border-color:#34495e;margin:8px 0">
      <span style="font-size:10px;opacity:.85">
        Camadas AIS: EMODnet vessel/route density (AIS agregado).<br>
        Ative «Tráfego AIS» e «Incidentes reais» no controlo de camadas.
      </span>
    </div>"""


def _legenda_html() -> str:
    return """
    <div style="position:fixed;bottom:28px;left:18px;z-index:9999;
        background:rgba(255,255,255,0.95);padding:12px 14px;border-radius:8px;
        box-shadow:0 1px 6px rgba(0,0,0,0.3);font:11px/1.45 Arial,sans-serif;color:#222;
        max-width:270px;">
      <b>Legenda</b><br>
      <i style="background:#800026;width:12px;height:12px;display:inline-block"></i> Risco &ge;0.80<br>
      <i style="background:#e31a1c;width:12px;height:12px;display:inline-block"></i> 0.50–0.80<br>
      <i style="background:#fd8d3c;width:12px;height:12px;display:inline-block"></i> 0.20–0.50<br>
      <i style="background:#ffeda0;width:12px;height:12px;display:inline-block"></i> &lt;0.20<br>
      <hr style="margin:5px 0">
      <span style="color:#1a5276">&#9632;</span> Tráfego AIS (EMODnet)<br>
      <span style="color:#8e44ad">&#9679;</span> Desembarque PT (imigração)<br>
      <span style="color:#922b21">&#9679;</span> Incidente IOM (migrantes)<br>
      <span style="color:#c0392b">&#9679;</span> Apreensão marítima (2020+)<br>
      <span style="color:navy">&#9650;</span> Aeródromo · <span style="color:#d35400">&#9733;</span> Base recomendada<br>
      <span style="color:#16a085">&#9679;</span> Setor de patrulha
    </div>"""


def _preparar_dados(frota_total: int | None = None):
    """Carrega grelha, risco, bases MCLP e camadas — partilhado por PNG e Folium."""
    pts = gerar_procura()
    bases = bases_proj()
    calcular_risco(pts, XLSX)
    ais_emb, ais_rot = _carregar_ais(pts)
    camadas = _carregar_camadas()
    val = camadas.get("validacao", {})
    if not val and os.path.exists(VALIDACAO_JSON):
        with open(VALIDACAO_JSON, encoding="utf-8") as f:
            val = json.load(f)

    R_calmo = raio_efetivo(CENARIOS_VENTO["calmo"])
    R_long = raio_por_autonomia(6.0, CENARIOS_VENTO["calmo"])

    pts_alto = [p for p in pts if p["risco"] >= LIMIAR]
    k_rec = 2
    rec = mclp(pts, bases, R_long, k_rec)
    bases_rec_idx = rec["bases_sel"]
    nomes_rec = [bases[b]["nome"] for b in bases_rec_idx]
    frac = rec["frac_risco"]
    setores = zonas_patrulha(pts_alto, k=6)
    frota_num = frota_total if frota_total is not None else 9
    frota_txt = frota_num if frota_total is not None else "—"

    return {
        "pts": pts, "bases": bases, "ais_emb": ais_emb, "ais_rot": ais_rot,
        "camadas": camadas, "val": val, "R_calmo": R_calmo, "R_long": R_long,
        "pts_alto": pts_alto, "k_rec": k_rec, "bases_rec_idx": bases_rec_idx,
        "nomes_rec": nomes_rec, "frac": frac, "setores": setores,
        "frota_num": frota_num, "frota_txt": frota_txt,
        "iom": camadas.get("iom", []),
        "des": camadas.get("desembarques_pt", []),
        "apr": camadas.get("apreensoes", []),
    }


def gerar(frota_total: int | None = None, html: bool = True):
    ctx = _preparar_dados(frota_total)
    pts, bases = ctx["pts"], ctx["bases"]
    ais_emb, ais_rot = ctx["ais_emb"], ctx["ais_rot"]
    camadas, val = ctx["camadas"], ctx["val"]
    R_calmo, R_long = ctx["R_calmo"], ctx["R_long"]
    bases_rec_idx = ctx["bases_rec_idx"]
    nomes_rec, frac = ctx["nomes_rec"], ctx["frac"]
    setores = ctx["setores"]
    frota_num, frota_txt = ctx["frota_num"], ctx["frota_txt"]
    k_rec = ctx["k_rec"]
    iom, des, apr = ctx["iom"], ctx["des"], ctx["apr"]

    png_path = exportar_figura_png(pts, bases, bases_rec_idx, ctx["pts_alto"], setores,
                                   camadas, R_calmo, R_long, nomes_rec, frac, frota_num)

    if not html:
        return {"ficheiro": None, "figura_png": png_path,
                "n_celulas": len(pts), "n_setores": len(setores),
                "bases_recomendadas": nomes_rec, "frac_risco": frac,
                "n_iom": len(iom), "n_desembarques": len(des), "n_apreensoes": len(apr),
                "tem_ais": ais_emb is not None}

    m = folium.Map(location=[38.5, -9.2], zoom_start=7, tiles=None, control_scale=True,
                   min_zoom=6, max_bounds=True)
    m.fit_bounds([[LAT_MIN, LON_MIN], [LAT_MAX, LON_MAX]])
    folium.TileLayer("CartoDB positron", name="Base clara").add_to(m)
    folium.TileLayer(
        tiles="https://tiles.openseamap.org/seamark/{z}/{x}/{y}.png",
        attr="OpenSeaMap", name="Carta náutica (OpenSeaMap)", overlay=True, show=False
    ).add_to(m)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", show=False).add_to(m)

    # ---- Risco agregado ----
    fg_heat = folium.FeatureGroup(name="① Risco — mapa de calor", show=True)
    HeatMap([[p["lat"], p["lon"], p["risco"]] for p in pts],
            radius=14, blur=18, min_opacity=0.25,
            gradient={0.2: "#ffeda0", 0.4: "#fd8d3c", 0.6: "#e31a1c", 0.85: "#800026"}
            ).add_to(fg_heat)
    fg_heat.add_to(m)

    fg_cel = folium.FeatureGroup(name="Risco — células (detalhe)", show=False)
    for p in pts:
        folium.CircleMarker(
            location=[p["lat"], p["lon"]], radius=3.4, weight=0,
            fill=True, fill_color=_cor_risco(p["risco"]), fill_opacity=0.85,
            popup=folium.Popup(
                f"<b>Risco: {p['risco']:.2f}</b><br>"
                f"Droga: {p['r_droga']:.2f} · Pesca: {p['r_pesca']:.2f}<br>"
                f"Poluição: {p['r_poluicao']:.2f} · Imigração: {p['r_imigracao']:.2f}<br>"
                f"Dist. costa: {p['dist_costa_km']:.0f} km", max_width=230)
        ).add_to(fg_cel)
    fg_cel.add_to(m)

    # ---- Ameaças individuais ----
    for chave, (titulo, _) in CORES_AMEACA.items():
        peso = PESOS_AMEACA[chave.split("_")[1]]
        fg = folium.FeatureGroup(name=f"Ameaça — {titulo} (w={peso:.2f})", show=False)
        HeatMap([[p["lat"], p["lon"], p[chave]] for p in pts],
                radius=13, blur=17, min_opacity=0.2).add_to(fg)
        fg.add_to(m)

    # ---- AIS: densidade de embarcações ----
    if ais_emb is not None:
        fg_ais = folium.FeatureGroup(name="② Tráfego AIS — embarcações (EMODnet)", show=True)
        dados = [[p["lat"], p["lon"], float(ais_emb[i])] for i, p in enumerate(pts)
                 if ais_emb[i] > 0.05]
        if dados:
            HeatMap(dados, radius=12, blur=15, min_opacity=0.3,
                    gradient={0.1: "#d6eaf8", 0.4: "#3498db", 0.7: "#1a5276", 1.0: "#0b2545"}
                    ).add_to(fg_ais)
        fg_ais.add_to(m)

    # ---- AIS: corredores de rotas ----
    if ais_rot is not None:
        fg_rot = folium.FeatureGroup(name="③ Tráfego AIS — corredores/rotas", show=False)
        dados = [[p["lat"], p["lon"], float(ais_rot[i])] for i, p in enumerate(pts)
                 if ais_rot[i] > 0.05]
        if dados:
            HeatMap(dados, radius=14, blur=16, min_opacity=0.25,
                    gradient={0.1: "#ebf5fb", 0.5: "#2e86c1", 1.0: "#154360"}
                    ).add_to(fg_rot)
        fg_rot.add_to(m)

    # ---- Desembarques PT (imigração) ----
    if des:
        fg_des = folium.FeatureGroup(
            name="④ Desembarques marítimos PT (imigração)", show=True)
        cluster_des = MarkerCluster(name="Desembarques cluster")
        for inc in des:
            folium.CircleMarker(
                location=[inc["lat"], inc["lon"]], radius=6,
                color="#6c3483", weight=1, fill=True, fill_color="#9b59b6", fill_opacity=0.75,
                popup=folium.Popup(
                    f"<b>Desembarque PT</b><br>"
                    f"Ano: {inc.get('ano', '?')}<br>"
                    f"Distrito: {inc.get('distrito', '?')}<br>"
                    f"Rota: {inc.get('rota', '?')}<br>"
                    f"Pessoas: {inc.get('n_pessoas', '?')}", max_width=240)
            ).add_to(cluster_des)
        cluster_des.add_to(fg_des)
        fg_des.add_to(m)

    # ---- Incidentes IOM ----
    if iom:
        fg_iom = folium.FeatureGroup(name="⑤ Incidentes reais — IOM Missing Migrants", show=True)
        cluster = MarkerCluster(name="IOM cluster")
        for inc in iom:
            folium.CircleMarker(
                location=[inc["lat"], inc["lon"]], radius=5,
                color="#922b21", weight=1, fill=True, fill_color="#e74c3c", fill_opacity=0.7,
                popup=folium.Popup(
                    f"<b>Incidente IOM</b><br>"
                    f"Data: {inc.get('data','?')}<br>"
                    f"Rota: {inc.get('rota','?')}<br>"
                    f"Vítimas: {inc.get('vitimas',1)}", max_width=240)
            ).add_to(cluster)
        cluster.add_to(fg_iom)
        fg_iom.add_to(m)

    # ---- Apreensões marítimas recentes ----
    if apr:
        fg_apr = folium.FeatureGroup(name="⑥ Apreensões marítimas (2020+)", show=False)
        for a in apr:
            folium.CircleMarker(
                location=[a["lat"], a["lon"]], radius=4,
                color="#641e16", weight=1, fill=True, fill_color="#c0392b", fill_opacity=0.65,
                popup=folium.Popup(f"<b>Apreensão marítima</b><br>Ano: {a.get('ano','?')}",
                                   max_width=180)
            ).add_to(fg_apr)
        fg_apr.add_to(m)

    # ---- Aeródromos ----
    fg_aer = folium.FeatureGroup(name="Aeródromos candidatos", show=False)
    for nome, lon, lat, reg in AERODROMOS:
        folium.Marker(
            [lat, lon], tooltip=nome,
            popup=folium.Popup(f"<b>{nome}</b><br>Região: {reg}", max_width=200),
            icon=folium.Icon(color="darkblue", icon="plane", prefix="fa")
        ).add_to(fg_aer)
    fg_aer.add_to(m)

    # ---- Bases recomendadas ----
    fg_rec = folium.FeatureGroup(name="Bases recomendadas + cobertura AR5", show=True)
    for b in bases_rec_idx:
        base = bases[b]
        folium.Marker(
            [base["lat"], base["lon"]], tooltip=f"BASE: {base['nome']}",
            popup=folium.Popup(
                f"<b>{base['nome']}</b><br>Alcance AR5: {R_long:.0f} km<br>"
                f"Raio tático: {R_calmo:.0f} km<br>"
                f"Sensor: EO/IR + <b>AIS integrado</b>", max_width=240),
            icon=folium.Icon(color="orange", icon="star", prefix="fa")
        ).add_to(fg_rec)
        folium.Polygon(_circulo_latlon(base, R_calmo), color="#d35400", weight=1.5,
                       fill=True, fill_color="#e67e22", fill_opacity=0.10).add_to(fg_rec)
        folium.Polygon(_circulo_latlon(base, R_long), color="#d35400", weight=1.0,
                       dash_array="6", fill=False).add_to(fg_rec)
    fg_rec.add_to(m)

    # ---- Setores de patrulha ----
    fg_set = folium.FeatureGroup(name="Zonas de patrulha (setores)", show=True)
    for i, s in enumerate(setores, 1):
        clat, clon = s["centro"]
        folium.CircleMarker(
            [clat, clon], radius=9, color="#16a085", weight=2,
            fill=True, fill_color="#1abc9c", fill_opacity=0.6,
            tooltip=f"Setor {i}",
            popup=folium.Popup(
                f"<b>Setor {i}</b><br>Risco médio: {s['risco_medio']:.2f}<br>"
                f"Células: {s['n']}", max_width=200)
        ).add_to(fg_set)
        folium.map.Marker(
            [clat, clon],
            icon=folium.DivIcon(html=f"<div style='font:bold 12px Arial;color:#0b5345'>{i}</div>")
        ).add_to(fg_set)
    fg_set.add_to(m)

    Fullscreen(position="topleft").add_to(m)
    MiniMap(toggle_display=True, position="bottomright").add_to(m)
    MeasureControl(primary_length_unit="kilometers",
                   secondary_length_unit="nauticalmiles").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    m.get_root().html.add_child(folium.Element(
        _painel_html(len(pts), k_rec, ", ".join(nomes_rec), frac, frota_txt, val)))
    m.get_root().html.add_child(folium.Element(_legenda_html()))

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    m.save(OUT)
    return {"ficheiro": os.path.abspath(OUT), "figura_png": png_path,
            "n_celulas": len(pts),
            "n_setores": len(setores), "bases_recomendadas": nomes_rec,
            "frac_risco": frac, "n_iom": len(iom), "n_desembarques": len(des),
            "n_apreensoes": len(apr),
            "tem_ais": ais_emb is not None}


def exportar_figura_png(pts, bases, bases_rec_idx, pts_alto, setores, camadas,
                        R_calmo, R_long, nomes_rec, frac, frota):
    """Figura estática para o relatório (Fig. 20) — alinhada com o painel Folium actual."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    from matplotlib.lines import Line2D

    fig_path = os.path.join(BASE, "resultados/figuras/20_mapa_interativo.png")
    os.makedirs(os.path.dirname(fig_path), exist_ok=True)

    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.set_facecolor("#e8f4f8")
    ax.set_xlim(LON_MIN - 0.15, LON_MAX + 0.15)
    ax.set_ylim(LAT_MIN - 0.1, LAT_MAX + 0.1)
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.set_title("Painel geoespacial SAD — risco, AIS, incidentes e bases AR5 (PT)", fontsize=11)

    # Células de risco (mar)
    lons = [p["lon"] for p in pts]
    lats = [p["lat"] for p in pts]
    rs = [p["risco"] for p in pts]
    sc = ax.scatter(lons, lats, c=rs, cmap="YlOrRd", s=8, alpha=0.75, vmin=0, vmax=1,
                    edgecolors="none", zorder=2)

    # Apreensões
    for a in camadas.get("apreensoes", []):
        ax.scatter(a["lon"], a["lat"], c="#c0392b", s=18, alpha=0.7, zorder=4,
                   edgecolors="#641e16", linewidths=0.4)

    # Desembarques PT
    for inc in camadas.get("desembarques_pt", []):
        ax.scatter(inc["lon"], inc["lat"], c="#8e44ad", s=35, marker="o",
                   edgecolors="#4a235a", linewidths=0.5, zorder=5, alpha=0.85)

    # IOM
    for inc in camadas.get("iom", []):
        ax.scatter(inc["lon"], inc["lat"], c="#9b59b6", s=80, marker="*",
                   edgecolors="#4a235a", linewidths=0.5, zorder=5)

    # Bases recomendadas + raios
    for b in bases_rec_idx:
        base = bases[b]
        ax.scatter(base["lon"], base["lat"], c="#e67e22", s=120, marker="^",
                   edgecolors="#d35400", linewidths=1, zorder=6)
        ax.annotate(base["nome"].split("(")[0].strip(), (base["lon"], base["lat"]),
                    xytext=(4, 4), textcoords="offset points", fontsize=7, color="#d35400")
        for r_km, alpha in ((R_calmo, 0.08), (R_long, 0.04)):
            circ = Circle((base["lon"], base["lat"]), r_km / 111.0,
                          fill=True, facecolor="#e67e22", edgecolor="#d35400",
                          alpha=alpha, linewidth=0.8, linestyle="--", zorder=1)
            ax.add_patch(circ)

    # Setores
    for i, s in enumerate(setores, 1):
        clat, clon = s["centro"]
        ax.scatter(clon, clat, c="#16a085", s=60, edgecolors="#0b5345", linewidths=0.8, zorder=5)
        ax.text(clon, clat, str(i), fontsize=7, ha="center", va="center", color="white", zorder=6)

    # Painel lateral (resumo)
    txt = (f"Q1: Sul/SW · Lisboa–Setúbal · NW\n"
           f"Q2: ≈ {frota} AR5 (24 h)\n"
           f"Q3: {', '.join(nomes_rec)}\n"
           f"Cobertura: {100*frac:.0f}% risco alto")
    ax.text(0.02, 0.98, txt, transform=ax.transAxes, fontsize=8, va="top",
            bbox=dict(boxstyle="round", facecolor="#152a45", alpha=0.85),
            color="white", family="monospace")

    leg = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#e31a1c", markersize=6, label="Risco"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#c0392b", markersize=6, label="Apreensões"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#8e44ad", markersize=6, label="Desembarques PT"),
        Line2D([0], [0], marker="*", color="w", markerfacecolor="#9b59b6", markersize=10, label="IOM"),
        Line2D([0], [0], marker="^", color="w", markerfacecolor="#e67e22", markersize=8, label="Base MCLP"),
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#16a085", markersize=6, label="Setor"),
    ]
    ax.legend(handles=leg, loc="lower right", fontsize=7, framealpha=0.9)
    plt.colorbar(sc, ax=ax, fraction=0.025, pad=0.02, label="Índice de risco")
    fig.tight_layout()
    fig.savefig(fig_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return os.path.abspath(fig_path)


if __name__ == "__main__":
    import sys
    html = "--png-only" not in sys.argv
    info = gerar(frota_total=9, html=html)
    print("Figura PNG:", info["figura_png"])
    if info["ficheiro"]:
        print("Mapa:", info["ficheiro"])
    print(f"  AIS={'sim' if info['tem_ais'] else 'não'}  desembarques={info['n_desembarques']}  "
          f"IOM={info['n_iom']}  apreensões={info['n_apreensoes']}")
