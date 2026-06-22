"""Actualiza r_imigracao em intensidades_reais.csv — grelha alinhada a gerar_procura()."""
from __future__ import annotations
import os
import pandas as pd
import numpy as np
from geo import gerar_procura
from dm.construir_dados_reais import campo_imigracao_combinado

BASE = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(BASE, "dados/processados/intensidades_reais.csv")
COLS = ["lon", "lat", "dist_costa_km", "r_droga", "r_pesca", "r_poluicao", "r_imigracao",
        "ais_embarcacoes", "ais_rotas"]


def _key(lon, lat):
    return round(float(lon), 5), round(float(lat), 5)


def main():
    pts = gerar_procura()
    imig, n_iom, n_pt = campo_imigracao_combinado(pts)

    old = {}
    if os.path.exists(OUT):
        df0 = pd.read_csv(OUT)
        for r in df0.itertuples():
            old[_key(r.lon, r.lat)] = r._asdict()

    rows = []
    for p, ri in zip(pts, imig):
        k = _key(p["lon"], p["lat"])
        prev = old.get(k, {})
        rows.append({
            "lon": p["lon"],
            "lat": p["lat"],
            "dist_costa_km": p["dist_costa_km"],
            "r_droga": prev.get("r_droga", 0.0),
            "r_pesca": prev.get("r_pesca", 0.0),
            "r_poluicao": prev.get("r_poluicao", 0.0),
            "r_imigracao": round(float(ri), 5),
            "ais_embarcacoes": prev.get("ais_embarcacoes", 0.0),
            "ais_rotas": prev.get("ais_rotas", 0.0),
        })

    df = pd.DataFrame(rows)[COLS]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"r_imigracao actualizado — IOM mar={n_iom}, desembarques PT={n_pt}")
    print(f"  linhas={len(df)}  méd={df['r_imigracao'].mean():.3f}  "
          f"máx={df['r_imigracao'].max():.3f}  >0.5: {(df['r_imigracao']>=0.5).sum()}")


if __name__ == "__main__":
    main()
