"""Reestrutura Relatorio_SAD_AR5.md: 18 → 11 secções (por blocos)."""
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

SEC_RE = re.compile(r"^## (\d+)\. (.+)$", re.MULTILINE)


def split_sections(text: str) -> tuple[str, dict[int, str]]:
    """Divide o corpo em prefixo + secções numeradas ## N."""
    m = SEC_RE.search(text)
    if not m:
        raise ValueError("Nenhuma secção ## N. encontrada")
    prefix = text[: m.start()]
    rest = text[m.start() :]
    parts = SEC_RE.split(rest)
    # parts: ['', '1', 'title', 'body', '2', 'title', 'body', ...]
    sections: dict[int, str] = {}
    i = 1
    while i < len(parts) - 2:
        num = int(parts[i])
        title = parts[i + 1].strip()
        body = parts[i + 2]
        sections[num] = f"## {num}. {title}\n{body}"
        i += 3
    if i < len(parts):
        # última secção sem título extra
        pass
    return prefix, sections


def renumber_headers(block: str, mapping: list[tuple[str, str]]) -> str:
    for old, new in mapping:
        block = block.replace(old, new, 1)
    return block


def build_section_4(s: dict[int, str]) -> str:
    b4 = s[4].replace(
        "## 4. Preparação e redução dos dados",
        "## 4. Pipeline de *data mining*\n\n"
        "As Secções 4.1 a 4.5 descrevem o pipeline analítico — preparação e redução, "
        "*clustering*, classificação e agregação difusa do risco — que alimenta a "
        "otimização (Secção 5).",
    )
    b5 = s[5].replace(
        "## 5. Modelação descritiva: segmentação espacial por *clustering*",
        "### 4.3 Modelação descritiva: segmentação espacial por *clustering*",
    )
    b6 = s[6].replace(
        "## 6. Modelação preditiva: deteção da natureza marítima das apreensões",
        "### 4.4 Modelação preditiva: deteção da natureza marítima das apreensões",
    )
    b6 = b6.replace("### 6.1 ", "#### 4.4.1 ")
    b6 = b6.replace("### 6.2 ", "#### 4.4.2 ")
    b6 = b6.replace("### 6.3 ", "#### 4.4.3 ")
    b7 = s[7].replace(
        "## 7. Agregação difusa do risco multi-ameaça",
        "### 4.5 Agregação difusa do risco multi-ameaça",
    )
    return b4 + "\n" + b5 + "\n" + b6 + "\n" + b7


def build_section_5(s: dict[int, str]) -> str:
    b8 = s[8].replace(
        "## 8. Otimização: localização de bases e dimensionamento da frota",
        "## 5. Otimização: localização de bases, dimensionamento da frota e sensibilidade",
    )
    b8 = b8.replace("### 8.1 ", "### 5.1 ")
    b8 = b8.replace("### 8.2 ", "### 5.2 ")
    b8 = b8.replace("### 8.3 ", "### 5.3 ")
    b10 = s[10].replace("## 10. Análise de sensibilidade", "### 5.4 Análise de sensibilidade")
    return b8 + "\n" + b10


def build_section_6(s: dict[int, str]) -> str:
    b = s[9].replace(
        "## 9. Painel geoespacial interativo e plataforma operacional",
        "## 6. Painel geoespacial interativo e plataforma operacional",
    )
    return b.replace("### 9.1 ", "### 6.1 ").replace("### 9.2 ", "### 6.2 ")


def build_section_7(s: dict[int, str]) -> str:
    b11 = s[11].replace(
        "## 11. Validação por estudo de caso",
        "### 7.1 Validação por estudo de caso",
    )
    b12 = s[12]
    # remover cabeçalho ## 12
    b12 = re.sub(
        r"^## 12\. Validação quantitativa: backtesting temporal e baseline de patrulha\n\n",
        "",
        b12,
        count=1,
    )
    b12 = b12.replace("### 12.1 ", "### 7.2 ")
    b12 = b12.replace("### 12.2 ", "### 7.3 ")
    b12 = b12.replace("### 12.3 ", "### 7.4 ")
    intro = (
        "## 7. Validação\n\n"
        "A validação do SAD combina confrontação qualitativa com cenários representativos "
        "(Secção 7.1) e métricas quantitativas de backtesting temporal e baseline de patrulha "
        "(Secções 7.2–7.4).\n\n"
    )
    return intro + b11 + "\n" + b12


def build_section_8(s: dict[int, str]) -> str:
    b13 = s[13].replace(
        "## 13. Discussão e apoio à decisão",
        "## 8. Discussão, limitações e recomendação",
    )
    b13 = b13.replace(
        "Esta secção responde explicitamente às quatro questões de investigação enunciadas na Secção 1,\n"
        "integrando os resultados das secções anteriores numa perspetiva de apoio à decisão.",
        "A discussão responde às quatro questões de investigação (Secção 1), integrando os resultados\n"
        "anteriores numa perspetiva de apoio à decisão.",
    )
    b14 = s[14].replace(
        "## 14. Limitações e ameaças à validade",
        "### 8.2 Limitações e ameaças à validade",
    )
    b15 = s[15].replace("## 15. Recomendação final", "### 8.3 Recomendação final")
    return b13 + "\n" + b14 + "\n" + b15


def fix_refs(text: str) -> str:
  """Substitui referências antigas por placeholders e depois pelos novos números."""
  pairs = [
      ("@@S16@@", "Secção 9"),
      ("@@S15@@", "Secção 8.3"),
      ("@@S14@@", "Secção 8.2"),
      ("@@S13@@", "Secção 8"),
      ("@@S12@@", "Secção 7"),
      ("@@S11@@", "Secção 7.1"),
      ("@@S10@@", "Secção 5.4"),
      ("@@S9@@", "Secção 6"),
      ("@@S8@@", "Secção 5"),
      ("@@S7@@", "Secção 4.5"),
      ("@@S6@@", "Secção 4.4"),
      ("@@S5@@", "Secção 4.3"),
      ("@@S4@@", "Secção 4"),
  ]
  # ordem decrescente para não sobrepor
  rules = [
      (r"Secção 16\b", "@@S16@@"),
      (r"Secção 15\b", "@@S15@@"),
      (r"Secção 14\b", "@@S14@@"),
      (r"Secção 13\b", "@@S13@@"),
      (r"Secção 12\b", "@@S12@@"),
      (r"Secção 11\b", "@@S11@@"),
      (r"Secção 10\b", "@@S10@@"),
      (r"Secção 9\b", "@@S9@@"),
      (r"Secção 8\.3", "@@S8@@.3"),  # handled below
      (r"Secção 8\.2", "@@S8@@.2"),
      (r"Secção 8\.1", "@@S8@@.1"),
      (r"Secção 8\b", "@@S8@@"),
      (r"Secção 7\b", "@@S7@@"),
      (r"Secção 6\b", "@@S6@@"),
      (r"Secção 5\b", "@@S5@@"),
      (r"Secções 4 a 7", "@@S4@@"),
      (r"Secções 4–8", "@@S4@@ e @@S5@@"),
      (r"Secções 4–7", "@@S4@@"),
      (r"Secções 11 e 12", "@@S7@@"),
      (r"Secções 14 a 16", "@@S8@@ e @@S9@@"),
      (r"Sec\. 11,", "@@S11@@,"),
      (r"Sec\. 10;", "@@S10@@;"),
      (r"Sec\. 8, 10;", "@@S8@@, @@S10@@;"),
      (r"Sec\. 7, Fig", "@@S7@@, Fig"),
      (r"Sec\. 8, Q1", "@@S8@@, Q1"),
      (r"Sec\. 8, MCLP", "@@S8@@, MCLP"),
      (r"Sec\. 8;", "@@S8@@;"),
      (r"Sec\. 11\)", "@@S11@@)"),
  ]
  for pat, ph in rules:
      text = re.sub(pat, ph, text)

  # subsecções 8.x → 5.x
  text = text.replace("@@S8@@.1", "Secção 5.1")
  text = text.replace("@@S8@@.2", "Secção 5.2")
  text = text.replace("@@S8@@.3", "Secção 5.3")

  for ph, new in pairs:
      text = text.replace(ph, new)

  # correcções pontuais
  fixes = [
      ("As Secção 4 descrevem", "A Secção 4 descreve"),
      ("índice de risco construído na Secção 4.5, o que", "índice de risco (Secção 4.5), o que"),
      ("convergência entre o *clustering* e o mapa de risco (Secção 4.3)",
       "convergência entre o *clustering* e o mapa de risco (Secção 4.3)"),
      ("validações por estudo de caso (Secção 7.1) e por\nbacktesting temporal (Secção 7)",
       "validações por estudo de caso (Secção 7.1) e por\nbacktesting temporal (Secção 7.2)"),
      ("(Secção 8.2, limitação II)", "(Secção 8.2, limitação II)"),
      ("documentada na Secção 6 e no", "documentada na Secção 6 e no"),
      ("As Secções 4 e 5 produzem", "As Secções 4 e 5 produzem"),
      ("Após a limpeza descrita na Secção 4,", "Após a limpeza descrita na Secção 4.1,"),
      ("projetada para a grelha de procura comum (Secção 4.5)",
       "projetada para a grelha de procura comum (Secção 4.5)"),
  ]
  for a, b in fixes:
      text = text.replace(a, b)

  # 1.3 estrutura
  text = re.sub(
      r"A Secção 2 enquadra teoricamente o trabalho\. A Secção 3 caracteriza os dados e o meio\n"
      r"operacional\. As Secções 4 a 7 descrevem o pipeline de análise — preparação e redução,\n"
      r"\*clustering\*, classificação e agregação difusa\. A Secção 8 formula e resolve a\n"
      r"otimização; a Secção 9 apresenta o painel interativo; a Secção 10 estuda a sensibilidade\.\n"
      r"As Secções 11 e 12 validam o sistema \(estudo de caso e backtesting quantitativo\)\. A\n"
      r"Secção 13 discute os resultados; as Secções 14 a 16 tratam limitações, recomendação e\n"
      r"conclusão\.",
      "A Secção 2 enquadra teoricamente o trabalho. A Secção 3 caracteriza os dados e o meio\n"
      "operacional. A Secção 4 descreve o pipeline de *data mining* (preparação, *clustering*,\n"
      "classificação e risco difuso). A Secção 5 formula e resolve a otimização e a sensibilidade;\n"
      "a Secção 6 apresenta o painel interativo e a plataforma operacional. A Secção 7 valida o\n"
      "sistema (estudo de caso e backtesting). As Secções 8 e 9 tratam discussão, limitações,\n"
      "recomendação e conclusão.",
      text,
  )
  text = text.replace(
      "documentada na Secção 9 e no\nAnexo D.",
      "documentada na Secção 6 e no\nAnexo D.",
  )
  text = text.replace(
      "às quais a Secção 10\nresponde de forma explícita:",
      "às quais a Secção 8\nresponde de forma explícita:",
  )
  return text


def clean_prefix(prefix: str) -> str:
    # remover guia do índice se existir
    g0 = prefix.find("### Guia do índice")
    if g0 >= 0:
        g1 = prefix.find("---\n\n## 1.", g0)
        if g1 < 0:
            g1 = prefix.find("---\n\n", g0)
        if g1 >= 0:
            prefix = prefix[:g0] + prefix[g1:]
    # substituir índice
    i0 = prefix.find("## Índice\n")
    i1 = prefix.find("---\n\n## 1. Introdução")
    if i0 >= 0 and i1 >= 0:
        prefix = prefix[:i0] + NEW_INDEX + "\n\n## 1. Introdução" + prefix[i1 + len("---\n\n## 1. Introdução") :]
    return prefix


def main():
    raw = MD.read_text(encoding="utf-8")
    prefix, sections = split_sections(raw)
    needed = list(range(1, 19))
    missing = [n for n in needed if n not in sections]
    if missing:
        raise ValueError(f"Secções em falta: {missing}")

    body = (
        sections[1]
        + sections[2]
        + sections[3]
        + build_section_4(sections)
        + build_section_5(sections)
        + build_section_6(sections)
        + build_section_7(sections)
        + build_section_8(sections)
        + sections[16].replace("## 16. Conclusão e trabalho futuro", "## 9. Conclusão e trabalho futuro")
        + sections[17].replace("## 17. Referências", "## 10. Referências")
        + sections[18].replace("## 18. Anexos", "## 11. Anexos")
    )

    prefix = clean_prefix(prefix)
    out = fix_refs(prefix + body)
    MD.write_text(out, encoding="utf-8")
    print("OK:", MD)


if __name__ == "__main__":
    main()
