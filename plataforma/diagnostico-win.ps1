# Diagnóstico rápido — enviar output à equipa se a plataforma falhar.
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Api = Join-Path $Root "api"
$Repo = Split-Path -Parent $Root

Write-Host "=== SAD AR5 — diagnóstico Windows ==="
Write-Host "Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
Write-Host "Pasta: $Root"
Write-Host ""

Write-Host "--- Ferramentas ---"
foreach ($t in @("python", "python3", "py", "node", "npm", "docker")) {
    $ok = Get-Command $t -ErrorAction SilentlyContinue
    if ($ok) { Write-Host "  OK  $t" } else { Write-Host "  --  $t (ausente)" }
}

Write-Host ""
Write-Host "--- Ficheiros de dados ---"
@(
    "dados\fontes\apreensoes_droga_PT.xlsx",
    "resultados\validacao.json",
    "resultados\camadas_mapa.json"
) | ForEach-Object {
    $p = Join-Path $Repo $_
    if (Test-Path $p) { Write-Host "  OK  $_" } else { Write-Host "  FALTA  $_" }
}

Write-Host ""
Write-Host "--- Dependências ---"
if (Test-Path (Join-Path $Api ".venv")) { Write-Host "  OK  api\.venv" } else { Write-Host "  FALTA  api\.venv — corra setup-win.ps1" }
if (Test-Path (Join-Path $Root "web\node_modules")) { Write-Host "  OK  web\node_modules" } else { Write-Host "  FALTA  web\node_modules" }

Write-Host ""
Write-Host "--- Portas ---"
foreach ($port in @(8080, 5173)) {
    $inUse = netstat -ano | Select-String ":$port\s+.*LISTENING"
    if ($inUse) { Write-Host "  OCUPADA  $port" } else { Write-Host "  livre  $port" }
}

Write-Host ""
Write-Host "--- Teste import API ---"
$py = Join-Path $Api ".venv\Scripts\python.exe"
if (Test-Path $py) {
    Push-Location $Api
    & $py -c "import main; print('  OK  import main')" 2>&1
    Pop-Location
} else {
    Write-Host "  SKIP (sem venv)"
}

Write-Host ""
Write-Host "--- Logs recentes ---"
foreach ($log in @("api.err.log", "api.log", "web.err.log")) {
    $p = Join-Path $Root ".run\$log"
    if (Test-Path $p) {
        Write-Host ">> $log"
        Get-Content $p -Tail 8 -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "   $_" }
    }
}

Write-Host ""
Write-Host "=== Fim diagnóstico ==="
