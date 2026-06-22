import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  MapContainer, TileLayer, Marker, Polyline, Popup, CircleMarker, Rectangle,
  useMapEvents, useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Ponto de demonstração: mar aberto a O de Sesimbra (~26 km da costa)
const API = "/api";
const DEMO_LON = -9.50;
const DEMO_LAT = 38.45;
const PT_BOUNDS = [[36.85, -11.0], [42.2, -7.38]];
const PT_LON = { lon_min: -11.0, lon_max: -7.38 };
const PT_CENTER = [39.5, -9.0];
const MAX_CELULAS_MAPA = 220;
const COR_FORCA = { FAP: "#3498db", Marinha: "#1abc9c", Exercito: "#2ecc71", Civil: "#bdc3c7", Operacional: "#f39c12" };
const LEGENDA_FORCAS = [
  ["FAP", "FAP"], ["Marinha", "Marinha"], ["Exercito", "Exército"], ["Civil", "Civil"], ["Operacional", "Lançamento"],
];

const COR_EMODNET = {
  droga: "#c0392b", pesca: "#27ae60", poluicao: "#2980b9",
  imigracao: "#8e44ad", geral: "#e67e22", costeira: "#95a5a6",
};

/** Escala de risco SAD (baixo → alto) — alinhada com validação (limiar 0,5). */
const ESCALA_RISCO = [
  { min: 0.7, cor: "#c0392b", rotulo: "Muito alto (≥0,7)" },
  { min: 0.5, cor: "#e67e22", rotulo: "Alto (0,5–0,7)" },
  { min: 0.3, cor: "#f1c40f", rotulo: "Médio (0,3–0,5)" },
  { min: 0, cor: "#3498db", rotulo: "Baixo (<0,3)" },
];

const CORES_SECTOR_24H = ["#e74c3c", "#9b59b6", "#1abc9c", "#e67e22", "#3498db", "#2ecc71"];

/** Camadas leves para demo em sala (arranque rápido, mapa fluido). */
const CAMADAS_APRESENTACAO = {
  risco: false, foco: false, emodnet: false, navios: true, rota: true, sectores: true,
  bases: true, corredor: true, clusters: true, iom: false, apreensoes: false, desembarques: false,
  incidentes: true,
};

const CAMADAS_COMPLETO = {
  risco: false, foco: true, emodnet: true, navios: true, rota: true, sectores: true,
  bases: true, corredor: true, clusters: true, iom: true, apreensoes: true, desembarques: true,
  incidentes: true,
};

function isBaseMclp(nome, mclpList) {
  if (!nome || !mclpList?.length) return false;
  const n = nome.toLowerCase();
  return mclpList.some((m) => {
    const chave = m.split("(")[0].trim().toLowerCase();
    return n.includes(chave) || chave.includes(n.split("—")[0].trim().toLowerCase());
  });
}

function iconBase(forca, activo = false, mclp = false) {
  const cor = COR_FORCA[forca] || "#95a5a6";
  const b = mclp ? "3px solid #f1c40f" : activo ? "3px solid #fff" : "1px solid #222";
  const sz = mclp ? 18 : 14;
  return L.divIcon({
    className: "",
    html: `<div style="background:${cor};width:${sz}px;height:${sz}px;border-radius:3px;border:${b};box-shadow:0 0 ${mclp ? 6 : 4}px #000"></div>`,
    iconSize: [sz, sz], iconAnchor: [sz / 2, sz / 2],
  });
}

async function get(path) {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function getSafe(path, fallback = null) {
  try {
    return await get(path);
  } catch {
    return fallback;
  }
}

async function post(path, body) {
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

function corCondicao(c) {
  if (c === "critica") return "#e74c3c";
  if (c === "limitada") return "#e67e22";
  if (c === "moderada") return "#f1c40f";
  return "#2ecc71";
}

function ventoDaBase(nomeBase, meteoLista) {
  if (!nomeBase || !meteoLista?.length) return null;
  const m = meteoLista.find(
    (mb) => mb.base === nomeBase || nomeBase.includes(mb.base?.slice(0, 8)) || mb.base?.includes(nomeBase.slice(0, 8)),
  );
  return m?.vento_ms ?? null;
}
function corRisco(r) {
  for (const faixa of ESCALA_RISCO) {
    if (r >= faixa.min) return faixa.cor;
  }
  return "#3498db";
}

function rotuloRisco(r) {
  for (const faixa of ESCALA_RISCO) {
    if (r >= faixa.min) return faixa.rotulo;
  }
  return ESCALA_RISCO[ESCALA_RISCO.length - 1].rotulo;
}

function MapClickHandler({ activo, onClick }) {
  useMapEvents({
    click(e) {
      if (activo) onClick(e.latlng.lat, e.latlng.lng);
    },
  });
  return null;
}

function MapResize() {
  const map = useMap();
  useEffect(() => {
    const fix = () => map.invalidateSize({ animate: false });
    fix();
    const t1 = setTimeout(fix, 100);
    const t2 = setTimeout(fix, 500);
    window.addEventListener("resize", fix);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      window.removeEventListener("resize", fix);
    };
  }, [map]);
  return null;
}

export default function App() {
  const [estado, setEstado] = useState(null);
  const [navios, setNavios] = useState([]);
  const [alertas, setAlertas] = useState([]);
  const [meteo, setMeteo] = useState([]);
  const [frota, setFrota] = useState(null);
  const [rota, setRota] = useState(null);
  const [modo, setModo] = useState("sortie");
  const [vento, setVento] = useState(8);
  const [nAlvos, setNAlvos] = useState(8);
  const [tOnH, setTOnH] = useState(4);
  const [celulas, setCelulas] = useState([]);
  const [avisosIpma, setAvisosIpma] = useState([]);
  const [noticiasRss, setNoticiasRss] = useState([]);
  const [camadas, setCamadas] = useState(CAMADAS_APRESENTACAO);
  const [modoApresentacao, setModoApresentacao] = useState(true);
  const [iomIncidentes, setIomIncidentes] = useState([]);
  const [incidentes, setIncidentes] = useState([]);
  const [apreensoes, setApreensoes] = useState([]);
  const [desembarques, setDesembarques] = useState([]);
  const [emodnetCelulas, setEmodnetCelulas] = useState([]);
  const [emodnetMeta, setEmodnetMeta] = useState(null);
  const [mclpNomes, setMclpNomes] = useState(["Porto (Sá Carneiro)", "Portimão"]);
  const [usarMeteoLive, setUsarMeteoLive] = useState(true);
  const [cliqueReactivo, setCliqueReactivo] = useState(false);
  const [cliqueLancamento, setCliqueLancamento] = useState(false);
  const [pontoReactivo, setPontoReactivo] = useState(null);
  const [basesLanc, setBasesLanc] = useState([]);
  const [baseSel, setBaseSel] = useState("");
  const [lancCustom, setLancCustom] = useState(null);
  const [tipoPatrulha, setTipoPatrulha] = useState("geral");
  const [cenarios, setCenarios] = useState([]);
  const [cenarioSel, setCenarioSel] = useState("");
  const [sadRespostas, setSadRespostas] = useState(null);
  const [regiaoCustom, setRegiaoCustom] = useState(null);
  const [cliqueRegiao, setCliqueRegiao] = useState(false);
  const [regiaoCliques, setRegiaoCliques] = useState([]);
  const [zonasFoco, setZonasFoco] = useState([]);
  const [clustersZonas, setClustersZonas] = useState([]);
  const [hudTab, setHudTab] = useState("operacao");
  const [corredorMapa, setCorredorMapa] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingPhase, setLoadingPhase] = useState("");
  const [calculandoRota, setCalculandoRota] = useState(false);
  const [fontesExternas, setFontesExternas] = useState("live");
  const [toast, setToast] = useState(null);
  const [incForm, setIncForm] = useState({
    titulo: "", detalhe: "", lat: DEMO_LAT, lon: DEMO_LON, severidade: "alta",
  });
  const tOnMin = frota?.t_on_limites?.min_h ?? 2;
  const tOnMax = frota?.t_on_limites?.max_h ?? (frota?.autonomia_util_h ? frota.autonomia_util_h - 0.5 : 14.5);
  const tOnRecom = frota?.t_on_limites?.recomendado_h ?? 4;

  useEffect(() => {
    if (tOnH > tOnMax) setTOnH(tOnMax);
    if (tOnH < tOnMin) setTOnH(tOnMin);
  }, [tOnMax, tOnMin, tOnH]);
  const toastTimer = useRef(null);
  const wsRef = useRef(null);
  const ventoRef = useRef(vento);
  const tipoPatrulhaRef = useRef(tipoPatrulha);
  ventoRef.current = vento;
  tipoPatrulhaRef.current = tipoPatrulha;

  const showToast = useCallback((msg, severidade = "media") => {
    setToast({ msg, severidade });
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 5000);
  }, []);

  const applyCore = useCallback((e, a, al, bl, f, risco, zonas) => {
    setEstado(e);
    setNavios(a.navios || []);
    setAlertas(al.alertas || []);
    setFrota(f);
    setCelulas((risco.celulas || []).slice(0, MAX_CELULAS_MAPA));
    setBasesLanc(bl.bases || []);
    setMclpNomes(bl.mclp_recomendadas || ["Porto (Sá Carneiro)", "Portimão"]);
    setBaseSel((prev) => prev || bl.mclp_recomendadas?.[0] || "");
    setCorredorMapa(zonas.corredor_costa || []);
    const foco = (zonas.zonas || []).flatMap((z) => z.celulas || []);
    setZonasFoco(foco);
  }, []);

  const applyCamadas = useCallback((m, ipma, rss, cen, sad, camIom, camApr, camDes, emod, clust) => {
    setMeteo(m?.bases || []);
    const avisos = (ipma?.avisos || []).filter((a) => a.titulo !== "Sem ligação IPMA");
    setAvisosIpma(avisos);
    setNoticiasRss(rss?.noticias || []);
    setCenarios(cen?.cenarios || []);
    setSadRespostas(sad);
    setIomIncidentes(camIom?.incidentes || []);
    setApreensoes(camApr?.apreensoes || []);
    setDesembarques(camDes?.desembarques || []);
    setEmodnetCelulas(emod?.celulas || []);
    setEmodnetMeta(emod);
    setClustersZonas(clust?.zonas || []);

    const modos = [m?.modo_fonte, ipma?.modo_fonte, rss?.modo_fonte];
    if (modos.every((x) => x === "cache_local")) setFontesExternas("offline");
    else if (modos.some((x) => x === "cache_local")) setFontesExternas("misto");
    else setFontesExternas("live");
  }, []);

  const refreshCamadasTipo = useCallback(async (tipo) => {
    const t = tipo ?? tipoPatrulha;
    const [zonas, emod, clust] = await Promise.all([
      get(`/zonas/patrulha?tipo=${t}&limiar=0.35`),
      get(`/camadas/emodnet?tipo=${t}&limiar=0.35`),
      get(`/zonas/clusters?tipo=${t}&limiar=0.5`),
    ]);
    setCorredorMapa(zonas.corredor_costa || []);
    setZonasFoco((zonas.zonas || []).flatMap((z) => z.celulas || []));
    setEmodnetCelulas(emod.celulas || []);
    setEmodnetMeta(emod);
    setClustersZonas(clust?.zonas || []);
  }, [tipoPatrulha]);

  const refreshLight = useCallback(async () => {
    const v = ventoRef.current;
    try {
      const [e, a, al, m, f, inc] = await Promise.all([
        get("/estado"),
        get("/ais/navios"),
        get("/alertas?limite=40"),
        get("/meteo/atual"),
        get(`/frota/dimensionar?vento_atual=${v}&vento_previsto=${v + 2}`),
        getSafe("/incidentes", { incidentes: [] }),
      ]);
      setEstado(e);
      setNavios(a.navios || []);
      setAlertas(al.alertas || []);
      setMeteo(m.bases || []);
      setFrota(f);
      setIncidentes(inc?.incidentes || []);
    } catch (err) {
      showToast(`Erro ao actualizar: ${err.message}`, "alta");
    }
  }, [showToast]);

  const refresh = useCallback(async () => {
    const v = ventoRef.current;
    const t = tipoPatrulhaRef.current;
    setLoading(true);
    setLoadingPhase("Operação…");
    try {
      const [e, a, al, bl, f, risco, zonas] = await Promise.all([
        get("/estado"),
        get("/ais/navios"),
        get("/alertas?limite=40"),
        get("/bases/lancamento"),
        get(`/frota/dimensionar?vento_atual=${v}&vento_previsto=${v + 2}`),
        get("/risco/celulas?limiar=0.15"),
        get(`/zonas/patrulha?tipo=${t}&limiar=0.35`),
      ]);
      applyCore(e, a, al, bl, f, risco, zonas);
      setLoading(false);

      setLoadingPhase("Camadas…");
      const settled = await Promise.allSettled([
        getSafe("/meteo/atual", { bases: [], modo_fonte: "cache_local" }),
        getSafe("/ipma/avisos", { avisos: [], modo_fonte: "cache_local" }),
        getSafe("/rss/noticias", { noticias: [], modo_fonte: "cache_local" }),
        get("/cenarios"),
        getSafe("/sad/respostas", null),
        getSafe("/camadas/iom", { incidentes: [] }),
        getSafe("/camadas/apreensoes", { apreensoes: [] }),
        getSafe("/camadas/desembarques", { desembarques: [] }),
        getSafe(`/camadas/emodnet?tipo=${t}&limiar=0.35`, { celulas: [] }),
        getSafe(`/zonas/clusters?tipo=${t}&limiar=0.5`, { zonas: [] }),
        getSafe("/incidentes", { incidentes: [] }),
      ]);
      const val = (i, fb) => (settled[i].status === "fulfilled" ? settled[i].value : fb);
      setIncidentes(val(10, { incidentes: [] }).incidentes || []);
      applyCamadas(
        val(0, { bases: [] }),
        val(1, { avisos: [] }),
        val(2, { noticias: [] }),
        val(3, { cenarios: [] }),
        val(4, null),
        val(5, { incidentes: [] }),
        val(6, { apreensoes: [] }),
        val(7, { desembarques: [] }),
        val(8, { celulas: [] }),
        val(9, { zonas: [] }),
      );
      const falhas = settled.filter((s) => s.status === "rejected").length;
      if (falhas > 0) {
        showToast(`${falhas} camada(s) em cache local — demo offline activa`, "media");
      }
    } catch (err) {
      showToast(`Erro ao carregar: ${err.message}`, "alta");
    } finally {
      setLoading(false);
      setLoadingPhase("");
    }
  }, [applyCore, applyCamadas, showToast]);

  useEffect(() => {
    if (!usarMeteoLive || !meteo.length) return;
    const v = ventoDaBase(baseSel, meteo);
    if (v != null && Math.abs(v - ventoRef.current) > 0.05) {
      setVento(v);
      refreshLight();
    }
  }, [usarMeteoLive, meteo, baseSel, refreshLight]);

  useEffect(() => {
    refresh();
    const t = setInterval(refreshLight, 120000);
    return () => clearInterval(t);
  }, [refresh, refreshLight]);

  const tipoPatrulhaInit = useRef(true);
  useEffect(() => {
    if (tipoPatrulhaInit.current) {
      tipoPatrulhaInit.current = false;
      return;
    }
    refreshCamadasTipo(tipoPatrulha);
  }, [tipoPatrulha, refreshCamadasTipo]);

  useEffect(() => {
    let fechado = false;
    let ws = null;
    let pingTimer = null;
    let reconnectTimer = null;
    let tentativas = 0;

    const conectar = () => {
      if (fechado) return;
      const proto = location.protocol === "https:" ? "wss" : "ws";
      ws = new WebSocket(`${proto}://${location.host}/api/ws/alertas`);
      wsRef.current = ws;

      ws.onmessage = (ev) => {
        const msg = JSON.parse(ev.data);
        if (msg.tipo === "alerta_novo" && msg.alerta) {
          setAlertas((prev) => {
            if (prev.some((a) => a.id === msg.alerta.id)) return prev;
            return [msg.alerta, ...prev].slice(0, 50);
          });
          showToast(msg.alerta.titulo, msg.alerta.severidade);
        } else if (msg.tipo === "sync") {
          if (msg.alertas) setAlertas(msg.alertas);
          if (msg.estado) setEstado((prev) => ({ ...prev, ...msg.estado }));
        }
      };

      ws.onopen = () => {
        tentativas = 0;
        ws.send("ping");
        pingTimer = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send("ping");
        }, 30000);
      };

      ws.onclose = () => {
        clearInterval(pingTimer);
        if (fechado) return;
        tentativas += 1;
        const espera = Math.min(15000, 1000 * 2 ** Math.min(tentativas, 4));
        reconnectTimer = setTimeout(conectar, espera);
      };

      ws.onerror = () => {
        try { ws.close(); } catch { /* fecho dispara onclose */ }
      };
    };

    conectar();

    return () => {
      fechado = true;
      clearInterval(pingTimer);
      clearTimeout(reconnectTimer);
      try { ws && ws.close(); } catch { /* noop */ }
    };
  }, [showToast]);

  const paramsLanc = () => {
    if (lancCustom) return { lon_lanc: lancCustom.lon, lat_lanc: lancCustom.lat, base: null };
    if (baseSel) return { base: baseSel };
    return {};
  };

  const paramsRegiao = () => {
    if (!regiaoCustom) return {};
    return { regiao: regiaoCustom };
  };

  const paramsMeteo = () => ({ usar_meteo_live: usarMeteoLive, vento_ms: vento });

  const paramsRota = () => ({
    n_alvos: nAlvos,
    t_on_h: tOnH,
  });

  const activarApresentacao = () => {
    setModoApresentacao(true);
    setCamadas(CAMADAS_APRESENTACAO);
    showToast("Modo apresentação — mapa optimizado para demo", "media");
  };

  const activarCompleto = () => {
    setModoApresentacao(false);
    setCamadas(CAMADAS_COMPLETO);
    showToast("Modo completo — todas as camadas analíticas", "media");
  };

  const resumoRota = (r) => {
    const pts = [];
    if (r?.zona_cluster?.nome) pts.push(r.zona_cluster.nome);
    if (r?.distancia_km != null) pts.push(`${r.distancia_km} km`);
    if (r?.n_pontos_patrol != null) pts.push(`${r.n_pontos_patrol} pts`);
    if (r?.tempo_h != null) pts.push(`${r.tempo_h} h`);
    return pts.join(" · ") || "rota calculada";
  };

  const calcularRota = async (lon, lat) => {
    if (calculandoRota) return;
    setCalculandoRota(true);
    try {
      const pl = { ...paramsLanc(), tipo_patrulha: tipoPatrulha, ...paramsRegiao(), ...paramsMeteo(), ...paramsRota() };
      if (cenarioSel) pl.cenario_id = cenarioSel;
      let r;
      if (modo === "sortie") {
        r = await post("/rotas/sortie", pl);
      } else if (modo === "plano24h") {
        r = await post("/rotas/plano24h", { k_bases: 2, ...pl });
      } else {
        const p = pontoReactivo || { lon: lon ?? -9.1, lat: lat ?? 38.7 };
        r = await post("/rotas/reativo", { lon: p.lon, lat: p.lat, ...paramsLanc(), ...paramsMeteo(), t_on_h: tOnH });
      }
      setRota(r);
      showToast(`Rota ${r?.modo || modo}: ${resumoRota(r)}`, "media");
    } catch (err) {
      showToast(`Erro ao calcular rota: ${err.message}`, "alta");
    } finally {
      setCalculandoRota(false);
    }
  };

  const exportarPlano = async () => {
    if (!rota) {
      showToast("Calcule uma rota primeiro", "media");
      return;
    }
    const pl = {
      modo,
      ...paramsRota(),
      ...paramsLanc(),
      tipo_patrulha: tipoPatrulha,
      ...paramsRegiao(),
      ...paramsMeteo(),
    };
    if (cenarioSel) pl.cenario_id = cenarioSel;
    if (modo === "plano24h") pl.k_bases = 2;
    if (modo === "reativo" && pontoReactivo) {
      pl.lon = pontoReactivo.lon;
      pl.lat = pontoReactivo.lat;
    }
    const plano = await post("/export/plano-missao", pl);
    const blob = new Blob([JSON.stringify(plano, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `plano_missao_sad_ar5_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("Plano de missão exportado (JSON)", "media");
  };

  const aplicarCenario = async (c) => {
    setCenarioSel(c.id);
    setModo(c.modo);
    setTipoPatrulha(c.tipo_patrulha);
    if (c.base) {
      setBaseSel(c.base);
      setLancCustom(null);
    }
    setRegiaoCustom(c.regiao || null);
    setRegiaoCliques([]);
    setCliqueRegiao(false);
    setCalculandoRota(true);
    try {
      const resp = await post(`/cenarios/${c.id}/executar`, {
        ...paramsMeteo(),
        base: c.base || baseSel || undefined,
      });
      setRota(resp.rota);
      showToast(`Cenário: ${c.nome} — ${resumoRota(resp.rota)}`, "media");
    } catch (err) {
      showToast(`Erro no cenário: ${err.message}`, "alta");
    } finally {
      setCalculandoRota(false);
    }
  };

  const limparRegiao = () => {
    setRegiaoCustom(null);
    setRegiaoCliques([]);
    setCenarioSel("");
  };

  const handleMapClick = (lat, lon) => {
    if (cliqueRegiao) {
      const next = [...regiaoCliques, lat];
      if (next.length === 1) {
        setRegiaoCliques(next);
        showToast("Limite N definido — clique limite S", "media");
        return;
      }
      const latMax = Math.max(next[0], lat);
      const latMin = Math.min(next[0], lat);
      const reg = { lat_min: latMin, lat_max: latMax, ...PT_LON };
      setRegiaoCustom(reg);
      setRegiaoCliques([]);
      setCliqueRegiao(false);
      setCenarioSel("");
      showToast(`Região: ${latMin.toFixed(2)}°–${latMax.toFixed(2)}° N`, "media");
      return;
    }
    if (cliqueLancamento) {
      setLancCustom({ lat, lon });
      setBaseSel("");
      setCliqueLancamento(false);
      showToast(`Lançamento: ${lat.toFixed(2)}°, ${lon.toFixed(2)}°`, "media");
      return;
    }
    if (cliqueReactivo) {
      setPontoReactivo({ lat, lon });
      setModo("reativo");
      calcularRota(lon, lat);
    }
  };

  const simular = async (tipo) => {
    try {
      const r = await post("/demo/simular", { tipo, aleatorio: true });
      const pt = r?.ponto;
      const titulo = r?.alerta?.titulo
        || (tipo === "spoofing" ? "Spoofing AIS simulado" : "Incidente simulado");
      const coords = pt ? ` · ${pt.lat?.toFixed(2)}°N, ${pt.lon?.toFixed(2)}°W` : "";
      showToast(`${titulo}${coords}`, r?.alerta?.severidade || (tipo === "spoofing" ? "critica" : "alta"));
      if (pt?.lat != null && pt?.lon != null) {
        setIncForm((f) => ({ ...f, lat: pt.lat, lon: pt.lon }));
      }
    } catch (err) {
      showToast(`Erro na simulação: ${err.message}`, "alta");
    }
    refresh();
  };

  const registarIncidente = async (e) => {
    e.preventDefault();
    await post("/incidentes", incForm);
    setIncForm({ titulo: "", detalhe: "", lat: DEMO_LAT, lon: DEMO_LON, severidade: "alta" });
    refresh();
    showToast("Incidente registado", "alta");
  };

  const toggleCamada = (k) => setCamadas((c) => ({ ...c, [k]: !c[k] }));

  const waypoints = rota?.waypoints || [];
  const linha = waypoints.map((w) => [w.lat, w.lon]);
  const sectoresRotas = rota?.rotas_sector || [];
  const corredor = rota?.corredor_costa?.length ? rota.corredor_costa : corredorMapa;
  const linhaCorredor = corredor.map((p) => [p.lat, p.lon]);
  const lancamentoActivo = lancCustom || basesLanc.find((b) => b.nome === baseSel);
  const regiaoBounds = regiaoCustom
    ? [[regiaoCustom.lat_min, regiaoCustom.lon_min], [regiaoCustom.lat_max, regiaoCustom.lon_max]]
    : null;

  return (
    <div className="layout">
      {toast && (
        <div className={`toast ${toast.severidade}`} onClick={() => setToast(null)}>
          {toast.msg}
        </div>
      )}

      <aside className="sidebar">
        <h1>SAD AR5 — Plataforma Operacional</h1>

        <div className="status-strip">
          {loading && (
            <div className="pill loading-pill" title={loadingPhase || "A carregar"}>
              {loadingPhase || "A carregar…"}
            </div>
          )}
          <div className={`pill ${estado?.modo_demo ? "demo" : "live"}`}>
            {estado?.modo_demo ? "Demo AIS" : "AIS live"}
          </div>
          <div className="pill">Navios <b>{estado?.n_navios ?? "—"}</b></div>
          <div className="pill">Alto risco <b>{estado?.risco_resumo?.n_alto_risco ?? 300}</b></div>
          <div className="pill">
            Frota <b>{frota?.analise_sad?.frota_costeira_24h ?? sadRespostas?.Q2_quantos?.frota_costeira ?? 9}</b>/
            <b>{frota?.analise_sad?.frota_total_alto_risco ?? sadRespostas?.Q2_quantos?.frota_total ?? 11}</b>
          </div>
          <div className="pill">Ganho <b>{sadRespostas?.validacao?.ganho_sad_vs_aleatorio ?? "2,06"}×</b></div>
          {modoApresentacao && <div className="pill apresentacao">Apresentação</div>}
          {fontesExternas !== "live" && (
            <div className="pill offline" title="Meteo/IPMA/RSS em cache local">
              {fontesExternas === "offline" ? "Offline OK" : "Rede parcial"}
            </div>
          )}
        </div>

        {modoApresentacao && (
          <div className="card apresentacao-banner">
            <b>Modo apresentação</b>
            <div className="stat">Mapa leve: bases, clusters, corredor, AIS e rota. Active camadas extra no separador Camadas.</div>
          </div>
        )}

        {fontesExternas === "offline" && (
          <div className="card offline-banner">
            <b>Dados externos em cache</b>
            <div className="stat">Grelha SAD, frota, rotas e camadas locais funcionam sem internet.</div>
          </div>
        )}

        {estado?.modo_demo && (
          <div className="card demo-banner">
            <b>Modo demonstração</b>
            <div className="stat">{estado.demo_mensagem || "Navios simulados — sem chave AIS"}</div>
          </div>
        )}

        <nav className="hud-tabs">
          {[
            ["operacao", "Operação"],
            ["camadas", "Camadas"],
            ["mais", "Mais"],
          ].map(([id, lbl]) => (
            <button
              key={id}
              type="button"
              className={`hud-tab ${hudTab === id ? "active" : ""}`}
              onClick={() => setHudTab(id)}
            >
              {lbl}
            </button>
          ))}
        </nav>

        <div className="row" style={{ marginBottom: 10 }}>
          <button className="btn" onClick={refresh} disabled={loading}>Atualizar</button>
          <button
            className={`btn ${modoApresentacao ? "active" : "secondary"}`}
            onClick={modoApresentacao ? activarCompleto : activarApresentacao}
            title="Alternar conjunto de camadas do mapa"
          >
            {modoApresentacao ? "Modo completo" : "Apresentação"}
          </button>
        </div>
        <div className="row" style={{ marginBottom: 10 }}>
          <button className="btn secondary" onClick={() => simular("spoofing")}>Sim. spoofing</button>
          <button className="btn secondary" onClick={() => simular("incidente")}>Sim. incidente</button>
        </div>

        {hudTab === "operacao" && (
          <>
            {sadRespostas && !sadRespostas.erro && (
              <div className="card sad-panel compact">
                <div className="metric-row">
                  <span><b>Q1</b> {(sadRespostas.Q1_onde?.zonas_patrulha || []).join(" · ")}</span>
                </div>
                <div className="metric-row">
                  <span><b>Q2</b> {sadRespostas.Q2_quantos?.frota_costeira ?? 9} costeiros · {sadRespostas.Q2_quantos?.frota_total ?? 11} total · {sadRespostas.Q2_quantos?.n_simultaneos ?? 3} sim.</span>
                </div>
                <div className="metric-row">
                  <span><b>Q3</b> {(sadRespostas.Q3_bases?.bases || ["Porto", "Portimão"]).join(" + ")}</span>
                </div>
              </div>
            )}

            {frota && (
              <div className="card compact">
                <div><b>Frota AR5</b> — plano {frota.frota_recomendada ?? frota.frota_total} · raio {frota.raio_operacional_km} km</div>
                <div className="stat">
                  Vento {frota.vento_atual_ms ?? vento} m/s · revisita {frota.revisita_h ?? 3} h · swath {frota.swath_km ?? 30} km
                </div>
              </div>
            )}

            {rota && (
              <div className={`card rota-resumo ${rota.dentro_autonomia === false ? "warn-card" : ""}`}>
                <b>Rota activa — {rota.modo}</b>
                {rota.zona_cluster?.nome && <div className="stat">Zona: {rota.zona_cluster.nome}</div>}
                {rota.fallback_local && (
                  <div className="stat" style={{ color: "#f1c40f" }}>
                    Zona de risco fora de alcance — patrulha do sector local da base.
                  </div>
                )}
                <div className="stat">
                  {rota.base && <>Base {rota.base} · </>}
                  {rota.distancia_km != null && <>{rota.distancia_km} km · </>}
                  {rota.tempo_h != null && <>{rota.tempo_h} h voo · </>}
                  {rota.n_pontos_patrol != null && <>{rota.n_pontos_patrol} pts patrulha</>}
                </div>
                {rota.estrategia_varrimento && (
                  <div className="stat">Varrimento: {rota.estrategia_varrimento}</div>
                )}
                {rota.corredor_operacional && (
                  <div className="stat">Corredor: {rota.corredor_operacional}</div>
                )}
                {rota.dentro_autonomia === false && <div className="warn">Fora de autonomia AR5</div>}
                {rota.meteo?.condicao && (
                  <div className="stat">Meteo: {rota.meteo.condicao} · vento {rota.meteo.vento_ms} m/s</div>
                )}
                {rota.validacao?.score != null && (
                  <div className={`validacao-rota ${rota.validacao.classe?.toLowerCase()}`}>
                    <b>Qualidade {rota.validacao.score}/100 · {rota.validacao.classe}</b>
                    {rota.validacao.pct_na_zona != null && (
                      <div className="stat">{rota.validacao.pct_na_zona}% na zona · cont. {rota.validacao.continuidade?.salto_medio_km} km méd</div>
                    )}
                    {rota.validacao.n_sectores != null && (
                      <div className="stat">{rota.validacao.n_sectores} sectores · {rota.validacao.n_sectores_rever} a rever</div>
                    )}
                    {(rota.validacao.avisos || []).slice(0, 2).map((av, i) => (
                      <div key={i} className="stat">• {av}</div>
                    ))}
                  </div>
                )}
              </div>
            )}

            <h2>Cenários</h2>
            <div className="cenarios-list">
              {cenarios.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  className={`card cenario-btn ${cenarioSel === c.id ? "activo" : ""}`}
                  onClick={() => aplicarCenario(c)}
                >
                  <b>{c.nome}</b>
                  <div className="stat">{c.descricao?.slice(0, 85)}{(c.descricao?.length > 85) ? "…" : ""}</div>
                </button>
              ))}
            </div>

            <h2>Patrulha e rotas</h2>
            <select value={tipoPatrulha} onChange={(e) => setTipoPatrulha(e.target.value)}>
              <option value="geral">Risco global (SAD)</option>
              <option value="costeira">Costeira uniforme</option>
              <option value="droga">Foco: droga</option>
              <option value="pesca">Foco: pesca INN</option>
              <option value="poluicao">Foco: poluição</option>
              <option value="imigracao">Foco: imigração</option>
            </select>
            <select value={baseSel} onChange={(e) => { setBaseSel(e.target.value); setLancCustom(null); }}>
              <option value="">— MCLP automático —</option>
              {basesLanc.map((b) => (
                <option key={b.nome} value={b.nome}>[{b.forca}] {b.nome}</option>
              ))}
            </select>
            <label className="check-row">
              <input type="checkbox" checked={usarMeteoLive} onChange={(e) => setUsarMeteoLive(e.target.checked)} />
              Meteo live nas rotas
            </label>
            {!usarMeteoLive && (
              <input type="number" value={vento} min={0} max={25} step={0.5}
                onChange={(e) => setVento(parseFloat(e.target.value) || 0)} />
            )}
            <div className="row">
              <label style={{ flex: 1 }}>Alvos
                <input type="number" value={nAlvos} min={4} max={20} onChange={(e) => setNAlvos(parseInt(e.target.value, 10) || 8)} />
              </label>
              <label style={{ flex: 1 }} title={`Autonomia AR5: ${frota?.autonomia_h ?? 16} h (−${frota?.reserva_h ?? 1} h reserva)`}>
                t<sub>on</sub> patrulha (h)
                <input
                  type="number"
                  value={tOnH}
                  min={tOnMin}
                  max={tOnMax}
                  step={0.5}
                  onChange={(e) => setTOnH(Math.min(tOnMax, Math.max(tOnMin, parseFloat(e.target.value) || tOnRecom)))}
                />
              </label>
            </div>
            <div className="stat autonomy-hint">
              Autonomia AR5: <b>{frota?.autonomia_h ?? 16} h</b> útil · t<sub>on</sub> máx. <b>{tOnMax} h</b>
              {modo === "plano24h" && <> · janela/sector <b>{frota?.t_on_limites?.janela_sector_h ?? 4} h</b></>}
              {tOnH >= tOnMax - 0.5 && <span className="warn"> · perto do limite</span>}
            </div>
            <select value={modo} onChange={(e) => setModo(e.target.value)}>
              <option value="sortie">Sortie — varrimento por zona k-means</option>
              <option value="plano24h">Plano 24 h — 6 sectores + clusters</option>
              <option value="reativo">Despacho reactivo (clique no mapa)</option>
            </select>
            <div className="row">
              <button className={`btn ${cliqueRegiao ? "active" : "secondary"}`} onClick={() => { setCliqueRegiao((v) => !v); setCliqueLancamento(false); setCliqueReactivo(false); setRegiaoCliques([]); }}>
                {cliqueRegiao ? "Clique limite…" : "Região (2 cliques)"}
              </button>
              <button className={`btn ${cliqueLancamento ? "active" : "secondary"}`} onClick={() => { setCliqueLancamento((v) => !v); setCliqueReactivo(false); setCliqueRegiao(false); }}>
                Lançamento mapa
              </button>
            </div>
            <div className="row">
              <button className={`btn ${calculandoRota ? "loading" : ""}`} onClick={() => calcularRota()} disabled={calculandoRota}>
                {calculandoRota ? "A calcular…" : "Calcular rota"}
              </button>
              <button className="btn secondary" onClick={exportarPlano}>Exportar</button>
              <button className={`btn ${cliqueReactivo ? "active" : "secondary"}`} onClick={() => { setCliqueReactivo((v) => !v); setCliqueLancamento(false); setCliqueRegiao(false); }}>
                {cliqueReactivo ? "Clique alvo…" : "Reactivo"}
              </button>
            </div>
            {regiaoCustom && (
              <div className="card stat">
                Região: {regiaoCustom.lat_min?.toFixed(2)}°–{regiaoCustom.lat_max?.toFixed(2)}° N
                <button className="btn secondary" style={{ marginLeft: 8 }} onClick={limparRegiao}>Limpar</button>
              </div>
            )}
            {rota?.modo === "plano_24h" && rota.agenda_24h?.length > 0 && (
              <div className="card agenda-24h">
                <b>Agenda 24 h</b>
                {rota.agenda_24h.map((a) => (
                  <div key={a.sector} className="stat">
                    S{a.sector} {a.janela_h} · {a.base_lancamento} · {a.dist_km} km
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {hudTab === "camadas" && (
          <>
            <h2>Camadas</h2>
            <div className="row toggles">
              {[
                ["clusters", "Zonas k-means"],
                ["foco", "Zona foco"],
                ["emodnet", "EMODnet"],
                ["risco", "Risco global"],
                ["navios", "AIS"],
                ["apreensoes", "Apreensões mar"],
                ["desembarques", "Desembarques"],
                ["incidentes", "Incidentes"],
                ["iom", "IOM"],
                ["bases", "Bases"],
                ["corredor", "Corredor"],
                ["rota", "Rota activa"],
                ["sectores", "Sectores 24h"],
              ].map(([k, lbl]) => (
                <button key={k} className={`btn ${camadas[k] ? "" : "secondary"}`} onClick={() => toggleCamada(k)}>
                  {lbl}
                </button>
              ))}
            </div>
            <div className="card stat">
              {clustersZonas.length} zonas k-means · {corredorMapa.length} pts corredor · {apreensoes.length} apreensões em mar
            </div>
          </>
        )}

        {hudTab === "mais" && (
          <>
            <h2>Registar incidente</h2>
            <form className="form-inc" onSubmit={registarIncidente}>
              <input placeholder="Título" required value={incForm.titulo}
                onChange={(e) => setIncForm({ ...incForm, titulo: e.target.value })} />
              <input placeholder="Detalhe" value={incForm.detalhe}
                onChange={(e) => setIncForm({ ...incForm, detalhe: e.target.value })} />
              <button className="btn" type="submit">Registar</button>
            </form>
            <h2>Incidentes ({incidentes.length})</h2>
            {incidentes.slice(0, 5).map((p) => (
              <div key={p.id} className={`card ${p.severidade}`}>
                <b>{p.titulo}</b>
                <div className="stat">{p.lat?.toFixed(2)}°, {p.lon?.toFixed(2)}° · {p.fonte}</div>
              </div>
            ))}
            <h2>Alertas ({alertas.length})</h2>
            {alertas.slice(0, 8).map((a) => (
              <div key={a.id} className={`card ${a.severidade}`}>
                <b>{a.titulo}</b>
                <div className="stat">{a.detalhe?.slice(0, 70)}</div>
              </div>
            ))}
            <h2>IPMA</h2>
            {avisosIpma.slice(0, 3).map((a, i) => (
              <div key={i} className="card"><b>{a.titulo}</b><div className="stat">{a.distrito}</div></div>
            ))}
            <h2>RSS</h2>
            {noticiasRss.slice(0, 3).map((n, i) => (
              <div key={i} className="card stat">{n.titulo?.slice(0, 60)}</div>
            ))}
          </>
        )}
      </aside>

      <main className="map-wrap">
        <MapContainer
          center={PT_CENTER}
          zoom={7}
          minZoom={6}
          maxZoom={12}
          maxBounds={PT_BOUNDS}
          maxBoundsViscosity={1.0}
          className="map-container"
        >
          <TileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; OpenStreetMap"
          />
          <MapResize />
          <MapClickHandler
            activo={cliqueReactivo || cliqueLancamento || cliqueRegiao}
            onClick={handleMapClick}
          />

          {regiaoBounds && (
            <Rectangle
              bounds={regiaoBounds}
              pathOptions={{ color: "#9b59b6", weight: 2, fillOpacity: 0.12, dashArray: "6 4" }}
            />
          )}

          {camadas.corredor && linhaCorredor.length > 1 && (
            <Polyline positions={linhaCorredor}
              pathOptions={{ color: "#2ecc71", weight: 2, opacity: 0.6, dashArray: "4 8" }} />
          )}

          {camadas.clusters && clustersZonas.map((z) => (
            <Rectangle
              key={`cl-${z.id}`}
              bounds={[[z.lat_min, z.lon_min], [z.lat_max, z.lon_max]]}
              pathOptions={{
                color: ["#e74c3c", "#9b59b6", "#1abc9c", "#e67e22", "#3498db", "#f1c40f"][z.id % 6],
                weight: 2,
                fillOpacity: 0.08,
                dashArray: "5 4",
              }}
            >
              <Popup>
                <b>Zona {z.rank}: {z.nome}</b><br />
                {z.n_celulas} células · risco médio {z.risco_medio}<br />
                k-means SAD (varrimento)
              </Popup>
            </Rectangle>
          ))}

          {camadas.bases && basesLanc.map((b) => (
            <Marker key={b.nome} position={[b.lat, b.lon]}
              icon={iconBase(b.forca, lancamentoActivo?.nome === b.nome && !lancCustom, isBaseMclp(b.nome, mclpNomes))}>
              <Popup>
                <b>{b.nome}</b>
                {isBaseMclp(b.nome, mclpNomes) && <><br /><b>★ Base MCLP</b></>}
                <br />
                {b.forca} · {b.dist_costa_km} km da costa<br />
                {b.tipo}
              </Popup>
            </Marker>
          ))}

          {camadas.emodnet && emodnetCelulas.map((c, i) => (
            <CircleMarker
              key={`em-${i}`}
              center={[c.lat, c.lon]}
              radius={3 + (c.intensidade || 0) * 5}
              pathOptions={{
                color: COR_EMODNET[tipoPatrulha] || COR_EMODNET.geral,
                fillColor: "transparent",
                fillOpacity: 0,
                weight: 2,
                dashArray: "3 2",
              }}
            >
              <Popup>
                EMODnet {tipoPatrulha}: {c.intensidade}<br />
                Risco global {c.risco}
              </Popup>
            </CircleMarker>
          ))}

          {lancCustom && (
            <Marker position={[lancCustom.lat, lancCustom.lon]}
              icon={iconBase("Operacional", true)}>
              <Popup>Lançamento personalizado</Popup>
            </Marker>
          )}

          {camadas.foco && zonasFoco.map((c, i) => (
            <CircleMarker
              key={`f-${i}`}
              center={[c.lat, c.lon]}
              radius={6 + (c.score || c.risco || 0) * 4}
              pathOptions={{
                color: "#e67e22",
                fillColor: corRisco(c.score ?? c.risco ?? 0),
                fillOpacity: 0.55,
                weight: 2,
                dashArray: "4 3",
              }}
            >
              <Popup>
                Foco {tipoPatrulha}: score {c.score ?? c.risco}<br />
                {rotuloRisco(c.score ?? c.risco ?? 0)}
              </Popup>
            </CircleMarker>
          ))}

          {camadas.risco && celulas.map((c, i) => (
            <CircleMarker
              key={`r-${i}`}
              center={[c.lat, c.lon]}
              radius={3 + c.risco * 5}
              pathOptions={{
                color: corRisco(c.risco),
                fillColor: corRisco(c.risco),
                fillOpacity: 0.5,
                weight: 1,
              }}
            >
              <Popup>
                Risco {c.risco} — {rotuloRisco(c.risco)}<br />
                Droga {c.r_droga} · Pesca {c.r_pesca}
              </Popup>
            </CircleMarker>
          ))}

          {camadas.iom && iomIncidentes.map((p) => (
            <CircleMarker key={p.id} center={[p.lat, p.lon]} radius={8}
              pathOptions={{
                color: "#6c3483",
                fillColor: "#9b59b6",
                fillOpacity: 0.9,
                weight: 2,
                dashArray: "1 0",
              }}>
              <Popup>
                <b>IOM — imigração irregular</b><br />
                {p.data} · {p.vitimas} vítima(s)<br />
                {p.fonte}
              </Popup>
            </CircleMarker>
          ))}

          {camadas.desembarques && desembarques.map((p) => (
            <CircleMarker key={p.id} center={[p.lat, p.lon]} radius={6}
              pathOptions={{
                color: "#1a5276",
                fillColor: "#5dade2",
                fillOpacity: 0.85,
                weight: 2,
                dashArray: "6 3",
              }}>
              <Popup>
                <b>Desembarque marítimo PT</b><br />
                {p.ano} · {p.n_pessoas} pessoas · {p.distrito}<br />
                {p.rota}<br />{p.fonte}
              </Popup>
            </CircleMarker>
          ))}

          {camadas.apreensoes && apreensoes.map((p) => (
            <CircleMarker key={p.id} center={[p.lat, p.lon]}
              radius={5 + Math.min(p.n, 6)}
              pathOptions={{
                color: "#922b21",
                fillColor: "#c0392b",
                fillOpacity: 0.75,
                weight: 2,
              }}>
              <Popup>
                <b>Apreensão marítima (UNODC)</b><br />
                {p.n} registo(s) · {p.ano_min}–{p.ano_max}<br />
                Só eventos marítimos em células de mar<br />
                {p.fonte}
              </Popup>
            </CircleMarker>
          ))}

          {camadas.incidentes && incidentes.map((p) => (
            <Marker key={p.id} position={[p.lat, p.lon]}
              icon={L.divIcon({
                className: "",
                html: `<div style="font-size:20px;line-height:20px;filter:drop-shadow(0 0 3px #000)">${
                  p.severidade === "critica" ? "🛑" : "⚠️"
                }</div>`,
                iconSize: [20, 20], iconAnchor: [10, 10],
              })}>
              <Popup>
                <b>{p.titulo}</b><br />
                {p.detalhe}<br />
                {p.severidade?.toUpperCase()} · {p.fonte}
              </Popup>
            </Marker>
          ))}

          {camadas.navios && navios.map((n) => (
            <CircleMarker key={n.mmsi} center={[n.lat, n.lon]} radius={n.mmsi === "263SIM999" ? 7 : 5}
              pathOptions={{
                color: n.sog_nos > 35 ? "#e74c3c" : n.mmsi === "263SIM999" ? "#f39c12" : "#2980b9",
                fillColor: n.mmsi === "263SIM999" ? "#f39c12" : "#3498db",
                fillOpacity: 0.85,
                weight: n.mmsi === "263SIM999" ? 3 : 1,
              }}>
              <Popup>
                <b>{n.nome}</b><br />MMSI {n.mmsi}<br />{n.sog_nos} nós
              </Popup>
            </CircleMarker>
          ))}

          {camadas.rota && modo !== "plano24h" && linha.length > 1 && (
            <Polyline positions={linha}
              pathOptions={{ color: "#f39c12", weight: 3, dashArray: "8 6" }} />
          )}

          {camadas.sectores && sectoresRotas.map((s) => (
            <Polyline
              key={`sec-${s.sector}`}
              positions={(s.waypoints || []).map((w) => [w.lat, w.lon])}
              pathOptions={{
                color: CORES_SECTOR_24H[(s.sector - 1) % 6],
                weight: modo === "plano24h" ? 4 : 2,
                opacity: modo === "plano24h" ? 0.92 : 0.85,
              }}
            />
          ))}

          {camadas.sectores && modo === "plano24h" && sectoresRotas.map((s) => {
            const wps = s.waypoints || [];
            if (!wps.length) return null;
            const mid = wps[Math.floor(wps.length / 2)];
            return (
              <Marker
                key={`lbl-${s.sector}`}
                position={[mid.lat, mid.lon]}
                icon={L.divIcon({
                  className: "",
                  html: `<div style="background:${CORES_SECTOR_24H[(s.sector - 1) % 6]};color:#fff;font-size:10px;font-weight:bold;padding:2px 5px;border-radius:4px;border:1px solid #fff;box-shadow:0 0 4px #000">S${s.sector}</div>`,
                  iconSize: [28, 16],
                  iconAnchor: [14, 8],
                })}
              >
                <Popup>
                  Sector {s.sector} · {s.janela_h}<br />
                  Base <b>{s.base}</b><br />
                  {s.dist_km} km · {s.n_pontos_patrol} pts patrulha
                </Popup>
              </Marker>
            );
          })}

          {camadas.sectores && rota?.sectores?.map((s) => (
            <CircleMarker key={`sm-${s.sector}`} center={[s.lat, s.lon]} radius={8}
              pathOptions={{ color: "#fff", fillColor: "#9b59b6", fillOpacity: 0.5 }}>
              <Popup>
                Sector {s.sector}<br />Base {s.base}<br />{s.janela_h}
              </Popup>
            </CircleMarker>
          ))}

          {pontoReactivo && (
            <Marker position={[pontoReactivo.lat, pontoReactivo.lon]}
              icon={L.divIcon({
                className: "",
                html: '<div style="color:#e74c3c;font-size:18px">✕</div>',
              })} />
          )}

          {camadas.rota && waypoints.map((w, i) => (
            <Marker key={i} position={[w.lat, w.lon]}
              icon={L.divIcon({
                className: "",
                html: `<div style="color:${
                  w.tipo === "base" ? "#95a5a6"
                  : w.tipo === "entrada_mar" ? "#1abc9c"
                  : w.tipo === "corredor" ? "#27ae60"
                  : w.tipo === "orbita" ? "#9b59b6"
                  : "#f39c12"
                };font-weight:bold;font-size:${w.tipo === "base" ? 10 : 12}px">${
                  w.tipo === "base" ? "B" : w.tipo === "entrada_mar" ? "M" : i
                }</div>`,
              })} />
          ))}
        </MapContainer>

        <div className="map-legend">
          <div className="map-legend-title">Legenda</div>
          <div className="legend-section-title">Escala de risco SAD</div>
          {ESCALA_RISCO.map((faixa) => (
            <div key={faixa.rotulo} className="legend-row">
              <span className="legend-swatch" style={{ background: faixa.cor }} />
              {faixa.rotulo}
            </div>
          ))}
          <div className="legend-section-title">Camadas</div>
          {LEGENDA_FORCAS.map(([k, lbl]) => (
            <div key={k} className="legend-row">
              <span className="legend-swatch" style={{ background: COR_FORCA[k] }} />
              {lbl}
            </div>
          ))}
          <div className="legend-row">
            <span className="legend-swatch" style={{ background: "#9b59b6" }} />
            IOM
          </div>
          <div className="legend-row">
            <span className="legend-swatch" style={{ background: "#e74c3c" }} />
            Apreensões
          </div>
          <div className="legend-row">
            <span style={{ width: 14, display: "inline-block" }}>⚠️</span>
            Incidente
          </div>
          <div className="legend-row">
            <span className="legend-line" style={{ background: "#2ecc71" }} />
            Corredor costeiro
          </div>
          <div className="legend-row">
            <span className="legend-line" style={{ background: "#f39c12" }} />
            Rota patrulha
          </div>
          <div className="legend-row">
            <span style={{ color: "#1abc9c", fontWeight: "bold", width: 14, display: "inline-block" }}>M</span>
            Entrada marítima
          </div>
          <div className="legend-row">
            <span style={{ color: "#95a5a6", fontWeight: "bold", width: 14, display: "inline-block" }}>B</span>
            Base (só se autonomia exigir)
          </div>
          <div className="legend-row">
            <span className="legend-swatch legend-hollow" style={{ borderColor: COR_EMODNET[tipoPatrulha] || COR_EMODNET.geral }} />
            EMODnet ({tipoPatrulha}) — anel
          </div>
          <div className="legend-row">
            <span className="legend-swatch legend-dashed" style={{ background: "#e67e22" }} />
            Foco patrulha
          </div>
          <div className="legend-row">
            <span className="legend-swatch" style={{ background: "#5dade2" }} />
            Desembarques (tracejado)
          </div>
          <div className="legend-row">
            <span className="legend-swatch" style={{ background: "#f1c40f", border: "2px solid #fff" }} />
            Base MCLP (Porto / Portimão)
          </div>
          {modo === "plano24h" && sectoresRotas.length > 0 && (
            <>
              <div className="legend-section-title">Sectores 24 h</div>
              {sectoresRotas.slice(0, 6).map((s) => (
                <div key={`leg-s${s.sector}`} className="legend-row">
                  <span className="legend-line" style={{ background: CORES_SECTOR_24H[(s.sector - 1) % 6] }} />
                  S{s.sector} — {s.base?.split("(")[0]?.trim() || s.base}
                </div>
              ))}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
