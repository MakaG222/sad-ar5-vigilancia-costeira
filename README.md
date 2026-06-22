# SAD AR5 — Plataforma operacional

Protótipo web quasi-tempo-real para apoio à vigilância costeira com o UAV TEKEVER AR5:
mapa de risco, meteo, AIS, rotas de patrulha, plano 24 h, dimensionamento de frota e alertas.

**Repositório:** https://github.com/MakaG222/sad-ar5-vigilancia-costeira

---

## Estrutura do repositório

O projeto divide-se em quatro zonas: a **plataforma** (API + interface), o **núcleo geoespacial** (`src/`), os **dados** de entrada e os **resultados** pré-calculados que a API carrega em runtime.

```
sad-ar5-vigilancia-costeira/
│
├── plataforma/                 # Aplicação executável (arrancar daqui)
│   ├── api/                    # Backend FastAPI (porta 8080)
│   │   ├── main.py             # Ponto de entrada da API
│   │   ├── requirements.txt    # Dependências Python da API
│   │   ├── services/           # Módulos: risco, rotas, meteo, AIS, alertas, …
│   │   ├── worker.py           # Tarefas periódicas (meteo, AIS, RSS)
│   │   └── smoke_test.py       # Teste rápido dos endpoints
│   ├── web/                    # Frontend React + Vite (porta 5173)
│   │   ├── src/App.jsx         # Interface principal (mapa Leaflet)
│   │   └── package.json        # Dependências Node.js
│   ├── setup-mac.sh            # Instalação única — macOS
│   ├── setup-win.ps1           # Instalação única — Windows
│   ├── start-mac.sh            # Arranque — macOS
│   ├── start-win.ps1           # Arranque — Windows
│   ├── stop-mac.sh             # Paragem — macOS
│   ├── stop-win.ps1            # Paragem — Windows
│   ├── .env.example            # Variáveis opcionais (copiar para .env)
│   ├── APRESENTACAO.md         # Roteiro de demonstração (~5 min)
│   └── README.md               # Detalhe adicional da plataforma
│
├── src/                        # Núcleo analítico (importado pela API)
│   ├── config.py               # Parâmetros AR5, bases, pesos, grelha
│   ├── geo.py                  # Operações geoespaciais
│   ├── risco.py                # Índice multi-ameaça por célula
│   ├── otimizacao.py           # MCLP e dimensionamento de frota
│   ├── rotas_maritimas.py      # Cálculo de rotas marítimas
│   ├── corredores_operacionais.py
│   └── apreensoes_mapa.py      # Camada de apreensões
│
├── dados/
│   ├── fontes/                 # Dados brutos (EMODnet, IOM, imigração, …)
│   └── processados/
│       └── intensidades_reais.csv   # Grelha costeira processada (1 156 células)
│
├── resultados/                 # JSON pré-calculados consumidos pela API
│   ├── resultados.json         # Respostas Q1–Q3, sensibilidade, frota
│   ├── validacao.json          # Backtest, baseline, ganho 2,13×
│   ├── camadas_mapa.json       # Incidentes, apreensões, geometrias
│   └── ahp_pesos.json          # Pesos AHP das ameaças
│
├── requirements.txt            # Dependências Python do núcleo (src/)
└── README.md                   # Este ficheiro
```

**Fluxo em runtime:** o utilizador abre o frontend (`plataforma/web`); este comunica com a API (`plataforma/api`); a API importa módulos de `src/` e lê ficheiros de `dados/` e `resultados/`.

> O relatório académico (Word/PDF) **não** faz parte deste repositório.

---

## Pré-requisitos

| Ferramenta | macOS | Windows |
|------------|-------|---------|
| Python | 3.10+ (`brew install python`) | 3.10+ ([python.org](https://www.python.org/downloads/) — marcar *Add to PATH*) |
| Node.js | 18+ (`brew install node`) | 18+ ([nodejs.org](https://nodejs.org/)) |
| npm | Incluído com Node | Incluído com Node |

---

## Arranque — macOS

Abra o **Terminal**, clone o repositório (se ainda não o fez) e entre na pasta `plataforma`:

```bash
git clone https://github.com/MakaG222/sad-ar5-vigilancia-costeira.git
cd sad-ar5-vigilancia-costeira/plataforma
```

**1. Instalação** (só na primeira vez — cria o ambiente Python e instala pacotes npm):

```bash
chmod +x setup-mac.sh start-mac.sh stop-mac.sh
./setup-mac.sh
```

**2. Arranque** da aplicação (API + interface):

```bash
./start-mac.sh
```

O script abre automaticamente o browser em **http://localhost:5173**.  
Documentação interativa da API: **http://127.0.0.1:8080/docs**

**3. Paragem:**

```bash
./stop-mac.sh
```

Logs em `plataforma/.run/api.log` e `plataforma/.run/web.log`.

---

## Arranque — Windows

Abra o **PowerShell**, clone o repositório e entre na pasta `plataforma`:

```powershell
git clone https://github.com/MakaG222/sad-ar5-vigilancia-costeira.git
cd sad-ar5-vigilancia-costeira\plataforma
```

**1. Instalação** (só na primeira vez):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup-win.ps1
```

**2. Arranque** da aplicação:

```powershell
.\start-win.ps1
```

O browser abre em **http://localhost:5173**.  
API: **http://127.0.0.1:8080/docs**

**3. Paragem:**

```powershell
.\stop-win.ps1
```

Logs em `plataforma\.run\api.log` e `plataforma\.run\web.log`.

---

## URLs

| Endereço | Descrição |
|----------|-----------|
| http://localhost:5173 | Interface web (mapa, rotas, alertas) |
| http://127.0.0.1:8080/docs | API Swagger (endpoints REST) |
| http://127.0.0.1:8080/api/estado | Estado do sistema (health check) |

---

## Resolução de problemas

| Sintoma | Solução |
|---------|---------|
| Porta 8080 ou 5173 ocupada | Correr `./stop-mac.sh` ou `.\stop-win.ps1` e voltar a arrancar |
| `python3` / `node` não encontrado | Instalar pré-requisitos (tabela acima) |
| Erro na primeira execução | Voltar a correr `setup-mac.sh` ou `setup-win.ps1` |
| Meteo/AIS em modo demo | Normal sem ligação à Internet; a plataforma usa dados locais de fallback |

---

## Documentação adicional

- [`plataforma/README.md`](plataforma/README.md) — arranque manual (dois terminais) e lista de funcionalidades
- [`plataforma/APRESENTACAO.md`](plataforma/APRESENTACAO.md) — roteiro de demonstração (~5 min)
