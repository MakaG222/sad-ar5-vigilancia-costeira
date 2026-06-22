#!/usr/bin/env bash
# Para API e frontend iniciados por start-mac.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
RUN="$ROOT/.run"

stop_pid_file() {
  local file="$1" name="$2"
  [[ -f "$file" ]] || return 0
  local pid
  pid="$(cat "$file")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    sleep 0.3
    kill -9 "$pid" 2>/dev/null || true
    echo "    $name parado (PID $pid)"
  fi
  rm -f "$file"
}

stop_pid_file "$RUN/api.pid" "API"
stop_pid_file "$RUN/web.pid" "Web"

if command -v lsof >/dev/null 2>&1; then
  for port in 8080 5173; do
    pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
    if [[ -n "$pids" ]]; then
      echo "    Libertar porta $port"
      kill $pids 2>/dev/null || true
      sleep 0.3
      kill -9 $pids 2>/dev/null || true
    fi
  done
fi

echo "==> Serviços parados."
