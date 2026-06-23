# Guia dos ficheiros do repositório

Documentação da estrutura do projeto **SAD AR5 — Vigilância Costeira** (CT302, Escola Naval).  
O repositório contém a **plataforma operacional** e o **núcleo analítico**; o relatório académico (Word/PDF) não está versionado.

---

## Raiz

| Ficheiro / pasta | Descrição |
|------------------|-----------|
| `README.md` | Instalação, arranque (Docker / macOS / Windows) e visão geral |
| `CHANGELOG.md` | Histórico de versões da plataforma |
| `CHECKLIST_DEFESA.md` | Verificações antes da apresentação oral |
| `LICENSE` | Licença MIT do código |
| `FICHEIROS.md` | Este guia |
| `pyproject.toml` | Configuração de `ruff`, `pytest` e cobertura |
| `.github/workflows/ci.yml` | Integração contínua (lint, testes, build, Docker) |
| `requirements.txt` | Dependências Python do núcleo (`src/`) |
| `scripts/` | Utilitários de integridade e dados |

---

## `plataforma/` — aplicação executável

| Ficheiro / pasta | Descrição |
|------------------|-----------|
| `Dockerfile` | Imagem Docker (API + frontend compilado) |
| `docker-compose.yml` | Orquestração local com um comando |
| `start-docker.sh` / `stop-docker.sh` | Arranque e paragem em Docker |
| `setup-*.sh` / `start-*.sh` | Instalação e arranque nativos (macOS / Windows) |
| `.env.example` | Variáveis opcionais (AIS, demo fixa, CORS, portas) |
| `ARCHITECTURE.md` | Diagrama técnico, endpoints e fluxo de dados |
| `APRESENTACAO.md` | Roteiro de demonstração (~5 min) |
| `docs/screenshot.png` | Captura da interface para o README |

### `plataforma/api/` — backend FastAPI

| Ficheiro / pasta | Descrição |
|------------------|-----------|
| `main.py` | Endpoints REST, WebSocket, lifespan e servir frontend |
| `worker.py` | Ciclo periódico: meteo, AIS, IPMA, RSS |
| `store.py` | Estado em memória (navios, alertas, meteo) |
| `smoke_test.py` | Teste de fumo dos endpoints (pré-demo) |
| `services/` | Módulos de negócio (ver abaixo) |
| `tests/` | Testes unitários (`pytest`) |

**Serviços principais (`services/`):**

| Módulo | Função |
|--------|--------|
| `patrulha_costeira.py` | Rotas: sortie, plano 24 h, reactivo |
| `frota.py` | Dimensionamento AR5 e métricas SAD |
| `ciencia.py` | Backtest, baseline e sensibilidade AHP (API) |
| `validacao_rota.py` | Score de qualidade de rotas (0–100) |
| `ais.py` | AIS real ou simulado |
| `demo_mode.py` | Demo determinística para apresentações |
| `grelha_cache.py` | Cache da grelha de risco |
| `risco_mapa.py` | Células de risco para o mapa |

### `plataforma/web/` — frontend React

| Ficheiro / pasta | Descrição |
|------------------|-----------|
| `src/App.jsx` | Componente principal e estado da UI |
| `src/constants.js` | Constantes de mapa, cores e camadas |
| `src/api/client.js` | Cliente HTTP para a API |
| `src/utils/mapUtils.js` | Funções de mapa (ícones, escala de risco) |
| `src/components/` | Componentes reutilizáveis (legenda, ciência, …) |
| `src/hooks/` | Hooks React (`useToast`, …) |
| `e2e/` | Testes end-to-end (Playwright) |

---

## `src/` — núcleo analítico SAD

Módulos Python importados pela API (não são uma aplicação autónoma).

| Ficheiro | Descrição |
|----------|-----------|
| `config.py` | Parâmetros AR5, bases, pesos AHP, limiares |
| `geo.py` | Grelha marítima, costa, projeção |
| `risco.py` | Índice multi-ameaça por célula |
| `otimizacao.py` | MCLP, set cover, dimensionamento de frota |
| `rotas_maritimas.py` | Rotas respeitando máscara de oceano |
| `apreensoes_mapa.py` | Apreensões marítimas para o mapa |
| `geocode.py` | Geocodificação de concelhos (apreensões) |

---

## `dados/` — fontes de entrada

| Pasta / ficheiro | Descrição |
|------------------|-----------|
| `fontes/apreensoes_droga_PT.xlsx` | Apreensões UNODC/SICAD |
| `fontes/imigracao_pt_costa.csv` | Desembarques marítimos PT |
| `fontes/iom_missing_migrants.csv` | Incidentes IOM |
| `fontes/emodnet/*.tif` | Rasters EMODnet (pesca, carga, AIS) — Git LFS |
| `processados/intensidades_reais.csv` | Intensidades por ameaça (pré-calculadas) |
| `README.md` | Origem, licenças e regeneração |

---

## `resultados/` — artefactos pré-calculados

Consumidos pela API em runtime (não requerem reexecutar o pipeline completo).

| Ficheiro | Descrição |
|----------|-----------|
| `validacao.json` | Backtest, baseline patrulha, respostas Q1–Q3 |
| `resultados.json` | Respostas analíticas e sensibilidade |
| `ahp_pesos.json` | Matriz e pesos AHP das ameaças |
| `camadas_mapa.json` | Geometrias IOM, apreensões, metadados |
| `demo_navios.json` | Posições AIS fixas (modo demo) |
| `manifest.json` | Checksums SHA-256 (integridade) |
| `README.md` | Descrição dos artefactos e métricas de referência |

---

## `scripts/`

| Script | Descrição |
|--------|-----------|
| `verificar_integridade.py` | Valida métricas canónicas e checksums |
| `gerar_manifest.py` | Regenera `resultados/manifest.json` |
| `regenerar_intensidades.py` | Regenera `intensidades_reais.csv` (requer `rasterio`) |

---

## Variáveis de ambiente relevantes

| Variável | Efeito |
|----------|--------|
| `AISSTREAM_API_KEY` | AIS em tempo real (opcional) |
| `DEMO_DETERMINISTICO=1` | Navios e meteo fixos (recomendado na apresentação) |
| `CORS_ORIGINS` | Origens permitidas (por omissão `*`) |
| `API_PORT` | Porta da API (8080) |
