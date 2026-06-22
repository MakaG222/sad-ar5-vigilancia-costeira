#!/usr/bin/env python3
"""Condensa o relatório: remove redundâncias, mantém métricas e validação (nota 20/20)."""
from __future__ import annotations
import re
from pathlib import Path

MD = Path(__file__).resolve().parent.parent / "relatorio" / "Relatorio_SAD_AR5.md"


def _between(text: str, start: str, end: str) -> tuple[str, str, str]:
    i = text.find(start)
    if i < 0:
        return text, "", ""
    j = text.find(end, i + len(start))
    if j < 0:
        return text, "", ""
    return text[:i], text[i:j], text[j:]


def main() -> None:
    t = MD.read_text(encoding="utf-8")

    # --- Secção 2: fundir subsecções teóricas longas ---
    sec2_compact = """### 2.3 Técnicas analíticas mobilizadas

O trabalho aplica o ciclo KDD (Fayyad et al., 1996) no paradigma Medir→Analisar→Agir (Marakas, 2003):
**PCA** para redução de dimensionalidade; **clustering** (k-médias, hierárquico, FCM, DBSCAN) para
segmentação espacial; **classificação** (Bayes, k-vizinhos, árvores CART, MLP) com validação cruzada
e SMOTE para classes raras; **lógica difusa** Mamdani para agregação prudencial do risco; e
**otimização de localização** (set cover e MCLP; Church & Revelle, 1974) para bases e frota.

"""
    pre, mid, post = _between(t, "### 2.3 Redução de dimensionalidade", "---\n\n## 3.")
    if mid:
        t = pre + sec2_compact + post

    # --- Secção 1.3: estrutura correcta ---
    t = re.sub(
        r"### 1\.3 Estrutura do documento\n\n[\s\S]*?(?=\n---\n\n## 2\.)",
        """### 1.3 Estrutura do documento

A Secção 2 enquadra teoricamente o SAD. A Secção 3 caracteriza dados e pipeline. As Secções 4–5
descrevem *data mining* e otimização. A Secção 6 apresenta o painel e a plataforma. A Secção 7
valida o sistema (estudo de caso e métricas quantitativas). As Secções 8–9 discutem limitações,
recomendam a configuração operacional e concluem.

""",
        t,
        count=1,
    )

    # --- Classificação: resumir narrativa pré-tabela (manter Tabela 3) ---
    old_cls = (
        "O **classificador de Bayes ingénuo** ilustra de forma paradigmática os perigos da classe rara"
    )
    if old_cls in t:
        pre, mid, post = _between(
            t,
            "### 6.2 Análise comparativa por família de algoritmos\n\n",
            "**Tabela 3.**",
        )
        if mid:
            resumo = (
                "A Tabela 3 sintetiza o desempenho em teste (configurações base e otimizadas). "
                "Em classes raras, a **PR-AUC** e a inspeção da matriz de confusão são mais informativas "
                "que a exatidão global (Davis & Goadrich, 2006). O Bayes maximiza sensibilidade à custa "
                "de falsos alarmes; k-vizinhos obtém o melhor F1 pontual (0,592); a árvore optimizada "
                "sobreajusta (ROC-AUC 0,77); o **MLP** equilibra ROC-AUC (0,944) e PR-AUC (0,674) e "
                "generaliza melhor em validação cruzada (0,93 ± 0,02).\n\n"
            )
            t = pre + resumo + post

    # --- Limiar: um parágrafo ---
    pre, mid, post = _between(t, "#### 4.4.3 Ajuste do limiar de decisão\n\n", "---\n\n\n### 4.5")
    if mid:
        curto = (
            "O limiar de decisão do MLP não deve fixar-se em 0,5: treinado com SMOTE (50/50), o F1 "
            "máximo (~0,68) ocorre perto de 0,95 no conjunto de teste real (3,4 % marítimo). O SAD "
            "expõe a curva precisão–sensibilidade (Figura 11) para escolha consciente do ponto de "
            "operação face à assimetria de custos.\n\n"
        )
        t = pre + curto + post

    # --- Plataforma 6.2: condensar ---
    pre, mid, post = _between(
        t,
        "### 6.2 Como a plataforma apoia o trabalho e conclusões operacionais\n\n",
        "---\n\n## 7. Validação",
    )
    if mid:
        curto = (
            "A plataforma consome `resultados.json`, `validacao.json` e `camadas_mapa.json`, "
            "permitindo exercitar cenários com meteo live, rotas OR-Tools e alertas WebSocket. "
            "Confirma visualmente Q1–Q3 (setores de risco, bases MCLP, ganho **2,06×**), demonstra "
            "o impacto do vento no alcance e suporta a apresentação oral via cenários pré-definidos "
            "(Figura 23). Modo demonstração AIS activa-se automaticamente sem chave API.\n\n"
        )
        t = pre + curto + post

    # --- Discussão Q1–Q4: versão compacta ---
    pre, mid, post = _between(
        t,
        "A discussão responde às quatro questões de investigação (Secção 1), integrando os resultados\nanteriores numa perspetiva de apoio à decisão.\n\n",
        "---\n\n\n### 8.2 Limitações",
    )
    if mid:
        compacta = """**Q1 — Onde?** Índice de risco e *clustering* convergem para Algarve e eixo Setúbal–Lisboa (correlação ponderado/difuso 0,76).

**Q2 — Previsão marítima?** O MLP com SMOTE atinge ROC-AUC 0,93 ± 0,02; PR-AUC privilegia a avaliação em classe rara.

**Q3 — Alcance ou sensor?** Com raio fixo 90 km cobrem-se 66,8 % do risco; com autonomia AR5 o constrangimento passa a ser **revisita sensorial** (Secção 5).

**Q4 — Frota e bases?** **Porto + Portimão** (MCLP) e **9–11 AR5** para 24 h (300 células alto risco); índice difuso como majorante prudencial (~27 AR5).

O SAD quantifica o compromisso entre cobertura, custo e risco residual sem impor a postura de comando.

"""
        t = pre + compacta + post

    # --- Limitações: lista compacta ---
    pre, mid, post = _between(
        t,
        "O rigor de um trabalho de apoio à decisão mede-se não apenas pelos resultados que produz, mas pela\nlucidez com que reconhece os seus próprios limites. Identificam-se, por isso, de forma explícita e\nordenada, as principais limitações do sistema e as ameaças à validade das suas conclusões, bem como\no seu provável sentido de enviesamento.\n\n",
        "O reconhecimento destas limitações não invalida as conclusões",
    )
    if mid:
        lims = """- **Fontes *proxy*:** EMODnet mede actividade AIS, não ilegalidade directa; imigração assenta em 20 desembarques PT + IOM filtrado.
- **Geocodificação administrativa:** ~83 % das apreensões; dilui sinal no limiar absoluto (Secção 7.6).
- **Pesos AHP:** rastreáveis mas dependentes de juízos de especialista (Secção 4.5).
- **Parâmetros sensoriais:** largura útil, revisita e disponibilidade são estimativas (sensibilidade Secção 5.4).
- **Cobertura idealizada:** não modela nebulosidade, mar agitado nem sazonalidade fina.
- **Classificação:** desequilíbrio 3,4 % marítimo limita precisão da classe minoritária.
- **Índice offline vs. plataforma:** risco estratégico estático; protótipo tático não recalcula o mapa em tempo real.
- **Validação externa:** estudo de caso e backtest não substituem interceções subquilométricas.

"""
        t = pre + lims + post

    # --- Anexo A: legendas curtas (manter referência às figuras) ---
    t = re.sub(
        r"\*\*Figura (\d+)\.\*\* [^\n]{80,}",
        lambda m: f"**Figura {m.group(1)}.** *(ver ficheiro em `resultados/figuras/`)*",
        t,
    )

    # --- Sumário executivo: mais directo ---
    pre, mid, post = _between(t, "## Sumário executivo\n\n", "\n---\n\n## Resumo")
    if mid and len(mid) > 600:
        curto = (
            "Este trabalho desenvolve um SAD para vigilância costeira de **Portugal Continental** "
            "com o UAV TEKEVER AR5, integrando *data mining*, otimização (MCLP) e protótipo web. "
            "Sobre **1156 células** marítimas (**300** de alto risco), responde: **(Q1)** patrulhar "
            "Algarve, Lisboa–Setúbal e NW; **(Q2)** ~**9–11 AR5** para 24 h; **(Q3)** bases "
            "**Porto + Portimão**. Validação: holdout 85,5 % em alto risco; ganho de patrulha "
            "**2,06×** vs aleatório (IC95 1,93–2,22). Plataforma *quasi*-tempo real com modo demo AIS.\n\n"
        )
        t = pre + "## Sumário executivo\n\n" + curto + post

    # --- Resumo: números e tamanho ---
    t = t.replace(
        "validação quantitativa confirma que o SAD captura **2,2× mais risco** que uma patrulha\n"
        "aleatória e que **44 %** das apreensões marítimas de 2023–2024 caem no top 20 % de risco\n"
        "(treino temporal ≤2022).",
        "validação quantitativa confirma ganho de patrulha **2,06×** vs aleatório (IC95 1,93–2,22) e "
        "**85,5 %** das apreensões 2023–2024 em células de alto risco (limiar 0,5; treino ≤2022).",
    )
    t = re.sub(
        r"## Resumo\n\n[\s\S]*?\n\*\*Palavras-chave:\*\*",
        """## Resumo

Desenvolveu-se um **SAD** para vigilância costeira de Portugal Continental com o UAV **TEKEVER AR5**,
integrando *data mining* (PCA, *clustering*, classificação com SMOTE, lógica difusa) e otimização
(MCLP, dimensionamento de frota). Dados: apreensões UNODC, EMODnet, 20 desembarques PT e IOM em mar.
Grelha de **1156 células** (**300** alto risco). Resultados: concentração no Algarve e Setúbal–Lisboa;
MLP com ROC-AUC 0,93 ± 0,02; **Porto + Portimão** cobrem 100 % do risco; **9–11 AR5** para 24 h;
ganho de patrulha **2,06×** (IC95 1,93–2,22); holdout 85,5 % em alto risco. Protótipo web com AIS demo.

**Palavras-chave:**""",
        t,
        count=1,
    )

    MD.write_text(t, encoding="utf-8")
    print(f"OK — relatório condensado: {MD} ({len(t.splitlines())} linhas)")


if __name__ == "__main__":
    main()
