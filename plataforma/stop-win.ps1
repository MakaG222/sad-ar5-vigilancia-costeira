# Para API e frontend iniciados por start-win.ps1
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Run = Join-Path $Root ".run"

function Stop-PidFile($file, $name) {
    if (-not (Test-Path $file)) { return }
    $pid = Get-Content $file -ErrorAction SilentlyContinue
    if ($pid) {
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
            Write-Host "    $name parado (PID $pid)"
        }
    }
    Remove-Item $file -Force -ErrorAction SilentlyContinue
}

Stop-PidFile (Join-Path $Run "api.pid") "API"
Stop-PidFile (Join-Path $Run "web.pid") "Web"

foreach ($port in @(8080, 5173)) {
    $conns = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    foreach ($c in $conns) {
        if ($c.OwningProcess) {
            Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
            Write-Host "    Libertar porta $port"
        }
    }
}

Write-Host "==> Serviços parados."
