# Notas de entrega — SAD AR5 (Grupo VI)

Métricas canónicas (pipeline `main.py` + `validacao.py`, Jun 2025):

| Métrica | Valor |
|---------|-------|
| Grelha | **1 156** células |
| Alto risco (limiar 0,5) | **274** |
| Holdout 2023–24 (multi-ameaça, limiar 0,5) | **85,2 %** (n=**54**) |
| Holdout top 20 % | **87,0 %** |
| Backtest só droga (top 20 %) | **94,4 %** |
| Ganho SAD vs aleatório | **2,13×** (IC95: 1,97–2,31) |
| Captura de risco (SAD) | **50,4 %** |
| Frota 24 h — faixa costeira | **9 AR5** (5 bases) |
| Frota 24 h — área total | **9 AR5** (rede distribuída) |
| Frota se só MCLP k=2 (Porto + Portimão) | **10 AR5** |
| MCLP k=2 | Porto + Portimão (100 % do risco) |
| Sensibilidade limiar 0,45 / 0,50 / 0,55 | 312 / **274** / 227 células |
| Sensibilidade disponibilidade D | 0,60→11 · 0,70→9 · 0,80→8 · 0,90→7 |

**Narrativa frota:** Porto + Portimão resolvem o MCLP; para vigilância persistente 24 h são necessários **9 AR5** na faixa costeira e na área total (rede distribuída), ou **10 AR5** se operarem apenas essas duas bases.

**Ficheiros de prova:** `resultados/validacao.json`, `resultados/resultados.json`, `relatorio/SIGA_FINAL.docx`.

**Plataforma:** `cd plataforma && ./setup.sh && ./start.sh` — barra de estado lê os JSON acima.
