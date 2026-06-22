"""
API da plataforma operacional SAD AR5 — protótipo tempo quasi-real.

Arranque:
    cd plataforma/api
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8080
"""
from __future__ import annotations
import asyncio
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from store import estado
from worker import worker_loop
from services.rotas import rota_sortie, rota_plano_24h, rota_reativa
from services.frota import dimensionar
from services.alertas import registar_incidente_manual
from services import ws_hub
from services.bases import listar_bases
from services.zonas_patrulha import zonas_por_tipo, listar_tipos
from services.zonas_cluster import clusters_risco, invalidar_cache_clusters
from services.cenarios import listar_cenarios, obter_cenario
from services.sad_respostas import carregar_respostas
from services.camadas_mapa import incidentes_iom, apreensoes_maritimas, resumo_camadas, aquecer_apreensoes
from services.grelha_cache import aquecer_grelha
from services.risco_mapa import carregar_celulas, get_celulas, resumo_risco
from services.offline_fallback import meteo_fallback, ipma_fallback, rss_fallback
from services.exportar import exportar_risco_geojson, exportar_validacao, exportar_plano_missao
from services.ais import modo_ais

_stop = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _stop.clear()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, aquecer_grelha)
    estado.risco_celulas = await loop.run_in_executor(None, carregar_celulas, 0.12)
    invalidar_cache_clusters()
    await loop.run_in_executor(None, aquecer_apreensoes)

    # Resposta imediata em /api/estado — sem bloquear em meteo/IPMA/AIS (rede lenta)
    estado.meteo_bases = meteo_fallback()
    estado.avisos_ipma = ipma_fallback()
    estado.noticias_rss = rss_fallback()
    estado.risco_resumo = resumo_risco()

    task = asyncio.create_task(worker_loop(_stop))
    yield
    _stop.set()
    await task


app = FastAPI(
    title="SAD AR5 — Plataforma Operacional",
    description="Meteo, AIS, rotas, frota e alertas — costa portuguesa",
    version="0.4.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegiaoReq(BaseModel):
    lat_min: float | None = None
    lat_max: float | None = None
    lon_min: float | None = None
    lon_max: float | None = None


class RotaSortieReq(BaseModel):
    base: str | None = None
    vento_ms: float = 8.0
    n_alvos: int = 8
    t_on_h: float | None = None
    lon_lanc: float | None = None
    lat_lanc: float | None = None
    tipo_patrulha: str = "geral"
    cenario_id: str | None = None
    regiao: RegiaoReq | None = None
    lat_min: float | None = None
    lat_max: float | None = None
    lon_min: float | None = None
    lon_max: float | None = None
    usar_meteo_live: bool = True


class Rota24Req(BaseModel):
    vento_ms: float = 8.0
    k_bases: int = 2
    t_on_h: float | None = None
    n_alvos: int = 8
    base: str | None = None
    lon_lanc: float | None = None
    lat_lanc: float | None = None
    tipo_patrulha: str = "geral"
    cenario_id: str | None = None
    regiao: RegiaoReq | None = None
    lat_min: float | None = None
    lat_max: float | None = None
    lon_min: float | None = None
    lon_max: float | None = None
    usar_meteo_live: bool = True


class ExecutarCenarioReq(BaseModel):
    vento_ms: float = 8.0
    base: str | None = None
    usar_meteo_live: bool = True


class RotaReativaReq(BaseModel):
    lon: float
    lat: float
    vento_ms: float = 8.0
    t_on_h: float | None = None
    base: str | None = None
    lon_lanc: float | None = None
    lat_lanc: float | None = None
    usar_meteo_live: bool = True


class IncidenteReq(BaseModel):
    titulo: str
    detalhe: str = ""
    lat: float
    lon: float
    severidade: str = "alta"


class SimularReq(BaseModel):
    tipo: str = Field("spoofing", description="spoofing | incidente | meteo")
    lat: float | None = None
    lon: float | None = None
    aleatorio: bool = True


class ExportPlanoReq(BaseModel):
    modo: str = "sortie"
    base: str | None = None
    vento_ms: float = 8.0
    n_alvos: int = 8
    t_on_h: float | None = None
    tipo_patrulha: str = "geral"
    cenario_id: str | None = None
    lon: float | None = None
    lat: float | None = None
    lon_lanc: float | None = None
    lat_lanc: float | None = None
    k_bases: int = 2
    usar_meteo_live: bool = True
    regiao: RegiaoReq | None = None
    lat_min: float | None = None
    lat_max: float | None = None
    lon_min: float | None = None
    lon_max: float | None = None


@app.get("/api/estado")
def get_estado():
    ais = modo_ais()
    return {
        "ultimo_meteo": estado.ultimo_meteo,
        "ultimo_ais": estado.ultimo_ais,
        "ultimo_ipma": estado.ultimo_ipma,
        "ultimo_rss": estado.ultimo_rss,
        "n_navios": len(estado.navios),
        "n_alertas": len(estado.alertas),
        "n_incidentes": len(estado.incidentes),
        "risco_resumo": estado.risco_resumo,
        "ais_fonte": ais["fonte"],
        "modo_demo": ais["modo_demo"],
        "demo_mensagem": ais["mensagem"],
        "dados_locais_ok": True,
        "offline_ready": True,
    }


def _meteo_resposta():
    bases = estado.meteo_bases
    validas = [b for b in bases if b.get("vento_ms") is not None and not b.get("erro")]
    if validas:
        return {
            "bases": validas,
            "atualizado": estado.ultimo_meteo,
            "modo_fonte": "live",
        }
    fb = meteo_fallback()
    return {
        "bases": fb,
        "atualizado": estado.ultimo_meteo,
        "modo_fonte": "cache_local",
        "mensagem": "Meteo em cache local (demo offline). Pode ajustar vento manualmente.",
    }


def _ipma_resposta():
    avisos = [a for a in estado.avisos_ipma if a.get("titulo") != "Sem ligação IPMA"]
    if avisos:
        return {"avisos": avisos, "atualizado": estado.ultimo_ipma, "modo_fonte": "live"}
    return {
        "avisos": ipma_fallback(),
        "atualizado": estado.ultimo_ipma,
        "modo_fonte": "cache_local",
        "mensagem": "IPMA indisponível — dados locais SAD activos.",
    }


def _rss_resposta():
    if estado.noticias_rss:
        return {"noticias": estado.noticias_rss, "atualizado": estado.ultimo_rss, "modo_fonte": "live"}
    return {
        "noticias": rss_fallback(),
        "atualizado": estado.ultimo_rss,
        "modo_fonte": "cache_local",
        "mensagem": "RSS offline — notícias locais de demonstração.",
    }


@app.get("/api/meteo/atual")
def meteo_atual():
    return _meteo_resposta()


@app.get("/api/meteo/previsao")
def meteo_previsao():
    return estado.meteo_previsao


@app.get("/api/ais/navios")
def ais_navios():
    return {"navios": list(estado.navios.values()), "atualizado": estado.ultimo_ais}


@app.get("/api/alertas")
def listar_alertas(limite: int = 50):
    return {"alertas": estado.alertas[:limite]}


@app.get("/api/incidentes")
def listar_incidentes():
    return {"incidentes": estado.incidentes}


def _kw_meteo(req) -> dict:
    return {
        "meteo_bases": estado.meteo_bases or None,
        "usar_meteo_live": getattr(req, "usar_meteo_live", True),
    }


@app.get("/api/camadas/resumo")
def get_camadas_resumo():
    return resumo_camadas()


@app.get("/api/camadas/iom")
def get_camadas_iom():
    return {"incidentes": incidentes_iom(), **resumo_camadas()}


@app.get("/api/camadas/apreensoes")
def get_camadas_apreensoes():
    return {"apreensoes": apreensoes_maritimas(), **resumo_camadas()}


@app.get("/api/camadas/desembarques")
def get_camadas_desembarques():
    from services.camadas_mapa import desembarques_pt
    return {"desembarques": desembarques_pt(), **resumo_camadas()}


@app.get("/api/camadas/emodnet")
def get_camadas_emodnet(tipo: str = "geral", limiar: float = 0.35):
    from services.camadas_emodnet import celulas_emodnet
    return celulas_emodnet(tipo, limiar)


@app.get("/api/cenarios")
def get_cenarios():
    return {"cenarios": listar_cenarios()}


@app.get("/api/sad/respostas")
def get_sad_respostas():
    return carregar_respostas()


def _regiao_req(req) -> dict | None:
    if req.regiao:
        return req.regiao.model_dump(exclude_none=True)
    if any(getattr(req, k, None) is not None for k in ("lat_min", "lat_max", "lon_min", "lon_max")):
        return {k: getattr(req, k) for k in ("lat_min", "lat_max", "lon_min", "lon_max")
                if getattr(req, k, None) is not None}
    return None


@app.post("/api/cenarios/{cenario_id}/executar")
def executar_cenario(cenario_id: str, req: ExecutarCenarioReq):
    c = obter_cenario(cenario_id)
    if not c:
        return {"erro": "Cenário não encontrado"}
    base = req.base if c.get("base") else None
    regiao = c.get("regiao")
    if c["modo"] == "plano24h":
        rota = rota_plano_24h(
            req.vento_ms, c.get("k_bases", 2), None, 8, base, None, None,
            c.get("tipo_patrulha", "geral"),
            regiao=regiao, cenario_id=cenario_id,
            **_kw_meteo(req),
        )
    else:
        rota = rota_sortie(
            base, req.vento_ms, 8, None, None, None,
            c.get("tipo_patrulha", "geral"),
            regiao=regiao, cenario_id=cenario_id,
            **_kw_meteo(req),
        )
    return {"cenario": c, "rota": rota}


@app.get("/api/zonas/tipos")
def get_tipos_patrulha():
    return {"tipos": listar_tipos()}


@app.get("/api/zonas/patrulha")
def get_zonas_patrulha(tipo: str = "geral", limiar: float = 0.35):
    return zonas_por_tipo(tipo, limiar)


@app.get("/api/zonas/clusters")
def get_zonas_clusters(tipo: str = "geral", k: int | None = None, limiar: float = 0.5):
    campo = tipo if tipo not in ("geral", "costeira") else "risco"
    return clusters_risco(k=k, limiar=limiar, tipo_campo=campo)


@app.get("/api/bases/lancamento")
def get_bases_lancamento():
    return listar_bases()


@app.get("/api/risco/celulas")
def risco_celulas(limiar: float = 0.15):
    celulas = estado.risco_celulas or get_celulas(limiar) or carregar_celulas(limiar)
    if limiar > 0:
        celulas = [c for c in celulas if c["risco"] >= limiar]
    return {
        "celulas": celulas,
        "resumo": estado.risco_resumo or {},
        "limiar": limiar,
    }


@app.get("/api/ipma/avisos")
def ipma_avisos():
    return _ipma_resposta()


@app.get("/api/rss/noticias")
def rss_noticias():
    return _rss_resposta()


@app.post("/api/incidentes")
async def criar_incidente(req: IncidenteReq):
    inc = registar_incidente_manual(req.titulo, req.detalhe, req.lat, req.lon, req.severidade)
    if inc.get("alerta_id"):
        alerta = next((a for a in estado.alertas if a["id"] == inc["alerta_id"]), None)
        if alerta:
            await ws_hub.notificar_alerta(alerta)
    return inc


@app.get("/api/demo/ponto-aleatorio")
def demo_ponto_aleatorio():
    from services.alertas import ponto_aleatorio_mar
    lon, lat, meta = ponto_aleatorio_mar()
    return {"lon": lon, "lat": lat, **meta}


@app.post("/api/demo/simular")
async def simular_alerta(req: SimularReq):
    from services.alertas import ponto_aleatorio_mar, snap_para_mar
    meta: dict = {}
    if req.aleatorio or req.lon is None or req.lat is None:
        lon, lat, meta = ponto_aleatorio_mar()
    else:
        lon, lat = snap_para_mar(req.lon, req.lat)
    ponto = {"lon": lon, "lat": lat, **meta}
    if req.tipo == "spoofing":
        from services.ais import _navio
        estado.navios["263SIM999"] = _navio(
            "263SIM999", lon, lat, "SIMULADO SPOOF", 48.0, 0.0)
        ev = estado.add_alerta(
            "spoofing", "critica", "Alerta simulado — spoofing",
            f"Embarcação injectada no mar ({lat:.2f}°N, {lon:.2f}°W).", lat, lon, dedupe_min=1)
        if ev:
            await ws_hub.notificar_alerta(ev)
        return {"ok": True, "alerta": ev, "ponto": ponto}
    inc = registar_incidente_manual(
        "Incidente simulado",
        f"Tipo={req.tipo} · {lat:.2f}°N, {lon:.2f}°W",
        lat, lon, "alta",
    )
    alerta = next((a for a in estado.alertas if a.get("id") == inc.get("alerta_id")), None)
    if alerta:
        await ws_hub.notificar_alerta(alerta)
    return {"ok": True, "alerta": alerta, "incidente": inc, "ponto": ponto}


@app.post("/api/rotas/sortie")
def post_rota_sortie(req: RotaSortieReq):
    if req.cenario_id:
        out = executar_cenario(req.cenario_id, ExecutarCenarioReq(vento_ms=req.vento_ms, base=req.base))
        return out.get("rota", out)
    reg = _regiao_req(req)
    return rota_sortie(
        req.base, req.vento_ms, req.n_alvos, req.t_on_h, req.lon_lanc, req.lat_lanc, req.tipo_patrulha,
        regiao=reg, cenario_id=req.cenario_id,
        lat_min=req.lat_min, lat_max=req.lat_max, lon_min=req.lon_min, lon_max=req.lon_max,
        **_kw_meteo(req),
    )


@app.post("/api/rotas/plano24h")
def post_rota_24h(req: Rota24Req):
    if req.cenario_id:
        return executar_cenario(req.cenario_id, ExecutarCenarioReq(vento_ms=req.vento_ms, base=req.base)).get("rota", {})
    reg = _regiao_req(req)
    return rota_plano_24h(
        req.vento_ms, req.k_bases, req.t_on_h, req.n_alvos, req.base, req.lon_lanc, req.lat_lanc,
        req.tipo_patrulha,
        regiao=reg, cenario_id=req.cenario_id,
        lat_min=req.lat_min, lat_max=req.lat_max, lon_min=req.lon_min, lon_max=req.lon_max,
        **_kw_meteo(req),
    )


@app.post("/api/rotas/reativo")
def post_rota_reativo(req: RotaReativaReq):
    return rota_reativa(
        req.lon, req.lat, req.vento_ms, req.base, req.lon_lanc, req.lat_lanc, req.t_on_h,
        **_kw_meteo(req),
    )


@app.get("/api/frota/dimensionar")
def get_frota(vento_atual: float = 8.0, vento_previsto: float | None = None):
    return dimensionar(vento_atual, vento_previsto)


@app.get("/api/export/risco")
def export_risco(limiar: float = 0.0):
    return exportar_risco_geojson(limiar)


@app.get("/api/export/validacao")
def export_validacao():
    return exportar_validacao()


@app.post("/api/export/plano-missao")
def export_plano(req: ExportPlanoReq):
    reg = _regiao_req(req)
    meta = {"modo": req.modo, "base": req.base, "cenario_id": req.cenario_id, "tipo_patrulha": req.tipo_patrulha}
    kw = _kw_meteo(req)
    if req.modo == "plano24h":
        rota = rota_plano_24h(
            req.vento_ms, req.k_bases, req.t_on_h, req.n_alvos, req.base, req.lon_lanc, req.lat_lanc,
            req.tipo_patrulha, regiao=reg, cenario_id=req.cenario_id,
            lat_min=req.lat_min, lat_max=req.lat_max, lon_min=req.lon_min, lon_max=req.lon_max,
            **kw,
        )
    elif req.modo == "reativo":
        rota = rota_reativa(
            req.lon or -9.1, req.lat or 38.7, req.vento_ms, req.base, req.lon_lanc, req.lat_lanc,
            req.t_on_h, **kw,
        )
    else:
        rota = rota_sortie(
            req.base, req.vento_ms, req.n_alvos, req.t_on_h, req.lon_lanc, req.lat_lanc,
            req.tipo_patrulha, regiao=reg, cenario_id=req.cenario_id,
            lat_min=req.lat_min, lat_max=req.lat_max, lon_min=req.lon_min, lon_max=req.lon_max,
            **kw,
        )
    return exportar_plano_missao(rota, meta)


@app.get("/api/export/plano-missao/geojson")
def export_plano_geojson(base: str | None = None, vento_ms: float = 8.0, cenario_id: str | None = None):
    req = RotaSortieReq(base=base, vento_ms=vento_ms, cenario_id=cenario_id)
    rota = post_rota_sortie(req)
    plano = exportar_plano_missao(rota, {"base": base, "cenario_id": cenario_id})
    return JSONResponse(plano)


@app.websocket("/api/ws/alertas")
async def ws_alertas(ws: WebSocket):
    await ws.accept()
    ws_hub.registar(ws)
    try:
        await ws.send_json({
            "tipo": "sync",
            "alertas": estado.alertas[:40],
            "estado": {
                "n_navios": len(estado.navios),
                "n_alertas": len(estado.alertas),
                "ultimo_meteo": estado.ultimo_meteo,
                "ultimo_ais": estado.ultimo_ais,
            },
        })
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        ws_hub.remover(ws)


_web_dist = os.path.join(ROOT, "plataforma", "web", "dist")
if os.path.isdir(_web_dist):
    app.mount("/", StaticFiles(directory=_web_dist, html=True), name="web")
