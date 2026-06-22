"""
Teste de fumo da plataforma SAD AR5 — valida que a API arranca e que os
endpoints e rotas respondem sem erros, antes de uma demo/defesa.

Uso:
    cd plataforma/api
    source .venv/bin/activate
    python smoke_test.py

Sai com código 0 se tudo OK, 1 se algum teste falhar.
"""
from __future__ import annotations

import sys

from fastapi.testclient import TestClient

import main


GET_OK = [
    "/api/estado",
    "/api/risco/celulas?limiar=0.0",
    "/api/risco/celulas?limiar=0.15",
    "/api/meteo/atual",
    "/api/ais/navios",
    "/api/alertas",
    "/api/incidentes",
    "/api/ipma/avisos",
    "/api/rss/noticias",
    "/api/cenarios",
    "/api/sad/respostas",
    "/api/bases/lancamento",
    "/api/zonas/tipos",
    "/api/zonas/patrulha?tipo=droga",
    "/api/zonas/clusters?tipo=droga",
    "/api/camadas/resumo",
    "/api/camadas/apreensoes",
    "/api/frota/dimensionar?vento_atual=8",
    "/api/export/validacao",
]


def main_smoke() -> int:
    falhas: list[str] = []
    ok = 0

    with TestClient(main.app) as c:
        for path in GET_OK:
            try:
                r = c.get(path)
                if r.status_code != 200:
                    falhas.append(f"GET {path} -> {r.status_code}")
                else:
                    ok += 1
                    print(f"  ok  GET {path}")
            except Exception as e:  # noqa: BLE001
                falhas.append(f"GET {path} -> {type(e).__name__}: {e}")

        # Rotas + bloco de validação (Fase 2)
        rotas = [
            ("/api/rotas/sortie", {"base": "Portimão", "tipo_patrulha": "droga", "usar_meteo_live": False, "vento_ms": 8}),
            ("/api/rotas/plano24h", {"k_bases": 2, "usar_meteo_live": False, "vento_ms": 8}),
            ("/api/rotas/reativo", {"lon": -8.9, "lat": 37.0, "usar_meteo_live": False, "vento_ms": 8}),
        ]
        for path, body in rotas:
            try:
                r = c.post(path, json=body)
                if r.status_code != 200:
                    falhas.append(f"POST {path} -> {r.status_code}")
                    continue
                data = r.json()
                if "validacao" not in data or data["validacao"].get("score") is None:
                    falhas.append(f"POST {path} -> sem bloco 'validacao' válido")
                else:
                    ok += 1
                    v = data["validacao"]
                    print(f"  ok  POST {path}  (qualidade {v['score']}/100 · {v['classe']})")
            except Exception as e:  # noqa: BLE001
                falhas.append(f"POST {path} -> {type(e).__name__}: {e}")

    print()
    if falhas:
        print(f"FALHOU: {len(falhas)} problema(s), {ok} OK")
        for f in falhas:
            print(f"  x  {f}")
        return 1
    print(f"TUDO OK — {ok} verificações passaram.")
    return 0


if __name__ == "__main__":
    sys.exit(main_smoke())
