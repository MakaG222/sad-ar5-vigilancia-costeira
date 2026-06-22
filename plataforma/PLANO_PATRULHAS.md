# Plano de desenvolvimento — Sistema de patrulhas SAD AR5

Documento de referência para evoluir a plataforma de rotas operacionais coerentes com o relatório e com a realidade marítima.

**Última verificação:** 20 jun 2026 — estado validado com smoke test (22/22) e demo Anti-droga Algarve (100/100 Coerente).

---

## 1. Diagnóstico (estado actual)

| Problema | Causa raiz | Estado |
|----------|------------|--------|
| Apreensões em terra | `camadas_mapa.json` com coordenadas de distrito | **Corrigido** — filtro `ponto_em_mar` + JSON regenerado |
| Foco / demo em terra | Critério `ponto_em_mar` inclui estuários; mapa OSM parece terra | **Corrigido** — `ponto_em_mar_mapa` (≥15 km, fora estuários) + `snap_para_mar()` |
| Rotas droga Algarve fracas | Sortie sem cluster k-means nem corredor | **Corrigido na demo** — cluster + corredor SW; TSP global mantém margem de melhoria |
| Rotas com saltos longos | TSP livre sobre pool disperso | **Mitigado** — pool `varrimento_kmeans_adjacente`; validação deteta saltos |

---

## 2. Arquitectura alvo do sistema de patrulhas

```
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 1 — Grelha SAD (1 156 células, só mar 8–300 km)     │
│  risco multi-ameaça · intensidades EMODnet/IOM/UNODC        │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 2 — Zonas operacionais                              │
│  • k-means (hotspots)                                       │
│  • Corredores por ameaça (SW droga, atlântico imigração…)   │
│  • Sectores costeiros 24 h (persistência)                   │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 3 — Selecção de alvos (sortie)                      │
│  Score = f(r_ameaça, risco, prox_costa) × bonus_corredor    │
│  Pool por adjacência (swath 30 km) + bandas N→S no cluster   │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 4 — Sequência de voo                                │
│  Entrada mar → TSP/OR-Tools → expansão marítima (corredor)  │
│  Restrições: autonomia AR5, vento, swath                    │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  CAMADA 5 — Validação (relatório + runtime)                 │
│  Backtest temporal · ganho vs aleat. · score rota HUD 0–100 │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Fases de implementação

### Fase 1 — Higiene espacial ✅ concluída

- [x] Apreensões: Excel marítimo → snap célula mar → validação `ponto_em_mar`
- [x] `camadas_mapa.json` regenerado
- [x] Foco/zonas: apenas `pts_mar()` / `pts_mar_mapa()`
- [x] Sortie: priorizar células do **cluster k-means** da base
- [x] Módulo `corredores_operacionais.py` (bonus SW Algarve para droga)
- [x] Marcadores demo (spoofing/incidente): `snap_para_mar()` com `ponto_em_mar_mapa`

### Fase 2 — Varrimento operacional credível ⚡ parcial (suficiente para defesa)

| Tarefa | Estado | Notas |
|--------|--------|-------|
| **2.1 Lawn-mower costeiro** | ⚡ Parcial | Pool adjacente + ordenação N→S (`varrimento_kmeans_adjacente`); sequência final ainda via TSP OR-Tools |
| **2.2 Faixa swath** | ⚡ Parcial | Adjacência `swath × 0.45`; sem faixa perpendicular sistemática à costa |
| **2.3 Corredores calibrados** | ⚡ Heurístico | Polígonos fixos em `corredores_operacionais.py`; não calibrados em runtime com AIS/apreensões |
| **2.4 Narrativa no HUD** | ✅ Feito | `zona_cluster`, `corredor_operacional`, bloco **Qualidade X/100 · Classe** |

**Resultado verificado (Portimão, droga):** zona «Algarve / SW», corredor «Aproximação SW (Magreb → Algarve)», **100/100 Coerente**, 0 saltos.

### Fase 3 — Persistência 24 h ⚡ parcial

- [x] Plano 24 h: 6 sectores + sortie por sector (API `/api/rotas/plano24h`)
- [x] Score validação por sector (smoke: **87/100 Coerente**)
- [ ] Hand-off explícito entre bases MCLP por sector
- [ ] Agenda operacional com janelas sincronizadas à frota 9/11

### Fase 4 — Validação automática de rotas ⚡ parcial (runtime)

- [x] Score 0–100 + classe Coerente/Aceitável/Rever (`validacao_rota.py`)
- [x] Métricas: % na zona, saltos vs swath, autonomia, cobertura estimada
- [x] Testes unitários (`tests/test_validacao_rota.py`)
- [ ] % células com `r_droga` ≥ limiar (métrica analítica holdout)
- [ ] Distância média a apreensões 2024
- [ ] Rejeição automática de rotas >20% fora do cluster
- [ ] Relatório PDF antes/depois

---

## 4. Regras de negócio (patrulhas que “fazem sentido”)

1. **Só mar operacional** — waypoints de patrulha em células mar; demo usa `ponto_em_mar_mapa`.
2. **Uma zona por sortie** — cluster k-means ou corredor único por missão de 4 h.
3. **Continuidade espacial** — adjacência no pool; validação penaliza saltos > 1,5× swath.
4. **Prioridade por ameaça** — droga: `r_droga` + corredor SW; imigração: rota atlântica.
5. **Autonomia** — distância ≤ alcance vento-ajustado; alerta se `dentro_autonomia=false`.
6. **Rastreabilidade** — rota regista base, zona, corredor, optimizador, vento, `validacao`.

---

## 5. Cenários de teste para a defesa

| Cenário | Base | Tipo | Resultado verificado (20/06/2026) |
|---------|------|------|-----------------------------------|
| Droga Algarve | Portimão | droga | ✅ Zona «Algarve / SW», corredor SW, **100/100 Coerente** |
| Imigração atlântica | Beja / Faro | imigracao | Cluster sul; validar oralmente lon < −8,5° |
| Risco global | Porto | geral | Cluster NW/centro; fallback sector local se fora alcance |
| Região manual | 2 cliques Algarve | droga | Caixa lat/lon; só células dentro |
| Plano 24 h | MCLP | geral | ✅ **87/100 Coerente** (smoke test) |
| Demo spoofing/incidente | — | — | ✅ `ponto_em_mar_mapa=True` após snap |

---

## 6. Ficheiros relevantes

| Ficheiro | Função |
|----------|--------|
| `src/geo.py` | `ponto_em_mar`, `ponto_em_mar_mapa`, grelha |
| `src/corredores_operacionais.py` | Corredores heurísticos por ameaça |
| `plataforma/api/services/patrulha_costeira.py` | Sortie, pool varrimento, TSP |
| `plataforma/api/services/validacao_rota.py` | Score qualidade rota (HUD) |
| `plataforma/api/services/alertas.py` | `snap_para_mar()` demo |
| `plataforma/api/services/zonas_cluster.py` | k-means hotspots |
| `plataforma/api/smoke_test.py` | 22 verificações pré-defesa |

---

## 7. Próximo passo (pós-entrega)

Refinar **Fase 2.1**: TSP local (janela deslizante) após pool N→S, em vez de TSP global — reduz cruzamentos residuais sem alterar a arquitectura actual.

**Para a defesa:** apresentar o sistema como **varrimento por cluster + validação automática de qualidade**, não como simulador de voo lawn-mower completo.
