# Instalação única da plataforma SAD AR5 no Windows.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Api = Join-Path $Root "api"
$Web = Join-Path $Root "web"

Write-Host "==> SAD AR5 — setup Windows"
Write-Host "    Pasta: $Root"
Write-Host ""

function Need-Cmd($name, $hint) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Host "ERRO: '$name' não encontrado."
        Write-Host "      $hint"
        exit 1
    }
}

Need-Cmd "python" "Instale Python 3.10+ em https://www.python.org/downloads/ (marque 'Add to PATH')."
Need-Cmd "node" "Instale Node.js 18+ em https://nodejs.org/"
Need-Cmd "npm" "Incluído com Node.js."

Write-Host "Python $(python --version) · Node $(node -v) · npm $(npm -v)"
Write-Host ""

Write-Host "==> API (venv + dependências Python)"
Set-Location $Api
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
& ".\.venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip -q
pip install -r requirements.txt
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

Write-Host "==> Setup concluído."
Write-Host ""
Write-Host "Arranque:"
Write-Host "  cd `"$Root`""
Write-Host "  .\start-win.ps1"
Write-Host ""
