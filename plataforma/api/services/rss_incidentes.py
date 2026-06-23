"""Feeds RSS / avisos operacionais (Portugal)."""
from __future__ import annotations

from datetime import datetime, timezone

import feedparser
import httpx

# Feeds estáveis; vários antigos (Marinha, DN) devolvem 404
FEEDS = [
    ("IPMA", "https://www.ipma.pt/pt/rss/avisos/index.xml"),
    ("Lusa", "https://www.lusa.pt/rss/"),
]

_PALAVRAS_MAR = {
    "mar", "marítim", "maritim", "costa", "navio", "embarca", "porto", "pesca",
    "migr", "droga", "contraband", "derram", "salvamento", "sos", "oceano",
    "atlânt", "atlant", "patrulh", "guarda", "naufrág", "naufrag", "ipma",
    "meteorolog", "vento", "avis", "marinha",
}


def _relevante(texto: str) -> bool:
    t = texto.lower()
    return any(p in t for p in _PALAVRAS_MAR)


async def _avisos_ipma_como_noticias() -> list[dict]:
    """Fallback: avisos IPMA activos como notícias operacionais."""
    from services.ipma import fetch_avisos_ipma

    out = []
    for a in await fetch_avisos_ipma():
        titulo = a.get("titulo", "")
        if titulo in ("Sem avisos IPMA activos", "Sem ligação IPMA"):
            continue
        out.append({
            "id": f"ipma-{titulo[:40]}",
            "fonte": "IPMA",
            "titulo": titulo,
            "resumo": a.get("detalhe", ""),
            "link": "https://www.ipma.pt/pt/otempo/avisos/",
            "publicado": a.get("inicio") or a.get("atualizado", ""),
            "criado_em": datetime.now(timezone.utc).isoformat(),
        })
    return out


async def fetch_rss() -> list[dict]:
    """Notícias/avisos filtrados por relevância marítima."""
    out: list[dict] = []
    vistos: set[str] = set()

    # Fonte principal fiável: API IPMA
    for item in await _avisos_ipma_como_noticias():
        vistos.add(item["id"])
        out.append(item)

    async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
        for fonte, url in FEEDS:
            try:
                r = await client.get(url, headers={"User-Agent": "SAD-AR5/1.0"})
                if r.status_code != 200 or "<rss" not in r.text.lower() and "<feed" not in r.text.lower():
                    continue
                feed = feedparser.parse(r.text)
            except Exception:
                continue
            for e in feed.entries[:20]:
                titulo = (e.get("title") or "").strip()
                link = e.get("link") or ""
                resumo = (e.get("summary") or e.get("description") or "")[:400]
                chave = link or titulo
                if not chave or chave in vistos:
                    continue
                if not _relevante(titulo + " " + resumo):
                    continue
                vistos.add(chave)
                out.append({
                    "id": chave[:80],
                    "fonte": fonte,
                    "titulo": titulo,
                    "resumo": resumo,
                    "link": link,
                    "publicado": e.get("published", ""),
                    "criado_em": datetime.now(timezone.utc).isoformat(),
                })

    out.sort(key=lambda x: x.get("publicado", ""), reverse=True)
    return out[:30]
