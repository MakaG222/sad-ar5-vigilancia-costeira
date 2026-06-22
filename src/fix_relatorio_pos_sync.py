#!/usr/bin/env python3
"""Correcções finais pós-sincronização do relatório."""
from __future__ import annotations
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MD = BASE / "relatorio" / "Relatorio_SAD_AR5.md"
VAL = BASE / "resultados" / "validacao.json"

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


def main() -> None:
    t = MD.read_text(encoding="utf-8")
    val = json.loads(VAL.read_text(encoding="utf-8"))
    bl = val["baseline_patrulha"]
    pct = f"{bl['ganho_sad_vs_aleatorio']:.2f}".replace(".", ",")

    # Remover Guia do índice
    t = re.sub(
        r"\n### Guia do índice[\s\S]*?(?=\n---\n\n## 1\. Introdução)",
        "\n",
        t,
        count=1,
    )

    # Substituir índice
    t = re.sub(
        r"## Índice\n[\s\S]*?\n---\n\n## 1\. Introdução",
        NEW_INDEX + "\n## 1. Introdução",
        t,
        count=1,
    )

    fixes = [
        ("alimenta a otimização (Secção 4.3)", "alimenta a otimização (Secção 5)"),
        ("documentada na Secção 4.4 e no", "documentada na Secção 6 e no"),
        ("camadas IOM/apreensões.", "camadas de desembarques PT/apreensões e exportação de plano de missão."),
        ("Ganho SAD vs aleatório: **2,22×**", f"Ganho SAD vs aleatório: **{pct}×**"),
        (
            "about 9 AR5 are required for persistent 24-h surveillance. Quantitative validation shows\n"
            "the DSS captures **2,06× more risk** than random patrol (95 % CI: 1,93–2,22) and places **85,5 %** of 2023–2024 maritime seizures in high-risk cells (threshold 0.5) (temporal train ≤2022). The study area is\n"
            "restricted to Portuguese continental maritime waters (longitude −11.0° to −7.38°), excluding Spain.",
            "about **9 AR5** (coastal) or **11 AR5** (full area) for persistent 24-h surveillance. Quantitative validation shows\n"
            "the DSS captures **2,06× more risk** than random patrol (95 % CI: 1,93–2,22) and places **85,5 %** of 2023–2024 maritime seizures in high-risk cells (threshold 0.5; train ≤2022). The study area is\n"
            "mainland Portugal only (1 156 cells, 300 high-risk; longitude −11.0° to −7.38°), excluding Spain.",
        ),
        (
            "irregular migration — the system applies preprocessing",
            "20 documented maritime landings in mainland Portugal (2019–2024) plus IOM data — the system applies preprocessing",
        ),
        # Limitação III — AHP já implementado (Sec. 4.5)
        (
            "**III — Ponderação fixa das ameaças.** Os pesos do índice agregado (0,35 / 0,25 / 0,20 / 0,20) foram\n"
            "fixados a partir da relevância e fiabilidade da evidência, mas constituem um juízo de valor não\n"
            "derivado de um procedimento multicritério formal. Uma metodologia estruturada como o Processo\n"
            "Analítico Hierárquico (AHP) tornaria estes pesos rastreáveis e auditáveis, e permitiria uma análise\n"
            "de sensibilidade sobre a própria ponderação.",
            "**III — Ponderação multicritério e juízos de especialista.** Os pesos do índice agregado "
            "(0,35 / 0,25 / 0,20 / 0,20) foram fundamentados pelo **Processo Analítico Hierárquico (AHP)** "
            "(Secção 4.5; Figura 24), com rácio de consistência aceitável (CR ≈ 0) e análise de sensibilidade "
            "±10 % que confirma estabilidade regional. Persiste, contudo, a dependência dos valores da matriz "
            "de comparação *pairwise* face a juízos de especialista sobre a relevância relativa das ameaças — "
            "o que limita a generalização a outros contextos institucionais sem revalidação do AHP.",
        ),
        # Limitação VII — índice offline vs plataforma tática
        (
            "**VII — Ausência de ligação a dados em tempo real.** O sistema opera sobre dados históricos e\n"
            "estáticos, não estando ligado a fontes operacionais em tempo real (AIS, deteção satélite, previsão\n"
            "meteorológica). O índice de risco é, assim, um instrumento de planeamento estratégico e tático, e não\n"
            "de resposta dinâmica a um contacto em curso.",
            "**VII — Índice estratégico vs. protótipo tático.** O **mapa de risco agregado** é calculado offline "
            "a partir de dados históricos (apreensões, EMODnet, desembarques) e constitui um instrumento de "
            "planeamento estratégico. A **plataforma web** (`plataforma/`) integra, como protótipo, AIS, meteo "
            "IPMA e rotas OR-Tools em modo *quasi*-tempo real, mas **não recalcula automaticamente** o índice de "
            "risco nem substitui uma cadeia C4I operacional — não sendo, por isso, um sistema de resposta "
            "dinâmica a um contacto em curso.",
        ),
        # Limitação I — imigração PT (20 desembarques)
        (
            "A imigração baseia-se nos\n"
            "incidentes do IOM Missing Migrants **georreferenciados em águas portuguesas** (`zona_maritima_pt`),\n"
            "que regista mortes e desaparecimentos — uma amostra trágica mas incompleta do fluxo total de\n"
            "travessias (apenas **1** incidente na caixa de estudo). Apenas o tráfico de droga assenta em eventos de\n"
            "interceção propriamente ditos. Estas fontes seriam idealmente complementadas por registos\n"
            "operacionais diretos (deteções do CleanSeaNet da EMSA, esforço de pesca do Global Fishing Watch\n"
            "validado contra infrações conhecidas, e dados da Frontex/SEF sobre desembarques).",
            "A imigração combina **20 desembarques marítimos documentados** em Portugal Continental "
            "(SEF/Frontex/CP, 2019–2024) com incidentes IOM em mar (`zona_maritima_pt`), via KDE ponderado "
            "70 % / 30 % — amostra pequena mas geograficamente coerente (70 % dos eventos em zona de alto risco; "
            "Secção 7.5). Apenas o tráfico de droga assenta em eventos de interceção propriamente ditos. "
            "Estas fontes seriam idealmente complementadas por registos operacionais diretos (CleanSeaNet/EMSA, "
            "Global Fishing Watch validado contra infrações, e fluxos Frontex em tempo quasi-real).",
        ),
        # Secção 9 — trabalho futuro (sem AHP; já feito)
        (
            "Identificam-se as seguintes linhas de trabalho futuro. Em primeiro lugar, aprofundar a integração\n"
            "de dados reais já iniciada — em que a pesca e a poluição passaram a basear-se na densidade de\n"
            "embarcações do EMODnet e a imigração nos incidentes do IOM Missing Migrants — incorporando\n"
            "adicionalmente o esforço de pesca do Global Fishing Watch validado contra infrações conhecidas e\n"
            "as deteções do CleanSeaNet da EMSA, de modo a distinguir a atividade lícita da genuinamente ilegal\n"
            "e os derrames efetivos do simples risco de derrame. Em segundo lugar, a substituição da ponderação fixa das ameaças por uma\n"
            "metodologia multicritério formal, como o Processo Analítico Hierárquico (AHP), que estruturasse os\n"
            "juízos de comando de forma rastreável. Em terceiro lugar, a generalização do modelo de otimização\n"
            "de um objetivo único para uma formulação multi-objetivo, gerando uma fronteira de Pareto entre\n"
            "risco coberto e número de aeronaves que explicitasse todo o espectro de compromissos. Por fim, a\n"
            "validação do sistema contra registos reais de interceções, que permitiria aferir, em condições\n"
            "operacionais, a capacidade preditiva do índice de risco e fechar o ciclo Medir–Analisar–Agir com\n"
            "um ciclo de aprendizagem contínua.",
            "Identificam-se as seguintes linhas de trabalho futuro. Em primeiro lugar, aprofundar a integração "
            "de fontes operacionais já iniciadas — EMODnet, **20 desembarques marítimos em Portugal Continental** "
            "(SEF/Frontex/CP) e IOM em mar — incorporando esforço de pesca do Global Fishing Watch validado "
            "contra infrações conhecidas e deteções CleanSeaNet da EMSA, de modo a distinguir atividade lícita "
            "de ilegal e derrames efetivos de simples risco. Em segundo lugar, generalizar o modelo de "
            "otimização de objetivo único para uma formulação **multi-objetivo**, gerando uma fronteira de "
            "Pareto entre risco coberto e número de aeronaves. Em terceiro lugar, validação contra "
            "interceções georreferenciadas com precisão subquilométrica e aprendizagem contínua (ciclo "
            "Medir–Analisar–Agir fechado). Por fim, endurecer a ligação entre o índice estratégico offline "
            "e a plataforma tática, com recálculo periódico automatizado do risco.",
        ),
        # Anexo D — pasta e números de entrega
        ("na pasta **`SIGA_GRUPOVI/`**", "na pasta **`SIGA_GRUPOVI_FINAL/`**"),
        ("SIGA_GRUPOVI/\n", "SIGA_GRUPOVI_FINAL/\n"),
        ("│   ├── validacao.json        Q1/Q2/Q3, backtest, baseline 2,2×", "│   ├── validacao.json        Q1/Q2/Q3, backtest, baseline 2,06×"),
        ("→ grelha 1 180 células", "→ grelha 1 156 células"),
        ("| Validação | Ganho SAD vs aleatório: **2,22×** |", f"| Validação | Ganho SAD vs aleatório: **{pct}×** (IC95 1,93–2,22) |"),
    ]
    for old, new in fixes:
        t = t.replace(old, new)

    MD.write_text(t, encoding="utf-8")
    print("OK:", MD)


if __name__ == "__main__":
    main()
