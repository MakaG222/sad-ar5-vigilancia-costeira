// Ponto de demonstração: mar aberto a O de Sesimbra (~26 km da costa)
export const API = "/api";
export const DEMO_LON = -9.50;
export const DEMO_LAT = 38.45;
export const PT_BOUNDS = [[36.85, -11.0], [42.2, -7.38]];
export const PT_LON = { lon_min: -11.0, lon_max: -7.38 };
export const PT_CENTER = [39.5, -9.0];
export const MAX_CELULAS_MAPA = 220;
export const COR_FORCA = { FAP: "#3498db", Marinha: "#1abc9c", Exercito: "#2ecc71", Civil: "#bdc3c7", Operacional: "#f39c12" };
export const LEGENDA_FORCAS = [
  ["FAP", "FAP"], ["Marinha", "Marinha"], ["Exercito", "Exército"], ["Civil", "Civil"], ["Operacional", "Lançamento"],
];

export const COR_EMODNET = {
  droga: "#c0392b", pesca: "#27ae60", poluicao: "#2980b9",
  imigracao: "#8e44ad", geral: "#e67e22", costeira: "#95a5a6",
};

/** Escala de risco SAD (baixo → alto) — alinhada com validação (limiar 0,5). */
export const ESCALA_RISCO = [
  { min: 0.7, cor: "#c0392b", rotulo: "Muito alto (≥0,7)" },
  { min: 0.5, cor: "#e67e22", rotulo: "Alto (0,5–0,7)" },
  { min: 0.3, cor: "#f1c40f", rotulo: "Médio (0,3–0,5)" },
  { min: 0, cor: "#3498db", rotulo: "Baixo (<0,3)" },
];

export const CORES_SECTOR_24H = ["#e74c3c", "#9b59b6", "#1abc9c", "#e67e22", "#3498db", "#2ecc71"];

/** Camadas leves para demo em sala (arranque rápido, mapa fluido). */
export const CAMADAS_APRESENTACAO = {
  risco: false, foco: false, emodnet: false, navios: true, rota: true, sectores: true,
  bases: true, corredor: true, clusters: true, iom: false, apreensoes: false, desembarques: false,
  incidentes: true,
};

export const CAMADAS_COMPLETO = {
  risco: false, foco: true, emodnet: true, navios: true, rota: true, sectores: true,
  bases: true, corredor: true, clusters: true, iom: true, apreensoes: true, desembarques: true,
  incidentes: true,
};
