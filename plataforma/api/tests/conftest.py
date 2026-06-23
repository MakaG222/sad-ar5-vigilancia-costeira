"""Configuração partilhada dos testes da API."""
from __future__ import annotations

import os
import sys

_API = os.path.join(os.path.dirname(__file__), "..")
_SRC = os.path.join(_API, "..", "..", "src")

for path in (_API, _SRC):
    if path not in sys.path:
        sys.path.insert(0, path)
