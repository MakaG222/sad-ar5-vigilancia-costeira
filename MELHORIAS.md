# Roteiro para um trabalho de nível 20 — SAD AR5

## Estado: já IMPLEMENTADO nesta versão
- ✅ Pré-processamento completo (limpeza, missing, transformação, discretização, codificação) — `dm/preproc.py`
- ✅ Análise exploratória e visualização — `dm/eda.py`
- ✅ Clustering (K-means + cotovelo/silhueta, hierárquico/dendrograma, DBSCAN) → zonas de patrulha — `dm/clustering.py`
- ✅ Classificação comparada (Naive Bayes, k-NN, Árvores CART Gini/entropia, MLP) com matriz de confusão, ROC, F1, AUC e tratamento de desequilíbrio — `dm/classificacao.py`
- ✅ Lógica difusa (sistema de Mamdani) para o risco — `dm/fuzzy_risco.py`
- ✅ Otimização de bases (set cover/MCLP) + dimensionamento de frota 24 h
- ✅ Relatório IMRaD em Word com revisão de literatura e referências de métodos

## Estado: NOVO — Fontes de dados reais e formatação estilo dissertação
A maior fragilidade da versão anterior era que três das quatro ameaças (pesca, poluição,
imigração) assentavam em *priors* gaussianos calibrados à mão. Foi substituída por **dados
reais, abertos e georreferenciados**, com aquisição programática e reprodutível:
- ✅ **Pesca ilegal e poluição → EMODnet Human Activities (vessel density, WCS)** — densidade
  de embarcações de pesca (tipo 02) e de carga+tanque (10+11), amostrada na grelha de procura
  (EPSG:3857), com compressão log, suavização espacial e normalização robusta por percentil.
  Rasters em `dados/fontes/emodnet/`.
- ✅ **Imigração irregular → IOM Missing Migrants Project (HDX, CC-BY 4.0)** — filtro
  `zona_maritima_pt` (apenas águas de Portugal Continental, sem Espanha): **1 incidente**
  georreferenciado na caixa de estudo; KDE ponderado pelo n.º de vítimas.
  Ficheiro `dados/fontes/iom_missing_migrants.csv`.
- ✅ **Tráfico de droga** — 9 725 apreensões reais geocodificadas (já existente), agora também
  por KDE.
- ✅ Pipeline `dm/construir_dados_reais.py` → `dados/processados/intensidades_reais.csv`,
  consumido por `risco.py` (com *fallback* automático para os priors se as fontes faltarem).
- ✅ **Âmbito geográfico PT** — grelha, risco, mapas e validação restritos à costa portuguesa
  (−11,0° a −7,38° W); Espanha/Golfo de Cádiz excluídos (`geo.zona_maritima_pt`).
- ✅ **Resultados recalculados** com dados reais: 2 bases (Porto + Portimão) cobrem 100 % do
  risco; frota persistente 24 h = **9 AR5**; **259** células de alto risco; **1 180** células
  na grelha.
- ✅ **Validação Fase C** (`src/validacao.py`) — backtesting temporal (2011–2022 → 2023–2024),
  baseline SAD vs aleatório (**2,2×** ganho), figuras 21–22, `validacao.json`.
- ✅ **Camadas AIS no painel interativo** — EMODnet vessel density + route density, **1**
  incidente IOM (PT), apreensões 2020+, painel lateral com métricas de validação, OpenSeaMap.

## Estado: anterior (subir um nível face ao melhor trabalho do ano anterior)
Análise do trabalho de referência ("Grupo Alface", melhor nota): a sua força não estava
na profundidade analítica (que a nossa supera largamente), mas na **tangibilidade
operacional** — mapas interativos, caso real validado e limitações honestas. Para subir
acima, mantivemos a nossa superioridade analítica e acrescentámos exatamente essas peças:
- ✅ **Painel geoespacial interativo (Folium)** — `src/mapa_interativo.py` → `resultados/mapa_interativo.html`:
  carta náutica navegável com mapa de calor do risco, camadas por ameaça, bases
  recomendadas com raios de cobertura, zonas de patrulha (setores) e controlo de camadas.
  Materializa o conhecimento no referencial onde a decisão é tomada (cadeia
  dados→informação→conhecimento→ação). É a peça que distinguia o trabalho de referência —
  agora assente numa base analítica muito mais forte.
- ✅ **Validação por estudo de caso** (Secção 11 + Tabela 7) — quatro cenários em águas PT
  (cocaína SW Cabo S. Vicente, haxixe Algarve oriental, imigração ao largo de Lisboa/IOM,
  pesca INN NW): o índice classifica cada um e a decomposição por ameaça é plausível.
- ✅ **Secção de Limitações e ameaças à validade** (Secção 13) — oito limitações explícitas
  e ordenadas (ao estilo honesto e granular do trabalho de referência), com o respetivo
  sentido de enviesamento.

## Melhorias adicionais (trabalho futuro)
Prioridade: 🔴 alto impacto · 🟠 médio · 🟢 polimento.

Itens já implementados nesta versão (não repetir como pendentes): AHP (`dm/ahp_pesos.py`),
backtesting temporal, baseline de patrulha, KDE com dados reais, painel Folium, plataforma web,
validação por estudo de caso, secção de limitações.

## A. Dados e rigor empírico
- ✅ **KDE com dados reais** — EMODnet, IOM, apreensões; `construir_dados_reais.py`
- 🟠 **Georreferenciar ao nível de concelho** em vez de centróide de distrito (melhoria sobre o estado actual)
- 🟠 **Normalizar por esforço/área** (ex.: apreensões por 1000 km² ou por densidade de
  tráfego) para evitar enviesamento por zonas mais fiscalizadas.
- 🟠 **Série temporal**: explorar sazonalidade (a droga e a migração têm picos em Q1/Q4)
  e propor patrulhamento adaptativo por mês.

## B. Modelação do risco
- ✅ **AHP para pesos** — `dm/ahp_pesos.py`, CR ≈ 0, Figura 24
- 🟠 **Análise de incerteza do risco** (Monte Carlo sobre pesos e sigmas)
- 🟢 Acrescentar uma 5.ª camada de **valor a proteger** (áreas protegidas/Natura 2000,
  rotas de SAR) para ponderar consequência, não só probabilidade.

## C. Modelo de otimização (o que mais pesa numa avaliação)
- 🔴 **Cobertura com revisita explícita** via modelo de **roteamento persistente**
  (Persistent Surveillance / Orienteering com janelas temporais) em vez do rácio
  area/(V·W·T). Resolver com OR-Tools (VRP) ou heurística documentada.
- 🔴 **Otimização multi-objetivo** (frota vs. risco coberto vs. tempo de revisita) com
  **fronteira de Pareto**, em vez de minimizar um único número.
- 🟠 **Probabilidade de deteção** dependente do estado do mar/alvo (modelo de busca de
  Koopman) em vez de cobertura binária dentro do raio.
- 🟠 **Robustez/estocástico**: otimização robusta a falhas de drone e a janelas de mau
  tempo (cenários com disponibilidade reduzida).

## D. Modelação operacional do AR5
- 🔴 Substituir o raio fixo por um **modelo de autonomia realista**: consumo vs.
  velocidade, vento em rota (componente de proa/cauda real), tempo de subida e reserva
  regulamentar — derivar o raio de cada base de forma física.
- 🟠 **Turnaround e manutenção** explícitos (filas/teoria de filas) para a disponibilidade
  D, em vez de um fator único.
- 🟢 Restrições reais: **espaço aéreo segregado**, NOTAM, separação do tráfego civil,
  limites de link RLOS vs. SATCOM.

## E. Validação
- ✅ **Backtesting temporal** e **baseline de patrulha** — `validacao.py`, Secção 7
- 🟠 **Validar contra interceções pontuais** (MAOC-N, semissubmersíveis) com coordenadas exactas

## F. SIG e visualização
- 🔴 Reintegrar no **QGIS** (coerência com o trabalho original): exportar o risco e as
  zonas como **GeoPackage/Shapefile** e produzir mapas cartográficos com CRS oficial
  (ETRS89/PT-TM06), batimetria e ZEE real (linhas de base da DGT/IH).
- ✅ **Dashboard interativo** (Folium) para o decisor explorar cenários — IMPLEMENTADO
  (`src/mapa_interativo.py` → `resultados/mapa_interativo.html`).
- 🟢 Mapas com escala, norte, grelha de coordenadas e fontes — qualidade de publicação.

## G. Dimensão económica e de decisão
- 🔴 **Análise custo-benefício**: custo por hora de voo do AR5 vs. valor das apreensões
  evitadas / multas de pesca / custo de derrames — justificar a frota economicamente.
- 🟠 **Comparação de alternativas**: AR5 vs. meios tripulados vs. satélite (matriz
  multicritério), para enquadrar a recomendação.

## H. Redação e formato académico
- 🔴 **Estrutura IMRaD** completa com revisão de literatura citando trabalhos de
  *maritime surveillance optimization* e *facility location* (10–20 referências
  académicas, não só institucionais).
- 🔴 **Normas de citação** (APA/IEEE) consistentes e numeração automática de
  figuras/tabelas; lista de figuras, tabelas e acrónimos.
- 🟠 **Formulação matemática formal** das funções objetivo e restrições (LaTeX), com
  definição de conjuntos, índices e variáveis.
- 🟢 Capa institucional, índice automático, paginação, resumo + abstract.

## I. Reprodutibilidade e engenharia
- 🟠 **Testes unitários** (pytest) para os módulos de geo/risco/otimização.
- 🟠 **Ambiente fixado** (requirements com versões exatas / `environment.yml`) e
  *seed* fixa para resultados determinísticos.
- 🟢 Notebook Jupyter de demonstração passo-a-passo + figuras inline.

---

### Se só houver tempo para 5 coisas (máximo impacto/nota)
1. Dados pontuais reais das 4 ameaças + KDE (A).
2. Pesos por AHP com rácio de consistência (B).
3. Otimização multi-objetivo com fronteira de Pareto (C).
4. Validação contra interceções reais + baseline aleatório (E).
5. Revisão de literatura + formalização matemática + normas de citação (H).
