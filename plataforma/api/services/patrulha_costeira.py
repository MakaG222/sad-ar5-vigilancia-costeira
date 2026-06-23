"""Patrulha costeira alinhada com o pipeline analítico SAD (grelha + MCLP)."""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from config import (
    AERODROMOS,
    AR5,
    BASES_MCLP_RECOMENDADAS,
    JANELA_SECTOR_H,
    LIMIAR_RISCO_OPERACIONAL,
    N_ALVOS_SORTIE_PADRAO,
    N_SECTORES_COSTA,
    RESERVA_H,
    SENSOR_SWATH_KM,
    T_ON_MIN_H,
    T_ON_SORTIE_H,
)
from corredores_operacionais import bonus_corredor, nome_corredor
from geo import (
    bases_lancamento,
    corredor_costeiro,
    inv_proj,
    proj,
    sectores_costa,
)
from otimizacao import dimensionar_persistencia, mclp, raio_por_autonomia
from rotas_maritimas import (
    distancia_km,
    expandir_rota_maritima,
    orbita_maritima,
    ponto_entrada_mar,
    ponto_entrada_mar_sector,
    snap_maritimo,
)
from services.cenarios import regiao_from_dict
from services.grelha_cache import pts_mar
from services.meteo_rotas import resolver_vento
from services.rotas_ortools import tsp_com_retorno
from services.zonas_cluster import clusters_risco, zona_mais_proxima, zona_por_regiao
from services.zonas_patrulha import TIPOS, zonas_por_tipo

LIMIAR = LIMIAR_RISCO_OPERACIONAL

_CAMPO_TIPO = {
    "droga": "r_droga",
    "pesca": "r_pesca",
    "poluicao": "r_poluicao",
    "imigracao": "r_imigracao",
    "geral": "risco",
    "costeira": "risco",
}


def _filtrar_regiao(celulas: list[dict], regiao: dict | None) -> list[dict]:
    if not regiao:
        return celulas
    out = []
    for p in celulas:
        if regiao.get("lat_min") is not None and p["lat"] < regiao["lat_min"]:
            continue
        if regiao.get("lat_max") is not None and p["lat"] > regiao["lat_max"]:
            continue
        if regiao.get("lon_min") is not None and p["lon"] < regiao["lon_min"]:
            continue
        if regiao.get("lon_max") is not None and p["lon"] > regiao["lon_max"]:
            continue
        out.append(p)
    return out


def _regiao_meta(regiao: dict | None) -> dict | None:
    if not regiao:
        return None
    return {k: round(v, 3) if v is not None else None for k, v in regiao.items()}


def _enriquecer_foco(celulas: list[dict], pts: list[dict], zonas_info: dict, sector_idx: int | None) -> list[dict]:
    from geo import ponto_em_mar
    out = [p for p in celulas if ponto_em_mar(p["lon"], p["lat"])]
    pts_m = [p for p in pts if ponto_em_mar(p["lon"], p["lat"])]
    zonas = zonas_info.get("zonas", [])
    alvo = next((z for z in zonas if sector_idx is None or z["sector"] == sector_idx), None)
    if not alvo:
        if sector_idx is None and zonas:
            alvo = {"celulas": [c for z in zonas for c in z.get("celulas", [])]}
        else:
            return out
    for c in alvo.get("celulas", []):
        match = next((p for p in pts_m if abs(p["lon"] - c["lon"]) < 0.01
                      and abs(p["lat"] - c["lat"]) < 0.01), None)
        if match and match not in out:
            out.append(match)
    return out


def _celulas_patrol_sector(pts: list[dict], sector: list[dict]) -> list[dict]:
    """Células marítimas da grelha SAD dentro da faixa lat/lon do sector."""
    from geo import ponto_em_mar
    if not sector:
        return []
    lat0 = min(p["lat"] for p in sector) - 0.03
    lat1 = max(p["lat"] for p in sector) + 0.03
    lon0 = min(p["lon"] for p in sector) - 0.35
    lon1 = max(p["lon"] for p in sector) + 0.35
    seen: set[tuple[float, float]] = set()
    out: list[dict] = []
    for p in pts:
        if not ponto_em_mar(p["lon"], p["lat"]):
            continue
        if not (lat0 <= p["lat"] <= lat1 and lon0 <= p["lon"] <= lon1):
            continue
        k = (round(p["lon"], 3), round(p["lat"], 3))
        if k in seen:
            continue
        seen.add(k)
        out.append(p)
    for p in sector:
        if not ponto_em_mar(p["lon"], p["lat"]):
            continue
        k = (round(p["lon"], 3), round(p["lat"], 3))
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out


def _carregar():
    pts = pts_mar()
    corredor = corredor_costeiro(pts, dist_max_km=45.0)
    alto = [p for p in pts if p["risco"] >= LIMIAR]
    return pts, corredor, alto


def _celulas_cluster(zona_cluster: dict | None, pts: list[dict]) -> list[dict] | None:
    """Resolve células completas da grelha a partir do cluster k-means."""
    from geo import ponto_em_mar
    if not zona_cluster or not zona_cluster.get("celulas"):
        return None
    keys = {(round(c["lon"], 2), round(c["lat"], 2)) for c in zona_cluster["celulas"]}
    out = []
    for p in pts:
        if not ponto_em_mar(p["lon"], p["lat"]):
            continue
        k = (round(p["lon"], 2), round(p["lat"], 2))
        if k in keys:
            out.append(p)
            continue
        if (zona_cluster["lat_min"] <= p["lat"] <= zona_cluster["lat_max"]
                and zona_cluster["lon_min"] <= p["lon"] <= zona_cluster["lon_max"]):
            out.append(p)
    return out if len(out) >= 3 else None


def _base_por_nome(nome: str | None, lon: float | None = None, lat: float | None = None) -> dict:
    if lon is not None and lat is not None:
        x, y = proj(lon, lat)
        return {
            "nome": nome or "Lançamento personalizado",
            "lon": lon, "lat": lat, "x": x, "y": y,
            "forca": "Operacional", "tipo": "personalizado",
            "dist_costa_km": None,
        }
    bases = bases_lancamento()
    if nome:
        for b in bases:
            if b["nome"] == nome:
                return b
        chave = nome.lower().split("(")[0].strip()
        parciais = [
            b for b in bases
            if chave in b["nome"].lower() or b["nome"].lower().startswith(chave)
        ]
        if parciais:
            return min(parciais, key=lambda b: len(b["nome"]))
    for prefer in BASES_MCLP_RECOMENDADAS:
        for b in bases:
            if b["nome"] == prefer:
                return b
    return bases[0] if bases else {"nome": "Portimão", "lon": -8.584, "lat": 37.149,
                                    "x": proj(-8.584, 37.149)[0], "y": proj(-8.584, 37.149)[1]}


def _base_mais_proxima(base_candidatas: list[dict], ponto: dict) -> dict:
    return min(base_candidatas, key=lambda b: distancia_km(b, ponto))


def _bases_mclp_canonicas(bases_op: list[dict]) -> list[dict]:
    """Par MCLP do relatório (Q3): Porto + Portimão — coordenadas dos aeródromos."""
    out: list[dict] = []
    for nome in BASES_MCLP_RECOMENDADAS:
        b = next((b for b in bases_op if b["nome"] == nome), None)
        if not b:
            chave = nome.lower().split("(")[0].strip()
            parciais = [
                x for x in bases_op
                if chave in x["nome"].lower() or x["nome"].lower().startswith(chave)
            ]
            if parciais:
                b = min(parciais, key=lambda x: len(x["nome"]))
        if not b:
            for an, lon, lat, regiao in AERODROMOS:
                if an == nome:
                    x, y = proj(lon, lat)
                    b = {
                        "nome": an, "lon": lon, "lat": lat, "x": x, "y": y,
                        "forca": "Operacional", "tipo": "mclp",
                        "dist_costa_km": None, "regiao": regiao,
                    }
                    break
        if b:
            out.append({**b, "nome": nome if nome in BASES_MCLP_RECOMENDADAS else b["nome"]})
    return out


def _base_mclp_sector(bases_mclp: list[dict], sector: list[dict]) -> dict:
    """Atribui Porto ao Norte e Portimão ao Sul (~39,3°N)."""
    if len(bases_mclp) < 2:
        cx = sum(p["x"] for p in sector) / len(sector)
        cy = sum(p["y"] for p in sector) / len(sector)
        return _base_mais_proxima(bases_mclp, {"x": cx, "y": cy})
    porto = next(
        (b for b in bases_mclp if "carneiro" in b["nome"].lower() or b["nome"].startswith("Porto")),
        bases_mclp[0],
    )
    portimao = next(
        (b for b in bases_mclp if "portim" in b["nome"].lower()),
        bases_mclp[-1],
    )
    lat_c = sum(p["lat"] for p in sector) / len(sector)
    return porto if lat_c >= 39.3 else portimao


def _score_celula(p: dict, tipo_patrulha: str) -> float:
    campo = _CAMPO_TIPO.get(tipo_patrulha, "risco")
    r_tipo = p.get(campo, p.get("risco", 0))
    risco = p.get("risco", 0)
    dist_c = p.get("dist_costa_km", 50)
    prox_costa = max(0.0, 1.0 - dist_c / 45.0)
    base = 0.55 * r_tipo + 0.30 * risco + 0.15 * prox_costa
    if tipo_patrulha in ("droga", "imigracao", "pesca"):
        base *= bonus_corredor(p["lon"], p["lat"], tipo_patrulha)
    return base


def _dist_km(p1: dict, p2: dict) -> float:
    return distancia_km(p1, p2)


def _vizinhos(celula: dict, pool: list[dict], max_km: float = 14.0) -> list[dict]:
    """Células adjacentes no pool (continuidade espacial para varrimento)."""
    out = []
    for p in pool:
        if p is celula:
            continue
        if _dist_km(celula, p) <= max_km:
            out.append(p)
    return out


def _pool_varrimento(
    base_mar: dict,
    celulas: list[dict],
    alcance: float,
    tipo_patrulha: str,
    n_alvos: int = N_ALVOS_SORTIE_PADRAO,
    zona_cluster: dict | None = None,
    lat_bounds: tuple[float, float] | None = None,
    obrigatorios: list[dict] | None = None,
) -> tuple[list[dict], dict]:
    """
    Selecção de pontos para varrimento operacional:
    - prioriza zona k-means (hotspot SAD)
    - equilibra risco alto + continuidade espacial (não saltar zonas)
    - inclui células adjacentes de risco moderado para não deixar buracos
  """
    from geo import ponto_em_mar
    n_alvos = max(4, min(20, int(n_alvos)))
    swath_km = SENSOR_SWATH_KM
    celulas = [p for p in celulas if ponto_em_mar(p["lon"], p["lat"])]

    def dist_b(p):
        return distancia_km(base_mar, p)

    cand = [p for p in celulas if dist_b(p) <= alcance * 0.94]
    if lat_bounds:
        lat0, lat1 = lat_bounds
        cand_lat = [p for p in cand if lat0 <= p["lat"] <= lat1]
        if len(cand_lat) >= 3:
            cand = cand_lat
    if not cand:
        cand = sorted(celulas, key=dist_b)[:min(n_alvos * 2, len(celulas))]
        if lat_bounds:
            lat0, lat1 = lat_bounds
            cand_lat = [p for p in cand if lat0 <= p["lat"] <= lat1]
            if cand_lat:
                cand = cand_lat

    # Refinar com células da zona cluster (se disponível)
    if zona_cluster and zona_cluster.get("celulas"):
        zkeys = {(round(c["lon"], 2), round(c["lat"], 2)) for c in zona_cluster["celulas"]}
        no_cluster = [
            p for p in cand
            if (round(p["lon"], 2), round(p["lat"], 2)) in zkeys
            or (zona_cluster["lat_min"] <= p["lat"] <= zona_cluster["lat_max"]
                and zona_cluster["lon_min"] <= p["lon"] <= zona_cluster["lon_max"])
        ]
        if len(no_cluster) >= 3:
            cand = no_cluster

    scored = sorted(cand, key=lambda p: _score_celula(p, tipo_patrulha), reverse=True)
    if not scored:
        return [], {}

    # Semente: melhor score dentro do alcance (ou células obrigatórias da zona de foco)
    pool: list[dict] = []
    seen: set[int] = set()
    for ob in obrigatorios or []:
        if dist_b(ob) <= alcance * 0.98 and id(ob) not in seen:
            pool.append(ob)
            seen.add(id(ob))
    if not pool and scored:
        pool = [scored[0]]
        seen = {id(scored[0])}
    elif scored and not pool:
        pool = [scored[0]]
        seen.add(id(scored[0]))
    elif scored and pool:
        for s in scored:
            if id(s) not in seen:
                pool.append(s)
                seen.add(id(s))
                break

    # Crescimento por adjacência (varrimento contíguo)
    anchor = pool[0] if pool else scored[0]
    frontier = list(_vizinhos(anchor, cand, max_km=swath_km * 0.45))
    while len(pool) < n_alvos and frontier:
        frontier.sort(key=lambda p: _score_celula(p, tipo_patrulha), reverse=True)
        nxt = frontier.pop(0)
        if id(nxt) in seen:
            continue
        if dist_b(nxt) > alcance * 0.94:
            continue
        pool.append(nxt)
        seen.add(id(nxt))
        for v in _vizinhos(nxt, cand, max_km=swath_km * 0.45):
            if id(v) not in seen:
                frontier.append(v)

    # Preencher com bandas N→S (cobertura costeira sistemática no sector)
    if len(pool) < n_alvos:
        bandas: dict[float, list] = {}
        fonte_bandas = [p for p in cand if id(p) not in seen] or cand
        for p in fonte_bandas:
            if id(p) in seen:
                continue
            bk = round(p["lat"], 1)
            bandas.setdefault(bk, []).append(p)
        for bk in sorted(bandas.keys(), reverse=True):
            for p in sorted(bandas[bk], key=lambda x: _score_celula(x, tipo_patrulha), reverse=True):
                if id(p) in seen:
                    continue
                if dist_b(p) > alcance * 0.94:
                    continue
                pool.append(p)
                seen.add(id(p))
                if len(pool) >= n_alvos:
                    break
            if len(pool) >= n_alvos:
                break

    # Último recurso: top score global
    for p in scored:
        if len(pool) >= n_alvos:
            break
        if id(p) not in seen and dist_b(p) <= alcance * 0.94:
            pool.append(p)
            seen.add(id(p))

    pool.sort(key=lambda p: (-p["lat"], p["lon"]))
    meta = {
        "estrategia": "varrimento_kmeans_adjacente",
        "zona_cluster": zona_cluster.get("nome") if zona_cluster else None,
        "zona_id": zona_cluster.get("id") if zona_cluster else None,
        "n_candidatas": len(cand),
        "swath_km": swath_km,
        "cobertura_estimada_km2": round(len(pool) * 95.0 * 0.35, 0),
    }
    return pool[:n_alvos], meta


def _pool_patrol(
    base_mar: dict,
    celulas: list[dict],
    alcance: float,
    tipo_patrulha: str,
    n_alvos: int = N_ALVOS_SORTIE_PADRAO,
    zona_cluster: dict | None = None,
) -> list[dict]:
    pool, _ = _pool_varrimento(base_mar, celulas, alcance, tipo_patrulha, n_alvos, zona_cluster)
    return pool


def _waypoint(p: dict, tipo: str = "patrulha", ordem: int | None = None) -> dict:
    wp = {
        "lon": p["lon"], "lat": p["lat"], "tipo": tipo,
        "risco": round(p.get("risco", 0), 2),
        "dist_costa_km": round(p.get("dist_costa_km", 0), 1),
        "nome": f"Patrulha r={p.get('risco', 0):.2f}",
    }
    if ordem is not None:
        wp["ordem_costa"] = ordem
    return wp


def _meteo_ctx(
    base: dict,
    meteo_bases: list[dict] | None,
    vento_ms: float | None,
    usar_meteo_live: bool,
    t_on_h: float,
    lat_sector: float | None = None,
    lon_sector: float | None = None,
) -> dict:
    return resolver_vento(
        base, meteo_bases, vento_ms, usar_meteo_live,
        lat_sector, lon_sector, t_on_h=t_on_h,
    )


def _rota_sector(
    base: dict,
    corredor: list[dict],
    celulas: list[dict],
    meteo_ctx: dict,
    tipo_patrulha: str = "geral",
    n_alvos: int = N_ALVOS_SORTIE_PADRAO,
    t_on_h: float = T_ON_SORTIE_H,
    zona_cluster: dict | None = None,
    sector: list[dict] | None = None,
    lat_bounds: tuple[float, float] | None = None,
    obrigatorios: list[dict] | None = None,
) -> tuple[list[dict], float, list[dict], dict]:
    """TSP costeiro marítimo com varrimento por zona, limitado pela autonomia AR5."""
    if sector:
        entrada = ponto_entrada_mar_sector(base, corredor, sector)
    else:
        entrada = ponto_entrada_mar(base, corredor)
    if not entrada:
        return [], 0.0, [], {}

    alcance = meteo_ctx["alcance_patrol_km"] * 0.90
    pool, meta_var = _pool_varrimento(
        entrada, celulas, alcance, tipo_patrulha, n_alvos, zona_cluster,
        lat_bounds=lat_bounds, obrigatorios=obrigatorios,
    )
    if not pool:
        return [], 0.0, [], meta_var

    ordem, dist_tsp = tsp_com_retorno(
        entrada, pool, alcance,
        meteo_ctx.get("vento_direcao_gr"),
        meteo_ctx["vento_ms"],
        corredor=corredor,
    )
    visitados = [pool[i] for i in ordem]

    nucleo = [dict(entrada, tipo="entrada_mar", nome="Entrada marítima")]
    for j, p in enumerate(visitados):
        nucleo.append({**p, "tipo": "patrulha", "nome": f"Patrulha {j + 1}"})
    nucleo.append(dict(entrada, tipo="entrada_mar", nome="Recuperação marítima"))

    wps, dist, meta = expandir_rota_maritima(nucleo, corredor, base, t_on_h, entrada_mar=entrada)
    meta = {**meta, **meta_var, "optimizador": "kmeans_varrimento_ortools_tsp"}
    if tipo_patrulha in ("droga", "imigracao", "pesca") and visitados:
        c0 = visitados[0]
        nc = nome_corredor(c0["lon"], c0["lat"], tipo_patrulha)
        if nc:
            meta["corredor_operacional"] = nc
    return wps, dist, visitados, meta


def _rota_sector_local(
    base: dict,
    corredor: list[dict],
    pts: list[dict],
    meteo_ctx: dict,
    tipo_patrulha: str,
    n_alvos: int,
    t_on_h: float,
    sector: list[dict] | None = None,
    lat_bounds: tuple[float, float] | None = None,
) -> tuple[list[dict], float, list[dict], dict]:
    """Patrulha do sector local alcançável quando a zona alvo está fora de alcance AR5.

    Selecciona as células de mar mais próximas da entrada do sector (round-trip viável),
    prioriza risco entre as próximas e ordena por TSP. Garante que nenhuma base devolve
    rota vazia.
    """
    from geo import ponto_em_mar
    ent = ponto_entrada_mar_sector(base, corredor, sector) if sector else ponto_entrada_mar(base, corredor)
    if not ent:
        return [], 0.0, [], {}
    alc = meteo_ctx["alcance_patrol_km"] * 0.90
    reach = [p for p in pts if ponto_em_mar(p["lon"], p["lat"])
             and distancia_km(ent, p) <= alc * 0.94]
    if lat_bounds:
        lat0, lat1 = lat_bounds
        reach_lat = [p for p in reach if lat0 <= p["lat"] <= lat1]
        if reach_lat:
            reach = reach_lat
    if not reach:
        return [], 0.0, [], {}
    reach.sort(key=lambda p: distancia_km(ent, p))
    cand_local = reach[:max(n_alvos * 3, 12)]
    cand_local.sort(key=lambda p: _score_celula(p, tipo_patrulha), reverse=True)
    pool_l = cand_local[:n_alvos]
    if not pool_l:
        return [], 0.0, [], {}
    ordem, _ = tsp_com_retorno(
        ent, pool_l, alc, meteo_ctx.get("vento_direcao_gr"), meteo_ctx["vento_ms"],
        corredor=corredor,
    )
    vis_l = [pool_l[i] for i in ordem]
    if not vis_l:
        return [], 0.0, [], {}
    nucleo = [dict(ent, tipo="entrada_mar", nome="Entrada marítima")]
    for j, p in enumerate(vis_l):
        nucleo.append({**p, "tipo": "patrulha", "nome": f"Patrulha {j + 1}"})
    nucleo.append(dict(ent, tipo="entrada_mar", nome="Recuperação marítima"))
    wps, dist, meta_l = expandir_rota_maritima(nucleo, corredor, base, t_on_h, entrada_mar=ent)
    meta = {**meta_l, "estrategia": "sector_local_proximidade",
            "optimizador": "local_proximidade_ortools_tsp", "fallback_local": True}
    return wps, dist, vis_l, meta


def _bloco_meteo_rota(meteo_ctx: dict, dist: float, t_on_h: float) -> dict:
    t_cruzeiro = dist / AR5["velocidade_cruzeiro_kmh"]
    autonomia_util = AR5["autonomia_h"] - RESERVA_H
    t_patrol = min(t_on_h, autonomia_util - t_cruzeiro)
    return {
        **meteo_ctx,
        "distancia_km": round(dist, 1),
        "tempo_voo_h": round(t_cruzeiro, 2),
        "tempo_patrol_h": round(max(t_patrol, 0), 2),
        "dentro_autonomia": t_cruzeiro <= autonomia_util,
        "margem_autonomia_h": round(autonomia_util - t_cruzeiro, 2),
    }


def rota_sortie_costeira(
    base_nome: str | None,
    vento_ms: float,
    n_alvos: int = N_ALVOS_SORTIE_PADRAO,
    t_on_h: float | None = None,
    lon_lanc: float | None = None,
    lat_lanc: float | None = None,
    tipo_patrulha: str = "geral",
    regiao: dict | None = None,
    cenario_id: str | None = None,
    meteo_bases: list[dict] | None = None,
    usar_meteo_live: bool = True,
) -> dict:
    regiao = regiao_from_dict(regiao)
    ton = float(t_on_h) if t_on_h is not None else T_ON_SORTIE_H
    ton = max(T_ON_MIN_H, min(ton, AR5["autonomia_h"] - RESERVA_H - 0.5))

    pts, corredor, _ = _carregar()
    base = _base_por_nome(base_nome, lon_lanc, lat_lanc)
    zonas_info = zonas_por_tipo(tipo_patrulha)

    campo_tipo = tipo_patrulha if tipo_patrulha not in ("geral", "costeira") else "risco"
    zona_cluster = zona_por_regiao(regiao, campo_tipo) if regiao else zona_mais_proxima(base, campo_tipo)

    corredor_reg = _filtrar_regiao(corredor, regiao)
    if regiao and not corredor_reg:
        corredor_reg = _filtrar_regiao(pts, regiao)

    # Prioridade: células do cluster k-means (zona operacional coerente)
    celulas_cluster = _celulas_cluster(zona_cluster, pts)
    lat_sec = lon_sec = None
    if celulas_cluster:
        celulas = celulas_cluster
        sector_label = zona_cluster["nome"] if zona_cluster else "Cluster SAD"
        idx = zona_cluster.get("id") if zona_cluster else None
        lat_sec = zona_cluster.get("centro_lat") if zona_cluster else sum(p["lat"] for p in celulas) / len(celulas)
        lon_sec = zona_cluster.get("centro_lon") if zona_cluster else sum(p["lon"] for p in celulas) / len(celulas)
    elif regiao and corredor_reg:
        celulas = _enriquecer_foco(corredor_reg, pts, zonas_info, None)
        sector_label = f"Região {regiao.get('lat_min', '?')}°–{regiao.get('lat_max', '?')}°N"
        idx = None
        lat_sec = sum(p["lat"] for p in corredor_reg) / len(corredor_reg)
        lon_sec = sum(p["lon"] for p in corredor_reg) / len(corredor_reg)
    else:
        sectores = sectores_costa(corredor, N_SECTORES_COSTA)

        def centro(sec):
            return {"x": sum(p["x"] for p in sec) / len(sec), "y": sum(p["y"] for p in sec) / len(sec)}

        sector = min(sectores, key=lambda s: distancia_km(base, centro(s)))
        idx = sectores.index(sector) + 1
        celulas = _enriquecer_foco(list(sector), pts, zonas_info, idx)
        sector_label = f"Sector costeiro {idx}/{len(sectores)}"
        lat_sec = sum(p["lat"] for p in sector) / len(sector)
        lon_sec = sum(p["lon"] for p in sector) / len(sector)

    meteo = _meteo_ctx(base, meteo_bases, vento_ms, usar_meteo_live, ton, lat_sec, lon_sec)
    wps, dist, visitados, meta = _rota_sector(
        base, corredor_reg or corredor, celulas, meteo, tipo_patrulha, n_alvos, ton,
        zona_cluster=zona_cluster,
    )

    # Fallback operacional: se a zona de risco está fora de alcance (round-trip) a partir
    # da base, patrulhar o sector local alcançável em vez de devolver rota vazia.
    fallback_local = False
    if not visitados and not regiao:
        wps_l, dist_l, vis_l, meta_l = _rota_sector_local(
            base, corredor, pts, meteo, tipo_patrulha, n_alvos, ton,
        )
        if vis_l:
            wps, dist, visitados, meta = wps_l, dist_l, vis_l, meta_l
            fallback_local = True
            zona_cluster = None
            sector_label = f"Sector local de {base['nome']} (zona de risco fora de alcance AR5)"

    meteo_rota = _bloco_meteo_rota(meteo, dist, ton)
    autonomia_util = AR5["autonomia_h"] - RESERVA_H

    transito_txt = (
        "com trânsito base→mar" if meta.get("transito_base")
        else "sem trânsito continental (lançamento marítimo)"
    )
    zona_txt = f" · zona {zona_cluster['nome']}" if zona_cluster else ""

    return {
        "modo": "sortie",
        "optimizador": meta.get("optimizador", "kmeans_varrimento_ortools_tsp"),
        "estrategia_varrimento": meta.get("estrategia"),
        "corredor_operacional": meta.get("corredor_operacional"),
        "fallback_local": fallback_local,
        "zona_cluster": zona_cluster,
        "cenario_id": cenario_id,
        "tipo_patrulha": tipo_patrulha,
        "tipo_label": TIPOS.get(tipo_patrulha, TIPOS["geral"])["label"],
        "regiao": _regiao_meta(regiao),
        "base": base["nome"],
        "forca": base.get("forca"),
        "sector_costa": idx,
        "sector_label": sector_label,
        "n_pontos_regiao": len(celulas),
        "n_pontos_patrol": len(visitados),
        "n_alvos_pedido": n_alvos,
        "t_on_h": ton,
        "vento_ms": meteo["vento_ms"],
        "alcance_max_km": meteo["alcance_patrol_km"],
        "distancia_km": round(dist, 1),
        "tempo_h": round(dist / AR5["velocidade_cruzeiro_kmh"], 2),
        "autonomia_h": AR5["autonomia_h"],
        "dentro_autonomia": dist / AR5["velocidade_cruzeiro_kmh"] <= autonomia_util,
        "rota_maritima": meta.get("rota_maritima", True),
        "transito_base": meta.get("transito_base", False),
        "pernas_mar": meta.get("pernas_mar", 0),
        "pernas_terra": meta.get("pernas_terra", 0),
        "meteo": meteo_rota,
        "n_alvos": len(visitados),
        "waypoints": wps,
        "corredor_costa": [{"lon": p["lon"], "lat": p["lat"]} for p in (corredor_reg or corredor)],
        "nota": (
            f"Sortie {sector_label}{zona_txt} — {len(visitados)} pontos marítimos, "
            f"varrimento {meta.get('estrategia', 'adjacente')}, "
            f"{ton:.1f} h patrulha, {transito_txt}; "
            f"vento {meteo['vento_ms']} m/s ({meteo['condicao']}). {meteo['impacto']}"
        ),
    }


def rota_plano_24h_costeira(
    vento_ms: float,
    k_bases: int = 2,
    t_on_h: float | None = None,
    n_alvos: int = N_ALVOS_SORTIE_PADRAO,
    base_nome: str | None = None,
    lon_lanc: float | None = None,
    lat_lanc: float | None = None,
    tipo_patrulha: str = "geral",
    regiao: dict | None = None,
    cenario_id: str | None = None,
    meteo_bases: list[dict] | None = None,
    usar_meteo_live: bool = True,
) -> dict:
    """Plano 24 h: sectores na região ou costa completa, vento por sector."""
    regiao = regiao_from_dict(regiao)
    ton_sector = float(t_on_h) if t_on_h is not None else JANELA_SECTOR_H
    ton_sector = max(T_ON_MIN_H, min(ton_sector, AR5["autonomia_h"] - RESERVA_H - 0.5))

    pts, corredor, alto = _carregar()
    zonas_info = zonas_por_tipo(tipo_patrulha)
    corredor = _filtrar_regiao(corredor, regiao) or corredor

    campo_tipo = tipo_patrulha if tipo_patrulha not in ("geral", "costeira") else "risco"
    clusters_data = clusters_risco(tipo_campo=campo_tipo)
    zonas_k = clusters_data.get("zonas", [])

    bases_op = bases_lancamento()
    bases_mclp = [b for b in bases_op if b["nome"] in BASES_MCLP_RECOMENDADAS]
    if not bases_mclp:
        bases_mclp = bases_op[:k_bases]

    vento_mclp = vento_ms
    if usar_meteo_live and meteo_bases:
        vals = []
        for b in bases_mclp:
            m = _meteo_ctx(b, meteo_bases, vento_ms, True, ton_sector)
            vals.append(m["vento_ms"])
        if vals:
            vento_mclp = max(vals)

    R = raio_por_autonomia(ton_sector, vento_mclp)
    bases_canonicas = _bases_mclp_canonicas(bases_op) or bases_mclp[:k_bases]

    if k_bases >= 2 and lon_lanc is None and lat_lanc is None:
        # Plano 24 h costa completa: sempre Porto + Portimão (ignora base do selector UI)
        bases_sel = bases_canonicas
    elif base_nome or (lon_lanc is not None and lat_lanc is not None):
        bases_sel = [_base_por_nome(base_nome, lon_lanc, lat_lanc)]
    else:
        bases_sel = bases_canonicas

    rec = mclp(pts, bases_op, R, k_bases)
    idx_list = [bases_op.index(b) for b in bases_sel if b in bases_op]
    if not idx_list:
        idx_list = rec.get("bases_sel") or [0]
    fr = dimensionar_persistencia(alto, bases_op, idx_list, 95.0)

    n_sec = min(N_SECTORES_COSTA, max(2, len(corredor) // 4)) if regiao else N_SECTORES_COSTA
    sectores = sectores_costa(corredor, n_sec)

    # Mapear zonas k-means aos sectores costeiros (por sobreposição lat)
    def _zona_do_sector(sector: list[dict]) -> dict | None:
        lat0 = min(p["lat"] for p in sector)
        lat1 = max(p["lat"] for p in sector)
        best, best_r = None, -1.0
        for z in zonas_k:
            overlap = min(lat1, z["lat_max"]) - max(lat0, z["lat_min"])
            if overlap > 0 and z["risco_total"] > best_r:
                best, best_r = z, z["risco_total"]
        return best

    rotas_sector = []
    sectores_meta = []
    meteo_sectores = []

    for i, sector in enumerate(sectores):
        cx = sum(p["x"] for p in sector) / len(sector)
        cy = sum(p["y"] for p in sector) / len(sector)
        lon_c, lat_c = inv_proj(cx, cy)
        base = _base_mclp_sector(bases_sel, sector)

        celulas_base = _celulas_patrol_sector(pts, sector)
        celulas = _enriquecer_foco(celulas_base, pts, zonas_info, i + 1 if not regiao else None)
        zona_sec = _zona_do_sector(sector)
        lat_min, lat_max = min(p["lat"] for p in sector), max(p["lat"] for p in sector)
        lat_bounds = (lat_min - 0.02, lat_max + 0.02)

        zona_foco = next((z for z in zonas_info.get("zonas", []) if z.get("sector") == i + 1), None)
        obrigatorios: list[dict] = []
        if zona_foco:
            for c in zona_foco.get("celulas", []):
                m = next(
                    (p for p in celulas
                     if abs(p["lon"] - c["lon"]) < 0.02 and abs(p["lat"] - c["lat"]) < 0.02),
                    None,
                )
                if m and m not in obrigatorios:
                    obrigatorios.append(m)
        n_sector = min(max(n_alvos, len(obrigatorios) or n_alvos), 16)

        janela_ini = int((i * JANELA_SECTOR_H) % 24)
        janela_fim = int(((i + 1) * JANELA_SECTOR_H) % 24)

        meteo = _meteo_ctx(base, meteo_bases, vento_ms, usar_meteo_live, ton_sector, lat_c, lon_c)
        wps, dist, visitados, meta = _rota_sector(
            base, corredor, celulas, meteo, tipo_patrulha, n_sector, ton_sector,
            zona_cluster=zona_sec, sector=sector, lat_bounds=lat_bounds, obrigatorios=obrigatorios,
        )
        sec_fallback = False
        if not visitados:
            wps_l, dist_l, vis_l, meta_l = _rota_sector_local(
                base, corredor, celulas, meteo, tipo_patrulha, n_sector, ton_sector,
                sector=sector, lat_bounds=lat_bounds,
            )
            if vis_l:
                wps, dist, visitados, meta = wps_l, dist_l, vis_l, meta_l
                sec_fallback = True
        meteo_sec = _bloco_meteo_rota(meteo, dist, ton_sector)
        meteo_sectores.append({"sector": i + 1, **meteo_sec})

        rotas_sector.append({
            "sector": i + 1,
            "base": base["nome"],
            "forca": base.get("forca"),
            "zona_cluster": zona_sec.get("nome") if zona_sec else None,
            "waypoints": wps,
            "dist_km": round(dist, 1),
            "n_pontos_patrol": len(visitados),
            "n_pontos": len(sector),
            "lat_min": round(lat_min, 2),
            "lat_max": round(lat_max, 2),
            "janela_h": f"{janela_ini:02d}:00–{janela_fim:02d}:00",
            "t_on_h": ton_sector,
            "rota_maritima": meta.get("rota_maritima", True),
            "fallback_local": sec_fallback,
            "meteo": meteo_sec,
        })
        risco_med = sum(p.get("risco", 0) for p in sector) / max(len(sector), 1)
        sectores_meta.append({
            "sector": i + 1,
            "lon": lon_c, "lat": lat_c,
            "base": base["nome"],
            "zona_cluster": zona_sec.get("nome") if zona_sec else None,
            "risco_medio": round(risco_med, 2),
            "n_pontos_costa": len(sector),
            "janela_h": f"{janela_ini:02d}:00–{janela_fim:02d}:00",
            "t_on_h": ton_sector,
            "vento_ms": meteo["vento_ms"],
            "operacional": meteo["operacional"],
        })

    vento_medio = round(
        sum(m["vento_ms"] for m in meteo_sectores) / max(len(meteo_sectores), 1), 1,
    )
    n_criticos = sum(1 for m in meteo_sectores if not m.get("operacional", True))

    try:
        with open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "resultados", "validacao.json"),
                  encoding="utf-8") as f:
            val = json.load(f)
        q2 = val.get("resposta_objetivo", {}).get("Q2_quantos", {})
        frota_costeira = q2.get("frota_costeira", 9)
        frota_total_analise = q2.get("frota_total", 11)
    except OSError:
        frota_costeira, frota_total_analise = 9, 11

    ar5_por_sector = max(1, round(frota_costeira / max(len(sectores), 1)))
    agenda_24h = []
    for sm, rs in zip(sectores_meta, rotas_sector):
        eh_mclp = any(
            m.split("(")[0].strip().lower() in sm["base"].lower()
            for m in BASES_MCLP_RECOMENDADAS
        )
        agenda_24h.append({
            "sector": sm["sector"],
            "janela_h": sm["janela_h"],
            "base_lancamento": sm["base"],
            "base_mclp": eh_mclp,
            "faixa_lat": f"{rs['lat_min']}°–{rs['lat_max']}°N",
            "dist_km": rs["dist_km"],
            "n_pontos_patrol": rs["n_pontos_patrol"],
            "n_ar5_sector": ar5_por_sector,
            "vento_ms": sm["vento_ms"],
            "operacional": sm["operacional"],
            "rota_maritima": rs.get("rota_maritima", True),
        })

    return {
        "modo": "plano_24h",
        "optimizador": "kmeans_varrimento_ortools_tsp",
        "zonas_kmeans": zonas_k,
        "cenario_id": cenario_id,
        "tipo_patrulha": tipo_patrulha,
        "tipo_label": TIPOS.get(tipo_patrulha, TIPOS["geral"])["label"],
        "regiao": _regiao_meta(regiao),
        "bases": [b["nome"] for b in bases_sel],
        "bases_mclp_recomendadas": BASES_MCLP_RECOMENDADAS,
        "vento_ms": vento_medio,
        "t_on_h": ton_sector,
        "janela_sector_h": JANELA_SECTOR_H,
        "frota_total": fr["frota_total"],
        "n_simultaneos": fr["n_simultaneos"],
        "revisita_h": fr.get("revisita_h", 3),
        "n_pontos_corredor": len(corredor),
        "n_sectores": len(sectores),
        "sectores": sectores_meta,
        "rotas_sector": rotas_sector,
        "agenda_24h": agenda_24h,
        "frota_resumo": {
            "n_simultaneos": fr["n_simultaneos"],
            "frota_plano": fr["frota_total"],
            "frota_costeira_analise": frota_costeira,
            "frota_total_analise": frota_total_analise,
            "revisita_h": fr.get("revisita_h", 3),
            "ar5_por_sector": ar5_por_sector,
        },
        "meteo": {
            "vento_medio_ms": vento_medio,
            "vento_mclp_ms": vento_mclp,
            "n_sectores_limitados": n_criticos,
            "por_sector": meteo_sectores,
            "fonte": meteo_sectores[0]["fonte"] if meteo_sectores else "manual",
        },
        "corredor_costa": [{"lon": p["lon"], "lat": p["lat"], "risco": round(p.get("risco", 0), 2)}
                           for p in corredor],
        "waypoints": rotas_sector[0]["waypoints"] if rotas_sector else [],
        "nota": (
            f"Plano 24 h — {len(sectores)} sectores N→S, {ton_sector:.1f} h/sector; "
            f"rotas marítimas sem travessia continental; vento médio {vento_medio} m/s. "
            f"{n_criticos} sector(es) com condições limitadas."
        ),
    }


def rota_reativa_costeira(
    lon: float, lat: float, vento_ms: float,
    base_nome: str | None = None,
    lon_lanc: float | None = None,
    lat_lanc: float | None = None,
    t_on_h: float | None = None,
    meteo_bases: list[dict] | None = None,
    usar_meteo_live: bool = True,
) -> dict:
    """Despacho reactivo: base → mar → alvo → órbita marítima → recuperação."""
    ton = float(t_on_h) if t_on_h is not None else T_ON_MIN_H
    pts, corredor, _ = _carregar()

    base = _base_por_nome(base_nome or None, lon_lanc, lat_lanc)
    if lon_lanc is None and base_nome is None:
        alvo_xy = {"x": proj(lon, lat)[0], "y": proj(lon, lat)[1]}
        base = _base_mais_proxima(bases_lancamento(), alvo_xy)

    alvo_mar = snap_maritimo(lon, lat, corredor)
    entrada = ponto_entrada_mar(base, corredor)
    meteo = _meteo_ctx(base, meteo_bases, vento_ms, usar_meteo_live, ton, lat, lon)
    alcance = meteo["alcance_patrol_km"]
    orbita_km = min(SENSOR_SWATH_KM / 2, 25)

    # Patrulha reactiva: órbita + células adjacentes de alto risco (não deixar buracos)
    pts_alto = [p for p in pts if p.get("risco", 0) >= LIMIAR]
    vizinhos = sorted(
        [p for p in pts_alto if distancia_km(alvo_mar, p) <= orbita_km * 1.8],
        key=lambda p: (-p.get("risco", 0), distancia_km(alvo_mar, p)),
    )[:4]

    nucleo = []
    if entrada:
        nucleo.append(dict(entrada, tipo="entrada_mar", nome="Entrada marítima"))
    nucleo.append({**alvo_mar, "tipo": "alvo", "nome": "Incidente/alerta"})
    for j, p in enumerate(vizinhos):
        nucleo.append({**p, "tipo": "patrulha", "nome": f"Varrimento adjacente {j + 1}"})
    for op in orbita_maritima(alvo_mar["lon"], alvo_mar["lat"], corredor, orbita_km):
        nucleo.append({**op, "tipo": "orbita", "nome": "Órbita patrulha"})
    if entrada:
        nucleo.append(dict(entrada, tipo="entrada_mar", nome="Recuperação marítima"))

    waypoints, dist_total, meta = expandir_rota_maritima(nucleo, corredor, base, ton)
    dist_ida = distancia_km(entrada or base, alvo_mar) if entrada else distancia_km(base, alvo_mar)

    t_total = dist_total / AR5["velocidade_cruzeiro_kmh"]
    autonomia_util = AR5["autonomia_h"] - RESERVA_H
    return {
        "modo": "reativo",
        "base": base["nome"],
        "forca": base.get("forca"),
        "alvo": {"lon": alvo_mar["lon"], "lat": alvo_mar["lat"]},
        "alvo_original": {"lon": lon, "lat": lat},
        "distancia_ida_km": round(dist_ida, 1),
        "distancia_km": round(dist_total, 1),
        "alcance_disponivel_km": alcance,
        "alcancavel": dist_ida <= alcance and meteo["operacional"],
        "tempo_h": round(t_total, 2),
        "t_on_h": ton,
        "dentro_autonomia": t_total <= autonomia_util,
        "rota_maritima": meta.get("rota_maritima", True),
        "transito_base": meta.get("transito_base", False),
        "meteo": _bloco_meteo_rota(meteo, dist_total, ton),
        "waypoints": waypoints,
        "n_pontos_adjacentes": len(vizinhos),
        "nota": (
            f"Despacho reactivo marítimo — órbita {orbita_km:.0f} km + {len(vizinhos)} células adjacentes; "
            f"{meta.get('pernas_terra', 0)} perna(s) terrestre(s). {meteo['impacto']}"
        ),
    }
