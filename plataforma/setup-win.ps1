# Instalacao unica da plataforma SAD AR5 no Windows.
# Node.js e OPCIONAL se web\dist\ ja existir (modo producao).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Api = Join-Path $Root "api"
$Web = Join-Path $Root "web"
$Repo = Split-Path -Parent $Root
$DistIndex = Join-Path $Web "dist\index.html"

Write-Host "==> SAD AR5 - setup Windows"
Write-Host "    Pasta: $Root"
Write-Host ""

Get-ChildItem $Root -Filter "*.ps1" | ForEach-Object {
    Unblock-File -LiteralPath $_.FullName -ErrorAction SilentlyContinue
}

function Find-PythonExe {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $v = & py -3 -c "import sys; print(sys.version_info[0])" 2>$null
        if ($v -eq "3") { return @{ Cmd = "py"; VenvArgs = @("-3", "-m", "venv") } }
    }
    foreach ($c in @("python", "python3")) {
        if (Get-Command $c -ErrorAction SilentlyContinue) {
            return @{ Cmd = $c; VenvArgs = @("-m", "venv") }
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

$HasNode = [bool](Get-Command node -ErrorAction SilentlyContinue)
$HasDist = Test-Path $DistIndex

if (-not $HasNode -and -not $HasDist) {
    Write-Host "ERRO: Node.js nao encontrado e web\dist em falta."
    Write-Host "      Opcao A: git pull (dist incluido no repo) e volte a correr setup"
    Write-Host "      Opcao B: instale Node.js 18+ em https://nodejs.org/"
    Write-Host "      Opcao C: use Docker Desktop e .\start-docker.ps1"
    exit 1
}

if ($HasNode) {
    Write-Host "Python: $($py.Cmd) | Node $(node -v) | npm $(npm -v)"
} else {
    Write-Host "Python: $($py.Cmd) | Node: (nao instalado - modo producao com dist)"
}
Write-Host ""

$need = @(
    (Join-Path $Repo "dados\fontes\apreensoes_droga_PT.xlsx"),
    (Join-Path $Repo "resultados\validacao.json")
)
foreach ($f in $need) {
    if (-not (Test-Path $f)) {
        Write-Host "ERRO: Ficheiro em falta: $f"
        Write-Host "      Descarregue o ZIP completo (pastas dados, resultados, plataforma)."
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

if ($HasNode) {
    Write-Host "==> Frontend (npm - modo desenvolvimento)"
    Set-Location $Web
    npm install
    Write-Host "    OK: node_modules pronto"
} else {
    Write-Host "==> Frontend (modo producao)"
    Write-Host "    OK: web\dist incluido - Node.js nao necessario"
}
Write-Host ""

$EnvEx = Join-Path $Root ".env.example"
$Env = Join-Path $Root ".env"
if (-not (Test-Path $Env) -and (Test-Path $EnvEx)) {
    Copy-Item $EnvEx $Env
    Write-Host "==> Criado .env"
}

Write-Host "==> Setup concluido."
Write-Host ""
Write-Host "Arranque: duplo-clique em INICIAR.bat"
if ($HasNode) {
    Write-Host "         ou .\start-win.ps1  (API :8080 + Web :5173)"
} else {
    Write-Host "         ou .\start-win.ps1  (tudo em http://localhost:8080)"
}
Write-Host ""
