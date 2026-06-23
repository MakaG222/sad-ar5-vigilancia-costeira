#!/usr/bin/env python3
"""Verifica integridade dos artefactos JSON canónicos do SAD."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "resultados" / "manifest.json"

CANON = {
    "validacao.json": {
        "baseline_patrulha.n_celulas_patrulha": 274,
        "baseline_patrulha.ganho_sad_vs_aleatorio": 2.13,
        "resposta_objetivo.Q2_quantos.frota_total": 9,
    },
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_nested(data: dict, dotted: str):
    cur = data
    for part in dotted.split("."):
        cur = cur[part]
    return cur


def main() -> int:
    erros: list[str] = []
    ok = 0

    for fname, checks in CANON.items():
        path = ROOT / "resultados" / fname
        if not path.is_file():
            erros.append(f"Ficheiro em falta: {path}")
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for key, esperado in checks.items():
            try:
                val = get_nested(data, key)
            except KeyError:
                erros.append(f"{fname}: chave {key} em falta")
                continue
            if val != esperado:
                erros.append(f"{fname}: {key}={val!r} (esperado {esperado!r})")
            else:
                ok += 1
                print(f"  ok  {fname} · {key} = {val}")

    demo = ROOT / "resultados" / "demo_navios.json"
    if demo.is_file():
        with open(demo, encoding="utf-8") as f:
            d = json.load(f)
        n = d.get("n", len(d.get("navios", [])))
        if n < 35:
            erros.append(f"demo_navios.json: apenas {n} navios")
        else:
            ok += 1
            print(f"  ok  demo_navios.json · n={n}")
    else:
        erros.append("demo_navios.json em falta")

    if MANIFEST.is_file():
        with open(MANIFEST, encoding="utf-8") as f:
            manifest = json.load(f)
        for rel, esperado in manifest.get("sha256", {}).items():
            path = ROOT / rel
            if not path.is_file():
                erros.append(f"manifest: ficheiro em falta {rel}")
                continue
            actual = sha256(path)
            if actual != esperado:
                erros.append(f"manifest: checksum {rel} diferente")
            else:
                ok += 1
                print(f"  ok  sha256 {rel}")

    print()
    if erros:
        print(f"FALHOU: {len(erros)} problema(s), {ok} OK")
        for e in erros:
            print(f"  x  {e}")
        return 1
    print(f"TUDO OK — {ok} verificações de integridade.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
