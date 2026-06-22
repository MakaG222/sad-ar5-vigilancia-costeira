# Arranca API (8080) + frontend (5173) no Windows.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Api = Join-Path $Root "api"
$Web = Join-Path $Root "web"
$Run = Join-Path $Root ".run"
$ApiPort = if ($env:API_PORT) { $env:API_PORT } else { "8080" }
$WebPort = if ($env:WEB_PORT) { $env:WEB_PORT } else { "5173" }

New-Item -ItemType Directory -Force -Path $Run | Out-Null

if (-not (Test-Path (Join-Path $Api ".venv")) -or -not (Test-Path (Join-Path $Web "node_modules"))) {
    Write-Host "Dependências em falta. A correr setup..."
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

Write-Host "==> SAD AR5 — arranque Windows"
Write-Host "    API  → http://127.0.0.1:$ApiPort"
Write-Host "    Web  → http://localhost:$WebPort"
Write-Host ""

$ApiLog = Join-Path $Run "api.log"
$WebLog = Join-Path $Run "web.log"
"" | Set-Content $ApiLog
"" | Set-Content $WebLog

$ApiStart = Join-Path $Api ".venv\Scripts\python.exe"
$ApiProc = Start-Process -FilePath $ApiStart -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", $ApiPort -WorkingDirectory $Api -RedirectStandardOutput $ApiLog -RedirectStandardError $ApiLog -PassThru -WindowStyle Hidden
$ApiProc.Id | Set-Content (Join-Path $Run "api.pid")
Write-Host "    API PID $($ApiProc.Id) · log $ApiLog"

$max = 60
$ok = $false
for ($i = 0; $i -lt $max; $i++) {
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:$ApiPort/api/estado" -UseBasicParsing -TimeoutSec 2 | Out-Null
        Write-Host "    API OK"
        $ok = $true
        break
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ok) {
    Write-Host "ERRO: API não respondeu. Ver $ApiLog"
    exit 1
}

$Vite = Join-Path $Web "node_modules\.bin\vite.cmd"
$WebProc = Start-Process -FilePath $Vite -ArgumentList "--host", "127.0.0.1", "--port", $WebPort -WorkingDirectory $Web -RedirectStandardOutput $WebLog -RedirectStandardError $WebLog -PassThru -WindowStyle Hidden
$WebProc.Id | Set-Content (Join-Path $Run "web.pid")
Write-Host "    Web PID $($WebProc.Id) · log $WebLog"

$ok = $false
for ($i = 0; $i -lt $max; $i++) {
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:$WebPort" -UseBasicParsing -TimeoutSec 2 | Out-Null
        Write-Host "    Web OK"
        $ok = $true
        break
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $ok) {
    Write-Host "ERRO: Web não respondeu. Ver $WebLog"
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

Write-Host "Serviços a correr em segundo plano. Use .\stop-win.ps1 para parar."
