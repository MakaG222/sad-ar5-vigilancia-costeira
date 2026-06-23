import L from "leaflet";
import { COR_FORCA, ESCALA_RISCO } from "../constants.js";

export function isBaseMclp(nome, mclpList) {
  if (!nome || !mclpList?.length) return false;
  const n = nome.toLowerCase();
  return mclpList.some((m) => {
    const chave = m.split("(")[0].trim().toLowerCase();
    return n.includes(chave) || chave.includes(n.split("—")[0].trim().toLowerCase());
  });
}

export function iconBase(forca, activo = false, mclp = false) {
  const cor = COR_FORCA[forca] || "#95a5a6";
  const b = mclp ? "3px solid #f1c40f" : activo ? "3px solid #fff" : "1px solid #222";
  const sz = mclp ? 18 : 14;
  return L.divIcon({
    className: "",
    html: `<div style="background:${cor};width:${sz}px;height:${sz}px;border-radius:3px;border:${b};box-shadow:0 0 ${mclp ? 6 : 4}px #000"></div>`,
    iconSize: [sz, sz], iconAnchor: [sz / 2, sz / 2],
  });
}

export function corCondicao(c) {
  if (c === "critica") return "#e74c3c";
  if (c === "limitada") return "#e67e22";
  if (c === "moderada") return "#f1c40f";
  return "#2ecc71";
}

export function ventoDaBase(nomeBase, meteoLista) {
  if (!nomeBase || !meteoLista?.length) return null;
  const m = meteoLista.find(
    (mb) => mb.base === nomeBase || nomeBase.includes(mb.base?.slice(0, 8)) || mb.base?.includes(nomeBase.slice(0, 8)),
  );
  return m?.vento_ms ?? null;
}

export function corRisco(r) {
  for (const faixa of ESCALA_RISCO) {
    if (r >= faixa.min) return faixa.cor;
  }
  return "#3498db";
}

export function rotuloRisco(r) {
  for (const faixa of ESCALA_RISCO) {
    if (r >= faixa.min) return faixa.rotulo;
  }
  return ESCALA_RISCO[ESCALA_RISCO.length - 1].rotulo;
}
