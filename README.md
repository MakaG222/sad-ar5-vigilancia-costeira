# SIGA GRUPO VI — SAD AR5 Vigilância Costeira

**CT302 — Sistemas de Apoio à Decisão** · Grupo VI · Escola Naval, Alfeite, 2026

CAD M Santos Neto · CAD EN-AEL Canotilho Castro · CAD M Silva Guerreiro · CAD M Ribeiro Gaspar

---

## O que é este projecto

Sistema de Apoio à Decisão (SAD) que combina **data mining** e **otimização** para planear a
vigilância costeira de Portugal Continental com o UAV **TEKEVER AR5**, face a quatro ameaças:
droga, pesca INN, poluição e imigração irregular.

Responde a três questões operacionais:

1. **Onde** patrulhar → mapa de risco + sectores costeiros  
2. **Quantos** AR5 → ~9 aeronaves para cobertura persistente 24 h  
3. **Que bases** → Porto (Sá Carneiro) + Portimão (100 % risco alto)

---

## Estrutura da entrega

| Pasta | Conteúdo |
|-------|----------|
| `relatorio/` | Relatório final (.md + .docx) — **leitura principal para o júri** |
| `dados/` | Fontes abertas (apreensões, IOM, EMODnet) + grelha processada |
| `src/` | Pipeline Python reprodutível |
| `resultados/` | Figuras, JSON, mapa interativo Folium |
| `plataforma/` | Protótipo web quasi-tempo-real (demo operacional) |

---

## Arranque rápido

### Relatório Word (formato APA 7)

```bash
cd src
python3 condensar_relatorio_apa.py   # opcional: versão mais concisa
python3 gerar_docx.py                # Times New Roman 12 pt, duplo espaçamento, refs APA
```

Abrir `relatorio/Relatório Final.docx` → actualizar índice no Word.

### Mapa interactivo (estático)
Abrir `resultados/mapa_interativo.html` no browser.

### Plataforma operacional (demo live)

**Requisitos:** macOS ou Linux, Python 3.10+, Node 18+

```bash
cd plataforma
chmod +x setup-mac.sh start-mac.sh stop-mac.sh   # 1.ª vez
./setup-mac.sh
./start-mac.sh
```

Abrir **http://localhost:5173** (API em http://localhost:8080).

Parar: `./stop-mac.sh`

#### Utilização

| Acção | Como |
|-------|------|
| **Plano 24 h** | Operação → modo «Plano 24 h» → Calcular rota. Mostra **6 sectores N→S** com rotas desde **Porto (Sá Carneiro)** e **Portimão**. |
| **Horas de patrulha** | Campo **t_on patrulha (h)** — limitado à autonomia AR5 (16 h − reserva). Valor recomendado: 4 h/sector. |
| **Cenários** | Botões de cenário (rotina 24 h, droga Algarve, vento forte, etc.) aplicam tipo de patrulha e parâmetros. |
| **Camadas** | Separador Camadas — risco, EMODnet, apreensões, IOM, clusters k-means. Legenda com **escala de cores de risco**. |
| **Spoofing / incidente** | Botões «Sim. spoofing» e «Sim. incidente» — ponto **aleatório no mar** ao longo de toda a costa. |
| **Exportar missão** | Calcular rota → Exportar (GeoJSON/CSV). |

Modo apresentação (arranque rápido): activo por defeito — desactive em Camadas para ver todas as camadas.

Ver também `plataforma/APRESENTACAO.md` e `DEMONSTRACAO.md`.

### Reproduzir análise completa

No macOS o comando é **`python3`** (não `python`). Na 1.ª vez:

```bash
chmod +x setup-python.sh && ./setup-python.sh
source .venv/bin/activate
cd src
python sincronizar_relatorio.py && python validacao.py && python gerar_docx.py
```

Pipeline completo (dados + DM + relatório):

```bash
source .venv/bin/activate
cd src
python -m dm.construir_dados_reais
python main.py
python -m dm.main_dm
python validacao.py
python gerar_docx.py
```

---

## Formatação (estilo CT302 / Grupo VI)

O relatório Word segue a estrutura dos trabalhos de referência CT302:

- Capa institucional + página de rosto (Grupo VI, Escola Naval)
- **Sumário executivo** (síntese assertiva)
- Resumo / Abstract bilingues
- Secções IMRaD numeradas com figuras e tabelas referenciadas
- Índices automáticos de figuras, tabelas e siglas
- Vocabulário alinhado com os PW: *data mining*, PCA, *clustering*, validação cruzada,
  lógica difusa, cobertura de conjunto, MCLP, decisão semiestruturada

---

## Resultados-chave (validação)

| Métrica | Valor |
|---------|-------|
| Células grelha PT | 1 156 |
| Alto risco (≥ 0,5) | 300 |
| Bases MCLP | Porto + Portimão |
| Frota 24 h | ≈ 9 AR5 (costeira) / 11 AR5 (total) |
| Ganho SAD vs aleatório | **2,06×** (IC95: 1,93–2,22) |
| ROC-AUC (MLP, CV 5-fold) | 0,93 ± 0,02 |

Ver `resultados/validacao.json` e `NOTAS_ENTREGA.md`.

---

## README técnico

### Dependências

- **Pipeline:** Python 3.10+ (`requirements.txt` na raiz)
- **Plataforma API:** `plataforma/api/requirements.txt`
- **Frontend:** Node 18+ (`plataforma/web/`)

### Pipeline analítico

```bash
chmod +x setup-python.sh && ./setup-python.sh
source .venv/bin/activate
cd src
python3 main.py          # grelha 1156 → risco → otimização → validação → mapa
python3 gerar_docx.py    # relatório Word
```

### API FastAPI (isolada)

```bash
cd plataforma/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8080
```

### Modo AIS

| Condição | Comportamento |
|----------|---------------|
| `AISSTREAM_API_KEY` definida | Tenta AIS real; fallback simulado se stream falhar |
| Sem chave | **Modo demonstração** automático — navios em células marítimas SAD |

Copiar `plataforma/.env.example` → `plataforma/.env` para chave opcional.

### Demonstração oral

Roteiro 3–5 min: `DEMONSTRACAO.md`

---

## Ligação entre componentes

```
dados/fontes → construir_dados_reais → risco.py → otimizacao.py → resultados.json
                                              ↓
                                    mapa_interativo.html + plataforma/web
                                              ↓
                                    Relatorio_SAD_AR5.md → .docx
```

A Secção 9 e o **Anexo D** do relatório documentam esta integração em detalhe.
