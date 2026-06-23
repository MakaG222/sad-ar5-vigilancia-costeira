# Plataforma operacional SAD AR5

Interface web quasi-tempo-real: meteo, AIS, mapa de risco, rotas de patrulha, plano 24 h, frota e alertas.

> O relatório académico (Word/PDF) **não** está neste repositório — ver [README](../README.md#relatório-académico).

**Repositório:** https://github.com/MakaG222/sad-ar5-vigilancia-costeira

---

## Escolher o modo de arranque

| Modo | Quando usar | Guia |
|------|-------------|------|
| **Docker** | Demonstração rápida, sem instalar Python/Node | [abaixo](#docker-recomendado) |
| **macOS nativo** | Desenvolvimento no Mac | [ARRANQUE-MACOS.md](ARRANQUE-MACOS.md) |
| **Windows nativo** | Desenvolvimento no PC | [ARRANQUE-WINDOWS.md](ARRANQUE-WINDOWS.md) |

---

## Docker (recomendado)

Funciona igual em macOS e Windows (com Docker Desktop).

```bash
cd plataforma
chmod +x start-docker.sh stop-docker.sh   # macOS/Linux
./start-docker.sh
```

Windows (PowerShell):

```powershell
cd plataforma
docker compose up --build -d
```

→ **http://localhost:8080** · Parar: `./stop-docker.sh` ou `docker compose down`

---

## macOS — resumo

**Primeira vez:**

```bash
chmod +x setup-mac.sh start-mac.sh stop-mac.sh
./setup-mac.sh
```

**Arranque:**

```bash
./start-mac.sh
```

→ http://localhost:5173 · Parar: `./stop-mac.sh`

Passo a passo completo: **[ARRANQUE-MACOS.md](ARRANQUE-MACOS.md)**

---

## Windows — resumo

Abra **PowerShell** (não o Prompt de Comandos `cmd`).

**Sem Git:** descarregue o [ZIP da release](https://github.com/MakaG222/sad-ar5-vigilancia-costeira/releases/tag/v1.0-final).

**Primeira vez:**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup-win.ps1
```

**Arranque:**

```powershell
.\start-win.ps1
```

→ http://localhost:5173 · Parar: `.\stop-win.ps1`

Passo a passo completo: **[ARRANQUE-WINDOWS.md](ARRANQUE-WINDOWS.md)**

---

## Verificação

```bash
cd api
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
python smoke_test.py               # 28/28 OK
```

---

## URLs

| Endereço | Descrição |
|----------|-----------|
| http://localhost:8080 | Interface + API (Docker) |
| http://localhost:5173 | Interface (desenvolvimento local) |
| http://127.0.0.1:8080/docs | API Swagger |
| http://127.0.0.1:8080/api/health | Health check |

---

## Capturas para o README

Com a API a correr em `http://127.0.0.1:8080`:

```bash
cd web
node scripts/capturar-docs.mjs
```

Gera PNG em `plataforma/docs/` (1440×900).

---

## Funcionalidades

- Mapa costeiro com camadas (risco, EMODnet, apreensões, IOM, clusters)
- Rotas: sortie, plano 24 h (6 sectores), despacho reactivo
- Painel Ciência: backtest, baseline, sensibilidade AHP
- Meteo live, avisos IPMA, RSS, AIS (ou modo demo)
- Exportação de plano de missão (GeoJSON/CSV)

Ver também [`APRESENTACAO.md`](APRESENTACAO.md) e [`../notebooks/analise_sad_ar5.ipynb`](../notebooks/analise_sad_ar5.ipynb).
