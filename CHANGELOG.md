# Changelog — SAD AR5 Plataforma

## [1.3.0] — 2026-06-23

### Adicionado
- Painel **Ciência** na UI: backtest temporal, comparador SAD vs aleatório vs uniforme, sliders AHP
- Endpoints `/api/ciencia/*` e recálculo de risco com pesos alternativos (`src/risco.aplicar_pesos`)
- Testes E2E Playwright, testes de alertas e validação científica
- `FICHEIROS.md` — guia da estrutura do repositório
- Rate limiting nas rotas de patrulha (`slowapi`), CORS configurável
- Git LFS para rasters `.tif`, script `regenerar_intensidades.py`

### Alterado
- Cobertura mínima de testes: 50%
- Refactor frontend: `PainelCiencia`, `hooks/useToast`

## [1.2.0] — 2026-06-23

### Adicionado
- Modo demo determinístico (`DEMO_DETERMINISTICO=1`) com navios fixos em `resultados/demo_navios.json`
- Refactor frontend: `constants.js`, `api/client.js`, `utils/mapUtils.js`, componentes `StatusStrip`, `MapLegend`, `MapControls`
- `scripts/verificar_integridade.py` e `scripts/gerar_manifest.py` para checksums JSON
- CI: `ruff` lint + cobertura `pytest`
- `dados/README.md` com origem e licenças dos dados

### Alterado
- Endpoint `/api/health` inclui `demo_deterministico`

## [1.1.0] — 2026-06-23

### Adicionado
- Docker Compose (`./start-docker.sh` → http://localhost:8080)
- Endpoint `/api/health`
- Job CI para build da imagem Docker

## [1.0.0] — 2026-06-23 — defesa CT302

### Adicionado
- CI GitHub Actions (smoke + pytest + build Vite)
- Testes unitários (MCLP, métricas, validação de rotas)
- `ARCHITECTURE.md`, `CHECKLIST_DEFESA.md`, `LICENSE`
- Screenshot e métricas canónicas alinhadas (274, 2,13×, 9 AR5)
- Tag `v1.0-defesa`
