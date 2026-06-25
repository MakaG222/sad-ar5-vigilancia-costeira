# Docker Compose no Windows (interface + API em http://localhost:8080)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERRO: Docker nao encontrado. Instale Docker Desktop:"
    Write-Host "      https://www.docker.com/products/docker-desktop/"
    exit 1
}

Write-Host "==> SAD AR5 - Docker (build + arranque)"
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "A aguardar API..."
for ($i = 0; $i -lt 180; $i++) {
    try {
        Invoke-WebRequest -Uri "http://127.0.0.1:8080/api/health" -UseBasicParsing -TimeoutSec 3 | Out-Null
        Write-Host "Pronto: http://localhost:8080"
        Start-Process "http://localhost:8080"
        exit 0
    } catch { Start-Sleep -Seconds 2 }
}
Write-Host "AVISO: API ainda a iniciar. Tente http://localhost:8080 dentro de 1-2 min."
Write-Host "Logs: docker compose logs -f"
