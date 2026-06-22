"""
gerar_docx_diff.py — Versão do relatório de entrega com alterações a amarelo.

Parte da versão Word anterior (Trabalho Final SAD.docx), aplica as correcções
do relatório revisto e realça em amarelo todo o texto novo ou modificado.

Uso:
  cd src
  python3 gerar_docx_diff.py
  python3 gerar_docx_diff.py /caminho/versao_anterior.docx /caminho/saida.docx
"""
from __future__ import annotations

import os
import sys
from copy import deepcopy

import shutil
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml import OxmlElement
from docx.text.paragraph import Paragraph

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REL_DIR = os.path.join(BASE, "relatorio")
def _default_antigo() -> str:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(os.path.dirname(base), "Trabalho Final SAD.docx")


ANTIGO_DEFAULT = _default_antigo()
OUT_DEFAULT = os.path.join(REL_DIR, "Trabalho Final SAD - ALTERACOES.docx")
OUT_ALT = os.path.join(REL_DIR, "Relatorio_SAD_AR5_ALTERACOES.docx")

# (texto_antigo_exacto, texto_novo) — parágrafos completos
PARA_REPLACEMENTS: list[tuple[str, str]] = [
    (
        "Os resultados indicam concentração de atividade ilícita no Algarve e no eixo Setúbal–Lisboa. O modelo MLP obteve uma ROC-AUC de 0,93 ± 0,02. A análise de otimização demonstra que Porto e Portimão garantem cobertura total do risco identificado, sendo necessária uma frota de 9 UAV AR5 para a faixa costeira prioritária e 11 UAV AR5 para a totalidade da área de alto risco, para assegurar vigilância contínua de 24 horas. O sistema apresenta ainda um ganho de patrulha de 2,06× (IC95 1,93–2,22) e uma taxa de cobertura de 85,5% em validação holdout. Foi desenvolvido um protótipo web com demonstração AIS.",
        "Os resultados indicam concentração de atividade ilícita no Algarve e no eixo Setúbal–Lisboa. O modelo MLP obteve uma ROC-AUC de 0,93 ± 0,02. Porto e Portimão cobrem 100 % do risco (MCLP k=2); para 24 h de vigilância persistente são necessários 9 AR5 na faixa costeira (cinco bases de lançamento) ou 11 AR5 na área total (rede de doze aeródromos). O sistema apresenta um ganho de patrulha de 2,06× (IC95 1,93–2,22) e 85,5 % de acerto em holdout. Foi desenvolvido um protótipo web com demonstração AIS.",
    ),
    (
        "A aplicação deste modelo à área total de alto risco (28 494 km²), servida pelas duas bases ótimas de Porto e Portimão, conduz a 4 aeronaves simultaneamente no ar e a uma frota total de 11 AR5, com uma distância média ao ponto de patrulha de 55,9 km e um tempo de estação de 13,9 horas. Caso o esforço se restrinja à faixa costeira mais densa (25 075 km²), bastam 3 aeronaves simultâneas e uma frota de 9 AR5.",
        "A aplicação deste modelo à área total de alto risco (28 494 km²), com a rede completa de doze bases seleccionada pelo trade-off de frota (Secção 5.3), conduz a 4 aeronaves simultâneas e a uma frota total de 11 AR5, com distância média de 55,9 km e tempo de estação de 13,9 h por sortida. Restringindo o esforço à faixa costeira (25 075 km²), alcançável a 90 km a partir de cinco bases — Santa Cruz, Cascais, Sines, Portimão e Faro —, bastam 3 aeronaves simultâneas e uma frota de 9 AR5. Importa não confundir este resultado com o MCLP a duas bases (Porto + Portimão): cobre igualmente 100 % do risco, mas exige 13 AR5 (Tabela B5). Distinguimos, ao longo do relatório, a localização mínima (Q3) do dimensionamento de frota (Q2).",
    ),
    (
        "A análise da frota total em função do número de bases (Tabela B5, Anexo B; Figura 18) revela um ponto de inflexão nítido. Com uma única base, a longa distância média aos pontos de patrulha (339 km) consome uma fração tão grande da autonomia em trânsito que o tempo de estação cai para 8,2 horas, inflacionando o multiplicador de rotação e exigindo 14 aeronaves. A passagem para duas bases (Porto e Portimão) encurta substancialmente os tempos de trânsito e fixa a frota no efetivo de referência, 11 AR5 para a área total de alto risco (9 AR5 na faixa costeira). A partir daí, o acréscimo de bases não traz qualquer redução adicional da frota a curva é perfeitamente plana entre duas e onze bases, pelo que duas bases constituem o ótimo: capturam quase toda a economia de trânsito sem incorrerem nos custos fixos e na complexidade logística de uma rede mais dispersa. A Tabela 6 resume as duas configurações recomendadas.",
        "A análise da frota em função do número de bases (Tabela B5; Figura 18) mostra dois resultados distintos. No MCLP — qual o mínimo de instalações que cobre o risco? — duas bases (Porto e Portimão) bastam. No dimensionamento de frota — quantas aeronaves para 24 h? — o mínimo é com doze bases (distância média 55,9 km, frota 11 AR5). Com Montijo sozinha: 120 km de trânsito médio, 12 AR5. Entre duas e onze bases a frota mantém-se em 13 AR5; só a rede completa reduz para 11. A Tabela 6 resume as configurações de emprego.",
    ),
    (
        "Dado que alguns parâmetros do modelo de dimensionamento são estimativas (designadamente a largura útil do sensor, o período de revisita e a disponibilidade), aferiu-se a robustez da recomendação variando-os isoladamente em torno do cenário de referência de 11 aeronaves (Figura 19; Tabela B6, Anexo B). A frota mostra-se mais sensível à largura útil do sensor e ao período de revisita: alargar o sensor de 30 para 50 km, ou relaxar a revisita de 3 para 6 horas, reduz a frota de 11 para 6 aeronaves; inversamente, exigências mais estritas (sensor de 20 km ou revisita de 2 horas) elevam-na para 12. A disponibilidade operacional tem um efeito mais moderado, fazendo variar a frota entre 11 (disponibilidade de 0,60) e 7 (disponibilidade de 0,90). Estes resultados têm uma leitura de apoio à decisão direta: o investimento que mais reduz o efetivo necessário não é a aquisição de mais aeronaves, mas a melhoria da capacidade sensorial de cada uma (sensores de maior alcance útil) e dos processos de manutenção que sustentam a disponibilidade. A recomendação de 11 aeronaves (área total de alto risco) é, em qualquer caso, estável dentro de uma banda plausível de parâmetros, o que lhe confere credibilidade para efeitos de planeamento.",
        "Dado que alguns parâmetros do modelo de dimensionamento são estimativas (largura útil do sensor, período de revisita e disponibilidade), aferiu-se a robustez variando-os isoladamente (Figura 19; Tabela B6). A frota é mais sensível à largura útil e à revisita: sensor de 50 km ou revisita de 6 h reduzem a frota de 11 para 6 aeronaves; exigências mais estritas (20 km ou 2 h) elevam-na para 14. A disponibilidade operacional varia a frota entre 13 (D = 0,60) e 9 (D = 0,90). O investimento que mais reduz o efetivo é melhorar sensores e manutenção, não adquirir mais aeronaves à toa. A recomendação de 11 AR5 mantém-se estável numa banda plausível de parâmetros.",
    ),
    (
        "O campo de risco relativo ao tráfico de droga foi reconstruído usando apenas apreensões marítimas até 2022; as restantes ameaças mantêm-se nos valores reais (EMODnet, desembarques PT). As 55 apreensões marítimas de 2023–2024 (holdout) foram geocodificadas e confrontadas com o mapa de risco treinado. ",
        "O campo de risco relativo ao tráfico de droga foi reconstruído usando apenas apreensões marítimas até 2022; as camadas de pesca, poluição e imigração mantêm-se estáticas (EMODnet, desembarques PT) — limitação explicitada na Secção 8.2. As 55 apreensões marítimas de 2023–2024 (holdout) foram geocodificadas e confrontadas com o mapa treinado. Os resultados (Figura 21; Tabela 8) mostram que: 85,5 % das apreensões caem no top 20 % de risco; o risco médio no holdout (0,72) excede o global (0,38); ao limiar 0,5, a taxa de acerto (85,5 %) supera o baseline aleatório (36,6 %) em 2,33×.",
    ),
    (
        "A discrepância entre o limiar fixo e o top 20 % reflete a geocodificação ao nível do distrito (Secção 5.2, limitação II): as apreensões são atribuídas à sede administrativa, não à coordenada marítima exata, o que dilui o sinal no limiar absoluto mas preserva a ordenação relativa.",
        "O top 20 % e o limiar 0,5 coincidem neste holdout (47 em 55 apreensões), coerente com a concentração no Algarve e Setúbal–Lisboa. A geocodificação administrativa (Secção 8.2) dilui o sinal no limiar absoluto noutros contextos, mas aqui preserva a ordenação relativa.",
    ),
    (
        "Sensibilidade ao limiar (Figura 25). Variar o limiar a 0,45 / 0,50 / 0,55 altera o n.º de células alto risco de 328 / 300 / 256 e o ganho SAD para 2.01× / 2.07× / 2.15×, a recomendação Porto + Portimão e a ordem de grandeza da frota mantêm-se.",
        "Sensibilidade ao limiar (Figura 25). Variar o limiar a 0,45 / 0,50 / 0,55 altera o n.º de células alto risco de 328 / 300 / 256 e o ganho SAD para 2,01× / 2,07× / 2,15×; a ordem de grandeza da frota (9–11 AR5) e o par MCLP Porto + Portimão mantêm-se.",
    ),
    (
        "Q4 — Frota e bases? Porto + Portimão (MCLP) e 9–11 AR5 para 24 h (300 células alto risco); índice difuso como majorante prudencial (~27 AR5).",
        "Q4 — Frota e bases? Porto + Portimão respondem ao MCLP (cobertura mínima); 9–11 AR5 para 24 h assumem rede costeira distribuída (Tabela 6); índice difuso como majorante prudencial (~27 AR5).",
    ),
    (
        "Fontes *proxy*: EMODnet mede atividade AIS, não ilegalidade direta; imigração assenta em 20 desembarques PT + IOM filtrado. Geocodificação administrativa: ~83 % das apreensões; dilui sinal no limiar absoluto (Secção 7.6). Pesos AHP: rastreáveis, mas dependentes de juízos de especialista (Secção 4.5). Parâmetros sensoriais: largura útil, revisita e disponibilidade são estimativas (sensibilidade Secção 5.4). Cobertura idealizada: não modela nebulosidade, mar agitado nem sazonalidade. Classificação: desequilíbrio 3,4 % marítimo limita precisão da classe minoritária. Índice offline vs. plataforma: risco estratégico estático; protótipo tático não recalcula o mapa em tempo real. Validação externa: estudo de caso e backtest não substituem interceções subquilométricas.",
        "Fontes *proxy*: EMODnet mede atividade AIS, não ilegalidade directa; imigração assenta em 20 desembarques PT + IOM filtrado. Geocodificação administrativa: ~83 % das apreensões; dilui sinal no limiar absoluto (Secção 7.6). Backtest temporal parcial: só a droga é cortada em 2022; pesca, poluição e imigração entram com campo estático. Pesos AHP: rastreáveis; valores adoptados arredondados dos pesos AHP (Secção 4.5). Parâmetros sensoriais: largura útil, revisita e disponibilidade são estimativas (Secção 5.4). Cobertura idealizada: não modela nebulosidade, mar agitado nem sazonalidade fina. Classificação: desequilíbrio 3,4 % marítimo limita precisão da classe minoritária. Índice offline vs. plataforma: risco estratégico estático; protótipo tático não recalcula o mapa em tempo real. Validação externa: estudo de caso e backtest não substituem interceções subquilométricas.",
    ),
    (
        "À luz da análise, recomenda-se a seguinte arquitetura de emprego para o AR5 na vigilância costeira de Portugal Continental. Em síntese: recomenda-se operar a partir do Porto (Sá Carneiro) e Portimão, com 9 AR5 para a faixa costeira prioritária ou 11 AR5 para a área total de alto risco. Como configuração de referência, propõe-se a operação a partir de duas bases: Porto (Sá Carneiro) e Portimão com uma frota de 11 aeronaves AR5, dimensionada para assegurar a revisita persistente, 24 horas por dia, da totalidade das 300 células de alto risco identificadas pela agregação ponderada, com uma margem de 10 %. ",
        "À luz da análise, recomenda-se a seguinte arquitectura de emprego para o AR5 na vigilância costeira de Portugal Continental. Em síntese: dois polos MCLP — Porto (Sá Carneiro) e Portimão — cobrem 100 % do risco alto; para operação persistente 24 h, dimensionar 9 AR5 na faixa costeira (cinco bases) ou 11 AR5 na área total (rede de doze aeródromos). Como configuração de referência, propõe-se a rede completa com frota de 11 AR5, mantendo Porto e Portimão como hubs principais. ",
    ),
    (
        "Esta configuração é ótima no número de bases e robusta face à variação plausível dos parâmetros sensoriais. Como configuração de contingência ou de arranque faseado, em caso de restrição orçamental ou de disponibilidade inicial limitada de aeronaves, recomenda-se concentrar o esforço na faixa costeira mais densa, com 9 aeronaves AR5, aceitando deixar descoberta a faixa mais ao largo, opção que retém a cobertura das zonas de maior densidade de atividade (Algarve e Setúbal–Lisboa) à custa do risco residual nas aproximações distantes. ",
        "A rede completa é óptima em frota (11 AR5) e robusta face à sensibilidade dos parâmetros sensoriais. Como contingência ou arranque faseado, concentra-se o esforço na faixa costeira com 9 AR5, aceitando descobrir a franja ao largo — retém Algarve e Setúbal–Lisboa à custa de risco residual distante. ",
    ),
    (
        "Para fundamentar formalmente os pesos da média ponderada, aplicou-se o método AHP (Saaty, 1980) aos quatro critérios: droga, pesca, poluição e imigração, com comparações par-a-par calibradas para vigilância costeira de Portugal Continental. A matriz obtida produz pesos 0.38 / 0.24 / 0.19 / 0.19 com razão de consistência 0.0002 (consistente). Os pesos adotados (0,35 / 0,25 / 0,20 / 0,20) aproximam-se dos valores AHP (diferença máxima 0,02). Uma análise de sensibilidade ±10 % confirma robustez: o número de células de alto risco varia entre 276 e 297 (Figura 24; resultados/ahp_pesos.json), sem alterar a hierarquia espacial nem a recomendação de bases.",
        "Os pesos da média ponderada não foram escolhidos arbitrariamente: aplicámos o AHP (Saaty, 1980) aos quatro critérios — droga, pesca, poluição e imigração — com comparações par-a-par para vigilância costeira de Portugal Continental (dm/ahp_pesos.py). A matriz dá 0,38 / 0,24 / 0,19 / 0,19 com razão de consistência 0,0002. Arredondámos para 0,35 / 0,25 / 0,20 / 0,20 no config.py por legibilidade operacional; sensibilidade ±10 % mantém o n.º de células alto risco entre 276 e 297 (Figura 24), sem alterar a hierarquia espacial nem o par MCLP.",
    ),
    (
        "Figura 14 - Graus de pertença do Fuzzy C-Means ao cluster dominante. difusa.",
        "Figura 14 - Graus de pertença do Fuzzy C-Means ao cluster dominante (lógica difusa).",
    ),
    (
        "Figura 18 - Frota total necessária em função do número de bases (ótimo em duas bases).",
        "Figura 18 - Frota total necessária em função do número de bases (mínimo em k = 12).",
    ),
    (
        "Figura 19 - Análise de sensibilidade do dimensionamento da frota aos parâmetros sensoriais. à disponibilidade operacional.",
        "Figura 19 - Sensibilidade do dimensionamento da frota à largura útil do sensor, ao tempo de revisita e à disponibilidade operacional.",
    ),
    (
        "Figura 20 - Painel geoespacial interativo do índice de risco. risco multi-ameaça (1156 células), apreensões marítimas 2020+, desembarques PT, bases MCLP (Porto + Portimão) com raios tático/operacional, seis setores de patrulha e painel Q1–Q3. O artefacto interativo completo está em resultados/mapa_interativo.html.",
        "Figura 20 - Painel geoespacial interativo: índice de risco multi-ameaça (1156 células), apreensões 2020+, desembarques PT, bases MCLP (Porto + Portimão), seis sectores de patrulha e painel Q1–Q3 (resultados/mapa_interativo.html).",
    ),
    (
        "Figura 22 - Comparação com a baseline de patrulha aleatória (ganho do SAD). patrulha aleatória e patrulha uniforme costeira.",
        "Figura 22 - Comparação da captura de risco: SAD versus patrulha aleatória e uniforme costeira.",
    ),
]

INSERTIONS: list[tuple[str, str]] = [
    (
        "2026",
        "Sumário executivo",
    ),
    (
        "Sumário executivo",
        "Portugal tem de vigiar uma ZEE desproporcionada face ao território continental, com quatro ameaças distintas a competir pelos mesmos meios. Este trabalho propõe um SAD que indica onde concentrar patrulhas AR5, quantas aeronaves manter em rotação 24 h e em que bases assentar a rede. O MCLP com duas bases (Porto Sá Carneiro e Portimão) cobre a totalidade do risco alto; para 24 h com trânsitos curtos, o dimensionamento usa cinco bases na faixa costeira (9 AR5) ou a rede completa de doze aeródromos (11 AR5). Uma patrulha orientada pelo risco captura 2,06× mais ameaça que uma patrulha aleatória (IC95 1,93–2,22); no holdout 2023–2024, 85,5 % das apreensões caem em células de alto risco.",
    ),
]

# (índice_tabela, linha, coluna, valor_antigo_substring, valor_novo)
TABLE_CELL_REPLACEMENTS: list[tuple[int, int, int, str, str]] = [
    (3, 0, 2, "Bases", "Bases de lançamento (dimensionamento frota)"),
    (3, 1, 2, "Porto + Portimão", "Santa Cruz, Cascais, Sines, Portimão, Faro"),
    (3, 2, 2, "Porto + Portimão", "Rede completa (12 aeródromos costeiros)"),
    (7, 2, 1, "11 AR5 (4 simultâneos) área total; 9 AR5 (3 simultâneos) faixa costeira",
     "11 AR5 (12 bases) área total; 9 AR5 (5 bases) faixa costeira"),
    (7, 2, 2, "Dimensionamento persistente (Secção 5.2; Tabela 6)",
     "Dimensionamento persistente com rede distribuída (Secção 5.2; Tabela 6)"),
    (7, 3, 1, "Porto (Sá Carneiro) + Portimão — cobrem 100 % do risco",
     "Porto (Sá Carneiro) + Portimão — MCLP k=2, 100 % do risco"),
    (7, 3, 2, "MCLP (Secção 5.3)",
     "Localização mínima (Secção 5.3); frota só com estas bases: 13 AR5"),
    (17, 1, 1, "107,7", "120,1"),
    (17, 1, 2, "12,9", "12,6"),
    (17, 1, 4, "9", "12"),
    (17, 2, 2, "146,1", "138,8"),
    (17, 2, 3, "12,1", "12,2"),
    (17, 2, 4, "10", "13"),
    (17, 3, 0, "3 a 11", "12"),
    (17, 3, 1, "Porto + Portimão", "Rede completa (12 aeródromos)"),
    (17, 3, 2, "146,1", "55,9"),
    (17, 3, 3, "12,1", "13,9"),
    (17, 3, 4, "10", "11"),
    (18, 1, 1, "20 → 12", "20 → 14"),
    (18, 2, 1, "2 → 12", "2 → 14"),
    (18, 3, 1, "0,60 → 11", "0,60 → 13"),
    (18, 3, 1, "0,70 → 9", "0,70 → 11"),
    (18, 3, 1, "0,90 → 7", "0,90 → 9"),
]


def _set_paragraph_text(paragraph: Paragraph, text: str, highlight: bool = True) -> None:
    for run in paragraph.runs:
        run.text = ""
    if paragraph.runs:
        run = paragraph.runs[0]
    else:
        run = paragraph.add_run()
    run.text = text
    if highlight:
        run.font.highlight_color = WD_COLOR_INDEX.YELLOW


def _insert_after(paragraph: Paragraph, text: str, highlight: bool = True) -> Paragraph:
    new_p = OxmlElement("w:p")
    paragraph._p.addnext(new_p)
    new_para = Paragraph(new_p, paragraph._parent)
    run = new_para.add_run(text)
    if highlight:
        run.font.highlight_color = WD_COLOR_INDEX.YELLOW
    return new_para


def _replace_in_paragraph(paragraph: Paragraph, old: str, new: str) -> bool:
    full = paragraph.text
    if old not in full:
        return False
    _set_paragraph_text(paragraph, full.replace(old, new, 1), highlight=True)
    return True


def _apply_table_cells(doc: Document) -> int:
    n = 0
    for ti, ri, ci, old_sub, new_val in TABLE_CELL_REPLACEMENTS:
        if ti >= len(doc.tables):
            continue
        table = doc.tables[ti]
        if ri >= len(table.rows) or ci >= len(table.rows[ri].cells):
            continue
        cell = table.rows[ri].cells[ci]
        for p in cell.paragraphs:
            if old_sub in p.text:
                new_text = p.text.replace(old_sub, new_val, 1)
                _set_paragraph_text(p, new_text, highlight=True)
                n += 1
    return n


def _add_tabela6_row(doc: Document) -> None:
    if len(doc.tables) <= 3:
        return
    table = doc.tables[3]
    if len(table.rows) >= 4:
        return
    row = table.add_row()
    vals = [
        "MCLP mínimo (referência Q3)",
        "28 494",
        "Porto (Sá Carneiro) + Portimão",
        "4",
        "≈ 13 AR5",
    ]
    for i, v in enumerate(vals):
        if i < len(row.cells):
            _set_paragraph_text(row.cells[i].paragraphs[0], v, highlight=True)


def gerar_diff(antigo_path: str = ANTIGO_DEFAULT, out_path: str = OUT_DEFAULT) -> str:
    if not os.path.isfile(antigo_path):
        raise FileNotFoundError(f"Versão anterior não encontrada: {antigo_path}")

    shutil.copy2(antigo_path, out_path)
    doc = Document(out_path)

    n_para = 0
    for old, new in PARA_REPLACEMENTS:
        for p in doc.paragraphs:
            if p.text.strip() == old.strip() or old in p.text:
                _set_paragraph_text(p, new, highlight=True)
                n_para += 1
                break

    n_ins = 0
    for anchor, text in INSERTIONS:
        for p in doc.paragraphs:
            if anchor in p.text:
                _insert_after(p, text, highlight=True)
                n_ins += 1
                break

    n_table = _apply_table_cells(doc)
    _add_tabela6_row(doc)

    # Nota de revisão no início (após capa — após parágrafo «2026»)
    for p in doc.paragraphs:
        if p.text.strip() == "2026":
            note = (
                "[REVISÃO CT302] Passagens a amarelo = alterações face à versão anterior "
                f"({os.path.basename(antigo_path)}). "
                f"Parágrafos: {n_para}; inserções: {n_ins}; células de tabela: {n_table + 1}."
            )
            _insert_after(p, note, highlight=True)
            break

    doc.save(out_path)
    print(f"Documento com alterações a amarelo: {out_path}")
    print(f"  Parágrafos substituídos: {n_para}")
    print(f"  Parágrafos inseridos: {n_ins}")
    print(f"  Células de tabela: {n_table + 1}")
    return out_path


if __name__ == "__main__":
    antigo = sys.argv[1] if len(sys.argv) > 1 else ANTIGO_DEFAULT
    saida = sys.argv[2] if len(sys.argv) > 2 else OUT_DEFAULT
    gerar_diff(antigo, saida)
    if saida == OUT_DEFAULT:
        shutil.copy2(saida, OUT_ALT)
