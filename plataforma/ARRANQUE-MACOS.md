# Arranque no macOS — guia passo a passo

Este guia explica como obter o código, instalar dependências e abrir a plataforma SAD AR5 no Mac.

---

## O que vai precisar

| Ferramenta | Para quê | Como instalar |
|------------|----------|---------------|
| **Terminal** | Correr comandos | Já incluído no macOS |
| **Python 3.10+** | API (backend) | [python.org](https://www.python.org/downloads/) ou `brew install python@3.12` |
| **Node.js 18+** | Interface web | [nodejs.org](https://nodejs.org/) ou `brew install node` |
| **Docker** (opcional) | Arranque sem instalar Python/Node | [Docker Desktop](https://www.docker.com/products/docker-desktop/) |
| **Git** (opcional) | Clonar o repositório | `brew install git` ou Xcode Command Line Tools |

---

## Passo 1 — Obter o código

### Opção A — Git (recomendado para desenvolvimento)

```bash
cd ~/Downloads
git clone https://github.com/MakaG222/sad-ar5-vigilancia-costeira.git
cd sad-ar5-vigilancia-costeira
```

### Opção B — ZIP (sem Git)

1. Abra: https://github.com/MakaG222/sad-ar5-vigilancia-costeira/releases/tag/v1.0-final  
2. Descarregue `sad-ar5-v1.0-final.zip`  
3. Duplo clique para extrair → pasta `sad-ar5-vigilancia-costeira`

---

## Passo 2 — Escolher modo de arranque

### Opção 1 — Docker (mais simples)

Não precisa de Python nem Node no Mac — só Docker Desktop.

```bash
cd ~/Downloads/sad-ar5-vigilancia-costeira/plataforma
chmod +x start-docker.sh stop-docker.sh
./start-docker.sh
```

→ Abra **http://localhost:8080** no Safari ou Chrome.

Parar:

```bash
./stop-docker.sh
```

### Opção 2 — Nativo (desenvolvimento)

Instala Python e Node uma vez; depois arranca mais rápido.

**Primeira vez (setup):**

```bash
cd ~/Downloads/sad-ar5-vigilancia-costeira/plataforma
chmod +x setup-mac.sh start-mac.sh stop-mac.sh
./setup-mac.sh
```

O script:
1. Cria ambiente virtual Python em `plataforma/api/.venv`
2. Instala dependências da API (`pip install -r requirements.txt`)
3. Instala pacotes npm do frontend (`npm install`)
4. Copia `.env.example` → `.env` (opcional)

**Cada vez que quiser usar a plataforma:**

```bash
cd ~/Downloads/sad-ar5-vigilancia-costeira/plataforma
./start-mac.sh
```

→ Interface: **http://localhost:5173**  
→ API (documentação): **http://127.0.0.1:8080/docs**

Parar:

```bash
./stop-mac.sh
```

---

## Passo 3 — Verificar que funciona

```bash
cd ~/Downloads/sad-ar5-vigilancia-costeira/plataforma/api
source .venv/bin/activate
python smoke_test.py
```

Deve mostrar **28/28 OK**.

---

## Resolução de problemas

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| `python3: command not found` | Python não instalado | `brew install python@3.12` |
| `node: command not found` | Node não instalado | `brew install node` |
| `Permission denied` nos scripts | Falta permissão de execução | `chmod +x setup-mac.sh start-mac.sh` |
| Porta 8080 ou 5173 ocupada | Sessão anterior aberta | `./stop-mac.sh` ou `./stop-docker.sh` |
| Mapa vazio / sem dados | API não arrancou | Verificar terminal da API; testar `/api/health` |
| Meteo/AIS em modo demo | Normal sem Internet | Ver [Limitações](../README.md#limitações) |

---

## Estrutura durante o arranque

```
plataforma/
├── api/          ← FastAPI (porta 8080)
├── web/          ← React/Vite (porta 5173)
├── start-mac.sh  ← Arranca API + frontend
└── start-docker.sh ← Tudo num contentor (porta 8080)
```

A API lê os dados analíticos em `../src/`, `../dados/` e `../resultados/` — não precisa de reexecutar o notebook para usar a plataforma.

---

## Notebook de análise (opcional)

Para reproduzir as figuras e métricas do relatório:

```bash
cd ~/Downloads/sad-ar5-vigilancia-costeira
pip install -r requirements.txt jupyter
jupyter notebook notebooks/analise_sad_ar5.ipynb
```
