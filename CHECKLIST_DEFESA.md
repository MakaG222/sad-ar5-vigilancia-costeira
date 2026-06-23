# Checklist pré-defesa — SAD AR5

Use esta lista no dia da apresentação ou na véspera.

## Ambiente

- [ ] Python 3.10+ e Node 18+ instalados **ou** Docker Desktop
- [ ] Repositório clonado: `git clone https://github.com/MakaG222/sad-ar5-vigilancia-costeira.git`
- [ ] Branch/tag actual: `v1.0-defesa` (ou `main` actualizado)

## Opção A — Docker (recomendado)

```bash
cd sad-ar5-vigilancia-costeira/plataforma
./start-docker.sh
```

- [ ] Browser abre em http://localhost:8080
- [ ] Health: http://localhost:8080/api/health → `"status": "ok"`

## Instalação e testes automáticos (local)

```bash
cd sad-ar5-vigilancia-costeira/plataforma
./setup-mac.sh          # ou setup-win.ps1 no Windows
cd api && source .venv/bin/activate
python smoke_test.py    # esperado: TUDO OK — 24 verificações
pytest tests/ -q        # esperado: todos passam
```

- [ ] Smoke test: **24/24 OK**
- [ ] Pytest: **0 falhas**

## Arranque local (sem Docker)

```bash
cd plataforma
./start-mac.sh          # ou start-win.ps1
```

- [ ] Browser abre em http://localhost:5173
- [ ] API responde em http://127.0.0.1:8080/api/estado

## Verificação visual (barra de estado)

- [ ] **Alto risco:** 274
- [ ] **Frota:** 9/9
- [ ] **Ganho:** 2,13×
- [ ] **Demo AIS** (ou AIS real se tiver chave)
- [ ] Base de lançamento: **— MCLP automático —** (por omissão)

## Demo operacional (~5 min)

Seguir [`plataforma/APRESENTACAO.md`](plataforma/APRESENTACAO.md):

1. [ ] Sortie desde **Portimão** → rota no mapa + toast de qualidade
2. [ ] **Plano 24 h** (MCLP automático) → sectores Norte **e** Sul (Portimão nos sectores 4–6)
3. [ ] **Sim. spoofing** → alerta em tempo real
4. [ ] Separador **Camadas** → apreensões ou EMODnet (opcional)
5. [ ] **Exportar** plano de missão (opcional)

## Modo offline (opcional)

- [ ] Desligar Wi-Fi → plataforma continua (grelha, rotas, clusters locais)
- [ ] Indicador de fallback visível se meteo/IPMA indisponíveis

## Paragem

```bash
./stop-docker.sh        # Docker
./stop-mac.sh           # ou stop-win.ps1 (local)
```

## Se algo falhar

| Problema | Acção |
|----------|-------|
| Porta ocupada | `./stop-docker.sh` ou `./stop-mac.sh` e voltar a arrancar |
| API lenta no 1.º arranque | Docker: até 150 s; local: até 90 s; ver logs |
| Docker não arranca | `docker compose logs -f` — verificar CBC / memória |
| Métricas erradas | Confirmar `resultados/validacao.json` presente |
| Rotas sem Portimão no plano 24 h | Base deve estar vazia (MCLP automático), não só Porto |
