export default function MapLegend({
  ESCALA_RISCO,
  LEGENDA_FORCAS,
  COR_FORCA,
  COR_EMODNET,
  tipoPatrulha,
  modo,
  sectoresRotas,
  CORES_SECTOR_24H,
}) {
  return (
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
  );
}
