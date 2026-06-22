"""Avisos meteorológicos IPMA (Portugal)."""
from __future__ import annotations
from datetime import datetime, timezone
import httpx

WARNINGS_URL = "https://api.ipma.pt/open-data/forecast/warnings/warnings_www.json"
AREAS_URL = "https://api.ipma.pt/open-data/distrits-islands.json"

# Tipos relevantes para operação costeira / AR5
TIPOS_MARITIMOS = {
    "agitação marítima", "agitacao maritima", "vento", "nevoeiro",
    "precipitação", "precipitacao", "trovoada", "tempo quente", "tempo frio",
}

_area_cache: dict[str, str] = {}


async def _carregar_areas(client: httpx.AsyncClient) -> dict[str, str]:
    global _area_cache
    if _area_cache:
        return _area_cache
    try:
        r = await client.get(AREAS_URL)
        r.raise_for_status()
        for item in r.json().get("data", []):
            cod = item.get("idAreaAviso")
            if cod:
                _area_cache[cod] = item.get("local") or cod
    except Exception:
        pass
    return _area_cache


def _severidade(nivel: str) -> str:
    n = (nivel or "").lower()
    if n in ("red", "vermelho", "4"):
        return "critica"
    if n in ("orange", "laranja", "3"):
        return "alta"
    if n in ("yellow", "amarelo", "2"):
        return "media"
    return "baixa"


async def fetch_avisos_ipma() -> list[dict]:
    """Avisos IPMA activos (amarelo/laranja/vermelho) via API open-data."""
    out: list[dict] = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            areas = await _carregar_areas(client)
            r = await client.get(WARNINGS_URL)
            r.raise_for_status()
            avisos = r.json()
        except Exception as e:
            return [{
                "tipo": "ipma",
                "severidade": "baixa",
                "titulo": "Sem ligação IPMA",
                "detalhe": "Não foi possível obter avisos. Meteo das bases continua via Open-Meteo.",
                "distrito": None,
                "erro": str(e)[:120],
            }]

    if not isinstance(avisos, list):
        avisos = []

    now = datetime.now(timezone.utc)
    for item in avisos:
        if not isinstance(item, dict):
            continue
        nivel = (item.get("awarenessLevelID") or "").lower()
        if nivel in ("green", "", "verde"):
            continue

        tipo = item.get("awarenessTypeName") or "Aviso"
        cod = item.get("idAreaAviso") or "?"
        nome = areas.get(cod, cod)
        texto = (item.get("text") or "").strip()
        inicio = item.get("startTime") or ""
        fim = item.get("endTime") or ""

        sev = _severidade(nivel)
        if tipo.lower() in TIPOS_MARITIMOS and sev == "media":
            sev = "alta" if "agitação" in tipo.lower() or "vento" in tipo.lower() else sev

        detalhe = texto or f"Válido de {inicio} a {fim}."
        out.append({
            "tipo": "ipma",
            "severidade": sev,
            "titulo": f"{tipo} — {nome}",
            "detalhe": detalhe[:500],
            "distrito": nome,
            "nivel": nivel,
            "inicio": inicio,
            "fim": fim,
            "atualizado": now.isoformat(),
        })

    out.sort(key=lambda a: {"critica": 0, "alta": 1, "media": 2, "baixa": 3}.get(a["severidade"], 9))
    if not out:
        out.append({
            "tipo": "ipma",
            "severidade": "baixa",
            "titulo": "Sem avisos IPMA activos",
            "detalhe": "Nenhum aviso amarelo, laranja ou vermelho para Portugal.",
            "distrito": None,
        })
    return out[:25]
