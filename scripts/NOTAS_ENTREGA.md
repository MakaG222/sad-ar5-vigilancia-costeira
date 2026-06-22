# Notas de entrega — SIGA Grupo VI

**CT302 · SAD AR5 · Vigilância Costeira PT Continental · 2026**

---

## Métricas canónicas (usar sempre estes valores)

| Métrica | Valor |
|---------|-------|
| Células grelha | **1 156** |
| Alto risco (limiar 0,5) | **300** |
| Ganho SAD vs aleatório | **2,06×** (IC95: 1,93–2,22) |
| Holdout 2023–24 | **85,5 %** em alto risco |
| Frota 24 h (Q2) | **9** costeira (5 bases) · **11** total (12 bases) |
| MCLP mínimo (Q3) | Porto (Sá Carneiro) + Portimão (100 % risco) |
| Frota se só MCLP k=2 | **13 AR5** (trânsitos longos) |

Fonte: `resultados/validacao.json`, `resultados/resultados.json`

**Nota:** Q3 (localização mínima) e Q2 (frota 24 h) respondem a perguntas diferentes — ver Tabela 6 do relatório.

---

## Demonstração ao vivo

- Sem chave AIS: **modo demonstração** activo automaticamente (navios simulados em células marítimas).
- Com `AISSTREAM_API_KEY` em `plataforma/.env`: dados AIS reais quando disponíveis.
- Roteiro completo: `DEMONSTRACAO.md`

---

## Estrutura da pasta

Ver `README.md` (índice principal). Relatório: `relatorio/Relatorio_SAD_AR5.docx`.
