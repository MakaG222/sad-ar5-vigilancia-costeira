"""
config.py — Parâmetros, especificações verificadas e fontes do Sistema de Apoio
à Decisão (SAD) para vigilância costeira com o UAV TEKEVER AR5.

Todos os valores numéricos de especificações e ameaças estão documentados com a
respetiva fonte no dicionário FONTES, para garantir rastreabilidade no relatório.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# 1. ESPECIFICAÇÕES VERIFICADAS DO TEKEVER AR5
#    Fonte: TEKEVER, AR5 Maritime/Defence datasheet (2025) e naval-technology.com
# ---------------------------------------------------------------------------
AR5 = {
    "autonomia_h": 16.0,          # endurance utilizável (16–20 h consoante payload)
    "autonomia_max_h": 20.0,
    "velocidade_cruzeiro_kmh": 100.0,
    "teto_servico_m": 3600.0,
    "mtow_kg": 180.0,
    "payload_kg": 50.0,
    "envergadura_m": 7.3,
    "alcance_rlos_km": 230.0,     # rádio linha de vista
    "alcance_satcom": "ilimitado",# SATCOM
    "sortie_ida_km": 1500.0,      # 1 sentido
    "sortie_ida_volta_km": 750.0, # missão de regresso
    "sensores": "EO/IR giro-estabilizado (zoom 30x), AIS, EPIRB, SIGINT",
}

# ---------------------------------------------------------------------------
# 2c. ÂMBITO GEOGRÁFICO — apenas costa e águas de Portugal Continental
#     (longitude −11,0° a −7,38°; ver geo.zona_maritima_pt). Exclui Espanha.
# ---------------------------------------------------------------------------
# Raio base de atuação por aeródromo (km). Herdado do trabalho SIG original
# (buffer de 90 km), tecnicamente conservador face ao alcance do AR5.
RAIO_BASE_KM = 90.0

# Reserva de combustível/segurança e tempo improdutivo por sortie (h)
RESERVA_H = 1.0

# Disponibilidade operacional média da frota (manutenção, turnaround, avarias)
DISPONIBILIDADE = 0.70

# Reserva estratégica adicional da frota (fração)
RESERVA_FROTA = 0.10

# ---------------------------------------------------------------------------
# 2b. PARÂMETROS DE COBERTURA SENSORIAL (persistência)
# ---------------------------------------------------------------------------
# Largura útil de deteção marítima do AR5 em patrulha (km). Combina EO/IR
# (zoom 30x) para alvos não cooperativos com AIS para alvos cooperativos.
# Valor conservador assumido; sujeito a análise de sensibilidade.
SENSOR_SWATH_KM = 30.0

# Tempo de revisita aceitável de cada célula de alto risco (h): intervalo
# máximo desejável entre passagens do sensor sobre a mesma zona.
TEMPO_REVISITA_H = 3.0

# Tempo mínimo de permanência em estação por sortie para reachability (h)
T_ON_MIN_H = 2.0

# Fatores de redução do alcance em função da intensidade do vento (m/s).
# Fonte: lógica do script SIG original (Relatorio_SIG_FINAL.pdf, secção 4.8.2).
def fator_vento(vel_ms: float) -> float:
    if vel_ms <= 5:
        return 1.0
    elif vel_ms <= 15:
        return 0.85
    else:
        return 0.70

# Assimetria a favor / contra o vento (apenas para visualização da zona real)
ASSIMETRIA_DOWN = 1.30
ASSIMETRIA_UP = 0.70

# ---------------------------------------------------------------------------
# 3. CENÁRIOS METEOROLÓGICOS A AVALIAR (velocidade do vento, m/s)
# ---------------------------------------------------------------------------
CENARIOS_VENTO = {
    "calmo": 4.0,       # fator 1.00  -> R = 90 km
    "moderado": 12.0,   # fator 0.85  -> R = 76.5 km
    "forte": 18.0,      # fator 0.70  -> R = 63 km
}

# ---------------------------------------------------------------------------
# 4. AERÓDROMOS COSTEIROS CANDIDATOS (Portugal Continental)
#    Bases candidatas a operar o AR5. Coordenadas WGS84 (lon, lat), fonte:
#    coordenadas públicas de aeroportos/aeródromos (AIP/OpenStreetMap).
#    regiao: N (Norte) / C (Centro) / S (Sul), como no trabalho SIG original.
# ---------------------------------------------------------------------------
AERODROMOS = [
    # nome, lon, lat, regiao
    ("Porto (Sá Carneiro)",   -8.681, 41.248, "N"),
    ("Aveiro (S. Jacinto)",   -8.741, 40.659, "N"),
    ("Braga",                 -8.445, 41.587, "N"),
    ("Monte Real (BA5)",      -8.887, 39.828, "C"),
    ("Santa Cruz",            -9.366, 39.128, "C"),
    ("Sintra (BA1)",          -9.339, 38.831, "C"),
    ("Cascais (Tires)",       -9.355, 38.725, "C"),
    ("Lisboa (H. Delgado)",   -9.134, 38.774, "C"),
    ("Montijo (BA6)",         -9.035, 38.704, "C"),
    ("Sines",                 -8.790, 37.957, "S"),
    ("Portimão",              -8.584, 37.149, "S"),
    ("Faro",                  -7.966, 37.014, "S"),
]

# Bases militares candidatas a lançamento AR5 (coordenadas públicas WGS84).
# Filtradas em geo.bases_lancamento() — apenas ≤20 km da linha de costa.
BASES_MILITARES = [
    # nome, lon, lat, força (FAP | Marinha | Exercito)
    ("Sintra (BA1 — FAP)",           -9.339, 38.831, "FAP"),
    ("Montijo (BA6 — FAP)",          -9.035, 38.704, "FAP"),
    ("Monte Real (BA5 — FAP)",       -8.887, 39.828, "FAP"),
    ("Alfeite — Escola Naval",       -9.166, 38.671, "Marinha"),
    ("Base Naval Lisboa (Cacilhas)", -9.148, 38.683, "Marinha"),
    ("LISNAVE / Estaleiro (Setúbal)", -8.893, 38.523, "Marinha"),
    ("Portimão — Zona Naval",        -8.537, 37.130, "Marinha"),
    ("Sagres — Fortaleza",           -8.948, 37.010, "Marinha"),
    ("Peniche — Forte costeiro",     -9.380, 39.356, "Exercito"),
    ("Sines — Zona militar",         -8.874, 37.955, "Exercito"),
    ("Belém — Artilharia (Lisboa)",  -9.206, 38.696, "Exercito"),
    ("Figueira da Foz — Zona costeira", -8.865, 40.145, "Exercito"),
]

# Distância máxima à costa para bases de lançamento AR5 (km)
RAIO_LANCAMENTO_COSTA_KM = 20.0

# Bases MCLP recomendadas pelo pipeline analítico (resultados/resultados.json)
BASES_MCLP_RECOMENDADAS = ["Porto (Sá Carneiro)", "Portimão"]

# Sectores de patrulha costeira (alinhado com mapa_interativo / relatório)
N_SECTORES_COSTA = 6

# Janela temporal por sector no plano 24 h (h) — 24 h / 6 sectores
JANELA_SECTOR_H = 24.0 / N_SECTORES_COSTA

# Tempo de patrulha efectiva por sortie (h) — derivado da análise de persistência
# (t_on ≈ autonomia − 2×dist_média/V − reserva; sector ≈ 4 h)
T_ON_SORTIE_H = 4.0

# N.º de alvos de patrulha por sortie (alinhado com validação: 274 células / ~8 por sector)
N_ALVOS_SORTIE_PADRAO = 8

# Limiar operacional de alto risco (validacao.json)
LIMIAR_RISCO_OPERACIONAL = 0.5

# ---------------------------------------------------------------------------
# 5. PESOS RELATIVOS DAS AMEAÇAS NO ÍNDICE DE RISCO
#    Ponderação multi-critério (soma = 1). Valores adoptados após AHP (Saaty):
#    0,376 / 0,243 / 0,191 / 0,191 (CR ≈ 0; ver dm/ahp_pesos.py). Arredondados
#    para 0,35 / 0,25 / 0,20 / 0,20 por legibilidade operacional; sensibilidade
#    ±10 % não altera a hierarquia espacial (relatório, Secção 4.5.1).
# ---------------------------------------------------------------------------
PESOS_AMEACA = {
    "droga": 0.35,       # AHP arredondado (exacto: 0,376); CR ≈ 0,0002
    "pesca": 0.25,       # exacto: 0,243
    "poluicao": 0.20,    # exacto: 0,191
    "imigracao": 0.20,   # exacto: 0,190
}

# ---------------------------------------------------------------------------
# 6. FONTES (para citação no relatório)
# ---------------------------------------------------------------------------
FONTES = {
    "AR5": "TEKEVER (2025). AR5 Maritime/Defence datasheet, tekever.com/ar5; "
           "naval-technology.com — Tekever AR5 Life Ray Evolution UAS.",
    "droga_excel": "Conjunto de dados de apreensões de droga em Portugal "
                   "(2011–2024), 9.727 registos (formato UNODC/IDS).",
    "droga_maritimo": "UNCTE/PJ, Relatório 2024: 87,2% da cocaína apreendida "
                      "entrou por via marítima; MAOC-N (Lisboa) coordena "
                      "interceções no Atlântico; semissubmersíveis detetados "
                      "perto dos Açores (Europol, 2025).",
    "pesca": "EMODnet Human Activities — densidade de embarcações de pesca (tipo 02) "
             "com anomalia pesca/AIS (proxy de esforço de pesca desproporcionado vs. tráfego); "
             "DGRM/EFCA (SIFICAP, JDP Western Waters).",
    "poluicao": "EMODnet — densidade de carga (10) + tanque (11); proxy de corredores "
                "de derrame (literatura EMSA CleanSeaNet, ~250 alertas/ano em águas PT).",
    "imigracao": "IOM Missing Migrants (incidentes em mar, PT continental) + "
                 "desembarques marítimos documentados (SEF/ACM, Frontex ARA, CP) "
                 "em dados/fontes/imigracao_pt_costa.csv — rota Atlântica Ocidental.",
    "sig_original": "Santos Neto, Silva Guerreiro & Ribeiro Gaspar (2026). "
                    "Vigilância Costeira com Drones (UAVs), Escola Naval (Alfeite).",
}
