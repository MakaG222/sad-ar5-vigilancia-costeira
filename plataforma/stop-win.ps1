# Para API e frontend iniciados por start-win.ps1
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Run = Join-Path $Root ".run"

function Stop-PidFile($file, $name) {
    if (-not (Test-Path $file)) { return }
    $savedPid = Get-Content $file -ErrorAction SilentlyContinue
    if ($savedPid) {
        $proc = Get-Process -Id $savedPid -ErrorAction SilentlyContinue
        if ($proc) {
            Stop-Process -Id $savedPid -Force -ErrorAction SilentlyContinue
            Write-Host "    $name parado (PID $savedPid)"
        }
    }
    Remove-Item $file -Force -ErrorAction SilentlyContinue
}

function Stop-Port($port) {
    $stopped = $false
    if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) {
        try {
            $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
            foreach ($c in $conns) {
                if ($c.OwningProcess) {
                    Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue
                    Write-Host "    Libertar porta $port (PID $($c.OwningProcess))"
                    $stopped = $true
                }
            }
        } catch { }
    }
    if (-not $stopped) {
        # Fallback sem módulo NetTCPIP (alguns Windows)
        $lines = netstat -ano | Select-String ":$port\s+.*LISTENING"
        foreach ($line in $lines) {
            if ($line -match '\s+(\d+)\s*$') {
                $procId = $matches[1]
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Host "    Libertar porta $port (PID $procId)"
            }
        }
    }
}

Stop-PidFile (Join-Path $Run "api.pid") "API"
Stop-PidFile (Join-Path $Run "web.pid") "Web"
foreach ($port in @(8080, 5173)) { Stop-Port $port }

Write-Host "==> Servicos parados."
