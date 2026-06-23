"""Optimização de rotas com OR-Tools (TSP com retorno à base marítima)."""
from __future__ import annotations

import math


def _custo_leg(
    p1: dict,
    p2: dict,
    corredor: list[dict] | None,
    vento_dir_gr: float | None,
    vento_ms: float,
) -> float:
    if corredor:
        from rotas_maritimas import distancia_leg_maritima
        d = distancia_leg_maritima(p1, p2, corredor)
    else:
        d = math.hypot(p1["x"] - p2["x"], p1["y"] - p2["y"])
    if vento_dir_gr is None or vento_ms <= 5 or d < 0.01:
        return d
    dx, dy = p2["x"] - p1["x"], p2["y"] - p1["y"]
    leg_bearing = math.degrees(math.atan2(dx, dy)) % 360
    diff = math.radians((leg_bearing - vento_dir_gr + 180) % 360 - 180)
    from config import ASSIMETRIA_DOWN, ASSIMETRIA_UP
    cos_a = math.cos(diff)
    if cos_a > 0.3:
        return d / ASSIMETRIA_DOWN
    if cos_a < -0.3:
        return d / ASSIMETRIA_UP
    return d


def _matriz_dist(
    nodes: list[dict],
    vento_dir_gr: float | None = None,
    vento_ms: float = 8.0,
    corredor: list[dict] | None = None,
) -> list[list[int]]:
    """Distâncias efectivas em metros (int) para OR-Tools."""
    n = len(nodes)
    m = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            d = _custo_leg(nodes[i], nodes[j], corredor, vento_dir_gr, vento_ms)
            m[i][j] = max(1, int(d * 1000))
    return m


def tsp_com_retorno(
    base: dict,
    alvos: list[dict],
    max_dist_km: float,
    vento_dir_gr: float | None = None,
    vento_ms: float = 8.0,
    corredor: list[dict] | None = None,
) -> tuple[list[int], float]:
    """
    Resolve TSP: base → alvos → base.
    Devolve (índices em alvos visitados, distância total km).
    Fallback greedy costeiro se OR-Tools falhar.
    """
    if not alvos:
        return [], 0.0

    nodes = [base] + alvos
    max_m = int(max_dist_km * 1000)

    try:
        from ortools.constraint_solver import pywrapcp, routing_enums_pb2

        dist = _matriz_dist(nodes, vento_dir_gr, vento_ms, corredor)
        n = len(nodes)
        manager = pywrapcp.RoutingIndexManager(n, 1, 0)
        routing = pywrapcp.RoutingModel(manager)

        def dist_cb(from_i, to_i):
            return dist[manager.IndexToNode(from_i)][manager.IndexToNode(to_i)]

        cb_idx = routing.RegisterTransitCallback(dist_cb)
        routing.SetArcCostEvaluatorOfAllVehicles(cb_idx)
        routing.AddDimension(cb_idx, 0, max_m, True, "Distance")

        params = pywrapcp.DefaultRoutingSearchParameters()
        params.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.SAVINGS
        )
        params.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        params.time_limit.seconds = 4

        sol = routing.SolveWithParameters(params)
        if not sol:
            return _greedy_costeira(base, alvos, max_dist_km, vento_dir_gr, vento_ms, corredor)

        ordem: list[int] = []
        idx = routing.Start(0)
        total = 0
        while not routing.IsEnd(idx):
            nxt = sol.Value(routing.NextVar(idx))
            node = manager.IndexToNode(nxt)
            if node > 0:
                ordem.append(node - 1)
            total += routing.GetArcCostForVehicle(idx, nxt, 0)
            idx = nxt
        return ordem, total / 1000.0
    except Exception:
        return _greedy_costeira(base, alvos, max_dist_km, vento_dir_gr, vento_ms, corredor)


def _greedy_costeira(
    base, alvos, max_dist_km,
    vento_dir_gr=None, vento_ms=8.0, corredor=None,
):
    """Varredura costeira N→S com custo vento-aware e pernas marítimas."""
    rest = sorted(
        range(len(alvos)),
        key=lambda i: (-alvos[i]["lat"], alvos[i]["lon"]),
    )
    ordem = []
    atual = base
    total = 0.0
    while rest:
        rest.sort(
            key=lambda i: _custo_leg(atual, alvos[i], corredor, vento_dir_gr, vento_ms),
        )
        i = rest.pop(0)
        d = _custo_leg(atual, alvos[i], corredor, vento_dir_gr, vento_ms)
        volta = _custo_leg(alvos[i], base, corredor, vento_dir_gr, vento_ms)
        if total + d + volta > max_dist_km:
            break
        total += d
        ordem.append(i)
        atual = alvos[i]
    if ordem:
        total += _custo_leg(atual, base, corredor, vento_dir_gr, vento_ms)
    return ordem, total
