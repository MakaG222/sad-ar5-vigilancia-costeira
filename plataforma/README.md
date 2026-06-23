# Plataforma operacional SAD AR5

Interface web quasi-tempo-real: meteo, AIS, mapa de risco, rotas de patrulha, plano 24 h, frota e alertas.

**Repositório:** https://github.com/MakaG222/sad-ar5-vigilancia-costeira

---

## Docker (recomendado)

```bash
chmod +x start-docker.sh stop-docker.sh
./start-docker.sh
```

→ http://localhost:8080 · Parar: `./stop-docker.sh`

```bash
chmod +x setup-mac.sh start-mac.sh stop-mac.sh
./setup-mac.sh
./start-mac.sh
```

→ http://localhost:5173 · Parar: `./stop-mac.sh`

---

## Windows

PowerShell na pasta `plataforma`:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup-win.ps1
.\start-win.ps1
```

→ http://localhost:5173 · Parar: `.\stop-win.ps1`

---

## Manual (macOS ou Windows)

**API** — `plataforma/api`:

```bash
python -m venv .venv
# macOS: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

**Web** — `plataforma/web`:

```bash
npm install
npm run dev
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

## Funcionalidades

- Mapa costeiro com camadas (risco, EMODnet, apreensões, IOM, clusters)
- Rotas: sortie, plano 24 h (6 sectores), despacho reactivo
- Cenários operacionais pré-configurados
- Simulação spoofing/incidente em ponto aleatório no mar
- Meteo live, avisos IPMA, RSS, AIS (ou modo demo)
- Exportação de plano de missão (GeoJSON/CSV)

Ver também [`APRESENTACAO.md`](APRESENTACAO.md) (roteiro de demo) e [`../README.md`](../README.md) (estrutura do repo e smoke test).
