# SAD AR5 — Plataforma Operacional

Protótipo web para planear e demonstrar vigilância costeira de Portugal Continental com o UAV **TEKEVER AR5**: mapa de risco, rotas de patrulha, plano 24 h, meteo, AIS e alertas em tempo quasi-real.

**CT302 — Sistemas de Apoio à Decisão** · Grupo VI · Escola Naval, 2026

---

## Requisitos

| Software | Versão mínima | macOS | Windows |
|----------|---------------|-------|---------|
| Python | 3.10+ | `brew install python` ou [python.org](https://www.python.org/downloads/) | [python.org](https://www.python.org/downloads/) — marcar **Add to PATH** |
| Node.js | 18+ | `brew install node` ou [nodejs.org](https://nodejs.org/) | [nodejs.org](https://nodejs.org/) |

---

## Instalação e arranque

### macOS

```bash
git clone https://github.com/MakaG222/sad-ar5-vigilancia-costeira.git
cd sad-ar5-vigilancia-costeira/plataforma

chmod +x setup-mac.sh start-mac.sh stop-mac.sh   # só na 1.ª vez
./setup-mac.sh    # instala dependências (uma vez)
./start-mac.sh    # arranca API + interface web
```

Abrir **http://localhost:5173**

Parar: `./stop-mac.sh`

### Windows

Abra **PowerShell** na pasta `plataforma`:

```powershell
git clone https://github.com/MakaG222/sad-ar5-vigilancia-costeira.git
cd sad-ar5-vigilancia-costeira\plataforma

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   # só nesta sessão, se necessário
.\setup-win.ps1    # instala dependências (uma vez)
.\start-win.ps1    # arranca API + interface web
```

Abrir **http://localhost:5173**

Parar: `.\stop-win.ps1`

> Se o Windows bloquear scripts PowerShell, use a política acima apenas na sessão actual ou execute os passos **manuais** abaixo.

---

## Arranque manual (dois terminais)

Útil para ver erros em directo. Funciona em **macOS** e **Windows**.

**Terminal 1 — API (porta 8080)**

```bash
cd plataforma/api
python3 -m venv .venv          # Windows: python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8080
```

**Terminal 2 — Interface web (porta 5173)**

```bash
cd plataforma/web
npm install
npm run dev
```

Abrir **http://localhost:5173**

| URL | Serviço |
|-----|---------|
| http://localhost:5173 | Interface web (mapa, rotas, alertas) |
| http://127.0.0.1:8080/docs | API (documentação Swagger) |

---

## Utilização

| Funcionalidade | Como usar |
|----------------|-----------|
| **Plano 24 h** | Separador Operação → modo «Plano 24 h» → **Calcular rota**. Mostra 6 sectores N→S com rotas desde **Porto (Sá Carneiro)** e **Portimão**. |
| **Horas de patrulha** | Campo **t_on patrulha (h)** — ajustável até ao limite da autonomia AR5 (16 h − reserva). Recomendado: 4 h por sector. |
| **Cenários** | Botões de cenário (rotina 24 h, droga Algarve, vento forte, etc.) aplicam tipo de patrulha e parâmetros. |
| **Camadas do mapa** | Separador Camadas — risco, EMODnet, apreensões, IOM, clusters k-means. Legenda com escala de cores de risco. |
| **Spoofing / incidente** | Botões «Sim. spoofing» e «Sim. incidente» — evento aleatório no mar ao longo da costa. |
| **Despacho reactivo** | Modo «Reactivo» + clique no mapa calcula rota para o alvo. |
| **Exportar missão** | Calcular rota → **Exportar** (GeoJSON/CSV). |

O **modo apresentação** está activo por defeito (arranque mais rápido). Desactive em Camadas para ver todas as camadas.

---

## AIS em tempo real (opcional)

Copie `plataforma/.env.example` para `plataforma/.env` e adicione uma chave [AISstream](https://aisstream.io):

```
AISSTREAM_API_KEY=sua_chave
```

Reinicie a plataforma. Sem chave, o sistema usa **navios simulados** em células marítimas — adequado para demonstração.

---

## Resolução de problemas

| Problema | macOS | Windows |
|----------|-------|---------|
| Python não encontrado | `brew install python` | Reinstalar Python com «Add to PATH» |
| Node não encontrado | `brew install node` | Reinstalar Node.js LTS |
| Porta 8080/5173 ocupada | `./stop-mac.sh` | `.\stop-win.ps1` |
| Mapa vazio | Confirmar API: `curl http://127.0.0.1:8080/api/estado` | Abrir http://127.0.0.1:8080/api/estado no browser |
| Script bloqueado | `chmod +x *.sh` | `Set-ExecutionPolicy -Scope Process Bypass` |

Logs automáticos: `plataforma/.run/api.log` e `plataforma/.run/web.log`

---

## Estrutura do repositório (plataforma)

```
plataforma/
├── api/          # Backend FastAPI (rotas, meteo, AIS, alertas)
├── web/          # Frontend React + Leaflet
├── setup-mac.sh  # Instalação macOS
├── start-mac.sh  # Arranque macOS
├── stop-mac.sh   # Parar macOS
├── setup-win.ps1 # Instalação Windows
├── start-win.ps1 # Arranque Windows
└── stop-win.ps1  # Parar Windows
```

Os dados analíticos (grelha de risco, validação) estão em `dados/` e `resultados/` e são carregados automaticamente pela API.

---

## Licença e autoria

Trabalho académico CT302 — Grupo VI, Escola Naval, Alfeite.

CAD M Santos Neto · CAD EN-AEL Canotilho Castro · CAD M Silva Guerreiro · CAD M Ribeiro Gaspar
