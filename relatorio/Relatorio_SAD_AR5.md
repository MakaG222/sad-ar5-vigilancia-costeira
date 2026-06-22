# Sistema de Apoio à Decisão para a Vigilância Costeira de Portugal Continental com o UAV TEKEVER AR5

### Modelo integrado de análise de dados e otimização para o dimensionamento e a localização de uma frota de vigilância marítima persistente (24 h)

**CT302 — Sistemas de Apoio à Decisão**
Grupo VI — CAD M Santos Neto · CAD EN-AEL Canotilho Castro · CAD M Silva Guerreiro · CAD M Ribeiro Gaspar
Escola Naval — Alfeite, 2026

---

## Sumário executivo

Portugal tem de vigiar uma ZEE desproporcionada face ao território continental, com quatro ameaças
distintas a competir pelos mesmos meios. Este trabalho propõe um SAD que indica **onde** concentrar
patrulhas AR5, **quantas** aeronaves manter em rotação 24 h e **em que bases** assentar a rede.
O mapa de risco assenta em dados reais (apreensões, EMODnet, desembarques documentados); a
otimização separa alcance de aeronave de cobertura sensorial persistente — e foi esta última que
nos levou à conclusão de que o gargalo não é o raio de 90 km do estudo SIG anterior, mas sim a
revisita do sensor.

Em termos operacionais: o **MCLP com duas bases** (Porto Sá Carneiro e Portimão) cobre a
totalidade do risco alto; para sustentar 24 h com trânsitos curtos, o dimensionamento usa **cinco
bases na faixa costeira** (9 AR5) ou a **rede completa de doze aeródromos** (11 AR5). Uma patrulha
orientada pelo risco captura **2,06×** mais ameaça que uma patrulha aleatória (IC95 1,93–2,22);
no holdout 2023–2024, **85,5 %** das apreensões caem em células de alto risco. Os sectores
prioritários são o Algarve, o eixo Setúbal–Lisboa e o noroeste ao largo de Peniche.


---

## Resumo

Desenvolveu-se um **SAD** para vigilância costeira de Portugal Continental com o UAV **TEKEVER AR5**,
integrando *data mining* (PCA, *clustering*, classificação com SMOTE, lógica difusa) e otimização
(MCLP, dimensionamento de frota). Fontes: apreensões UNODC, EMODnet, 20 desembarques PT e IOM em mar.
Grelha de **1156 células** (**300** alto risco). Concentração no Algarve e Setúbal–Lisboa;
MLP com ROC-AUC 0,93 ± 0,02; **Porto + Portimão** cobrem 100 % do risco (MCLP k=2); **9–11 AR5**
para 24 h com rede costeira distribuída (5 ou 12 bases de lançamento); ganho de patrulha **2,06×**
(IC95 1,93–2,22); holdout 85,5 % em alto risco. Protótipo web com AIS demo.

**Palavras-chave:** Sistemas de Apoio à Decisão; *data mining*; *clustering*;
classificação; lógica difusa; otimização; localização de instalações; vigilância
marítima; veículos aéreos não tripulados; TEKEVER AR5.

## Abstract

This work develops a Decision Support System (DSS) for employing the TEKEVER AR5 unmanned aerial
vehicle (UAV) in the maritime surveillance of mainland Portugal, where scarce assets must be
allocated over a vast area against simultaneous, heterogeneous threats — drug trafficking, illegal,
unreported and unregulated (IUU) fishing, pollution and irregular migration. Coupling a
data-mining pipeline (preprocessing, PCA, spatial clustering, comparative classification validated
by stratified cross-validation, and fuzzy multi-threat aggregation) with a facility-location and
fleet-sizing model, it answers three operational questions: *where* to focus surveillance, *how
many* aircraft sustain it around the clock, and *from which bases* they operate. The model
explicitly separates aircraft *range* from persistent *sensor coverage*. Over a study area of
**1 156 cells** (300 high-risk; mainland Portugal only), illicit activity concentrates in the
Algarve and the Setúbal–Lisbon axis; the maritime nature of a seizure is predictable with strong
discrimination (ROC-AUC = 0.93 ± 0.02); and the limiting factor is sensor coverage, not range.
Two bases — **Porto and Portimão** — cover 100 % of the risk under the MCLP (k=2); sustaining
24-h surveillance with short transits requires about **9 AR5** along the coastal belt (five launch
bases) or **11 AR5** over the full high-risk area (twelve bases). Validation shows the DSS captures
**2.06× more risk** than random patrol (95 % CI 1.93–2.22) and places **85.5 %** of 2023–2024
maritime seizures in high-risk cells (threshold 0.5; train ≤ 2022).

**Keywords:** Decision Support Systems; data mining; clustering; classification; fuzzy
logic; optimization; facility location; maritime surveillance; unmanned aerial
vehicles; TEKEVER AR5.

---

## Índice

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

## 1. Introdução


A República Portuguesa exerce jurisdição sobre uma das maiores Zonas Económicas
Exclusivas (ZEE) da União Europeia, com uma área marítima que excede em mais de
dezoito vezes a sua superfície terrestre. Esta vasta extensão, conjugada com a posição
geográfica do país no flanco sudoeste do continente europeu — à entrada do Mediterrâneo
e no termo das rotas atlânticas provenientes de África e da América do Sul —, coloca
sobre as autoridades nacionais um encargo de fiscalização considerável. Sobre o mesmo
espaço incidem, em simultâneo, ameaças de natureza muito distinta: o tráfico de
estupefacientes por via marítima, a pesca ilegal, não declarada e não regulamentada
(INN), a poluição por descargas de hidrocarbonetos e a imigração irregular. Cada uma
destas ameaças possui assinaturas espaciais, temporais e comportamentais próprias, e
todas competem pelos mesmos meios de vigilância, inerentemente escassos.

A doutrina clássica de fiscalização marítima assenta em meios tripulados — navios de
patrulha oceânica e aeronaves de patrulhamento marítimo — cujo custo-hora elevado e
cuja autonomia limitada restringem severamente a persistência da cobertura. É neste
contexto que os veículos aéreos não tripulados (UAV) de longa autonomia, de que o
**TEKEVER AR5** é um exemplo maduro e de origem nacional, se afirmam como um multiplicador
de força: com uma autonomia que ronda as 16 a 20 horas e um conjunto sensorial que
combina câmaras eletro-óticas e de infravermelhos, recetor de Sistema de Identificação
Automática (AIS) e capacidade de interceção de sinais, o AR5 permite manter uma
presença sensorial sobre áreas extensas a uma fração do custo dos meios convencionais.
A questão deixa de ser, portanto, *se* se deve recorrer a estes meios, e passa a ser
*como* os empregar de forma ótima.

Esta passagem do «se» para o «como» é, na sua essência, um problema de apoio à decisão.
Trata-se de uma decisão **semiestruturada** — na aceção de Simon (1977) e da matriz
tipo-nível de decisão popularizada por Gorry e Scott Morton —, situada ao nível do
controlo de gestão e do planeamento: comporta componentes perfeitamente quantificáveis
(a autonomia da aeronave, a área a cobrir, o alcance dos sensores) mas também elementos
de juízo que não admitem formulação puramente algorítmica (a ponderação relativa das
ameaças, a tolerância a falhas de cobertura, a aceitação de risco residual). Decisões
desta natureza são precisamente o domínio por excelência dos Sistemas de Apoio à
Decisão (SAD), que não pretendem substituir o decisor, mas sim ampliar a sua capacidade
de análise, tornando explícitos os dados, os modelos e os compromissos subjacentes
(Turban, Sharda, & Delen, 2011).

O presente trabalho parte de um estudo anterior do mesmo grupo (Santos Neto, Silva
Guerreiro, & Ribeiro Gaspar, 2026), no qual, recorrendo a Sistemas de Informação
Geográfica (SIG), se modelaram as áreas de atuação do AR5 em função das condições de
vento. Esse estudo, embora sólido na sua caracterização geográfica, adotava um raio
operacional fixo e conservador de 90 km e não procurava otimizar o número nem a
localização dos meios. O contributo deste trabalho é, portanto, duplo: por um lado,
substituir a delimitação geográfica estática por um **índice de risco fundamentado em
dados**, extraído por técnicas de *data mining* a partir de evidência empírica; por
outro, formular e resolver explicitamente os problemas de **localização de bases** e de
**dimensionamento de frota**, transformando o conhecimento sobre as ameaças em
recomendações operacionais quantificadas.

### 1.1 Objetivos e questões de investigação

O objetivo geral é conceber, implementar e validar um SAD que apoie o emprego do AR5 na
vigilância costeira de Portugal Continental. Deste objetivo geral decorrem as seguintes
questões de investigação, que orientam a estrutura do trabalho e às quais a Secção 5
responde de forma explícita:

- **Q1.** Onde se concentra, de facto, a atividade ilícita marítima, e é essa
  concentração consistente entre fontes de dados e métodos de análise independentes?
- **Q2.** É possível prever a natureza marítima de uma ocorrência a partir dos seus
  atributos, e que algoritmo o faz com maior fiabilidade num cenário de classes
  fortemente desequilibradas?
- **Q3.** Qual é o fator que efetivamente limita a cobertura — o alcance da aeronave ou
  a capacidade de revisita sensorial?
- **Q4.** Quantas aeronaves e quantas bases são necessárias para garantir uma vigilância
  persistente 24 horas, e qual a sensibilidade desse efetivo aos parâmetros do sistema?

### 1.2 Contribuições

As principais contribuições deste trabalho são: (i) a construção de um índice de risco
marítimo multi-ameaça a partir de dados reais, agregado por duas vias metodologicamente
distintas (média ponderada e inferência difusa) cuja convergência é quantificada; (ii)
a validação cruzada desse índice através de *clustering* não supervisionado, que
reproduz, de forma independente, os pontos quentes que o modelo de risco identifica;
(iii) a demonstração empírica de que o paradigma de raio fixo do estudo anterior
subestima grosseiramente a capacidade do sistema; e (iv) um modelo de dimensionamento de
frota que separa o alcance da cobertura sensorial e cuja robustez é aferida por análise
de sensibilidade.

### 1.3 Estrutura do documento

A Secção 2 enquadra teoricamente o SAD. A Secção 3 caracteriza dados e pipeline. As Secções 4–5
descrevem *data mining* e otimização. A Secção 6 apresenta o painel e a plataforma. A Secção 7
valida o sistema (estudo de caso e métricas quantitativas). As Secções 8–9 discutem limitações,
recomendam a configuração operacional e concluem.


---

## 2. Enquadramento teórico e revisão de literatura


### 2.1 Sistemas de Apoio à Decisão e o processo de decisão

Um Sistema de Apoio à Decisão é, na definição consensual da literatura, um sistema de
informação interativo, baseado em computador, que combina dados e modelos para auxiliar
decisores na resolução de problemas semiestruturados ou não estruturados (Turban et al.,
2011). A sua génese conceptual remonta ao modelo de processo de decisão de Simon (1977),
que decompõe a decisão em três fases sucessivas e iterativas: **inteligência**
(identificação e diagnóstico do problema, recolha de dados), **conceção** (formulação e
modelação de alternativas) e **escolha** (seleção e implementação da alternativa
preferida). Marakas (2003) reformula este ciclo numa sequência operacionalmente sugestiva
— **Medir → Analisar → Agir** — que se adota neste trabalho por traduzir com fidelidade o
seu fluxo: medem-se as ameaças através dos dados disponíveis, analisam-se esses dados por
técnicas de *data mining* e otimização, e age-se através de uma recomendação concreta de
emprego de meios. Subjacente a todo o processo está a hierarquia **dados → informação →
conhecimento**: os registos brutos de apreensões e os relatórios institucionais
constituem dados; a sua transformação em mapas de risco, agrupamentos e modelos
preditivos produz informação; e a síntese desta no número e na localização ótima de meios
constitui o conhecimento acionável que o SAD entrega ao decisor.

### 2.2 Extração de conhecimento e *data mining*

A componente analítica do trabalho insere-se no processo de **descoberta de conhecimento
em bases de dados** (*Knowledge Discovery in Databases*, KDD), formalizado por Fayyad,
Piatetsky-Shapiro e Smyth (1996) como uma sequência de etapas — seleção,
pré-processamento, transformação, *data mining* e interpretação/avaliação — das quais o
*data mining* propriamente dito é apenas o passo de aplicação dos algoritmos. As tarefas
de *data mining* dividem-se classicamente em **descritivas**, que procuram resumir a
estrutura latente dos dados (de que o *clustering* é o exemplo central), e
**preditivas**, que procuram inferir o valor de uma variável-alvo (de que a classificação
é o caso mais comum). Ambas são mobilizadas neste trabalho de forma complementar: a
segmentação descritiva identifica zonas de patrulha, e a modelação preditiva caracteriza
os determinantes da atividade marítima.

### 2.3 Técnicas analíticas mobilizadas

O trabalho aplica o ciclo KDD (Fayyad et al., 1996) no paradigma Medir→Analisar→Agir (Marakas, 2003):
**PCA** para redução de dimensionalidade; **clustering** (k-médias, hierárquico, FCM, DBSCAN) para
segmentação espacial; **classificação** (Bayes, k-vizinhos, árvores CART, MLP) com validação cruzada
e SMOTE para classes raras; **lógica difusa** Mamdani para agregação prudencial do risco; e
**otimização de localização** (set cover e MCLP; Church & Revelle, 1974) para bases e frota.

---

## 3. Caracterização dos dados e do meio operacional


**Âmbito geográfico.** Todo o sistema — grelha de procura, intensidades de risco, mapas,
otimização e validação — restringe-se à **costa e às águas marítimas de Portugal
Continental** (longitude −11,0° a −7,38°, até ~300 km da costa), **excluindo Espanha** e
águas sob jurisdição estrangeira.

### 3.1 O conjunto de dados de apreensões

A espinha dorsal empírica do trabalho é um conjunto de dados de **9 727 registos de
apreensões de droga** em Portugal entre **2011 e 2024**, com treze atributos que combinam
a dimensão temporal (data), a dimensão geográfica (região, cidade e região
administrativa), a dimensão substantiva (tipo de substância, unidade e quantidade) e a
dimensão contextual (local físico da apreensão e modo de transporte). Em termos da
tipologia de dados da disciplina, coexistem atributos **numéricos contínuos** (a
quantidade apreendida), **categóricos nominais** (a substância, o local) e
**temporais/ordinais** (a data). Após a limpeza descrita na Secção 4.1, retêm-se **9 725
registos** úteis.

A distribuição por tipo de substância, após agrupamento, revela um claro domínio da
cannabis (4 676 registos) e da cocaína (3 502 registos), seguidas a larga distância pelos
opióides (989), estimulantes (410), alucinogénios (98), «outras» substâncias (32) e
medicamentos (18). Esta distribuição é coerente com o posicionamento de Portugal como ponto
de entrada do haxixe norte-africano e da cocaína sul-americana no espaço europeu.

### 3.2 As quatro ameaças e a sua assinatura espacial

A construção de um índice de risco multi-ameaça exige sustentar cada ameaça em **dados
reais, abertos e georreferenciados**, e não em juízos qualitativos. A Tabela 1 identifica,
para cada ameaça, a fonte de dados operacional efetivamente utilizada para construir o seu
campo de intensidade espacial (Secção 3.4) e a respetiva assinatura geográfica.

**Tabela 1.** *Fontes de dados reais por ameaça e respetiva assinatura espacial.*

| Ameaça | Fonte de dados real utilizada | Natureza do dado | Assinatura espacial observada |
|---|---|---|---|
| Tráfico de droga | 9 725 apreensões UNODC/IDS (2011–2024), geocodificadas por distrito costeiro | Eventos pontuais (n = 335 marítimos) | Algarve (haxixe) e eixo Setúbal–Lisboa; aproximações atlânticas SW (cocaína) |
| Pesca ilegal (INN) | EMODnet *vessel density* pesca (02) + anomalia pesca/AIS | Grelha de intensidade AIS (horas) + rácio pesca/tráfego | Bancos do NW (≈ 42°N), ao largo de Peniche–Lisboa e sul do Algarve |
| Poluição/derrames | EMODnet *vessel density* — carga (10) + tanque (11) | Grelha de intensidade AIS (horas) | Corredor de tráfego N–S a oeste de Lisboa (≈ 10,2°W) e Cabo de São Vicente |
| Imigração irregular | `imigracao_pt_costa.csv` (20 desembarques SEF/Frontex/CP, 2019–2024) + IOM em águas marítimas PT | Eventos pontuais georreferenciados (n = 20 desembarques; 0 incidentes IOM em mar PT após filtro rigoroso) | Algarve (rotas atlânticas) e corredor Setúbal–Lisboa |

### 3.3 O TEKEVER AR5

O AR5 é um UAV tático de asa fixa, de fabrico nacional, cujas especificações verificadas
(TEKEVER, 2025) sustentam a modelação operacional: autonomia de 16 a 20 horas, velocidade
de cruzeiro de 100 km/h, teto de serviço de 3 600 m, peso máximo à descolagem de 180 kg com
50 kg de carga útil, comunicações em linha de vista até 230 km e por satélite sem limite
prático de alcance, e um conjunto sensorial composto por sistema eletro-ótico/infravermelho
giro-estabilizado com ampliação de 30×, recetor AIS, recetor de baliza de emergência
(EPIRB) e capacidade de interceção de sinais (SIGINT). Destas especificações decorre uma
distância de projeção que pode atingir 1 500 km num só sentido, ou 750 km em missões de ida
e volta — valores que, como adiante se demonstra, excedem em larga medida o raio de 90 km
adotado no estudo de referência.

### 3.4 Aquisição e construção das intensidades de risco a partir de dados abertos

Uma contribuição central desta versão do trabalho é a substituição de quaisquer campos de
risco postulados *a priori* por **intensidades derivadas de dados reais**, adquiridos de
forma programática e reprodutível a partir de repositórios públicos (módulo
`dm/construir_dados_reais.py`). Para a **pesca ilegal** e a **poluição**, recorreu-se ao
serviço Web Coverage Service (WCS) do **EMODnet Human Activities**, do qual se extraiu a
densidade média de embarcações (em horas de presença AIS por célula) para a janela
geográfica de Portugal Continental (EPSG:3857), nas categorias de *pesca* (para a pesca
INN) e de *carga* e *tanque* (cuja sobreposição constitui o proxy físico do risco de
derrame, por coincidir com os corredores de maior tráfego mercante, à semelhança da
concentração de alertas do serviço CleanSeaNet da EMSA). Para a **imigração irregular**, compilou-se o ficheiro `dados/fontes/imigracao_pt_costa.csv` com **20 desembarques marítimos documentados** em Portugal Continental (Algarve e Setúbal, 2019–2024), a partir de registos públicos SEF/Frontex e comunicações da GNR/CP. Complementarmente, descarregou-se o **IOM Missing Migrants Project** (HDX, CC-BY 4.0) e filtraram-se incidentes **estritamente em águas marítimas** (função `ponto_em_mar`, caixa −11,0° a −7,38° W, 36,85° a 42,20° N — sem território continental nem águas espanholas). O campo de imigração combina **70 %** do KDE dos desembarques nacionais com **30 %** do KDE IOM marítimo (`campo_imigracao_combinado`), reforçando o sinal no Algarve onde se concentram as chegadas documentadas. Para o **tráfico de droga**, geocodificaram-se as apreensões de natureza
marítima ao nível do distrito costeiro.

Cada fonte é depois projetada para a grelha de procura comum (Secção 4.5). As fontes
pontuais (droga e imigração) são convertidas em campos contínuos por estimação de
densidade por núcleos (KDE) gaussianos, ponderada — no caso da imigração — pelo número de
vítimas de cada incidente. As grelhas de densidade de embarcações são amostradas em cada
célula, comprimidas logaritmicamente (a densidade de tráfego é fortemente assimétrica),
suavizadas espacialmente (um pesqueiro ou corredor é uma *área*, não um ponto) e
normalizadas de forma robusta por percentil. Deste modo, as quatro intensidades passam a
refletir padrões observados — e não pressupostos —, ficando o sistema original de núcleos
fundamentados disponível apenas como mecanismo de salvaguarda (*fallback*) caso as fontes
não estejam acessíveis.

Para o **tráfico de droga**, cada apreensão marítima geocodificada contribui para um KDE gaussiano com **peso temporal** exp(−0,15×Δanos), privilegiando padrões recentes sem descartar o histórico. Para a **pesca INN**, a densidade EMODnet de embarcações de pesca (75 %) combina-se com a **anomalia pesca/AIS** (25 %) — o rácio entre esforço de pesca e tráfego geral na célula, que realça pesqueiros com atividade desproporcionada.


### 3.5 Arquitectura do pipeline analítico

O fluxo de ponta a ponta do SAD resume-se ao esquema seguinte (Figura A — pipeline integrado):

```
Dados abertos  →  Processamento  →  Grelha marítima  →  Índice de risco  →  Validação  →  Mapa / plataforma
(EMODnet, IOM,     KDE, AHP,         1156 células        multi-ameaça         backtest +      decisão
 apreensões PT)    data mining      (só PT continental)  (4 ameaças)          baseline 2,06×   operacional
```

Cada etapa gera artefactos rastreáveis (`intensidades_reais.csv`, `resultados.json`, `validacao.json`,
`camadas_mapa.json`) consumidos pelo painel Folium e pela API FastAPI.

### 3.6 Decisões técnicas justificadas

| Decisão | Valor adotado | Justificação |
|---|---|---|
| Discretização espacial | **1156 células** (~10 km, apenas mar PT) | Resolução adequada à patrulha costeira sem explosão computacional; reprodutível via `geo.gerar_procura` |
| Classificação alto risco | Limiar **0,5** → **300 células** | Limiar interpretável e fixado *antes* do baseline de patrulha (mesmo N em todas as estratégias) |
| Ganho SAD vs aleatório | **2,06×** (IC95: 1,93–2,22) | Calibração empírica com bootstrap (500 réplicas) sobre captura de massa de risco |
| Bases MCLP (Q3) | **Porto + Portimão** | Cobertura de 100 % do risco alto com o mínimo de instalações (k=2) |
| Frota 24 h (Q2) | **9 / 11 AR5** | Com 5 ou 12 bases de lançamento (Tabela 6) |
| Dados AIS na plataforma | **Híbrido** (real + simulado) | AISStream quando há chave API; *fallback* automático com embarcações em células SAD para demonstração offline |

---

## 4. Pipeline de *data mining*

As Secções 4.1 a 4.5 descrevem o pipeline analítico — preparação e redução, *clustering*, classificação e agregação difusa do risco — que alimenta a otimização (Secção 5).


### 4.1 Preparação dos dados

A preparação dos dados é a fase mais trabalhosa e, simultaneamente, a mais determinante de
qualquer projeto de *data mining*, na medida em que vale o princípio de que dados de má
qualidade produzem necessariamente modelos de má qualidade (*garbage in, garbage out*). O
módulo de pré-processamento executa, por esta ordem, as seguintes operações. A **limpeza**
remove os registos desprovidos de data, substância ou quantidade — apenas dois em quase dez
mil —, harmoniza variantes textuais inconsistentes (designadamente a designação «Western
and Central Europe», normalizada para «West and Central Europe») e corrige gralhas
toponímicas detetadas por inspeção. O **tratamento de valores omissos** substitui as
quantidades em falta pela mediana da respetiva unidade — preferida à média por ser robusta a
*outliers* — e atribui o rótulo «Desc.» às regiões sem geocódigo. A **transformação**
deriva, a partir da data, o ano, o mês e a estação do ano, e converte todas as quantidades
para uma unidade comum (gramas), aplicando-lhes adicionalmente a transformação logarítmica
log(1 + g) para comprimir a forte assimetria positiva característica das apreensões, em que
um pequeno número de operações de grande dimensão coexiste com uma maioria de apreensões
modestas. A **discretização** reduz as 42 substâncias originais a sete grupos farmacológicos
e classifica as regiões em três faixas latitudinais (Norte, Centro, Sul). A **codificação**
converte as variáveis categóricas em representação binária (*one-hot*, com um indicador por
categoria) e normaliza as variáveis numéricas por padronização Z-score, *y′* = (*y* − *ȳ*)/*s*,
passo indispensável para os algoritmos sensíveis a distâncias. Finalmente, define-se a
variável-alvo binária `marítimo`, que assume o valor 1 quando o local de apreensão remete
para águas, porto ou águas internacionais, ou quando o modo de transporte é uma
embarcação.

A construção da variável-alvo mereceu cuidado particular para evitar **fuga de informação**
(*data leakage*; Kaufman, Rosset, Perlich, & Stitelman, 2012): excluíram-se dos atributos
preditores todas as variáveis que, direta ou indiretamente, codificassem a própria definição
de «marítimo» (designadamente o local físico e o modo de transporte), retendo-se apenas
atributos genuinamente antecedentes — o grupo de droga, a
quantidade, a região e os descritores temporais. Esta opção, embora penalize as métricas em
termos absolutos, assegura que o desempenho reportado reflete a verdadeira capacidade
preditiva do sistema num cenário real, e não um artefacto de contaminação.

### 4.2 Redução de dimensionalidade

A codificação *one-hot* das variáveis categóricas expande o espaço de atributos, tornando
pertinente uma análise da sua dimensão intrínseca por PCA. O resultado é, em si mesmo,
revelador: a primeira componente principal explica apenas 14,5 % da variância total e a
segunda 10,5 %, sendo necessárias dez componentes para acumular 80 % da variância (Figura 3;
Tabela B1, Anexo B). Esta dispersão da variância por muitas direções traduz uma elevada
dimensão intrínseca, consequência direta da natureza categórica e pouco correlacionada dos
atributos, e fornece uma justificação empírica para o recurso a modelos não lineares (como o
perceptrão multicamada) e para a preferência por métricas de avaliação robustas, dado que
nenhuma projeção de baixa dimensão captura adequadamente a estrutura dos dados.

---


### 4.3 Modelação descritiva: segmentação espacial por *clustering*


A primeira aplicação de *data mining* visa responder à questão Q1 — onde se concentra a
atividade ilícita — de forma independente do modelo de risco, conferindo-lhe validação
externa. Geocodificaram-se os registos ao nível do concelho ou distrito (operação que cobre
cerca de 83 % das observações), projetaram-se as coordenadas e aplicou-se *clustering* sobre
as apreensões do território continental.

A escolha do número de grupos apoiou-se conjuntamente no método do cotovelo e no coeficiente
de silhueta (Figura 4). A inércia decresce de forma acentuada até k = 4, ponto a partir do
qual os ganhos se tornam marginais, e o coeficiente de silhueta atinge o seu máximo
(**0,749**) precisamente em k = 4, convergência que fundamenta solidamente esta escolha. O
DBSCAN, aplicado como termo de comparação, identifica dez núcleos densos, refletindo a
existência de subconcentrações urbanas dentro das grandes regiões.

Aplicado especificamente às apreensões de natureza marítima, o k-médias define quatro zonas
de patrulha cuja distribuição é inequívoca (Tabela 2): o **Algarve** concentra 123
apreensões (53 % do total marítimo), o eixo **Setúbal–Lisboa** 87 (37 %) e a faixa
**Porto–Noroeste** 21 (9 %), restando um núcleo interior residual de 3 ocorrências. Os
centróides destas três zonas costeiras coincidem, com notável aproximação, com os máximos do
índice de risco (Secção 4.5), o que constitui a validação cruzada pretendida: dois
caminhos analíticos independentes — um assente na evidência institucional agregada das quatro
ameaças, outro na geometria empírica das apreensões — convergem para o mesmo retrato
espacial.

O *Fuzzy C-Means*, aplicado às mesmas observações, corrobora a robustez desta segmentação:
o coeficiente de partição difusa de **0,923** indica grupos bem separados, com a maioria das
observações a exibir um grau de pertença elevado ao seu cluster dominante (Figura 6). A
fuzzificação acrescenta, contudo, informação operacionalmente útil ao assinalar as
observações de fronteira — tipicamente situadas entre o Algarve e o Alentejo litoral —, cuja
afetação ambígua sugere a conveniência de uma cobertura sensorial contínua em vez de
fronteiras de patrulha rígidas.

**Tabela 2.** *Zonas de patrulha marítimas identificadas por k-médias (k = 4).*

| Zona | Centróide (lat, lon) | N.º de apreensões | Peso relativo |
|---|---|---|---|
| Algarve | (37,03 ; −7,93) | 123 | 53 % |
| Setúbal–Lisboa | (38,63 ; −8,93) | 87 | 37 % |
| Porto–Noroeste | (41,17 ; −8,55) | 21 | 9 % |
| Interior (residual) | (41,77 ; −6,74) | 3 | 1 % |

---


### 4.4 Modelação preditiva: deteção da natureza marítima das apreensões


A segunda aplicação responde à questão Q2: será possível, conhecidos apenas os atributos
antecedentes de uma apreensão, prever se esta é de natureza marítima? A resposta tem valor
operacional direto, pois a identificação dos determinantes da via marítima informa a
afetação do esforço de vigilância.

#### 4.4.1 Desenho experimental

O problema é de classificação binária fortemente desequilibrada: apenas **3,4 %** das
observações são marítimas. Este desequilíbrio condiciona todo o desenho experimental. Em
primeiro lugar, torna a exatidão global uma métrica enganadora — um classificador trivial que
nunca preveja «marítimo» atingiria cerca de 96,6 % de exatidão sem qualquer utilidade —, razão
pela qual se privilegiam a sensibilidade, a pontuação F1, a área sob a curva ROC (ROC-AUC) e,
muito em particular, a **área sob a curva precisão–sensibilidade (PR-AUC)**, que Davis e
Goadrich (2006) demonstram ser mais informativa do que a ROC-AUC quando a classe positiva é
rara; todas são complementadas pela inspeção direta das matrizes de confusão. Em segundo
lugar, motiva a aplicação de técnicas de reequilíbrio. Adotou-se o **SMOTE** (*Synthetic
Minority Over-sampling Technique*; Chawla, Bowyer, Hall, & Kegelmeyer, 2002), que gera
exemplos sintéticos da classe minoritária por interpolação entre vizinhos, em vez da simples
replicação. Crucialmente, o SMOTE foi **encapsulado num pipeline** (`ImbPipeline`) de modo a
ser reaplicado apenas nos folds de treino de cada partição da validação cruzada, evitando a
fuga de informação que resultaria de sobreamostrar antes de particionar; as árvores de decisão
recorrem, em alternativa, à ponderação de classes (`class_weight`).

Cada uma das quatro famílias de algoritmos foi avaliada em duas configurações: uma
**base**, com parâmetros por omissão, e uma **otimizada** por pesquisa exaustiva em grelha
(`GridSearchCV`) com validação cruzada estratificada de cinco folds, maximizando o F1. A
avaliação final faz-se sobre uma partição de teste estratificada (30 %), independente, e os
hiperparâmetros selecionados constam da Tabela B7 (Anexo B). Os atributos preditores são o
grupo de droga, a quantidade (logaritmizada), a região e os descritores temporais —
excluindo-se deliberadamente, como discutido na Secção 4.1, quaisquer variáveis que
codifiquem a definição do alvo.

#### 4.4.2 Análise comparativa por família de algoritmos

A Tabela 3 sintetiza o desempenho em teste e a Tabela B4 (Anexo B) os resultados da validação
cruzada das configurações otimizadas. A leitura conjunta revela um padrão pedagogicamente rico.

O **classificador de Bayes ingénuo** ilustra de forma paradigmática os perigos da classe rara
combinada com a violação do pressuposto de independência. Atinge uma sensibilidade de 0,98 —
deteta quase todas as apreensões marítimas —, mas a sua confiança positiva colapsa para 0,04,
inundando o decisor de falsos alarmes. A otimização do parâmetro de suavização eleva a sua
ROC-AUC de 0,87 para 0,90, mas a PR-AUC permanece modesta (0,44), e o F1 não ultrapassa 0,08.
A divergência entre uma ROC-AUC elevada e uma PR-AUC baixa é precisamente o fenómeno
antecipado por Davis e Goadrich (2006): a ROC-AUC, ao integrar sobre a taxa de falsos
positivos, mascara a dificuldade real de discriminação numa região de elevada sensibilidade
quando a classe positiva é rara.

Os **k-vizinhos mais próximos** beneficiam claramente da otimização: a seleção de cinco
vizinhos com ponderação pela distância eleva a pontuação F1 de 0,531 (base) para **0,592**
(otimizada), o melhor valor pontual em teste, sustentado por uma sensibilidade de 0,78 e uma
confiança positiva de 0,48. As **árvores de decisão** oferecem um caso de estudo instrutivo
sobre os limites da otimização: a procura em grelha, ao maximizar o F1, selecionou uma árvore
sem limite de profundidade que, embora atinja a maior confiança positiva (0,50), vê a sua
sensibilidade cair para 0,55 e, sobretudo, a sua capacidade de ordenação degradar-se
acentuadamente (ROC-AUC de 0,77 e PR-AUC de 0,36) — sintoma claro de sobreajuste. A árvore base,
mais rasa, generaliza melhor em termos de PR-AUC (0,55). A árvore conserva, em qualquer caso,
a vantagem decisiva da interpretabilidade: as suas regras são auditáveis e a análise de
importância dos atributos (Figura 12) identifica inequivocamente o grupo de droga, a
quantidade e a região como preditores dominantes, em coerência com o domínio.

O **perceptrão multicamada** revela-se o modelo mais equilibrado e robusto. Na sua configuração
otimizada (uma camada oculta de 64 neurónios), alcança simultaneamente a maior **ROC-AUC
(0,944)** e a maior **PR-AUC (0,674)** em teste, com uma sensibilidade de 0,80 — combinação que
nenhum outro modelo iguala. Esta superioridade confirma-se na validação cruzada, onde mantém a
maior ROC-AUC (**0,926 ± 0,022**) e a maior PR-AUC (**0,625 ± 0,069**), atestando uma
generalização estável. A sua capacidade de modelar interações não lineares entre atributos
compensa a elevada dimensão intrínseca evidenciada pela PCA. O custo é a opacidade: ao
contrário da árvore, o perceptrão não fornece regras explícitas, exigindo técnicas de
explicabilidade *post hoc* para a sua justificação.

**Tabela 3.** *Desempenho dos classificadores no conjunto de teste, em configuração base e
otimizada (F1 e AUC como extensão à nomenclatura da disciplina). Em negrito, os melhores
valores de cada métrica.*

| Modelo | Precisão/exatidão | Confiança positiva | Sensibilidade | F1 | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|
| Bayes (base) | 0,225 | 0,042 | **0,980** | 0,081 | 0,870 | 0,153 |
| Bayes (otim.) | 0,225 | 0,042 | **0,980** | 0,081 | 0,900 | 0,438 |
| k-vizinhos (base) | 0,950 | 0,394 | 0,812 | 0,531 | 0,912 | 0,522 |
| **k-vizinhos (otim.)** | 0,963 | 0,476 | 0,782 | **0,592** | 0,913 | 0,515 |
| Árvore (base) | 0,942 | 0,341 | 0,733 | 0,465 | 0,888 | 0,549 |
| Árvore (otim.) | **0,965** | **0,500** | 0,554 | 0,526 | 0,769 | 0,357 |
| MLP (base) | 0,950 | 0,389 | 0,802 | 0,524 | 0,921 | 0,673 |
| **MLP (otim.)** | 0,954 | 0,418 | 0,802 | 0,549 | **0,944** | **0,674** |

A divergência sistemática entre métricas — designadamente entre a ROC-AUC e a PR-AUC para o
Bayes, ou entre o F1 pontual (favorável aos k-vizinhos) e a discriminação global (favorável ao
perceptrão) — sublinha a importância de não fundamentar conclusões num único indicador nem numa
única partição. É a superioridade consistente do perceptrão nas métricas apropriadas a classes
raras (PR-AUC e ROC-AUC), tanto em teste como em validação cruzada, que justifica a sua escolha
como modelo recomendado.

O limiar de decisão do MLP não deve fixar-se em 0,5: treinado com SMOTE (50/50), o F1 máximo (~0,68) ocorre perto de 0,95 no conjunto de teste real (3,4 % marítimo). O SAD expõe a curva precisão–sensibilidade (Figura 11) para escolha consciente do ponto de operação face à assimetria de custos.

---


### 4.5 Agregação difusa do risco multi-ameaça


Identificadas as zonas de concentração e os determinantes da via marítima, importa sintetizar
as quatro ameaças num único **índice de risco** georreferenciado que sirva de procura ao modelo
de otimização. O território marítimo foi discretizado numa grelha de **1156 células** de
aproximadamente 95 km² cada. Para cada célula, computou-se a intensidade de cada ameaça (num
intervalo de 0 a 1) a partir das **fontes de dados reais** descritas na Secção 3.4 — densidade
de embarcações do EMODnet para a pesca e a poluição, e estimação de densidade por núcleos
sobre desembarques documentados em PT, incidentes IOM em mar e apreensões marítimas para a imigração
e o tráfico —, e combinaram-se as quatro intensidades por duas vias metodologicamente
distintas.


#### Justificação dos pesos por AHP (Processo de Hierarquia Analítica)

Os pesos da média ponderada não foram escolhidos arbitrariamente: aplicámos o **AHP** (Saaty, 1980)
aos quatro critérios — droga, pesca, poluição e imigração — com comparações par-a-par calibradas
para vigilância costeira de **Portugal Continental** (`dm/ahp_pesos.py`). A matriz resultante dá
**0,38 / 0,24 / 0,19 / 0,19** com **razão de consistência 0,0002** (bem abaixo do limiar de 0,10).
Arredondámos para **0,35 / 0,25 / 0,20 / 0,20** no `config.py` por legibilidade operacional; a
diferença máxima é 0,02 e uma sensibilidade ±10 % mantém o n.º de células alto risco entre 276 e 297
(Figura 24; `resultados/ahp_pesos.json`), sem alterar a hierarquia espacial nem o par MCLP.

A primeira via é uma **média ponderada**, com pesos de 0,35 para o tráfico de droga, 0,25 para a
pesca ilegal e 0,20 para cada uma das restantes ameaças — ponderação que reflete a maior
disponibilidade e fiabilidade da evidência relativa ao tráfico. A segunda via é um **sistema de
inferência difusa** de tipo Mamdani, no qual as quatro intensidades são fuzzificadas em termos
linguísticos (baixo, médio, alto) por funções de pertença triangulares, combinadas por uma base
de dez regras SE–ENTÃO que codificam o conhecimento operacional (por exemplo, «se a intensidade
de droga é alta E a de imigração é alta, então o risco é muito alto»), e desfuzzificadas pelo
método do centróide (Figura 14).

A comparação entre as duas vias é instrutiva (Figura 15). Os dois índices estão fortemente
correlacionados (coeficiente de Pearson de **0,76**), o que confere confiança à robustez do
mapa de risco face à escolha do método de agregação. Contudo, o índice difuso é
sistematicamente mais **precaucionário**: ao aplicar a lógica de que a coincidência de várias
ameaças numa mesma célula eleva desproporcionadamente o risco — um efeito de conjunção que a
média ponderada dilui —, o sistema difuso classifica como de alto risco uma área
substancialmente maior (682 células contra as 300 da média ponderada), elevando
correspondentemente a frota estimada (cerca de 27 contra 11 aeronaves). Ambos os mapas
preservam, todavia, a mesma hierarquia espacial, com primazia inequívoca do quadrante
sul/sudoeste. A escolha entre as duas agregações é, em rigor, uma decisão de postura: a média
ponderada corresponde a um planeamento de esforço médio, enquanto a agregação difusa
corresponde a uma postura conservadora que dimensiona para o pior caso de coincidência de
ameaças. No que se segue, adota-se a média ponderada como cenário de referência, reservando-se
o índice difuso como majorante prudencial.

---

## 5. Otimização: localização de bases, dimensionamento da frota e sensibilidade


### 5.1 Cobertura de risco e a falácia do raio fixo

A questão Q3 — alcance *versus* cobertura sensorial — é respondida de forma cristalina pela
análise de cobertura. Replicando o pressuposto do estudo de referência, com um raio operacional
de 90 km, e resolvendo o problema de cobertura máxima sobre o conjunto de doze aeródromos
candidatos, obtém-se um resultado contundente: **mesmo selecionando todas as doze bases
disponíveis, apenas 66,8 % do risco total fica coberto** (Tabela B2, Anexo B). Sob este
paradigma, 31 das 274 células de alto risco situadas mais ao largo permanecem
estruturalmente fora de alcance (Tabela B3) — e a situação agrava-se com vento desfavorável, subindo as
não cobríveis para 58 (vento moderado) e 100 (vento forte), à medida que o raio efetivo
se contrai para 76,5 km e 63 km, respetivamente. A conclusão é inequívoca: o raio de 90 km não é
uma propriedade da aeronave, mas uma restrição autoimposta pelo estudo anterior, e é ela, e não
a capacidade do AR5, que limita a cobertura.

Quando se substitui esse raio pela **autonomia real** da aeronave — que, descontando o trânsito
e mantendo uma reserva prudente, permite um raio de alcance da ordem dos 450 a 650 km —, o quadro
inverte-se por completo. Uma única base bem posicionada passa a alcançar a totalidade das 300
células de alto risco, e o problema de cobertura deixa de ser sobre *se* é possível cobrir o risco, para
passar a ser sobre *como* o cobrir de forma persistente e eficiente. A Figura 17 contrasta
visualmente os dois paradigmas.

### 5.2 Dimensionamento para vigilância persistente

A cobertura de alcance é condição necessária mas não suficiente: que uma aeronave *chegue* a uma
célula não significa que o seu sensor a *observe com a frequência requerida*. Esta distinção
entre alcance e **cobertura sensorial persistente** é o cerne do modelo de dimensionamento. Uma
aeronave em órbita observa, a cada instante, apenas uma faixa de largura útil limitada (estimada
em 30 km para o sensor EO/IR em condições típicas). O número de aeronaves que têm de estar
simultaneamente no ar (*n*ₛᵢₘ), o multiplicador de rotação que sustenta a presença durante 24 horas
(*M*) e a frota total (*N*) obtêm-se por:

*n*ₛᵢₘ = ⌈ A / (V · W · T) ⌉

*M* = (24 / *t*ₒₙ) / *D*

*N* = ⌈ *n*ₛᵢₘ · *M* · 1,1 ⌉

onde *A* é a área a cobrir, *V* a velocidade de patrulha do UAV, *W* a largura útil do sensor, *T* o
período máximo de revisita, *t*ₒₙ o tempo de estação efetivo por sortida e *D* a disponibilidade
operacional da frota (fixada em 0,70 para acomodar manutenção e indisponibilidades); a margem de
10 % cobre imprevistos operacionais.

A aplicação deste modelo à área total de alto risco (28 494 km²), com a **rede completa de doze
bases** seleccionada pelo trade-off de frota (Secção 5.3), conduz a **4 aeronaves simultâneas**
e a uma **frota total de 11 AR5**, com distância média ao ponto de patrulha de 55,9 km e tempo
de estação de 13,9 h por sortida. Restringindo o esforço à faixa costeira mais densa (25 075 km²,
alcançável a 90 km a partir de **cinco bases** — Santa Cruz, Cascais, Sines, Portimão e Faro),
bastam **3 aeronaves simultâneas** e uma **frota de 9 AR5**.

Importa não confundir este resultado com o do MCLP a duas bases (Porto + Portimão): essa
configuração cobre igualmente 100 % do risco, mas os trânsitos mais longos elevam a frota
necessária para **13 AR5** (Tabela B5). Por isso distinguimos, ao longo do relatório, a
**localização mínima** (Q3) do **dimensionamento de frota** (Q2).

### 5.3 O número ótimo de bases

A análise da frota total em função do número de bases (Tabela B5, Anexo B; Figura 18) mostra dois
resultados que convém separar. Do ponto de vista do **MCLP** — «qual o mínimo de instalações que
cobre o risco?» — **duas bases** (Porto e Portimão) bastam para alcançar praticamente a
totalidade das 300 células de alto risco. Do ponto de vista do **dimensionamento de frota** —
«quantas aeronaves para 24 h?» — a curva tem um mínimo nítido com **doze bases**: a distância
média cai para 55,9 km, o tempo de estação sobe para 13,9 h e a frota fixa-se em **11 AR5**.

Com uma única base (Montijo), os trânsitos consomem demasiada autonomia (distância média 120 km,
frota **12 AR5**). Entre **duas e onze bases** a frota permanece em **13 AR5** — Porto e
Portimão cobrem o risco, mas não encurtam o trânsito o suficiente para reduzir rotações. Só com
a rede completa (k = 12) se atinge o ótimo de frota. A Tabela 6 resume as configurações que
recomendamos para o emprego operacional.

**Tabela 6.** *Configurações de emprego recomendadas (cenário de média ponderada).*

| Configuração | Área (km²) | Bases de lançamento (dimensionamento frota) | Aeronaves simultâneas | Frota total (24 h) |
|---|---|---|---|---|
| Faixa costeira | 25 075 | Santa Cruz, Cascais, Sines, Portimão, Faro | 3 | ≈ 9 AR5 |
| Área total de alto risco | 28 494 | Rede completa (12 aeródromos costeiros) | 4 | ≈ 11 AR5 |
| MCLP mínimo (referência Q3) | 28 494 | Porto (Sá Carneiro) + Portimão | 4 | ≈ 13 AR5 |

A última linha não é a configuração de emprego recomendada, mas explicita o que acontece se se
optar pelo par MCLP sem reforço de bases intermédias: cobre-se o risco, mas a frota sobe.

---


### 5.4 Análise de sensibilidade


Dado que alguns parâmetros do modelo de dimensionamento são estimativas (designadamente a largura
útil do sensor, o período de revisita e a disponibilidade), aferiu-se a robustez da
recomendação variando-os isoladamente em torno do cenário de referência de 11 aeronaves (Figura
19; Tabela B6, Anexo B). A frota mostra-se mais sensível à **largura útil do sensor** e ao
**período de revisita**: alargar o sensor de 30 para 50 km, ou relaxar a revisita de 3 para 6
horas, reduz a frota de 11 para 6 aeronaves; inversamente, exigências mais estritas (sensor de 20
km ou revisita de 2 horas) elevam-na para 14. A **disponibilidade operacional** tem um efeito mais
moderado, fazendo variar a frota entre **13** (disponibilidade de 0,60) e **9** (disponibilidade de
0,90). Estes resultados têm uma leitura de apoio à decisão direta: o investimento que mais reduz
o efetivo necessário não é a aquisição de mais aeronaves, mas a melhoria da capacidade sensorial
de cada uma (sensores de maior alcance útil) e dos processos de manutenção que sustentam a
disponibilidade. A recomendação de 11 aeronaves (área total de alto risco) é, em qualquer caso, estável dentro de uma banda
plausível de parâmetros, o que lhe confere credibilidade para efeitos de planeamento.

---

## 6. Painel geoespacial interativo e plataforma operacional


Um Sistema de Apoio à Decisão só cumpre verdadeiramente a sua função quando o conhecimento que
produz chega ao decisor numa forma diretamente interpretável e acionável. Por isso, para além das
figuras estáticas que documentam a análise, o sistema materializa-se num **painel geoespacial
interativo** (ficheiro `resultados/mapa_interativo.html`), construído sobre a biblioteca *Folium*
— uma interface Python para a *framework* cartográfica *Leaflet.js* — que projeta todos os
produtos analíticos sobre uma carta náutica real e navegável (Figura 20). Esta opção responde a
uma das principais boas práticas de visualização em SAD: a informação deve ser apresentada num
suporte que o operador reconheça e manipule, com possibilidade de ampliação, medição de distâncias
e ativação seletiva de camadas, em vez de imagens fixas descontextualizadas.

O painel organiza-se em **camadas sobreponíveis e comutáveis** pelo utilizador, integrando
dados de risco, **tráfego AIS** e **incidentes reais**:

1. **Risco agregado** — mapa de calor do índice multi-ameaça e detalhe por célula (popup com
   decomposição droga/pesca/poluição/imigração).
2. **Tráfego AIS (EMODnet)** — densidade de embarcações e corredores de rotas marítimas derivados
   do AIS agregado (camadas `vesseldensity_all` e `routedensity_all`), alinhadas com a capacidade
   sensorial do AR5 (recetor AIS integrado).
3. **Incidentes reais** — **20 desembarques marítimos** documentados em Portugal Continental
   (Algarve/Setúbal, 2019–2024) e 187 apreensões marítimas recentes (2020+), geocodificadas,
   sobrepostos ao mapa de risco (sem incidentes IOM em mar PT após filtro rigoroso).
4. **Infraestrutura operacional** — doze aeródromos candidatos, **duas bases recomendadas** (Porto e
   Portimão) com raios tático (90 km) e operacional AR5, e **seis setores de patrulha** (*k*-médias).

Um **painel lateral** resume as respostas ao objetivo (onde, quantos, quais bases) e as métricas de
validação (backtesting temporal e ganho face a patrulha aleatória). O painel inclui carta náutica
(OpenSeaMap), controlo de camadas, medição em km/milhas náuticas, mini-mapa e ecrã inteiro (Figura 20).

O valor deste artefacto é duplo. Do ponto de vista operacional, transforma um relatório analítico
num **instrumento de planeamento de missão** que um Centro de Coordenação pode usar para situar
visualmente o risco, as bases e os setores, e medir distâncias de projeção em tempo real. Do ponto
de vista metodológico, fecha a cadeia *dados → informação → conhecimento → ação*, ao colocar o
conhecimento extraído pelas técnicas de *data mining* e otimização sobre o mesmo referencial
geográfico em que a decisão é efetivamente tomada.

### 6.1 Plataforma operacional quase em tempo real

Para fechar o ciclo **dados → informação → conhecimento → ação**, desenvolveu-se uma **plataforma
web** (`plataforma/`) que consome os mesmos produtos analíticos do pipeline (`resultados.json`,
`validacao.json`, `camadas_mapa.json`, grelha SAD) e expõe capacidades operacionais em tempo
quase em tempo real:

| Módulo | Função | Ligação ao relatório |
|--------|--------|----------------------|
| Meteo (Open-Meteo) | Vento por base; impacto no alcance AR5 | Secção 5, Secção 5.4; `fator_vento` |
| Mapa de risco | Células multi-ameaça (filtro mar) | Secção 4.5, Fig. 16 |
| Camadas IOM + apreensões | Dados reais sobre o mapa | Sec. 3, 11; `camadas_mapa.json` |
| Rotas OR-Tools | Sortie N→S, plano 24 h (6 sectores), reativo | Secção 5, Q1/Q2/Q3 |
| Cenários pré-definidos | 7 missões alinhadas ao relatório | Secção 7.1, Tabela 7 |
| Bases militares | FAP/Marinha/Exército ≤ 20 km costa | Secção 5, MCLP |
| WebSocket | Alertas meteo, AIS, IPMA, RSS | Apoio à decisão dinâmica |
| Exportação plano missão | GeoJSON/CSV da rota e sectores | Sec. 6.2; `/api/export/*` |

A meteorologia **condiciona diretamente** o planeamento: cada rota calcula vento efetivo
(estação Open-Meteo mais próxima do sector), **fator de redução de alcance**, autonomia útil e
viabilidade operacional (limiar 18 m/s). O plano 24 h atribui vento **por sector costeiro**,
reflectindo a variabilidade ao longo do litoral.

O procedimento de arranque da plataforma (instalação de dependências e lançamento dos serviços) está descrito no **Anexo C — Reprodução computacional e arranque da plataforma**.

A plataforma não substitui o painel Folium (útil para relatório e *briefing* estático); **complementa-o**
com ingestão periódica (~2 min), simulação de alertas e cálculo interativo de rotas — ponte entre
o modelo analítico e o centro de coordenação.

A plataforma consome `resultados.json`, `validacao.json` e `camadas_mapa.json`, permitindo exercitar cenários com meteo live, rotas OR-Tools e alertas WebSocket. Confirma visualmente Q1–Q3 (setores de risco, bases MCLP, ganho **2,06×**), demonstra o impacto do vento no alcance e suporta a apresentação oral via cenários pré-definidos (Figura 23). Modo demonstração AIS ativa-se automaticamente sem chave API.

---

## 7. Validação

A validação do SAD combina confrontação qualitativa com cenários representativos (Secção 7.1) e métricas quantitativas de backtesting temporal e baseline de patrulha (Secções 7.2–7.4).

### 7.1 Validação por estudo de caso


A validação de um modelo de risco não se esgota na sua coerência interna; exige confrontá-lo com a
realidade que pretende descrever. À falta de um registo público georreferenciado e exaustivo de
interceções, recorre-se a uma estratégia de validação por **estudo de caso sobre cenários
representativos**, ancorados em padrões de ocorrência reais e documentados em fontes abertas (cf.
Secção 3.2), à semelhança da prática consagrada na validação de sistemas de apoio à decisão
marítima. O procedimento é direto: para cada cenário, introduzem-se as suas coordenadas no SAD e
verifica-se (i) se o índice de risco as classifica, *a priori*, como zona de elevado risco, e (ii)
qual a base recomendada e a distância de projeção que o sistema lhe associa. Os quatro cenários
cobrem deliberadamente as quatro ameaças e as principais geografias de ameaça identificadas.

O **primeiro cenário** reproduz a aproximação atlântica de cocaína a sudoeste do Cabo de São
Vicente, o padrão associado às interceções coordenadas pelo MAOC-N e à deteção de embarcações
semissubmersíveis nas aproximações marítimas portuguesas (Europol, 2025). Introduzidas as coordenadas
(36,8 °N; 9,3 °W), o SAD devolve um índice de risco de **0,59** — acima do limiar de alto risco
(0,5) —, dominado pelas componentes de droga (0,74) e de poluição (0,60, refletindo a coincidência
com o dispositivo de separação de tráfego), com a base de **Portimão a 73 km** a assegurar a
cobertura. O **segundo cenário** representa a entrada de haxixe pelas aproximações marítimas do
Algarve oriental (37,05 °N; 8,40 °W): risco **0,52**, dominado pela componente de droga (0,87),
com **Portimão a 19 km** como base de projeção mais próxima. O **terceiro cenário**, de imigração
irregular por desembarque no Algarve (37,02 °N; 7,88 °W) — padrão documentado em `imigracao_pt_costa.csv` —
regista risco elevado, com contributo dominante da componente de imigração e **Portimão** como base
de projeção mais próxima. O **quarto cenário**, de pesca ilegal nos
pesqueiros do noroeste (42,05 °N; 9,20 °W), ilustra com igual nitidez o comportamento discriminante
do modelo: o risco agregado é moderado (**0,33**), mas a sua decomposição revela uma componente de
pesca quase máxima (1,00) e componentes de droga, poluição e imigração baixas — exatamente o perfil
esperado de uma zona de pesqueiro afastada das rotas de tráfico —, com a base do **Porto a 99 km**.

Em todos os cenários, a localização documentada da ameaça é corretamente classificada pelo sistema
no escalão de risco que lhe corresponderia *a priori*, e a configuração de duas bases recomendada
projeta cobertura sobre todos eles. Acresce que a decomposição por ameaça (Tabela 7) é
substantivamente plausível em cada caso, o que confere ao índice não apenas validade preditiva mas
também **transparência diagnóstica**: o operador não recebe um número opaco, mas a explicação de
*porque* uma dada área é de risco. Esta concordância entre o output do SAD e os padrões reais de
ameaça constitui a validação externa pretendida, complementando a validação cruzada interna já
estabelecida pela convergência entre o *clustering* e o mapa de risco (Secção 4.3).

**Tabela 7.** *Validação por estudo de caso: resposta do SAD a quatro cenários documentados.*

| Cenário (ameaça dominante) | Coordenadas | Risco | Droga / Pesca / Poluição / Imigração | Base recomendada (distância) |
|---|---|---|---|---|
| Cocaína — aproximação SW (C. S. Vicente) | 36,8 °N; 9,3 °W | 0,59 | 0,74 / 0,35 / 0,60 / 0,01 | Portimão (73 km) |
| Haxixe — ao largo do Algarve | 37,05 °N; 8,40 °W | 0,52 | 0,87 / 0,13 / 0,25 / 0,01 | Portimão (19 km) |
| Imigração — desembarque Algarve (SEF/Frontex) | 37,02 °N; 7,88 °W | ≥ 0,50 | — / — / — / alto | Portimão (< 30 km) |
| Pesca INN — pesqueiros do noroeste | 42,05 °N; 9,20 °W | 0,33 | 0,06 / 1,00 / 0,12 / 0,01 | Porto (99 km) |

---



Para além da validação qualitativa por estudo de caso, o sistema foi submetido a dois testes
quantitativos que respondem diretamente à pergunta «os resultados estão de acordo com o objetivo?»:
um **backtesting temporal** sobre apreensões marítimas e uma **comparação com baselines** de
patrulha.

### 7.2 Backtesting temporal (apreensões 2011–2022 → teste 2023–2024)

O campo de risco relativo ao tráfico de droga foi reconstruído usando apenas apreensões marítimas
até **2022**; as camadas de pesca, poluição e imigração mantêm-se estáticas (EMODnet, desembarques
PT) — uma limitação que explicitamos na Secção 8.2. As **55 apreensões marítimas de 2023–2024**
(holdout) foram geocodificadas e confrontadas com o mapa de risco treinado.
Os resultados (Figura 21; Tabela 8) mostram que:

- **85,5 %** das apreensões do holdout caem no **top 20 %** de risco (mais de 4× a referência de 20 %);
- o risco médio nas localizações do holdout (**0,72**) excede claramente o risco médio global (**0,38**);
- ao limiar fixo de 0,5, a taxa de acerto (**85,5 %**) supera o baseline aleatório (**36,6 %**) em **2,33×**.

O top 20 % e o limiar 0,5 coincidem neste holdout (47 em 55 apreensões) — o que é coerente com a
concentração do tráfico no Algarve e no eixo Setúbal–Lisboa. A geocodificação ao nível do distrito
(Secção 8.2) dilui o sinal no limiar absoluto em outros contextos, mas aqui preserva a ordenação
relativa.

### 7.3 Baseline de patrulha (SAD vs aleatório vs uniforme)

Fixado o mesmo número de células patrulhadas (**300**, igual ao n.º de células de alto risco), comparou-se
a **captura de risco** (fração do risco total coberta) entre três estratégias (Figura 22; Tabela 8):

| Estratégia | % do risco capturado | Ganho vs aleatório |
|---|---|---|
| **SAD** (top-N por risco) | **53,6 %** | **2,06×** (IC95: 1,93–2,22) |
| Aleatório (média de 500 simulações) | 26,0 ± 0,9 % | 1,0× |
| Uniforme costeiro (espaçamento regular) | 32,5 % | 1,65× |

O SAD concentra mais de **duas vezes** o risco que uma patrulha aleatória ou uniforme com o mesmo
esforço — evidência quantitativa de que a otimização por risco multi-ameaça real (AIS + IOM +
apreensões) produz ganhos operacionais mensuráveis.

### 7.4 Caixas de resposta ao objetivo

**Tabela 8.** *Síntese de validação quantitativa e respostas operacionais.*

| Questão | Resposta do SAD | Evidência |
|---|---|---|
| **Q1 — Onde patrulhar?** | Sul/SW (Algarve), Lisboa–Setúbal, NW/Peniche; corredores AIS a O de Lisboa | Clustering + mapa AIS + estudo de caso (Tabelas 2, 7) |
| **Q2 — Quantos drones (24 h)?** | **11 AR5** (4 simultâneos) área total; **9 AR5** (3 simultâneos) faixa costeira | Dimensionamento persistente com 12 ou 5 bases (Secção 5.2; Tabela 6) |
| **Q3 — Quais bases?** | **Porto (Sá Carneiro) + Portimão** — MCLP k=2, 100 % do risco | Localização mínima (Secção 5.3); frota com só estas bases: 13 AR5 |
| **Validação** | Holdout 2023–24: 85.5 % acima limiar 0,5; imigração: 70 % desembarques em zona alto risco; patrulha SAD 2.06× vs aleatória | Figuras 21–24; `validacao.json` |

---


### 7.5 Validação da camada de imigração (Portugal Continental)

Para a ameaça com menor densidade de registos públicos georreferenciados, aplicou-se um teste
específico sobre os **20 desembarques marítimos** do ficheiro `imigracao_pt_costa.csv`.
**70 %** dos eventos caem em células com intensidade de imigração ≥ 0,5
(risco médio nos eventos: **0.68**), confirmando que o KDE combinado
(SEF/Frontex/CP + IOM mar) captura o corredor algarvio documentado. O âmbito é estritamente **Portugal
Continental** — Açores, Madeira e águas espanholas estão excluídos. Complementarmente, um **holdout temporal** (treino ≤ 2022, teste n = 8) atribui **100 %** dos desembarques 2023–2024 ao terço superior do campo KDE treinado (limiar 0.01), reduzindo circularidade.


### 7.6 Leitura crítica das métricas

Esta subsecção explicita **o que cada número prova** e **onde termina a evidência**, em linha com
a exigência de rigor de um SAD de mestrado.

**Dois mapas de risco distintos.** O mapa **operacional** classifica **300** células
como alto risco (limiar 0,5; todas as fontes). O mapa de **treino do backtest** (droga temporal ≤ 2022
+ camadas estáticas) regista **423** células ≥ 0,5 —
a diferença reflecte o reforço imigração/EMODnet no produto final, não um erro de pipeline.

**Ganho ~2.06× na patrulha.** Com **300** células patrulhadas
(25.9 % da grelha), o SAD captura **53.6 %** da massa total de risco
frente a **26.0 %** de uma patrulha aleatória com o mesmo esforço.
O índice de Gini (**0.400**) confirma concentração espacial: o ganho mede sobretudo
**priorização** de risco, não deteção garantida de eventos futuros.

**Contraste droga isolada vs SAD completo.** O backtest usando **apenas** o campo de droga temporal (top 20 % = 232 células) atinge **0.0 %** no holdout (baseline 20.3 %), enquanto o mapa multi-ameaça atinge **85.5 %**. Isto demonstra que a integração de pesca/poluição/imigração **não é decorativa** — é o que permite ao SAD priorizar zonas onde as apreensões recentes efetivamente ocorrem.

**Sensibilidade ao limiar (Figura 25).** Variar o limiar a 0,45 / 0,50 / 0,55 altera o n.º de células alto risco
de 328 / 300 / 256
e o ganho SAD para 2,01× / **2,07×** / 2,15× —
a ordem de grandeza da frota (9–11 AR5) e o par MCLP Porto + Portimão mantêm-se.

**Tabela 9.** *Síntese da leitura crítica.*

| Métrica | Valor | O que prova | Limite |
|---|---|---|---|
| Backtest multi-ameaça | 85.5 % (n=55) | Apreensões recentes em zonas já prioritárias | Geocódigo administrativo |
| Backtest só droga | 0.0 % (top 20 %) | Camada isolada insuficiente | Reforça papel EMODnet/imigração |
| Ganho patrulha | 2.06× (IC95 1,93–2,22) | Priorização de massa de risco | Esforço fixo em N células |
| Imigração (total) | 70 % em zona ≥ 0,5 | Coerência regional Algarve | n = 20 eventos |
| Imigração holdout | 100 % (teste n=8) | KDE treinado sem eventos futuros | Amostra pequena |

Em síntese: os valores são **coerentes e defensáveis**; o contributo do SAD é tornar explícitos os
compromissos entre concentração de risco, esforço de patrulha e incerteza das fontes.

## 8. Discussão, limitações e recomendação

### 8.1 Discussão das questões de investigação

**Q1 — Onde?** Índice de risco e *clustering* convergem para Algarve e eixo Setúbal–Lisboa (correlação ponderado/difuso 0,76).

**Q2 — Previsão marítima?** O MLP com SMOTE atinge ROC-AUC 0,93 ± 0,02; PR-AUC privilegia a avaliação em classe rara.

**Q3 — Alcance ou sensor?** Com raio fixo 90 km cobrem-se 66,8 % do risco; com autonomia AR5 o constrangimento passa a ser **revisita sensorial** (Secção 5).

**Q4 — Frota e bases?** **Porto + Portimão** respondem ao MCLP (cobertura mínima); **9–11 AR5**
para 24 h assumem rede costeira distribuída (Tabela 6); índice difuso como majorante prudencial
(~27 AR5).

O SAD quantifica o compromisso entre cobertura, custo e risco residual sem impor a postura de comando.

---


### 8.2 Limitações e ameaças à validade


- **Fontes *proxy*:** EMODnet mede atividade AIS, não ilegalidade directa; imigração assenta em 20 desembarques PT + IOM filtrado.
- **Geocodificação administrativa:** ~83 % das apreensões; dilui sinal no limiar absoluto (Secção 7.6).
- **Backtest temporal parcial:** só a droga é cortada em 2022; pesca, poluição e imigração entram com campo estático — possível optimismo no holdout multi-ameaça.
- **Pesos AHP:** rastreáveis mas dependentes de juízos de especialista (Secção 4.5); valores adoptados arredondados dos pesos AHP.
- **Parâmetros sensoriais:** largura útil, revisita e disponibilidade são estimativas (sensibilidade Secção 5.4).
- **Cobertura idealizada:** não modela nebulosidade, mar agitado nem sazonalidade fina.
- **Classificação:** desequilíbrio 3,4 % marítimo limita precisão da classe minoritária.
- **Índice offline vs. plataforma:** risco estratégico estático; protótipo tático não recalcula o mapa em tempo real.
- **Validação externa:** estudo de caso e backtest não substituem interceções subquilométricas.

O reconhecimento destas limitações não invalida as conclusões — designadamente a demonstração de que
o constrangimento do sistema é a cobertura sensorial e não o alcance, que é robusta a todas elas —,
mas delimita com honestidade o âmbito em que devem ser interpretadas e orienta o aperfeiçoamento
futuro do sistema.

---


### 8.3 Recomendação final


À luz da análise, recomenda-se a seguinte arquitectura de emprego para o AR5 na vigilância costeira
de Portugal Continental. Em síntese: **dois polos MCLP — Porto (Sá Carneiro) e Portimão — cobrem
100 % do risco alto; para operação persistente 24 h, dimensionar 9 AR5 na faixa costeira (cinco
bases de lançamento) ou 11 AR5 na área total (rede de doze aeródromos).**

Como **configuração de referência**, propõe-se a operação com **rede completa e frota de 11 AR5**,
assegurando revisita persistente das 300 células de alto risco (margem operacional de 10 %).
Os polos Porto + Portimão mantêm-se como **hubs principais** mesmo quando se usam bases
intermédias para encurtar trânsitos. Como **configuração de contingência ou de arranque faseado**,
em caso de restrição orçamental, concentra-se o esforço na **faixa costeira com 9 AR5**,
aceitando descobrir a franja mais ao largo. Para missões de elevada criticidade, o **índice difuso**
funciona como majorante prudencial (~27 AR5).

A decisão entre estas configurações é, em última análise, uma decisão de comando que deve ponderar
explicitamente o orçamento disponível, a aceitação de risco residual e o nível de ameaça
prevalecente. O contributo do SAD é tornar cada uma destas opções transparente e quantificada.

---

## 9. Conclusão e trabalho futuro


O presente trabalho concretizou um Sistema de Apoio à Decisão completo para a vigilância costeira
de Portugal Continental com o UAV TEKEVER AR5, integrando um pipeline de *data mining* com um
modelo de otimização. Da análise resultaram três contributos principais. Primeiro, a confirmação,
por dois métodos independentes, de que a atividade ilícita marítima se concentra no sul e
sudoeste do país, o que confere validação externa ao mapa de risco. Segundo, a demonstração de
que a natureza marítima de uma apreensão é previsível com boa discriminação (ROC-AUC de 0,93 em
validação cruzada para o perceptrão multicamada), num exercício que ilustra de forma exemplar os
desafios da classe rara e a inadequação da exatidão como métrica. Terceiro, e talvez o mais
relevante para a doutrina operacional, a evidência quantitativa de que o paradigma de raio fixo de
90 km do estudo anterior subestima grosseiramente a capacidade do sistema: explorada a autonomia
real do AR5, o constrangimento deixa de ser o alcance e passa a ser a cobertura sensorial
persistente, que duas bases e nove aeronaves asseguram para a totalidade do risco.

Identificam-se as seguintes linhas de trabalho futuro. Em primeiro lugar, aprofundar a integração de fontes operacionais já iniciadas — EMODnet, **20 desembarques marítimos em Portugal Continental** (SEF/Frontex/CP) e IOM em mar — incorporando esforço de pesca do Global Fishing Watch validado contra infrações conhecidas e deteções CleanSeaNet da EMSA, de modo a distinguir atividade lícita de ilegal e derrames efetivos de simples risco. Em segundo lugar, generalizar o modelo de otimização de objetivo único para uma formulação **multi-objetivo**, gerando uma fronteira de Pareto entre risco coberto e número de aeronaves. Em terceiro lugar, validação contra interceções georreferenciadas com precisão subquilométrica e aprendizagem contínua (ciclo Medir–Analisar–Agir fechado). Por fim, endurecer a ligação entre o índice estratégico offline e a plataforma tática, com recálculo periódico automatizado do risco.

---

## 10. Referências


Bezdek, J. C. (1981). *Pattern recognition with fuzzy objective function algorithms*. Plenum Press.

Breiman, L., Friedman, J. H., Olshen, R. A., & Stone, C. J. (1984). *Classification and regression trees*. Wadsworth.

Chawla, N. V., Bowyer, K. W., Hall, L. O., & Kegelmeyer, W. P. (2002). SMOTE: Synthetic minority over-sampling technique. *Journal of Artificial Intelligence Research, 16*, 321–357. https://doi.org/10.1613/jair.953

Church, R., & ReVelle, C. (1974). The maximal covering location problem. *Papers in Regional Science, 32*(1), 101–118. https://doi.org/10.1111/j.1435-5597.1974.tb00902.x

Cover, T., & Hart, P. (1967). Nearest neighbor pattern classification. *IEEE Transactions on Information Theory, 13*(1), 21–27. https://doi.org/10.1109/TIT.1967.1053964

Davis, J., & Goadrich, M. (2006). The relationship between precision-recall and ROC curves. In *Proceedings of the 23rd International Conference on Machine Learning* (pp. 233–240). ACM. https://doi.org/10.1145/1143844.1143874

Ester, M., Kriegel, H.-P., Sander, J., & Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. In *Proceedings of the 2nd International Conference on Knowledge Discovery and Data Mining* (pp. 226–231). AAAI Press.

European Fisheries Control Agency. (2024). *Annual report 2023*. EFCA.

European Maritime Safety Agency. (2024). *CleanSeaNet service: Annual overview*. EMSA.

European Marine Observation and Data Network. (2025). *EMODnet Human Activities: Vessel density maps* [conjunto de dados]. Serviço Web Coverage Service. https://emodnet.ec.europa.eu/en/human-activities

Europol. (2025). *EU drug markets analysis: Maritime cocaine trafficking*. Publications Office of the European Union.

Fayyad, U., Piatetsky-Shapiro, G., & Smyth, P. (1996). From data mining to knowledge discovery in databases. *AI Magazine, 17*(3), 37–54. https://doi.org/10.1609/aimag.v17i3.1230

Frontex. (2025). *Risk analysis for 2024–2025*. European Border and Coast Guard Agency.

Global Fishing Watch. (2025). *Global AIS-based apparent fishing effort dataset* (version 3.0) [conjunto de dados]. https://doi.org/10.5281/zenodo.14982712

International Organization for Migration. (2024). *Displacement tracking matrix: Mixed migration flows to Europe*. IOM.

International Organization for Migration. (2026). *Missing Migrants Project* [conjunto de dados]. Humanitarian Data Exchange (CC-BY 4.0). https://data.humdata.org/dataset/iom-missing-migrants-project-data

Jolliffe, I. T. (2002). *Principal component analysis* (2nd ed.). Springer. https://doi.org/10.1007/b98835

Kaufman, S., Rosset, S., Perlich, C., & Stitelman, O. (2012). Leakage in data mining: Formulation, detection, and avoidance. *ACM Transactions on Knowledge Discovery from Data, 6*(4), 1–21. https://doi.org/10.1145/2382577.2382579

Mamdani, E. H., & Assilian, S. (1975). An experiment in linguistic synthesis with a fuzzy logic controller. *International Journal of Man-Machine Studies, 7*(1), 1–13. https://doi.org/10.1016/S0020-7373(75)80002-2

Marakas, G. M. (2003). *Decision support systems in the 21st century* (2nd ed.). Prentice Hall.

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., … Duchesnay, E. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research, 12*, 2825–2830.

Rousseeuw, P. J. (1987). Silhouettes: A graphical aid to the interpretation and validation of cluster analysis. *Journal of Computational and Applied Mathematics, 20*, 53–65. https://doi.org/10.1016/0377-0427(87)90125-7

Rumelhart, D. E., Hinton, G. E., & Williams, R. J. (1986). Learning representations by back-propagating errors. *Nature, 323*, 533–536. https://doi.org/10.1038/323533a0

Santos Neto, Silva Guerreiro, & Ribeiro Gaspar. (2026). *Vigilância costeira com drones (UAVs): Modelação de áreas de atuação em ambiente SIG* [Relatório de projeto]. Escola Naval.

Simon, H. A. (1977). *The new science of management decision* (rev. ed.). Prentice Hall.

Saaty, T. L. (1980). *The analytic hierarchy process: Planning, priority setting, resource allocation*. McGraw-Hill.

TEKEVER. (2025). *AR5 maritime surveillance UAV: Technical datasheet*. TEKEVER.

Toregas, C., Swain, R., ReVelle, C., & Bergman, L. (1971). The location of emergency service facilities. *Operations Research, 19*(6), 1363–1373. https://doi.org/10.1287/opre.19.6.1363

Tufte, E. R. (2001). *The visual display of quantitative information* (2nd ed.). Graphics Press.

Turban, E., Sharda, R., & Delen, D. (2011). *Decision support and business intelligence systems* (9th ed.). Prentice Hall.

United Nations Office on Drugs and Crime. (2024). *World drug report 2024*. United Nations.

Ward, J. H. (1963). Hierarchical grouping to optimize an objective function. *Journal of the American Statistical Association, 58*(301), 236–244. https://doi.org/10.1080/01621459.1963.10500845

Zadeh, L. A. (1965). Fuzzy sets. *Information and Control, 8*(3), 338–353. https://doi.org/10.1016/S0019-9958(65)90241-X

---

## 11. Anexos


### Anexo A — Figuras

**Figura 1.** Panorama exploratório das apreensões (EDA): distribuição temporal, por tipo e geográfica.
de droga, histograma de quantidades e percentagem de apreensões marítimas por grupo.

![Figura 1](../resultados/dm/eda_panorama.png)

**Figura 2.** Distribuição das apreensões por região (diagrama de caixa).
contagem de apreensões por região (Norte/Centro/Sul).

![Figura 2](../resultados/dm/eda_boxplot_regiao.png)

**Figura 3.** Redução de dimensionalidade por PCA: projeção das observações no plano das duas
primeiras componentes (colorida pela classe marítima) e variância explicada por componente.

![Figura 3](../resultados/dm/proj_pca.png)

**Figura 4.** Seleção do número de clusters: método do cotovelo e coeficiente de silhueta.

![Figura 4](../resultados/dm/clu_elbow_silhueta.png)

**Figura 5.** Clustering *k*-means: solução geral (esquerda) e restrita ao domínio marítimo (direita).
(direita).

![Figura 5a](../resultados/dm/clu_kmeans_geral.png) ![Figura 5b](../resultados/dm/clu_kmeans_maritimo.png)

**Figura 6.** Agrupamento hierárquico (dendrograma, esquerda) e Fuzzy C-Means (direita).
com grau de pertença ao cluster dominante (à direita).

![Figura 6a](../resultados/dm/clu_dendrograma.png) ![Figura 6b](../resultados/dm/clu_fuzzy_cmeans.png)

**Figura 7.** Comparação de desempenho das quatro famílias de classificadores.
teste.

![Figura 7](../resultados/dm/clf_comparacao.png)

**Figura 8.** Validação cruzada estratificada dos classificadores.
e desvio-padrão de F1, ROC-AUC e PR-AUC.

![Figura 8](../resultados/dm/clf_validacao_cruzada.png)

**Figura 9.** Matrizes de confusão dos classificadores no conjunto de teste.

![Figura 9](../resultados/dm/clf_confusao.png)

**Figura 10.** Curvas ROC (esquerda) e curvas precisão–sensibilidade (direita) dos
classificadores.

![Figura 10a](../resultados/dm/clf_roc.png) ![Figura 10b](../resultados/dm/clf_pr.png)

**Figura 11.** Análise de ajuste do limiar de decisão do modelo recomendado (perceptrão
multicamada otimizado): confiança positiva, sensibilidade e F1 em função do limiar.

![Figura 11](../resultados/dm/clf_limiar.png)

**Figura 12.** Importância relativa dos atributos na árvore de decisão otimizada.

![Figura 12](../resultados/dm/clf_importancia.png)

**Figura 13.** Árvore de decisão otimizada (CART): primeiros níveis.

![Figura 13](../resultados/dm/clf_arvore.png)

**Figura 14.** Graus de pertença do Fuzzy C-Means ao *cluster* dominante (lógica difusa).

![Figura 14](../resultados/dm/fuzzy_pertencas.png)

**Figura 15.** Índice de risco difuso *versus* média ponderada: mapas e correlação.

![Figura 15](../resultados/dm/fuzzy_vs_ponderado.png)

**Figura 16.** Índice de risco marítimo multi-ameaça (agregação por média ponderada).

![Figura 16](../resultados/figuras/01_risco.png)

**Figura 17.** Cobertura de risco: cenário conservador com raio de 90 km (esquerda) *versus*
cenário recomendado com autonomia real (direita).

![Figura 17a](../resultados/figuras/03_cobertura_conservador.png) ![Figura 17b](../resultados/figuras/04_cobertura_alargado.png)

**Figura 18.** Frota total necessária em função do número de bases (mínimo em k = 12).

![Figura 18](../resultados/figuras/08_frota_vs_bases.png)

**Figura 19.** Sensibilidade do dimensionamento da frota à largura útil do sensor, ao tempo de
revisita e à disponibilidade operacional.

![Figura 19](../resultados/figuras/07_sensibilidade.png)

**Figura 20.** Painel geoespacial interativo: índice de risco multi-ameaça (1156 células),
apreensões marítimas 2020+, desembarques PT, bases MCLP (Porto + Portimão), seis sectores de
patrulha e painel Q1–Q3. O artefacto completo está em `resultados/mapa_interativo.html`.

![Figura 20](../resultados/figuras/20_mapa_interativo.png)

**Figura 21.** Backtesting temporal: taxa de acerto do SAD (treino com apreensões até 2022) no
holdout de apreensões marítimas 2023–2024, face a baselines aleatório e referência top 20 %.

![Figura 21](../resultados/figuras/21_backtest_temporal.png)

**Figura 22.** Comparação da captura de risco: SAD *versus* patrulha aleatória e uniforme costeira.
patrulha aleatória e patrulha uniforme costeira.

![Figura 22](../resultados/figuras/22_baseline_patrulha.png)

**Figura 23.** Plataforma operacional: meteo, AIS, risco e alertas em tempo quase real.
(protótipo web em `plataforma/`).

![Figura 23](../resultados/figuras/23_plataforma_operacional.png)

**Figura 24.** Pesos das ameaças por AHP (Saaty) face à ponderação adotada.

![Figura 24](../resultados/figuras/24_ahp_pesos.png)

**Figura 25.** Sensibilidade da classificação ao limiar de decisão.

![Figura 25](../resultados/figuras/25_sensibilidade_limiar.png)

### Anexo B — Tabelas de resultados

**Tabela B1.** *Variância explicada pelas dez primeiras componentes principais.*

| Componente | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Variância (%) | 14,5 | 10,5 | 9,8 | 8,3 | 7,9 | 7,7 | 6,6 | 6,2 | 5,7 | 5,7 |
| Acumulada (%) | 14,5 | 25,0 | 34,8 | 43,1 | 51,0 | 58,7 | 65,3 | 71,5 | 77,3 | 82,9 |

**Tabela B2.** *Cobertura máxima do risco em função do número de bases, com raio operacional de
90 km (cenário do estudo anterior).*

| N.º de bases (k) | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | ≥ 9 |
|---|---|---|---|---|---|---|---|---|---|
| Fração do risco coberta | 31,1 % | 44,0 % | 51,6 % | 57,7 % | 61,0 % | 64,4 % | 65,3 % | 66,2 % | 66,8 % |

**Tabela B3.** *Cobertura por cenário de vento (universo: as 274 células de alto risco;
alcance geográfico a ≤ raio efetivo de qualquer uma das doze bases costeiras;
cobríveis + não cobríveis = 274).*

| Cenário de vento | Raio efetivo (km) | Células cobríveis | Células não cobríveis |
|---|---|---|---|
| Calmo (4 m/s) | 90,0 | 243 | 31 |
| Moderado (12 m/s) | 76,5 | 216 | 58 |
| Forte (18 m/s) | 63,0 | 174 | 100 |

**Tabela B4.** *Validação cruzada estratificada de cinco folds das configurações otimizadas
(média ± desvio-padrão). Em negrito, os melhores valores.*

| Modelo | F1 (média ± dp) | ROC-AUC (média ± dp) | PR-AUC (média ± dp) |
|---|---|---|---|
| Bayes (otim.) | 0,080 ± 0,001 | 0,858 ± 0,059 | 0,326 ± 0,136 |
| k-vizinhos (otim.) | 0,551 ± 0,032 | 0,893 ± 0,036 | 0,484 ± 0,065 |
| Árvore (otim.) | **0,560 ± 0,033** | 0,783 ± 0,033 | 0,371 ± 0,050 |
| **Perceptrão multicamada (otim.)** | 0,551 ± 0,053 | **0,926 ± 0,022** | **0,625 ± 0,069** |

**Tabela B5.** *Frota total e parâmetros operacionais em função do número de bases (área total de
alto risco).*

| N.º de bases | Bases selecionadas | Dist. média (km) | Tempo de estação (h) | Frota total |
|---|---|---|---|---|
| 1 | Montijo (BA6) | 120,1 | 12,6 | 12 |
| 2 a 11 | Porto + Portimão | 138,8 | 12,2 | 13 |
| 12 | Rede completa (12 aeródromos) | 55,9 | 13,9 | 11 |

**Tabela B6.** *Análise de sensibilidade da frota total.*

| Parâmetro | Valores testados → frota |
|---|---|
| Largura útil do sensor (km) | 20 → 14 · 30 → 11 · 40 → 9 · 50 → 6 |
| Período de revisita (h) | 2 → 14 · 3 → 11 · 4 → 9 · 6 → 6 |
| Disponibilidade operacional | 0,60 → 13 · 0,70 → 11 · 0,80 → 10 · 0,90 → 9 |

**Tabela B7.** *Hiperparâmetros selecionados por GridSearchCV (configurações otimizadas).*

| Família | Hiperparâmetros selecionados |
|---|---|
| Bayes (Naive) | var_smoothing = 1e-8 |
| k-vizinhos | n_neighbors = 5, weights = distance |
| Árvore de decisão | criterion = gini, max_depth = None, min_samples_leaf = 1 |
| Perceptrão multicamada | hidden_layer_sizes = (64), alpha = 1e-4 |

### Anexo C — Reprodução computacional e arranque da plataforma

O sistema está integralmente implementado em Python e é reprodutível através dos seguintes
comandos:

```bash
pip install -r requirements.txt
cd src
python -m dm.construir_dados_reais   # intensidades reais (EMODnet AIS + IOM + apreensões)
python validacao.py                 # backtesting temporal + baseline (Fase C)
python main.py             # índice de risco, otimização de bases e dimensionamento de frota
python -m dm.main_dm        # pipeline de data mining (EDA, PCA, clustering, classificação, difuso)
python mapa_interativo.py   # painel geoespacial interativo (resultados/mapa_interativo.html)
python gerar_docx.py        # geração do presente relatório em formato Word
```

As fontes de dados reais (densidade de embarcações do EMODnet e incidentes do IOM Missing Migrants)
residem em `dados/fontes/`; o passo `dm.construir_dados_reais` amostra-as sobre a grelha de procura
e escreve `dados/processados/intensidades_reais.csv`, consumido por `risco.py`. O painel interativo
(`resultados/mapa_interativo.html`) abre-se diretamente em qualquer navegador.

Todos os parâmetros do sistema — pesos das ameaças, especificações do AR5, largura útil do
sensor, período de revisita, disponibilidade e cenários de vento — estão centralizados no ficheiro
`src/config.py`. Os resultados numéricos são exportados para `resultados/resultados.json` e
`resultados/dm/dm_resultados.json`, e as figuras para `resultados/figuras/` e `resultados/dm/`.

**Plataforma operacional:**

```bash
cd plataforma && ./setup-mac.sh && ./start-mac.sh
# http://localhost:5173  ·  API: http://127.0.0.1:8080/docs
```

### Anexo D — Mapa de integração do projeto SIGA (Grupo VI)

A entrega final unificada encontra-se na pasta de entrega **`SIGA_GRUPOVI_ENTREGA/`**, que articula todos os
componentes:

```
SIGA_GRUPOVI_ENTREGA/
├── README.md                 ← índice mestre e arranque
├── NOTAS_ENTREGA.md
├── DEMONSTRACAO.md           ← roteiro 3–5 min          ← métricas canónicas e notas
├── dados/                    ← fontes + processados (grelha PT)
│   ├── fontes/               apreensões, IOM, EMODnet, SIG ref.
│   └── processados/          intensidades_reais.csv
├── src/                      ← pipeline analítico (Python)
│   ├── config.py … validacao.py
│   ├── dm/                   data mining (EDA → classificação → difuso)
│   └── gerar_docx.py         Markdown → Word (formatação CT302)
├── resultados/               ← saídas numéricas e visuais
│   ├── figuras/              otimização (01–08, 20–22)
│   ├── dm/                   figuras data mining + dm_resultados.json
│   ├── resultados.json       bases, frota, cenários vento
│   ├── validacao.json        Q1/Q2/Q3, backtest, baseline 2,06×
│   ├── camadas_mapa.json     IOM + apreensões (plataforma)
│   └── mapa_interativo.html  painel Folium
├── relatorio/
│   ├── Relatorio_SAD_AR5.md  ← fonte única de verdade
│   └── Relatorio_SAD_AR5.docx
└── plataforma/               ← protótipo operacional web
    ├── api/                  FastAPI + OR-Tools + meteo
    └── web/                  React/Leaflet (dist/ incluído)
```

**Fluxo de dados:**

1. `dados/fontes/` → `dm/construir_dados_reais.py` → `dados/processados/intensidades_reais.csv`
2. `intensidades_reais.csv` + `config.py` → `risco.py` → grelha 1156 células
3. Grelha → `otimizacao.py` → `resultados.json` (MCLP k=2; frota 9–11 AR5 com rede distribuída)
4. Apreensões → `dm/` → figuras + `dm_resultados.json`
5. Grelha + camadas → `mapa_interativo.py` + `plataforma/api/` → decisão operacional
6. `Relatorio_SAD_AR5.md` → `gerar_docx.py` → entrega Word (capa Grupo VI, índices auto)

**Respostas operacionais (validacao.json):**

| Questão | Resposta |
|---------|----------|
| Q1 — Onde? | Algarve · Setúbal–Lisboa · NW/Peniche |
| Q2 — Quantos? | 11 AR5 área total (12 bases) · 9 AR5 faixa costeira (5 bases) |
| Q3 — Bases (MCLP)? | Porto (Sá Carneiro) + Portimão (100 % risco; frota só com estas: 13 AR5) |
| Validação | Ganho SAD vs aleatório: **2,06×** |
