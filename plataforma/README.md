# Plataforma operacional SAD AR5

Protótipo web quasi-tempo-real: meteo, AIS, risco SAD, rotas optimizadas, frota dinâmica e alertas push.

## Arranque no macOS (recomendado)

**Requisitos:** macOS com [Homebrew](https://brew.sh) — `python3` e `node` (npm).

```bash
cd plataforma
chmod +x setup-mac.sh start-mac.sh stop-mac.sh   # só na 1.ª vez
./setup-mac.sh    # instalação única (venv + npm)
./start-mac.sh    # arranca API + web e abre o browser
```

| URL | Serviço |
|-----|---------|
| http://localhost:5173 | Interface web |
| http://127.0.0.1:8080/docs | API (Swagger) |

Parar tudo:

```bash
./stop-mac.sh
```

Logs em `.run/api.log` e `.run/web.log`.

### AIS tempo real (opcional)

Edite `plataforma/.env` (criado no setup):

```bash
AISSTREAM_API_KEY=sua_chave   # https://aisstream.io
```

Reinicie com `./stop-mac.sh && ./start-mac.sh`.

---

## Arranque manual (dois terminais)

Útil para ver erros em directo no Terminal.

**Terminal 1 — API (porta 8080)**

```bash
cd plataforma/api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

**Terminal 2 — Frontend (porta 5173)**

```bash
cd plataforma/web
npm install
npm run dev
```

Abrir http://localhost:5173

### Build produção (uma só porta)

```bash
cd plataforma/web && npm run build
cd ../api && source .venv/bin/activate && uvicorn main:app --port 8080
# http://localhost:8080
```

---

## Resolução de problemas (Mac)

| Problema | Solução |
|----------|---------|
| `python3: command not found` | `brew install python` |
| `node: command not found` | `brew install node` |
| Porta 8080/5173 ocupada | `./stop-mac.sh` ou `lsof -ti tcp:8080 \| xargs kill` |
| Mapa vazio / sem dados | Confirmar que a API está a correr (`curl http://127.0.0.1:8080/api/estado`) |
| Permissão negada nos scripts | `chmod +x setup-mac.sh start-mac.sh stop-mac.sh` |

---

## Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| Meteo | Open-Meteo actual + previsão 12 h nas 12 bases |
| IPMA | Avisos meteorológicos via API IPMA |
| RSS | Feeds IPMA, Marinha, Diário de Notícias (incidentes) |
| AIS | AISStream (se chave) ou tráfego simulado PT |
| Risco SAD | Camada de células de risco no mapa (droga, pesca, etc.) |
| Rotas | Sortie TSP (OR-Tools), plano 24 h com sectores, despacho reactivo |
| Frota | Recálculo com vento actual + previsto |
| Alertas | Meteo, IPMA, RSS, spoofing, zona risco, cobertura, incidentes |
| WebSocket | Push de alertas em tempo real (`/api/ws/alertas`) |
| UI | Camadas mapa, toast alertas, registo manual incidentes, clique reactivo |

## Evolução por semanas

- **Semana 1** ✅ MVP: API + UI base (meteo, AIS, rotas greedy, alertas)
- **Semana 2** ✅ RSS, camada risco SAD, WebSocket push, OR-Tools TSP
- **Semana 3** ✅ IPMA avisos, registo manual incidentes na UI, sectores 24 h, toggles camadas

## Endpoints principais

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/estado` | Resumo operacional |
| GET | `/api/risco/celulas` | Células de risco para mapa |
| GET | `/api/ipma/avisos` | Avisos IPMA |
| GET | `/api/rss/noticias` | Notícias RSS |
| POST | `/api/incidentes` | Registo manual |
| POST | `/api/rotas/sortie` | Rota sortie OR-Tools |
| POST | `/api/rotas/plano24h` | Plano 24 h + sectores |
| POST | `/api/rotas/reativo` | Despacho reactivo |
| WS | `/api/ws/alertas` | Alertas live |

## Teste de fumo (antes da defesa)

Valida que a API arranca e que todos os endpoints + rotas respondem sem erros:

```bash
cd plataforma/api
source .venv/bin/activate
python smoke_test.py
```

Sai com código 0 e imprime a qualidade de cada rota (Fase 2). Útil correr antes da apresentação.

## Demo

- Botões **Sim. spoofing** / **Sim. incidente** injectam alertas de demonstração
- **Clique p/ reactivo** + clique no mapa calcula rota de despacho
- Worker actualiza meteo/AIS/risco/IPMA/RSS a cada ~2 min
