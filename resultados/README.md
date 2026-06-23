# Artefactos pré-calculados — SAD AR5

JSON consumidos pela API em runtime. Não é necessário reexecutar o pipeline analítico completo para demonstrar a plataforma.

| Ficheiro | Conteúdo |
|----------|----------|
| `validacao.json` | Backtest temporal, baseline de patrulha, respostas Q1–Q3 e métricas de validação |
| `resultados.json` | Dimensionamento de frota, sensibilidade e cenários operacionais |
| `ahp_pesos.json` | Matriz de comparações par-a-par e pesos AHP das quatro ameaças |
| `camadas_mapa.json` | Geometrias IOM, apreensões marítimas e metadados para o mapa |
| `demo_navios.json` | Posições AIS fixas para o modo de demonstração (`DEMO_DETERMINISTICO=1`) |
| `manifest.json` | Checksums SHA-256 para verificação de integridade |

## Integridade

```bash
python scripts/verificar_integridade.py
python scripts/gerar_manifest.py   # após alterar qualquer JSON acima
```

## Métricas de referência

Valores canónicos validados pela CI (ver `scripts/verificar_integridade.py`):

- 274 células de patrulha (limiar operacional 0,5)
- Ganho SAD vs patrulha aleatória: 2,13×
- Frota recomendada (faixa costeira): 9 AR5
