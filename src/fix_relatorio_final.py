"""Correcções finais após reestruturação 18→11."""
from __future__ import annotations
import re
from pathlib import Path

MD = Path(__file__).resolve().parent.parent / "relatorio" / "Relatorio_SAD_AR5.md"

NEW_INDEX = """## Índice

1. Introdução
2. Enquadramento teórico e revisão de literatura
3. Caracterização dos dados e do meio operacional
4. Pipeline de *data mining* (preparação, *clustering*, classificação, risco difuso)
5. Otimização: localização de bases, frota e sensibilidade
6. Painel geoespacial interativo e plataforma operacional
7. Validação (estudo de caso e quantitativa)
8. Discussão, limitações e recomendação
9. Conclusão e trabalho futuro
10. Referências
11. Anexos (A — Figuras · B — Tabelas · C — Reprodução · D — Mapa SIGA)

---
"""


def move_sensitivity_section(text: str) -> str:
    m54 = re.search(
        r"\n### 5\.4 Análise de sensibilidade\n.*?\n---\n\n(?=## 7\. Validação)",
        text,
        re.DOTALL,
    )
    if not m54:
        return text
    block = m54.group(0).rstrip()
    block = block[: -len("\n---\n\n")]  # remove trailing separator
    text = text[: m54.start()] + "\n---\n\n## 7. Validação" + text[m54.end() :]
    anchor = "| Área total de alto risco | 18 996 | Porto + Portimão | 3 | ≈ 9 AR5 |\n\n---"
    if anchor not in text:
        raise ValueError("Âncora para inserir 5.4 não encontrada")
    return text.replace(anchor, "| Área total de alto risco | 18 996 | Porto + Portimão | 3 | ≈ 9 AR5 |\n\n" + block + "\n\n---", 1)


def main():
    text = MD.read_text(encoding="utf-8")

    # Índice
    text = re.sub(r"## Índice\n.*?(?=\n---\n\n## 1\. Introdução)", NEW_INDEX.rstrip() + "\n", text, count=1, flags=re.DOTALL)

    # Mover 5.4 para dentro da secção 5
    text = move_sensitivity_section(text)

    replacements = [
        ("documentada na Secção 4.4 e no", "documentada na Secção 6 e no"),
        ("às quais a Secção 4.3.4\nresponde de forma explícita:", "às quais a Secção 8\nresponde de forma explícita:"),
        (
            "A Secção 2 enquadra teoricamente o trabalho. A Secção 3 caracteriza os dados e o meio\n"
            "operacional. As Secção 4 descrevem o pipeline de análise — preparação e redução,\n"
            "*clustering*, classificação e agregação difusa. A Secção 4.3 formula e resolve a\n"
            "otimização; a Secção 4.4 apresenta o painel interativo; a Secção 4.3.4 estuda a sensibilidade.\n"
            "As Secção 4.5 validam o sistema (estudo de caso e backtesting quantitativo). A\n"
            "Secção 4.3 discute os resultados; as Secções 8 e 9 tratam limitações, recomendação e\n"
            "conclusão.",
            "A Secção 2 enquadra teoricamente o trabalho. A Secção 3 caracteriza os dados e o meio\n"
            "operacional. A Secção 4 descreve o pipeline de *data mining* (preparação, *clustering*,\n"
            "classificação e risco difuso). A Secção 5 formula e resolve a otimização e a sensibilidade;\n"
            "a Secção 6 apresenta o painel interativo e a plataforma operacional. A Secção 7 valida o\n"
            "sistema (estudo de caso e backtesting). As Secções 8 e 9 tratam discussão, limitações,\n"
            "recomendação e conclusão.",
        ),
        ("otimização (Secção 4.3).", "otimização (Secção 5)."),
        ("Sec. 3, 11;", "Sec. 3, 7.1;"),
        ("(Sec. 11) funcionam", "(Sec. 7.1) funcionam"),
        ("(Secção 4.5.1) e métricas", "(Secção 7.1) e métricas"),
        ("(Secção 4.3.2, limitação II)", "(Secção 8.2, limitação II)"),
        ("Dimensionamento persistente (Secção 4.3.2;", "Dimensionamento persistente (Secção 5.2;"),
        ("MCLP (Secção 4.3.3)", "MCLP (Secção 5.3)"),
        ("de sensibilidade da Secção 4.3.4 demonstra", "de sensibilidade da Secção 5.4 demonstra"),
        ("estudo de caso (Secção 4.5.1) e por\nbacktesting temporal (Secção 4.5)",
         "estudo de caso (Secção 7.1) e por\nbacktesting temporal (Secção 7.2)"),
        ("o dimensionamento de frota da Secção 4.3 endereça.", "o dimensionamento de frota da Secção 5 endereça."),
        ("mapa de risco (Secção 4.3).", "mapa de risco (Secção 4.3)."),  # correct
    ]
    for old, new in replacements:
        if old not in text:
            print("SKIP:", old[:50])
        text = text.replace(old, new)

  # Meteo table: add 5.4
    text = text.replace("| Sec. 5; `fator_vento` |", "| Sec. 5, 5.4; `fator_vento` |")

    MD.write_text(text, encoding="utf-8")
    print("Corrigido:", MD)


if __name__ == "__main__":
    main()
