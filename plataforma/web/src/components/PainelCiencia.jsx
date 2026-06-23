import React, { useEffect, useState } from "react";
import { get } from "../api/client.js";

const AMEACAS = [
  ["droga", "Droga"],
  ["pesca", "Pesca INN"],
  ["poluicao", "Poluição"],
  ["imigracao", "Imigração"],
];

function BarraComparacao({ estrategias }) {
  if (!estrategias?.length) return null;
  const max = Math.max(...estrategias.map((e) => e.captura_pct), 1);
  return (
    <div className="baseline-bars">
      {estrategias.map((e) => (
        <div key={e.nome} className="baseline-row">
          <span className="baseline-label">{e.nome}</span>
          <div className="baseline-track">
            <div
              className={`baseline-fill ${e.nome.includes("SAD") ? "sad" : ""}`}
              style={{ width: `${(e.captura_pct / max) * 100}%` }}
            />
          </div>
          <span className="baseline-val">{e.captura_pct}%</span>
        </div>
      ))}
    </div>
  );
}

export default function PainelCiencia() {
  const [backtest, setBacktest] = useState(null);
  const [baseline, setBaseline] = useState(null);
  const [ahp, setAhp] = useState(null);
  const [pesos, setPesos] = useState({ droga: 0.35, pesca: 0.25, poluicao: 0.2, imigracao: 0.2 });
  const [sens, setSens] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [bt, bl, ah] = await Promise.all([
          get("/ciencia/backtest"),
          get("/ciencia/baseline"),
          get("/ciencia/ahp"),
        ]);
        setBacktest(bt);
        setBaseline(bl);
        setAhp(ah);
        if (ah?.pesos_adotados) setPesos(ah.pesos_adotados);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  useEffect(() => {
    if (loading) return undefined;
    const t = setTimeout(() => {
      const q = new URLSearchParams(
        Object.fromEntries(Object.entries(pesos).map(([k, v]) => [k, String(v)])),
      ).toString();
      get(`/ciencia/sensibilidade-pesos?${q}`).then(setSens).catch(() => {});
    }, 250);
    return () => clearTimeout(t);
  }, [pesos, loading]);

  if (loading) return <div className="card compact">A carregar validação científica…</div>;

  return (
    <div className="ciencia-panel">
      <h2>Validação científica</h2>

      {backtest && (
        <div className="card compact">
          <b>Backtest temporal</b>
          <div className="stat">
            Corte {backtest.ano_corte} · holdout n={backtest.n_holdout} · acerto limiar{" "}
            {(100 * (backtest.taxa_acerto_limiar || 0)).toFixed(1)}% · ganho rel.{" "}
            {backtest.ganho_relativo_limiar?.toFixed(1)}×
          </div>
          <div className="stat muted">{backtest.nota}</div>
        </div>
      )}

      {baseline && (
        <div className="card compact">
          <b>Baseline patrulha (N={baseline.n_celulas_patrulha} células)</b>
          <BarraComparacao estrategias={baseline.estrategias} />
          <div className="stat">
            Ganho SAD vs aleatório: <b>{baseline.ganho_sad_vs_aleatorio}×</b>
            {baseline.ganho_ic95_bootstrap && (
              <> (IC95 {baseline.ganho_ic95_bootstrap[0]}–{baseline.ganho_ic95_bootstrap[1]})</>
            )}
          </div>
          <div className="stat">Gini risco: {baseline.indice_gini_risco}</div>
        </div>
      )}

      {ahp && (
        <div className="card compact">
          <b>Sensibilidade AHP — pesos das ameaças</b>
          <div className="stat">
            CR={ahp.consistency_ratio} · {ahp.consistente ? "consistente" : "rever"}
          </div>
          {AMEACAS.map(([k, lbl]) => (
            <label key={k} className="peso-slider">
              <span>{lbl}</span>
              <input
                type="range"
                min="0.05"
                max="0.6"
                step="0.01"
                value={pesos[k]}
                onChange={(e) => setPesos((p) => ({ ...p, [k]: parseFloat(e.target.value) }))}
              />
              <span>{(pesos[k] * 100).toFixed(0)}%</span>
            </label>
          ))}
          {sens && (
            <div className="stat">
              Alto risco (limiar 0,5): <b>{sens.n_alto_risco}</b> células
              {sens.delta_celulas !== 0 && (
                <span className={sens.delta_celulas > 0 ? "up" : "down"}>
                  {" "}({sens.delta_celulas > 0 ? "+" : ""}{sens.delta_celulas} vs referência)
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
