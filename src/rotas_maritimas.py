"""
rotas_maritimas.py — Roteamento marítimo/costeiro para patrulhas AR5.

As pernas de patrulha seguem o corredor costeiro da análise SAD e evitam
travessia continental. O trânsito base→mar só é incluído quando necessário
para gestão de autonomia (distância significativa à costa).
"""
from __future__ import annotations

import math

from shapely.geometry import LineString, Point

from geo import proj, terra_polygon, ponto_em_mar, distancia_costa_km


def segmento_cruza_terra(p1: dict, p2: dict) -> bool:
    """True se a linha recta entre dois pontos intersecta terra."""
    line = LineString([
        proj(p1["lon"], p1["lat"]),
        proj(p2["lon"], p2["lat"]),
    ])
    return line.intersects(terra_polygon())


def _xy(p: dict) -> tuple[float, float]:
    if "x" in p and "y" in p:
        return p["x"], p["y"]
    return proj(p["lon"], p["lat"])


def distancia_km(p1: dict, p2: dict) -> float:
    x1, y1 = _xy(p1)
    x2, y2 = _xy(p2)
    return math.hypot(x2 - x1, y2 - y1)


def ponto_entrada_mar(base: dict, corredor: list[dict]) -> dict | None:
    """Ponto marítimo de lançamento/recuperação mais próximo da base."""
    if not corredor:
        return None
    best = min(corredor, key=lambda p: distancia_km(base, p))
    return _mk_entrada(best)


def _mk_entrada(best: dict) -> dict:
    return {
        "lon": best["lon"],
        "lat": best["lat"],
        "x": best["x"],
        "y": best["y"],
        "tipo": "entrada_mar",
        "nome": "Entrada marítima",
        "dist_costa_km": best.get("dist_costa_km"),
        "risco": best.get("risco", 0),
    }


def ponto_entrada_mar_sector(base: dict, corredor: list[dict], sector: list[dict]) -> dict | None:
    """Entrada marítima no sector de patrulha (não a mais próxima da base globalmente)."""
    if not corredor or not sector:
        return ponto_entrada_mar(base, corredor)
    lat0 = min(p["lat"] for p in sector) - 0.05
    lat1 = max(p["lat"] for p in sector) + 0.05
    no_sector = [p for p in corredor if lat0 <= p["lat"] <= lat1]
    if not no_sector:
        no_sector = list(sector)
    best = min(no_sector, key=lambda p: distancia_km(base, p))
    return _mk_entrada(best)


def snap_maritimo(lon: float, lat: float, corredor: list[dict]) -> dict:
    """Projecta um ponto para a zona marítima operacional mais próxima."""
    if ponto_em_mar(lon, lat):
        x, y = proj(lon, lat)
        return {"lon": lon, "lat": lat, "x": x, "y": y}
    if not corredor:
        x, y = proj(lon, lat)
        return {"lon": lon, "lat": lat, "x": x, "y": y}
    alvo = {"lon": lon, "lat": lat, "x": proj(lon, lat)[0], "y": proj(lon, lat)[1]}
    best = min(corredor, key=lambda p: distancia_km(alvo, p))
    return dict(best)


def waypoints_leg_maritima(p1: dict, p2: dict, corredor: list[dict]) -> list[dict]:
    """
    Pontos intermédios no corredor costeiro para evitar travessia de terra.
    Devolve lista vazia se a perna recta já é marítima.
    """
    if not segmento_cruza_terra(p1, p2):
        return []

    lat_lo = min(p1["lat"], p2["lat"]) - 0.15
    lat_hi = max(p1["lat"], p2["lat"]) + 0.15
    norte = p1["lat"] > p2["lat"]
    cands = [p for p in corredor if lat_lo <= p["lat"] <= lat_hi]
    cands.sort(key=lambda p: (-p["lat"], p["lon"]) if norte else (p["lat"], p["lon"]))

    path: list[dict] = []
    atual = p1
    for c in cands:
        if distancia_km(atual, c) < 3.0:
            continue
        if segmento_cruza_terra(atual, c):
            continue
        path.append(c)
        atual = c
        if not segmento_cruza_terra(atual, p2):
            return path

    # Segunda passagem: todos os corredor entre latitudes (mais denso)
    if segmento_cruza_terra(atual, p2):
        for c in cands:
            if c in path:
                continue
            if segmento_cruza_terra(atual, c) or segmento_cruza_terra(c, p2):
                continue
            path.append(c)
            atual = c
            if not segmento_cruza_terra(atual, p2):
                return path

    if path:
        return path

    if cands:
        mid = min(cands, key=lambda c: distancia_km(p1, c) + distancia_km(c, p2))
        if not segmento_cruza_terra(p1, mid):
            return [mid]
    return []


def _cadeia_maritima(p1: dict, p2: dict, corredor: list[dict], max_iter: int = 6) -> list[dict]:
    """Constrói cadeia p1 → … → p2 sem pernas terrestres (quando possível)."""
    chain = [p1, p2]
    for _ in range(max_iter):
        novo = [chain[0]]
        mudou = False
        for j in range(len(chain) - 1):
            a, b = chain[j], chain[j + 1]
            if segmento_cruza_terra(a, b):
                inter = waypoints_leg_maritima(a, b, corredor)
                if not inter:
                    lat_lo = min(a["lat"], b["lat"])
                    lat_hi = max(a["lat"], b["lat"])
                    norte = a["lat"] > b["lat"]
                    extras = [c for c in corredor if lat_lo - 0.05 <= c["lat"] <= lat_hi + 0.05]
                    extras.sort(key=lambda c: (-c["lat"], c["lon"]) if norte else (c["lat"], c["lon"]))
                    for c in extras:
                        if not segmento_cruza_terra(novo[-1], c):
                            inter.append(c)
                    if inter:
                        mudou = True
                if inter:
                    novo.extend(inter)
                    mudou = True
                else:
                    b_snap = snap_maritimo(b["lon"], b["lat"], corredor)
                    if not segmento_cruza_terra(a, b_snap):
                        b = b_snap
                        mudou = True
            novo.append(b)
        chain = novo
        if not mudou:
            break
    return chain[1:]


def distancia_leg_maritima(p1: dict, p2: dict, corredor: list[dict]) -> float:
    """Distância efectiva km ao longo do corredor marítimo."""
    if not segmento_cruza_terra(p1, p2):
        return distancia_km(p1, p2)
    chain = [p1] + _cadeia_maritima(p1, p2, corredor)
    if distancia_km(chain[-1], p2) > 0.5:
        chain.append(p2)
    total = 0.0
    for i in range(len(chain) - 1):
        total += distancia_km(chain[i], chain[i + 1])
    return total


def _wp_dict(p: dict, tipo: str, nome: str | None = None, **extra) -> dict:
    wp = {
        "lon": p["lon"],
        "lat": p["lat"],
        "tipo": tipo,
        "nome": nome or tipo,
    }
    if "risco" in p:
        wp["risco"] = round(p["risco"], 2)
    if "dist_costa_km" in p:
        wp["dist_costa_km"] = round(p["dist_costa_km"], 1)
    wp.update(extra)
    return wp


def transito_base_necessario(base: dict, entrada_mar: dict, t_on_h: float) -> bool:
    """
    Incluir perna base→mar apenas se a distância terrestre for relevante
    para a gestão de autonomia (>5% do alcance útil ou >8 km).
    """
    d = distancia_km(base, entrada_mar)
    if d < 3.0:
        return False
    from config import AR5, RESERVA_H
    from otimizacao import raio_por_autonomia

    alcance = raio_por_autonomia(t_on_h, 8.0)
    # margem: trânsito consome autonomia se >8 km ou >5% alcance
    return d > 8.0 or d > alcance * 0.05


def expandir_rota_maritima(
    nucleo: list[dict],
    corredor: list[dict],
    base: dict | None = None,
    t_on_h: float = 4.0,
    entrada_mar: dict | None = None,
) -> tuple[list[dict], float, dict]:
    """
    Expande sequência de pontos de patrulha em rota marítima completa.

    nucleo: [entrada_mar, patrulha..., entrada_mar] ou [patrulha...]
    Devolve (waypoints, distancia_km, meta).
    """
    if not nucleo:
        return [], 0.0, {"pernas_terra": 0, "pernas_mar": 0}

    entrada = entrada_mar
    if entrada is None and base and corredor:
        entrada = ponto_entrada_mar(base, corredor)

    seq = list(nucleo)
    if entrada and seq:
        if distancia_km(seq[0], entrada) < 2.0:
            pass  # nucleo já começa na entrada marítima
        elif seq[0].get("tipo") != "entrada_mar":
            seq = [entrada] + seq
        if len(seq) > 1 and distancia_km(seq[-1], entrada) > 2.0 and seq[-1].get("tipo") != "entrada_mar":
            seq = seq + [dict(entrada, nome="Recuperação marítima")]

    expandidos: list[dict] = []
    dist_total = 0.0
    pernas_terra = 0
    pernas_mar = 0

    incluir_base_ida = base and entrada and transito_base_necessario(base, entrada, t_on_h)
    incluir_base_volta = incluir_base_ida

    if incluir_base_ida:
        expandidos.append(_wp_dict(base, "base", base.get("nome", "Base")))
        dist_total += distancia_km(base, entrada)
        if segmento_cruza_terra(base, entrada):
            pernas_terra += 1
        else:
            pernas_mar += 1

    for i, p in enumerate(seq):
        if i == 0:
            expandidos.append(_wp_dict(p, p.get("tipo", "entrada_mar"), p.get("nome", "Entrada marítima")))
            continue
        prev = seq[i - 1]
        inter = _cadeia_maritima(prev, p, corredor)
        chain = [prev] + inter
        if not inter or distancia_km(chain[-1], p) > 0.5:
            chain.append(p)
        else:
            chain[-1] = p
        for j in range(len(chain) - 1):
            a, b = chain[j], chain[j + 1]
            dist_total += distancia_km(a, b)
            if segmento_cruza_terra(a, b):
                pernas_terra += 1
            else:
                pernas_mar += 1
        for ip in inter:
            expandidos.append(_wp_dict(ip, "corredor", "Corredor costeiro"))
        expandidos.append(_wp_dict(chain[-1], p.get("tipo", "patrulha"), p.get("nome")))

    if incluir_base_volta and entrada:
        dist_total += distancia_km(entrada, base)
        if segmento_cruza_terra(entrada, base):
            pernas_terra += 1
        else:
            pernas_mar += 1
        expandidos.append(_wp_dict(base, "base", base.get("nome", "Base")))

    meta = {
        "pernas_terra": pernas_terra,
        "pernas_mar": pernas_mar,
        "entrada_mar": entrada,
        "transito_base": incluir_base_ida,
        "rota_maritima": pernas_terra == 0 or pernas_mar >= max(pernas_terra * 2, 4),
    }
    return expandidos, round(dist_total, 1), meta


def orbita_maritima(
    lon: float,
    lat: float,
    corredor: list[dict],
    raio_km: float,
) -> list[dict]:
    """Quatro pontos de órbita em mar, alinhados com a costa local."""
    centro = snap_maritimo(lon, lat, corredor)
    cx, cy = _xy(centro)
    # Deslocamentos aproximados: E/W ao longo costa, N/S offshore
    offsets = [
        (raio_km, 0),
        (0, raio_km * 0.85),
        (-raio_km, 0),
        (0, -raio_km * 0.85),
    ]
    pts = []
    for dx, dy in offsets:
        p = {"x": cx + dx, "y": cy + dy}
        from geo import inv_proj
        lon_p, lat_p = inv_proj(p["x"], p["y"])
        if ponto_em_mar(lon_p, lat_p):
            pts.append({"lon": lon_p, "lat": lat_p, "x": p["x"], "y": p["y"]})
        else:
            snapped = snap_maritimo(lon_p, lat_p, corredor)
            pts.append(snapped)
    return pts
