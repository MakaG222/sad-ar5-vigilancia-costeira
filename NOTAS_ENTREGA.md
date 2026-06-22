# Notas de entrega — SIGA Grupo VI

**CT302 · SAD AR5 · Vigilância Costeira PT Continental · 2026**

---

## Métricas canónicas (usar sempre estes valores)

| Métrica | Valor |
|---------|-------|
| Células grelha | **1 156** |
| Alto risco (limiar 0,5) | **300** |
| Ganho SAD vs aleatório | **2,06×** (IC95: 1,93–2,22) |
| Frota 24 h | **9** costeiros · **11** total |
| Bases MCLP | Porto (Sá Carneiro) + Portimão |

Fonte: `resultados/validacao.json`

---

## Demonstração ao vivo

- Sem chave AIS: **modo demonstração** activo automaticamente (navios simulados em células marítimas).
- Com `AISSTREAM_API_KEY` em `plataforma/.env`: dados AIS reais quando disponíveis.
- Roteiro completo: `DEMONSTRACAO.md`

---

## Versão apresentação (v0.4)

Esta pasta inclui optimizações para defesa do projecto:

- **Modo apresentação** (mapa leve por defeito)
- **Demo offline** (meteo/IPMA/RSS com cache local)
- **Feedback visual** ao calcular rotas

Guia rápido: `plataforma/APRESENTACAO.md`

