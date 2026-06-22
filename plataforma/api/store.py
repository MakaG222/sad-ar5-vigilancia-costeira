"""Estado partilhado em memória (MVP local). Substituível por Redis/SQLite."""
from __future__ import annotations
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class EstadoGlobal:
    navios: dict[str, dict] = field(default_factory=dict)
    alertas: list[dict] = field(default_factory=list)
    incidentes: list[dict] = field(default_factory=list)
    meteo_bases: list[dict] = field(default_factory=list)
    meteo_previsao: dict = field(default_factory=dict)
    avisos_ipma: list[dict] = field(default_factory=list)
    noticias_rss: list[dict] = field(default_factory=list)
    risco_celulas: list[dict] = field(default_factory=list)
    risco_resumo: dict = field(default_factory=dict)
    ultimo_ais: str | None = None
    ultimo_meteo: str | None = None
    ultimo_rss: str | None = None
    ultimo_ipma: str | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    _dedupe: dict[str, datetime] = field(default_factory=dict)

    def add_alerta(self, tipo: str, severidade: str, titulo: str, detalhe: str,
                   lat: float | None = None, lon: float | None = None,
                   meta: dict | None = None,
                   dedupe_min: int = 15) -> dict | None:
        """Regista alerta; ignora duplicados recentes (mesmo tipo+título)."""
        now = datetime.now(timezone.utc)
        chave = f"{tipo}|{titulo[:60]}"
        exp = self._dedupe.get(chave)
        if exp and exp > now:
            return None
        self._dedupe[chave] = now + timedelta(minutes=dedupe_min)
        # limpar chaves expiradas
        self._dedupe = {k: v for k, v in self._dedupe.items() if v > now}

        aid = f"ALT-{len(self.alertas)+1:04d}"
        ev = {
            "id": aid, "tipo": tipo, "severidade": severidade,
            "titulo": titulo, "detalhe": detalhe,
            "lat": lat, "lon": lon, "meta": meta or {},
            "criado_em": _now(), "lido": False,
        }
        self.alertas.insert(0, ev)
        self.alertas = self.alertas[:200]
        return ev


estado = EstadoGlobal()
