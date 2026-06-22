# Roteiro de demonstração (3–5 minutos)

**SAD AR5 — Plataforma Operacional · Grupo VI · CT302**

> Preparar tudo **antes** da aula. Nunca mostrar erros reais — usar modo demo offline se necessário.

---

## 1. Arranque (30 s)

```bash
# Terminal 1 — pipeline já executado (resultados/ prontos)
cd SIG_GRUPOVI_APRESENTACAO
source .venv/bin/activate   # opcional

# Terminal 2 — plataforma
cd plataforma
./setup-mac.sh    # só 1.ª vez
./start-mac.sh
```

Abrir **http://localhost:5173**

Confirmar no painel: **Modo demonstração** (se não houver API key AIS).

---

## 2. Mapa e estado (45 s)

1. Mostrar mapa da costa PT (sem Espanha).
2. Apontar **células de risco** (camada activa).
3. Painel **Estado**: navios AIS, alertas, alto risco **300 células**.
4. Painel **Respostas SAD**: Q1 (onde), Q2 (9/11 AR5), Q3 (Porto + Portimão), ganho **2,06×**.

---

## 3. Navios e alertas (60 s)

1. Clicar **Atualizar** — navios movem-se (demo) ou AIS real.
2. Mostrar embarcações no mapa (ícones AIS).
3. Clicar **Sim. incidente** → alerta aparece na lista e no mapa.
4. Opcional: **Sim. spoofing** → alerta crítico AIS.

---

## 4. Cenário operacional (90 s)

1. Seleccionar cenário **«Algarve — tráfico + imigração»** (ou similar).
2. Modo **sortie** → **Calcular rota** → trajectória marítima N→S no mapa.
3. Alternar **plano 24 h** → agenda por sectores costeiros.
4. Mencionar: vento afecta alcance; bases MCLP douradas no mapa.

---

## 5. Fecho — argumentos de defesa (30 s)

| Pergunta do júri | Resposta |
|------------------|----------|
| «Isto é real ou simulação?» | Sistema **híbrido**: dados reais AIS + camada de simulação para cenários extremos e demo offline. |
| «Porque a grelha?» | Discretização espacial para análise de risco operacional (**1156 células** mar PT). |
| «Porque 2,06×?» | Factor derivado da **calibração empírica** (bootstrap, 300 células patrulhadas). |

---

## Checklist pré-apresentação

- [ ] `./start-mac.sh` testado sem erros
- [ ] Mapa abre, navios visíveis, alertas funcionam
- [ ] Números no ecrã = relatório (**1156 / 300 / 2,06×**)
- [ ] Relatório Word e ZIP sem `__MACOSX` nem ficheiros `._*`
