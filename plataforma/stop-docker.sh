#!/usr/bin/env bash
set -euo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"
docker compose down
echo "==> Contentor SAD AR5 parado."
