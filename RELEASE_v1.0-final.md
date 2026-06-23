## SAD AR5 — Entrega final (CT302, Escola Naval)

Protótipo operacional de apoio à vigilância costeira com UAV TEKEVER AR5: mapa de risco multi-ameaça, rotas de patrulha, plano 24 h, dimensionamento de frota, alertas e validação científica.

### Arranque rápido

```bash
git clone https://github.com/MakaG222/sad-ar5-vigilancia-costeira.git
cd sad-ar5-vigilancia-costeira/plataforma
./start-docker.sh
```

→ http://localhost:8080

### Conteúdo do repositório

| Pasta | Função |
|-------|--------|
| `plataforma/` | API FastAPI + interface React |
| `src/` | Núcleo analítico (risco, MCLP, rotas) |
| `dados/` | Fontes de entrada |
| `resultados/` | JSON pré-calculados (Q1–Q3, validação) |

### Relatório académico

O relatório Word/PDF **não está incluído** neste repositório — apenas código e dados da plataforma.

### Respostas SAD (resumo)

| Pergunta | Resposta |
|----------|----------|
| Q1 — Onde patrulhar? | Algarve, Lisboa–Setúbal, NW/Peniche |
| Q2 — Quantos AR5? | 9 AR5 (3 simultâneos, faixa costeira) |
| Q3 — Onde colocar bases? | Porto + Portimão (MCLP k=2) |

### Verificação

```bash
cd plataforma/api && source .venv/bin/activate
python smoke_test.py
python ../../scripts/verificar_integridade.py
```

### Documentação

- [README](https://github.com/MakaG222/sad-ar5-vigilancia-costeira/blob/main/README.md) — instalação, limitações e capturas
- [FICHEIROS.md](https://github.com/MakaG222/sad-ar5-vigilancia-costeira/blob/main/FICHEIROS.md) — guia da estrutura
