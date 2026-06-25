# Arranque no Windows — guia passo a passo

Este guia corrige os erros mais comuns (`git is not recognized`, `Set-ExecutionPolicy` não funciona, scripts `.ps1` não encontrados, **API não responde**).

---

## Forma mais simples (recomendada)

1. Descarregue o ZIP completo da [release v1.0-final](https://github.com/MakaG222/sad-ar5-vigilancia-costeira/releases/tag/v1.0-final)
2. Extraia a pasta (deve conter `plataforma\`, `dados\`, `resultados\`, `src\`)
3. Abra a pasta `plataforma`
4. **Duplo-clique em `INICIAR.bat`**

Na primeira vez o setup demora alguns minutos (Python + npm). Depois abre o browser em http://localhost:5173

---

## Erros frequentes e causa

| Mensagem | O que significa |
|----------|-----------------|
| `'git' is not recognized` | Git não está instalado — use o **ZIP** em vez de clone |
| `'Set-ExecutionPolicy' is not recognized` | Está no **CMD** em vez do **PowerShell** |
| `'.\setup-win.ps1' is not recognized` | Pasta errada **ou** está no CMD |
| `RedirectStandardOutput and RedirectStandardError are same` | Script antigo — atualize para a versão mais recente |
| `API não respondeu em 180s` | 1.º arranque lento ou dados em falta — ver `diagnostico-win.ps1` |
| `Ficheiro em falta: apreensoes_droga_PT.xlsx` | ZIP incompleto — não copie só a pasta `plataforma` |
| Interface abre mas mapa vazio | API ainda a carregar grelha — aguarde 1–2 min e F5 |

> **Importante:** os scripts `.ps1` só funcionam no **PowerShell** (`PS C:\...>`), não no Prompt de Comandos (`C:\...>`).

---

## O que vai precisar

| Ferramenta | Para quê | Como instalar |
|------------|----------|---------------|
| **PowerShell** | Executar scripts de setup | Tecla Windows → escrever *PowerShell* → Enter |
| **Python 3.10+** | API (backend) | [python.org](https://www.python.org/downloads/) — marque **Add python.exe to PATH** |
| **Node.js 18+** | Interface web | [nodejs.org](https://nodejs.org/) |
| **Git** (opcional) | Clonar repositório | [git-scm.com](https://git-scm.com/download/win) |
| **Docker Desktop** (opcional) | Arranque sem Python/Node | [docker.com](https://www.docker.com/products/docker-desktop/) |

---

## Passo 1 — Obter o código

### Opção A — ZIP (sem Git, mais simples)

1. Abra no browser:  
   https://github.com/MakaG222/sad-ar5-vigilancia-costeira/releases/tag/v1.0-final

2. Descarregue **`sad-ar5-v1.0-final.zip`**

3. Clique direito → **Extrair tudo** → por exemplo:  
   `C:\Users\Utilizador\Downloads\sad-ar5-vigilancia-costeira`

### Opção B — Git

```powershell
cd $HOME\Downloads
git clone https://github.com/MakaG222/sad-ar5-vigilancia-costeira.git
```

---

## Passo 2 — Abrir o PowerShell na pasta certa

1. Tecla **Windows** → escreva **PowerShell** → Enter  
2. Confirme que o prompt mostra `PS C:\...>` (não `C:\...>`)  
3. Navegue até à pasta `plataforma`:

```powershell
cd C:\Users\Utilizador\Downloads\sad-ar5-vigilancia-costeira\plataforma
```

(Ajuste o caminho se extraiu noutro sítio.)

---

## Passo 3 — Escolher modo de arranque

### Opção 1 — Docker (recomendado se tiver Docker Desktop)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-docker.ps1
```

Ou manualmente: `docker compose up --build -d`

→ **http://localhost:8080**

Parar: `docker compose down`

### Opção 2 — Nativo (Python + Node)

**Primeira vez:**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup-win.ps1
```

O script cria `.venv` em `api\`, instala dependências Python e `npm install` no frontend.

**Cada utilização:**

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-win.ps1
```

→ Interface: **http://localhost:5173**  
→ API: **http://127.0.0.1:8080/docs**

Parar: `.\stop-win.ps1`

---

## Passo 4 — Verificar

```powershell
cd C:\Users\Utilizador\Downloads\sad-ar5-vigilancia-costeira\plataforma\api
.\.venv\Scripts\Activate.ps1
python smoke_test.py
```

Deve terminar com **28/28 OK**.

---

## Resolução de problemas

| Sintoma | Solução |
|---------|---------|
| `python` não encontrado | Reinstalar Python com «Add to PATH»; ou usar `py -3` (launcher Windows) |
| `npm` não encontrado | Instalar Node.js; reiniciar PowerShell |
| Porta 8080 ocupada | `.\stop-win.ps1` e voltar a arrancar |
| Erro de execução de scripts | `Set-ExecutionPolicy -Scope Process Bypass` no **PowerShell** |
| Interface abre mas mapa vazio | Aguardar grelha (1–2 min) ou ver http://127.0.0.1:8080/api/health |
| Erro desconhecido | `.\diagnostico-win.ps1` e enviar o output à equipa |

---

## Estrutura

```
plataforma\
├── api\           ← FastAPI (porta 8080)
├── web\           ← React/Vite (porta 5173)
├── INICIAR.bat    ← Duplo-clique para arrancar (mais fácil)
├── setup-win.ps1  ← Instalação (1.ª vez)
├── start-win.ps1  ← Arranque
├── stop-win.ps1   ← Paragem
├── start-docker.ps1
└── diagnostico-win.ps1  ← Se algo falhar
```

A API usa os dados em `..\src\`, `..\dados\` e `..\resultados\` — a plataforma funciona sem reexecutar o notebook.

---

## Notebook de análise (opcional)

```powershell
cd C:\Users\Utilizador\Downloads\sad-ar5-vigilancia-costeira
pip install -r requirements.txt jupyter
jupyter notebook notebooks\notebook_final.ipynb
```
