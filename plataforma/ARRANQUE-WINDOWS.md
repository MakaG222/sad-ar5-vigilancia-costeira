# Arranque no Windows — guia passo a passo

Os erros que aparecem no **Prompt de Comandos (CMD)** são normais se:

1. **Git não está instalado** — `'git' is not recognized`
2. Está a usar **CMD** em vez de **PowerShell** — `Set-ExecutionPolicy` e `.\setup-win.ps1` só funcionam no PowerShell
3. A pasta do projeto **ainda não foi descarregada** — `cd sad-ar5-vigilancia-costeira` falha

---

## Opção A — Sem Git (mais simples)

1. Abra no browser:  
   https://github.com/MakaG222/sad-ar5-vigilancia-costeira/releases/tag/v1.0-final

2. Descarregue **`sad-ar5-v1.0-final.zip`**

3. Clique com o botão direito no ZIP → **Extrair tudo** → por exemplo para  
   `C:\Users\Utilizador\Downloads\sad-ar5-vigilancia-costeira`

4. Continue na **Opção B** ou **Opção C** abaixo (a partir do passo «Abrir PowerShell»).

---

## Opção B — Com Git instalado

1. Instale Git: https://git-scm.com/download/win  
   (durante a instalação, marque **«Git from the command line and also from 3rd-party software»**)

2. Feche e reabra o terminal.

3. No **PowerShell** (não CMD):

```powershell
cd $HOME\Downloads
git clone https://github.com/MakaG222/sad-ar5-vigilancia-costeira.git
cd sad-ar5-vigilancia-costeira\plataforma
```

---

## Abrir o PowerShell (obrigatório para os scripts `.ps1`)

- Tecla **Windows**, escreva **PowerShell**, Enter  
  **ou**
- Botão direito no menu Iniciar → **Terminal (Admin)** / **Windows PowerShell**

Confirme que o prompt mostra algo como `PS C:\Users\...>` — **não** `C:\Users\...>`.

---

## Opção C — Docker (recomendado se tiver Docker Desktop)

Não precisa de Python nem Node no PC — só Docker.

1. Instale [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Abra **PowerShell** na pasta `plataforma`:

```powershell
cd C:\Users\Utilizador\Downloads\sad-ar5-vigilancia-costeira\plataforma
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-docker.sh
```

Se `.\start-docker.sh` não funcionar no Windows, use:

```powershell
docker compose up --build -d
```

→ Abra **http://localhost:8080**

---

## Opção D — Python + Node (desenvolvimento)

**Pré-requisitos:** Python 3.10+ e Node.js 18+  
- Python: https://www.python.org/downloads/ — marque **«Add python.exe to PATH»**  
- Node: https://nodejs.org/

Na pasta `plataforma`, em **PowerShell**:

```powershell
cd C:\Users\Utilizador\Downloads\sad-ar5-vigilancia-costeira\plataforma
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup-win.ps1
.\start-win.ps1
```

→ Browser em **http://localhost:5173** (interface)  
→ API em **http://127.0.0.1:8080/docs**

Parar:

```powershell
.\stop-win.ps1
```

---

## Resolução de problemas

| Mensagem | Causa | Solução |
|----------|-------|---------|
| `'git' is not recognized` | Git não instalado | Opção A (ZIP) ou instalar Git |
| `Set-ExecutionPolicy` não reconhecido | Está no CMD | Abrir **PowerShell** |
| `setup-win.ps1` não reconhecido | Pasta errada ou CMD | `cd` até `...\plataforma` no PowerShell |
| `python` não encontrado | Python não no PATH | Reinstalar Python com «Add to PATH» |
| Porta 8080 ocupada | Serviço anterior | `.\stop-win.ps1` e voltar a arrancar |

---

## Verificação rápida

```powershell
cd C:\Users\Utilizador\Downloads\sad-ar5-vigilancia-costeira\plataforma\api
.\.venv\Scripts\Activate.ps1
python smoke_test.py
```

Deve terminar com **28/28 OK**.
