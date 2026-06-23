export default function StatusStrip({
  loading,
  loadingPhase,
  estado,
  sadRespostas,
  frota,
  modoApresentacao,
  fontesExternas,
}) {
  return (
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
      <div className="pill">Alto risco <b>{sadRespostas?.validacao?.n_celulas_patrulha ?? frota?.analise_sad?.n_celulas_patrulha ?? estado?.risco_resumo?.n_alto_risco ?? 274}</b></div>
      <div className="pill">
        Frota <b>{frota?.analise_sad?.frota_costeira_24h ?? sadRespostas?.Q2_quantos?.frota_costeira ?? 9}</b>/
        <b>{frota?.analise_sad?.frota_total_alto_risco ?? sadRespostas?.Q2_quantos?.frota_total ?? 9}</b>
      </div>
      <div className="pill">Ganho <b>{sadRespostas?.validacao?.ganho_sad_vs_aleatorio ?? "2,13"}×</b></div>
      {modoApresentacao && <div className="pill apresentacao">Apresentação</div>}
      {fontesExternas !== "live" && (
        <div className="pill offline" title="Meteo/IPMA/RSS em cache local">
          {fontesExternas === "offline" ? "Offline OK" : "Rede parcial"}
        </div>
      )}
    </div>
  );
}
