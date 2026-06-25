# Instalação única da plataforma SAD AR5 no Windows.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Api = Join-Path $Root "api"
$Web = Join-Path $Root "web"
$Repo = Split-Path -Parent $Root

Write-Host "==> SAD AR5 - setup Windows"
Write-Host "    Pasta: $Root"
Write-Host ""

# Desbloquear scripts descarregados da Internet (ZIP)
Get-ChildItem $Root -Filter "*.ps1" | ForEach-Object {
    Unblock-File -LiteralPath $_.FullName -ErrorAction SilentlyContinue
}

function Find-PythonExe {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $v = & py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($v) { return @{ Cmd = "py"; VenvArgs = @("-3", "-m", "venv"); PipArgs = @("-3", "-m", "pip") } }
    }
    foreach ($c in @("python", "python3")) {
        if (Get-Command $c -ErrorAction SilentlyContinue) {
            return @{ Cmd = $c; VenvArgs = @("-m", "venv"); PipArgs = @("-m", "pip") }
        }
    }
    return $null
}

$py = Find-PythonExe
if (-not $py) {
    Write-Host "ERRO: Python 3.10+ nao encontrado."
    Write-Host "      Instale em https://www.python.org/downloads/"
    Write-Host "      Marque 'Add python.exe to PATH' e reinicie o PowerShell."
    exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: Node.js nao encontrado. Instale em https://nodejs.org/"
    exit 1
}

Write-Host "Python: $($py.Cmd) | Node $(node -v) | npm $(npm -v)"
Write-Host ""

# Verificar dados necessários
$need = @(
    (Join-Path $Repo "dados\fontes\apreensoes_droga_PT.xlsx"),
    (Join-Path $Repo "resultados\validacao.json")
)
foreach ($f in $need) {
    if (-not (Test-Path $f)) {
        Write-Host "ERRO: Ficheiro em falta: $f"
        Write-Host "      Descarregue o ZIP completo da release v1.0-final (nao use so a pasta plataforma)."
        exit 1
    }
}

Write-Host "==> API (venv + dependencias Python)"
Set-Location $Api
if (-not (Test-Path ".venv")) {
    & $py.Cmd @($py.VenvArgs + ".venv")
}
$pip = Join-Path $Api ".venv\Scripts\pip.exe"
$python = Join-Path $Api ".venv\Scripts\python.exe"
& $python -m pip install --upgrade pip -q
& $pip install -r requirements.txt
Write-Host "    OK: .venv pronto"
Write-Host ""

Write-Host "==> Frontend (npm)"
Set-Location $Web
npm install
Write-Host "    OK: node_modules pronto"
Write-Host ""

$EnvEx = Join-Path $Root ".env.example"
$Env = Join-Path $Root ".env"
if (-not (Test-Path $Env) -and (Test-Path $EnvEx)) {
    Copy-Item $EnvEx $Env
    Write-Host "==> Criado .env (edite AISSTREAM_API_KEY se tiver chave AIS)"
}

Write-Host "==> Setup concluido."
Write-Host ""
Write-Host "Arranque (PowerShell nesta pasta):"
Write-Host "  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass"
Write-Host "  .\start-win.ps1"
Write-Host ""
Write-Host "Ou faca duplo-clique em INICIAR.bat"
Write-Host ""
