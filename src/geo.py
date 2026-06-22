"""
geo.py — Geografia do problema: projeção métrica local, linha de costa de
Portugal Continental, polígono de terra (máscara de oceano), bases candidatas e
geração da grelha de pontos de procura (zonas marítimas a vigiar).
"""
from __future__ import annotations
import math
import numpy as np
from shapely.geometry import LineString, Polygon, Point

from config import AERODROMOS, BASES_MILITARES, RAIO_LANCAMENTO_COSTA_KM

LAT0 = 39.5
_KX = 111.320 * math.cos(math.radians(LAT0))
_KY = 110.574

LON_MIN, LON_MAX = -11.0, -7.38
LAT_MIN, LAT_MAX = 36.85, 42.20

COSTA_LONLAT = [
    (-8.880, 41.870), (-8.780, 41.690), (-8.780, 41.450), (-8.740, 41.250),
    (-8.680, 41.000), (-8.745, 40.640), (-8.860, 40.150), (-8.930, 39.600),
    (-9.080, 39.360), (-9.420, 38.780), (-9.480, 38.690), (-9.230, 38.660),
    (-8.930, 38.470), (-8.820, 38.100), (-8.880, 37.950), (-8.800, 37.730),
    (-8.990, 37.030), (-8.930, 37.010), (-8.660, 37.090), (-8.540, 37.100),
    (-8.270, 37.090), (-7.930, 36.970), (-7.520, 37.160), (-7.400, 37.180),
]


def proj(lon: float, lat: float) -> tuple[float, float]:
    return (lon * _KX, lat * _KY)


def inv_proj(x: float, y: float) -> tuple[float, float]:
    return (x / _KX, y / _KY)


def zona_maritima_pt(lon: float, lat: float) -> bool:
    return LON_MIN <= lon <= LON_MAX and LAT_MIN <= lat <= LAT_MAX


def costa_linestring() -> LineString:
    return LineString([proj(lon, lat) for lon, lat in COSTA_LONLAT])


def distancia_costa_km(lon: float, lat: float) -> float:
    x, y = proj(lon, lat)
    return float(Point(x, y).distance(costa_linestring()))


def terra_polygon() -> Polygon:
    """Polígono de terra (Portugal + interior a Este da costa)."""
    pts = [proj(lon, lat) for lon, lat in COSTA_LONLAT]
    lon_n = COSTA_LONLAT[0][0]
    # Fecho: norte (fronteira) → este → sul; evita falsos «mar» a N do Minho
    pts += [
        proj(lon_n, 42.25),
        proj(-6.0, 42.25),
        proj(-6.0, 37.0),
        proj(COSTA_LONLAT[-1][0], COSTA_LONLAT[-1][1]),
    ]
    return Polygon(pts)


def ponto_em_mar(lon: float, lat: float) -> bool:
    """True se o ponto está no oceano operacional (fora de terra, faixa costeira)."""
    if not zona_maritima_pt(lon, lat):
        return False
    x, y = proj(lon, lat)
    if terra_polygon().contains(Point(x, y)):
        return False
    d = Point(x, y).distance(costa_linestring())
    return 8.0 <= d <= 300.0


# Faixa mínima ao largo + estuários excluídos — só para camadas de mapa (evita pontos em rias)
MAR_MAPA_MIN_KM = 15.0
MAR_MAPA_MAX_KM = 42.0  # corredor operacional; além disto no «interior» é artefacto da costa simplificada

ESTUARIOS = [
    {"lat_min": 38.35, "lat_max": 39.15, "lon_min": -9.45, "lon_max": -8.65},  # Tejo / Mar da Palha
    {"lat_min": 38.30, "lat_max": 38.75, "lon_min": -9.15, "lon_max": -8.50},  # Sado
    {"lat_min": 40.85, "lat_max": 41.35, "lon_min": -8.95, "lon_max": -8.45},  # Douro
    {"lat_min": 40.30, "lat_max": 40.82, "lon_min": -8.80, "lon_max": -8.18},  # Mondego / Aveiro / Baixo Vouga
    {"lat_min": 40.45, "lat_max": 40.95, "lon_min": -8.95, "lon_max": -8.45},  # Ria de Aveiro / Mira (ao largo)
    {"lat_min": 36.85, "lat_max": 37.45, "lon_min": -8.20, "lon_max": -7.25},  # Ria Formosa / Guadiana
    {"lat_min": 37.05, "lat_max": 37.30, "lon_min": -9.00, "lon_max": -8.65},  # Lagos / Alvor
    {"lat_min": 38.40, "lat_max": 38.75, "lon_min": -9.40, "lon_max": -9.05},  # Peniche / Lourinhã
]


def em_estuario(lon: float, lat: float) -> bool:
    """True se o ponto cai num estuário/ria (excluir do mapa marítimo)."""
    for e in ESTUARIOS:
        if e["lat_min"] <= lat <= e["lat_max"] and e["lon_min"] <= lon <= e["lon_max"]:
            return True
    return False


def ponto_em_mar_mapa(lon: float, lat: float, min_km: float = MAR_MAPA_MIN_KM) -> bool:
    """
    Mar aberto para visualização na plataforma.
    Mais restritivo que ponto_em_mar: faixa 15–42 km, fora de estuários,
    e exclui o «falso oceano» a leste (artefacto do polígono de terra grosseiro).
    """
    if em_estuario(lon, lat):
        return False
    if not ponto_em_mar(lon, lat):
        return False
    d = distancia_costa_km(lon, lat)
    if d < min_km:
        return False
    # Interior alentejano classificado erradamente como mar (costa simplificada)
    if d > MAR_MAPA_MAX_KM and lon > -10.0:
        return False
    # Algarve oriental: só mar aberto (lon < -8.5) ou muito ao largo
    if lat < 37.55 and lon > -8.45 and d < 28.0:
        return False
    return True


def bases_lancamento(max_dist_costa_km: float | None = None) -> list[dict]:
    lim = max_dist_costa_km if max_dist_costa_km is not None else RAIO_LANCAMENTO_COSTA_KM
    vistos: set[str] = set()
    out: list[dict] = []

    def _add(nome, lon, lat, forca, tipo):
        if nome in vistos:
            return
        d = distancia_costa_km(lon, lat)
        if d > lim:
            return
        x, y = proj(lon, lat)
        vistos.add(nome)
        out.append({
            "nome": nome, "lon": lon, "lat": lat, "x": x, "y": y,
            "forca": forca, "tipo": tipo,
            "dist_costa_km": round(d, 1),
            "regiao": "N" if lat > 40.5 else ("S" if lat < 38.0 else "C"),
        })

    for nome, lon, lat, forca in BASES_MILITARES:
        _add(nome, lon, lat, forca, "militar")
    for nome, lon, lat, regiao in AERODROMOS:
        # Evitar duplicados civis junto a bases militares (ex. Monte Real, Sintra)
        dup = False
        for b in out:
            if math.hypot(b["x"] - proj(lon, lat)[0], b["y"] - proj(lon, lat)[1]) < 3.0:
                dup = True
                break
            if nome.split("(")[0].strip()[:6] in b["nome"] or b["nome"][:6] in nome:
                if math.hypot(b["x"] - proj(lon, lat)[0], b["y"] - proj(lon, lat)[1]) < 8.0:
                    dup = True
                    break
        if not dup:
            _add(nome, lon, lat, "Civil", "aerodromo")

    out.sort(key=lambda b: (-b["lat"], b["lon"]))
    return out


def corredor_costeiro(pts: list[dict], dist_max_km: float = 40.0) -> list[dict]:
    bins: dict[float, dict] = {}
    for p in pts:
        d = p.get("dist_costa_km", 999)
        if d > dist_max_km:
            continue
        key = round(p["lat"], 1)
        if key not in bins or d < bins[key]["dist_costa_km"]:
            bins[key] = p
    return sorted(bins.values(), key=lambda p: (-p["lat"], p["lon"]))


def sectores_costa(corredor: list[dict], n: int = 6) -> list[list[dict]]:
    if not corredor:
        return []
    n = max(1, min(n, len(corredor)))
    chunk = max(1, math.ceil(len(corredor) / n))
    return [
        corredor[i * chunk:(i + 1) * chunk]
        for i in range(n)
        if corredor[i * chunk:(i + 1) * chunk]
    ]


def bases_proj() -> list[dict]:
    out = []
    for nome, lon, lat, regiao in AERODROMOS:
        x, y = proj(lon, lat)
        out.append({"nome": nome, "lon": lon, "lat": lat, "regiao": regiao, "x": x, "y": y})
    return out


def gerar_procura(dist_min_km: float = 8.0, dist_max_km: float = 300.0,
                  passo_graus: float = 0.10) -> list[dict]:
    costa = costa_linestring()
    terra = terra_polygon()
    lons = np.arange(LON_MIN, LON_MAX + passo_graus * 0.5, passo_graus)
    lats = np.arange(LAT_MIN, LAT_MAX + passo_graus * 0.5, passo_graus)
    pts = []
    for lon in lons:
        for lat in lats:
            if not zona_maritima_pt(lon, lat):
                continue
            x, y = proj(lon, lat)
            p = Point(x, y)
            if terra.contains(p):
                continue
            d = p.distance(costa)
            if dist_min_km <= d <= dist_max_km:
                pts.append({"lon": float(lon), "lat": float(lat),
                            "x": x, "y": y, "dist_costa_km": float(d)})
    return pts


if __name__ == "__main__":
    pts = gerar_procura()
    print("Pontos de procura gerados:", len(pts))
    print("Bases lançamento:", len(bases_lancamento()))
    print("Corredor costa:", len(corredor_costeiro(pts)))
