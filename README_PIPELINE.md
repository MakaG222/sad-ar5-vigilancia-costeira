# SAD AR5 — Sistema de Apoio à Decisão para Vigilância Costeira com Drones

Sistema de apoio à decisão (SAD) que otimiza o emprego do UAV **TEKEVER AR5** na
vigilância da costa de **Portugal Continental**, com o objetivo de combater quatro
ameaças marítimas — **tráfico de droga, pesca ilegal (INN), poluição/derrames e
imigração irregular** — determinando:

1. **Quais as zonas** que devem ser patrulhadas (mapa de risco multi-ameaça);
2. **Quantos drones** são necessários para garantir cobertura **persistente 24 h**;
3. **Onde** colocar as bases (aeródromos costeiros) para minimizar a frota.

**Âmbito geográfico:** costa e águas marítimas de Portugal Continental (longitude
−11,0° a −7,38°, latitude 36,85° a 42,20°), **excluindo Espanha**. Grelha de
**1 156 células**; **300** células de alto risco (limiar 0,5).

O trabalho estende a prova de conceito SIG/QGIS original (Escola Naval, Alfeite),
acrescentando: dados verificados das quatro ameaças, um índice de risco espacial,
um modelo de otimização de localização (set cover + MCLP) e um dimensionamento de
frota que separa **alcance** de **cobertura sensorial persistente**.

## Estrutura

```
SAD_GRUPOVI_final/
├── dados/
│   ├── fontes/              # apreensões, IOM, rasters EMODnet
│   └── processados/         # intensidades_reais.csv (grelha PT)
├── src/
│   ├── config.py            # specs AR5, parâmetros, pesos, FONTES
│   ├── geo.py               # projeção, costa PT, grelha, zona_maritima_pt
│   ├── risco.py             # índice de risco multi-ameaça
│   ├── otimizacao.py        # set cover, MCLP, frota (alcance + persistência)
│   ├── validacao.py         # backtesting temporal + baseline de patrulha
│   ├── main.py              # pipeline de otimização + figuras + validação + mapa
│   ├── mapa_interativo.py   # painel geoespacial interativo (Folium → HTML)
│   ├── gerar_docx.py        # gera o relatório em Word a partir do Markdown
│   └── dm/                  # MÓDULO DE DATA MINING
│       ├── construir_dados_reais.py  # EMODnet + IOM (PT) + apreensões → CSV
│       ├── geocode.py        # geocodificação de distritos/concelhos
│       ├── preproc.py        # limpeza, missing, transformação, codificação
│       ├── eda.py            # análise exploratória e visualização
│       ├── projecao.py       # redução de dimensionalidade (PCA/ACP)
│       ├── clustering.py     # k-médias, hierárquico, Fuzzy C-Means, DBSCAN
│       ├── classificacao.py  # Bayes, k-vizinhos, árvores, MLP + validação cruzada
│       ├── fuzzy_risco.py    # sistema de inferência difusa
│       └── main_dm.py        # orquestrador do data mining + integração
├── resultados/              # otimização: figuras/, JSON, CSV, mapa interativo
│   └── dm/                  # data mining: figuras + dm_resultados.json
├── relatorio/               # relatório final (Markdown + Word)
└── requirements.txt
```

## Como executar

```bash
pip install -r requirements.txt
cd src

# 1. Intensidades reais (EMODnet AIS + IOM em águas PT + apreensões)
python -m dm.construir_dados_reais

# 2. Pipeline completo: risco, otimização, figuras, validação, mapa
python main.py

# 3. Data mining (EDA, clustering, classificação, difuso)
python -m dm.main_dm

# 4. Relatório Word (a partir do Markdown)
python gerar_docx.py
```

Comandos opcionais isolados:

```bash
python validacao.py        # só Fase C (backtest + baseline)
python mapa_interativo.py  # só o painel HTML
```

Saídas: figuras em `resultados/figuras/` e `resultados/dm/`; valores em
`resultados/resultados.json`, `resultados/validacao.json` e
`resultados/dm/dm_resultados.json`; **painel interativo** em
`resultados/mapa_interativo.html`; relatório em `relatorio/Relatório Final.docx`.

## Técnicas de Sistemas de Apoio à Decisão aplicadas

Processo de decisão (Medir→Analisar→Agir) · pré-processamento (valores omissos,
normalização Z-score, codificação) · visualização · redução de dimensionalidade
(PCA/ACP) · clustering (k-médias com cotovelo/silhueta, hierárquico/Ward, Fuzzy
C-Means, DBSCAN) · classificação (Bayes, k-vizinhos, árvores CART Gini/entropia,
perceptrão multicamada) com matriz de confusão e validação cruzada · lógica difusa ·
otimização de localização (cobertura de conjunto, cobertura máxima) · validação
temporal e baseline de patrulha.

## Resultado principal

Com **2 bases costeiras (Porto Sá Carneiro + Portimão)** que cobrem 100 % do risco de
alto, são necessários **≈ 9 AR5** para vigilância persistente 24 h de toda a área de
alto risco (≈ 24 600 km²), ou **≈ 9 AR5** na configuração costeira com 4 bases táticas
(raio 90 km). Com o raio conservador de 90 km do estudo anterior, **mesmo 12 bases
cobrem apenas 66,8 % do risco** — o constrangimento é a cobertura sensorial, não o
alcance. Validação quantitativa: SAD captura **2,06× mais risco** que patrulha aleatória
(IC95: 1,93–2,22); **85,5 %** das apreensões marítimas 2023–2024 em células de alto risco
(limiar 0,5; treino ≤2022).

Ver `relatorio/Relatorio_SAD_AR5.md` para o relatório completo.

## Entrega final unificada

A pasta **`SIGA_GRUPOVI/`** (ao lado deste projecto, em `~/Downloads/SIGA_GRUPOVI/`) contém
todos os ficheiros finais: relatório Word, dados, código, resultados, figuras e plataforma
(sem dependências `.venv`/`node_modules`). Ver `README.md` e `DEMONSTRACAO.md` nessa pasta.

Para regenerar:
```bash
bash scripts/empacotar_siga.sh ~/Downloads/SIGA_GRUPOVI
```

## Plataforma operacional (web)

Protótipo quasi-tempo-real em `plataforma/` (meteo, AIS, mapa de risco, rotas, alertas).

**macOS — arranque em 2 comandos:**

```bash
cd plataforma
./setup-mac.sh && ./start-mac.sh
```

Abrir http://localhost:5173 · Detalhes em [`plataforma/README.md`](plataforma/README.md).
