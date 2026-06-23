"""Worker de fundo: meteo + AIS + alertas (~2 min)."""
from __future__ import annotations

import asyncio
import copy
from datetime import datetime, timezone

from services import ws_hub
from services.ais import atualizar_ais
from services.alertas import (
    alertas_cobertura,
    alertas_ipma,
    alertas_meteo,
    alertas_risco_navios,
    alertas_rss,
)
from services.ipma import fetch_avisos_ipma
from services.meteo import fetch_meteo_bases
from services.risco_mapa import carregar_celulas, resumo_risco
from services.rss_incidentes import fetch_rss
from services.spoofing import verificar_todos
from store import estado

INTERVALO_S = 120  # 2 min — quasi tempo real


async def ciclo_ingestao() -> None:
    navios_ant = copy.deepcopy(estado.navios)
    novos_alertas: list[dict] = []

    def _push(ev_dict):
        if ev_dict is None:
            return
        a = estado.add_alerta(**ev_dict)
        if a:
            novos_alertas.append(a)

    try:
        bases, prev = await asyncio.wait_for(fetch_meteo_bases(), timeout=25.0)
        validas = [b for b in bases if b.get("vento_ms") is not None and not b.get("erro")]
        if not validas:
            from services.offline_fallback import meteo_fallback
            bases = meteo_fallback()
            prev = {}
    except Exception:
        from services.offline_fallback import meteo_fallback
        bases = meteo_fallback()
        prev = {}

    async with estado.lock:
        estado.meteo_bases = bases
        estado.meteo_previsao = prev
        estado.ultimo_meteo = datetime.now(timezone.utc).isoformat()

    # Risco SAD (cache mapa)
    celulas = carregar_celulas(limiar=0.12)
    estado.risco_celulas = celulas
    estado.risco_resumo = resumo_risco()

    # IPMA + RSS (timeouts — não bloquear worker indefinidamente)
    try:
        avisos = await asyncio.wait_for(fetch_avisos_ipma(), timeout=15.0)
    except Exception:
        from services.offline_fallback import ipma_fallback
        avisos = ipma_fallback()
    estado.avisos_ipma = avisos
    estado.ultimo_ipma = datetime.now(timezone.utc).isoformat()
    for ev in alertas_ipma(avisos):
        _push(ev)

    try:
        rss = await asyncio.wait_for(fetch_rss(), timeout=15.0)
    except Exception:
        from services.offline_fallback import rss_fallback
        rss = rss_fallback()
    estado.noticias_rss = rss
    estado.ultimo_rss = datetime.now(timezone.utc).isoformat()
    for ev in alertas_rss(rss):
        _push(ev)

    try:
        await asyncio.wait_for(atualizar_ais(), timeout=20.0)
    except Exception:
        pass

    for ev in alertas_meteo(bases):
        _push(ev)
    for ev in verificar_todos(navios_ant, estado.navios):
        _push(ev)
    for ev in alertas_risco_navios(estado.navios):
        _push(ev)
    for ev in alertas_cobertura():
        _push(ev)

    for a in novos_alertas:
        await ws_hub.notificar_alerta(a)

    await ws_hub.notificar_sync(estado.alertas, {
        "n_navios": len(estado.navios),
        "n_alertas": len(estado.alertas),
        "ultimo_meteo": estado.ultimo_meteo,
        "ultimo_ais": estado.ultimo_ais,
    })


async def worker_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await ciclo_ingestao()
        except Exception as e:
            estado.add_alerta("sistema", "baixa", "Erro no worker", str(e))
        try:
            await asyncio.wait_for(stop.wait(), timeout=INTERVALO_S)
        except asyncio.TimeoutError:
            pass
