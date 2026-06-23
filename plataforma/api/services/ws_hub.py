"""Hub WebSocket — push de alertas e eventos em tempo real."""
from __future__ import annotations

import asyncio

from fastapi import WebSocket

_clientes: set[WebSocket] = set()
_lock = asyncio.Lock()


def registar(ws: WebSocket) -> None:
    _clientes.add(ws)


def remover(ws: WebSocket) -> None:
    _clientes.discard(ws)


async def broadcast(payload: dict) -> None:
    async with _lock:
        mortos: list[WebSocket] = []
        for ws in list(_clientes):
            try:
                await ws.send_json(payload)
            except Exception:
                mortos.append(ws)
        for ws in mortos:
            _clientes.discard(ws)


async def notificar_alerta(alerta: dict) -> None:
    await broadcast({"tipo": "alerta_novo", "alerta": alerta})


async def notificar_sync(alertas: list[dict], estado_resumo: dict) -> None:
    await broadcast({
        "tipo": "sync",
        "alertas": alertas[:40],
        "estado": estado_resumo,
    })
