# Arranca API (8080) + frontend (5173) no Windows.
# Nota: usar apenas ASCII nas strings (compativel com Windows PowerShell 5.1).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Api = Join-Path $Root "api"
$Web = Join-Path $Root "web"
$Run = Join-Path $Root ".run"
$ApiPort = if ($env:API_PORT) { $env:API_PORT } else { "8080" }
$WebPort = if ($env:WEB_PORT) { $env:WEB_PORT } else { "5173" }

function Write-LogTail($path, $lines = 20) {
    if (Test-Path $path) {
        Write-Host "--- ultimas linhas de $path ---"
        Get-Content $path -Tail $lines -ErrorAction SilentlyContinue | ForEach-Object { Write-Host $_ }
        Write-Host "--------------------------------"
    }
}

function Sec-Label([int]$n) {
    return "$n s"
}

function Wait-Http($url, $label, $maxSec = 180) {
    for ($i = 0; $i -lt $maxSec; $i++) {
        try {
            Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3 | Out-Null
            Write-Host "    $label OK"
            return $true
        } catch {
            if ($i % 10 -eq 9) {
                $sec = Sec-Label ($i + 1)
                Write-Host "    ... a esperar de $label ($sec)"
            }
            Start-Sleep -Seconds 1
        }
    }
    return $false
}

function Start-LoggedProcess($file, $argList, $wd, $outLog, $errLog) {
    # PowerShell nao permite redireccionar stdout e stderr para o MESMO ficheiro.
    return Start-Process -FilePath $file -ArgumentList $argList `
        -WorkingDirectory $wd `
        -RedirectStandardOutput $outLog `
        -RedirectStandardError $errLog `
        -PassThru -WindowStyle Hidden
}

New-Item -ItemType Directory -Force -Path $Run | Out-Null

if (-not (Test-Path (Join-Path $Api ".venv")) -or -not (Test-Path (Join-Path $Web "node_modules"))) {
    Write-Host "Dependencias em falta. A correr setup..."
    & (Join-Path $Root "setup-win.ps1")
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

Write-Host "==> SAD AR5 - arranque Windows"
Write-Host "    API  -> http://127.0.0.1:$ApiPort"
Write-Host "    Web  -> http://localhost:$WebPort"
Write-Host ""

$ApiLog = Join-Path $Run "api.log"
$ApiErr = Join-Path $Run "api.err.log"
$WebLog = Join-Path $Run "web.log"
$WebErr = Join-Path $Run "web.err.log"
"" | Set-Content $ApiLog
"" | Set-Content $ApiErr
"" | Set-Content $WebLog
"" | Set-Content $WebErr

$ApiPy = Join-Path $Api ".venv\Scripts\python.exe"
if (-not (Test-Path $ApiPy)) {
    Write-Host "ERRO: venv em falta. Corra: .\setup-win.ps1"
    exit 1
}

$ApiProc = Start-LoggedProcess $ApiPy @(
    "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", $ApiPort
) $Api $ApiLog $ApiErr
$ApiProc.Id | Set-Content (Join-Path $Run "api.pid")
Write-Host "    API PID $($ApiProc.Id) - logs $ApiLog"

if (-not (Wait-Http "http://127.0.0.1:$ApiPort/api/health" "API (health)" 180)) {
    Write-Host "ERRO: API nao respondeu em 180 s."
    Write-LogTail $ApiLog
    Write-LogTail $ApiErr
    Write-Host "Dica: corra .\diagnostico-win.ps1 para mais detalhes"
    exit 1
}

# Aquecimento da grelha (pode demorar no 1. arranque)
Write-Host "    A aquecer dados (grelha de risco)..."
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
if ($warm) {
    Write-Host "    Grelha pronta"
} else {
    Write-Host "    AVISO: grelha ainda a carregar - a interface pode demorar"
}

$ViteJs = Join-Path $Web "node_modules\vite\bin\vite.js"
if (-not (Test-Path $ViteJs)) {
    Write-Host "ERRO: Vite nao instalado. Corra: .\setup-win.ps1"
    exit 1
}

$node = (Get-Command node).Source
$WebProc = Start-LoggedProcess $node @(
    $ViteJs, "--host", "127.0.0.1", "--port", $WebPort
) $Web $WebLog $WebErr
$WebProc.Id | Set-Content (Join-Path $Run "web.pid")
Write-Host "    Web PID $($WebProc.Id) - logs $WebLog"

if (-not (Wait-Http "http://127.0.0.1:$WebPort" "Web" 60)) {
    Write-Host "ERRO: Frontend nao respondeu."
    Write-LogTail $WebLog
    Write-LogTail $WebErr
    exit 1
}

Write-Host ""
Write-Host "=========================================="
Write-Host "  Plataforma pronta"
Write-Host "  Abrir: http://localhost:$WebPort"
Write-Host "  Docs API: http://127.0.0.1:$ApiPort/docs"
Write-Host ""
Write-Host "  Parar:  .\stop-win.ps1"
Write-Host "  Logs:   .run\api.log  .run\web.log"
Write-Host "=========================================="
Write-Host ""

Start-Process "http://localhost:$WebPort"
Write-Host "Servicos em segundo plano. Use .\stop-win.ps1 para parar."
