# Arranca plataforma SAD AR5 no Windows.
# Modo producao (sem Node): API + interface em http://localhost:8080
# Modo dev (com Node): API :8080 + Vite :5173
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Api = Join-Path $Root "api"
$Web = Join-Path $Root "web"
$Run = Join-Path $Root ".run"
$DistIndex = Join-Path $Web "dist\index.html"
$ApiPort = if ($env:API_PORT) { $env:API_PORT } else { "8080" }
$WebPort = if ($env:WEB_PORT) { $env:WEB_PORT } else { "5173" }

function Write-LogTail($path, $lines = 20) {
    if (Test-Path $path) {
        Write-Host "--- ultimas linhas de $path ---"
        Get-Content $path -Tail $lines -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
        Write-Host "--------------------------------"
    }
}

function Sec-Label([int]$n) { return "$n s" }

function Wait-Http($url, $label, $maxSec = 180) {
    for ($i = 0; $i -lt $maxSec; $i++) {
        try {
            Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3 | Out-Null
            Write-Host "    $label OK"
            return $true
        } catch {
            if ($i % 10 -eq 9) {
                $sec = Sec-Label ($i + 1)
                Write-Host "    ... a esperar $label ($sec)"
            }
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Start-LoggedProcess($file, $argList, $wd, $outLog, $errLog) {
    return Start-Process -FilePath $file -ArgumentList $argList `
        -WorkingDirectory $wd `
        -RedirectStandardOutput $outLog `
        -RedirectStandardError $errLog `
        -PassThru -WindowStyle Hidden
}

$HasNode = [bool](Get-Command node -ErrorAction SilentlyContinue)
$HasDist = Test-Path $DistIndex
$HasModules = Test-Path (Join-Path $Web "node_modules")
$ProdMode = $HasDist -and (-not $HasNode -or -not $HasModules)

New-Item -ItemType Directory -Force -Path $Run | Out-Null

$NeedSetup = (-not (Test-Path (Join-Path $Api ".venv")))
if ($ProdMode) {
    $NeedSetup = $NeedSetup -or (-not $HasDist)
} else {
    $NeedSetup = $NeedSetup -or (-not $HasModules)
}

if ($NeedSetup) {
    Write-Host "Dependencias em falta. A correr setup..."
    & (Join-Path $Root "setup-win.ps1")
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

& (Join-Path $Root "stop-win.ps1") 2>$null

$EnvFile = Join-Path $Root ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*([^#=]+)=(.*)$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
        }
    }
}

if ($ProdMode) {
    Write-Host "==> SAD AR5 - arranque Windows (modo producao)"
    Write-Host "    URL  -> http://localhost:$ApiPort"
} else {
    Write-Host "==> SAD AR5 - arranque Windows (modo desenvolvimento)"
    Write-Host "    API  -> http://127.0.0.1:$ApiPort"
    Write-Host "    Web  -> http://localhost:$WebPort"
}
Write-Host ""

$ApiLog = Join-Path $Run "api.log"
$ApiErr = Join-Path $Run "api.err.log"
$WebLog = Join-Path $Run "web.log"
$WebErr = Join-Path $Run "web.err.log"
"" | Set-Content $ApiLog
"" | Set-Content $ApiErr

$ApiPy = Join-Path $Api ".venv\Scripts\python.exe"
if (-not (Test-Path $ApiPy)) {
    Write-Host "ERRO: venv em falta. Corra: .\setup-win.ps1"
    exit 1
}

$ApiProc = Start-LoggedProcess $ApiPy @(
    "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", $ApiPort
) $Api $ApiLog $ApiErr
$ApiProc.Id | Set-Content (Join-Path $Run "api.pid")
Write-Host "    API PID $($ApiProc.Id)"

if (-not (Wait-Http "http://127.0.0.1:$ApiPort/api/health" "API" 180)) {
    Write-Host "ERRO: API nao respondeu."
    Write-LogTail $ApiLog
    Write-LogTail $ApiErr
    Write-Host "Corra: .\diagnostico-win.ps1"
    exit 1
}

Write-Host "    A aquecer grelha de risco..."
$warm = $false
for ($i = 0; $i -lt 120; $i++) {
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/api/health" -TimeoutSec 5
        if ($r.grelha_pronta) { $warm = $true; break }
    } catch { }
    if ($i % 15 -eq 14) {
        $sec = Sec-Label ($i + 1)
        Write-Host "    ... grelha ($sec)"
    }
    Start-Sleep -Seconds 1
}
if ($warm) { Write-Host "    Grelha pronta" } else { Write-Host "    AVISO: grelha ainda a carregar" }

if ($ProdMode) {
    $openUrl = "http://localhost:$ApiPort"
    Write-Host ""
    Write-Host "=========================================="
    Write-Host "  Plataforma pronta (sem Node.js)"
    Write-Host "  Abrir: $openUrl"
    Write-Host "  Parar: .\stop-win.ps1"
    Write-Host "=========================================="
    Start-Process $openUrl
    Write-Host "Servico API em segundo plano."
    exit 0
}

# --- Modo dev: Vite ---
"" | Set-Content $WebLog
"" | Set-Content $WebErr
$ViteJs = Join-Path $Web "node_modules\vite\bin\vite.js"
if (-not (Test-Path $ViteJs)) {
    Write-Host "ERRO: Vite em falta. Corra: .\setup-win.ps1"
    exit 1
}
$node = (Get-Command node).Source
$WebProc = Start-LoggedProcess $node @(
    $ViteJs, "--host", "127.0.0.1", "--port", $WebPort
) $Web $WebLog $WebErr
$WebProc.Id | Set-Content (Join-Path $Run "web.pid")
Write-Host "    Web PID $($WebProc.Id)"

if (-not (Wait-Http "http://127.0.0.1:$WebPort" "Web" 60)) {
    Write-Host "ERRO: Frontend nao respondeu."
    Write-LogTail $WebLog
    Write-LogTail $WebErr
    exit 1
}

$openUrl = "http://localhost:$WebPort"
Write-Host ""
Write-Host "=========================================="
Write-Host "  Plataforma pronta"
Write-Host "  Abrir: $openUrl"
Write-Host "  Parar: .\stop-win.ps1"
Write-Host "=========================================="
Start-Process $openUrl
Write-Host "Servicos em segundo plano."
