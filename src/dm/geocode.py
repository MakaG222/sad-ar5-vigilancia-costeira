"""
geocode.py — Geocodificação aproximada dos tokens de "Administrative Region"
(distritos/concelhos) para coordenadas (lat, lon), e classificação
continental/ilhas e costeiro/interior.

Cobre os tokens mais frequentes do dataset (>90% dos registos). Tokens não
mapeados são descartados nas análises geográficas (clustering).
Fonte das coordenadas: localização pública das sedes de concelho/distrito.
"""
from __future__ import annotations

# token -> (lat, lon)
COORDS = {
    # --- distritos / grandes concelhos continentais ---
    "Lisboa": (38.72, -9.14), "Lisba": (38.72, -9.14),
    "Porto": (41.15, -8.61), "Portio": (41.15, -8.61),
    "Faro": (37.02, -7.93), "Setúbal": (38.52, -8.89), "Setubal": (38.52, -8.89),
    "Aveiro": (40.64, -8.65), "Leiria": (39.74, -8.81), "Leira": (39.74, -8.81),
    "Coimbra": (40.21, -8.43), "Braga": (41.55, -8.42),
    "Santarém": (39.23, -8.69), "Santarem": (39.23, -8.69),
    "Beja": (38.02, -7.86), "Amadora": (38.75, -9.23),
    "Castelo Branco": (39.82, -7.49), "Viseu": (40.66, -7.91),
    "Viana Do Castelo": (41.69, -8.83), "Vila Real": (41.30, -7.74),
    "Bragança": (41.81, -6.76), "Braganca": (41.81, -6.76),
    "Guarda": (40.54, -7.27), "Portalegre": (39.29, -7.43),
    "Évora": (38.57, -7.91), "Evora": (38.57, -7.91),
    "Oeiras": (38.69, -9.31), "Vila Nova De Gaia": (41.12, -8.61),
    "Moita": (38.65, -8.99), "Seixal": (38.64, -9.10), "Almada": (38.68, -9.16),
    "Cascais": (38.70, -9.42), "Albufeira": (37.09, -8.25),
    "Odivelas": (38.79, -9.18), "Loures": (38.83, -9.17),
    "Sintra": (38.80, -9.38), "Portimão": (37.14, -8.54),
    "Barcelos": (41.53, -8.62), "Seia": (40.42, -7.70),
    "Matosinhos": (41.18, -8.69), "Vila Nova De Famalicão": (41.41, -8.52),
    "Arruda Dos Vinhos": (38.96, -9.08), "Barreiro": (38.66, -9.07),
    "Vila Do Bispo": (37.08, -8.91), "Vila Franca De Xira": (38.96, -8.99),
    "Guimarães": (41.44, -8.29), "Espinho": (41.00, -8.64),
    "Loulé": (37.14, -8.02), "Grândola": (38.17, -8.57), "Maia": (41.23, -8.62),
    "Palmela": (38.57, -8.90), "Oliveira De Azeméis": (40.84, -8.48),
    "Vila Do Conde": (41.35, -8.74), "Sesimbra": (38.44, -9.10),
    "Paços De Ferreira": (41.28, -8.38), "Pombal": (39.92, -8.63),
    "Idanha-A-Nova": (39.92, -7.24), "Torres Vedras": (39.09, -9.26),
    "Felgueiras": (41.37, -8.19), "Gondomar": (41.14, -8.53),
    "Santa Maria Da Feira": (40.93, -8.54), "Rio Maior": (39.34, -8.94),
    "Silves": (37.19, -8.44), "Odemira": (37.60, -8.64),
    "Caldas Da Rainha": (39.40, -9.14), "Montijo": (38.70, -8.97),
    "Paredes": (41.20, -8.33), "Olhão": (37.03, -7.84), "Almeida": (40.73, -6.91),
    "Azambuja": (39.07, -8.87), "Salvaterra De Magos": (39.02, -8.79),
    "Águeda": (40.58, -8.45), "Almeirim": (39.21, -8.62),
    "Figueira Da Foz": (40.15, -8.86), "Santo Tirso": (41.34, -8.48),
    "Marinha Grande": (39.75, -8.93), "Abrantes": (39.46, -8.20),
    "Mirandela": (41.49, -7.18), "Trofa": (41.34, -8.56), "Alcobaça": (39.55, -8.98),
    "Castro Verde": (37.70, -8.08), "Benavente": (38.98, -8.81),
    "Santiago Do Cacém": (38.02, -8.69), "Amarante": (41.27, -8.08),
    "Lagos": (37.10, -8.67), "Oliveira Do Bairro": (40.51, -8.50),
    "Valongo": (41.19, -8.50), "Ílhavo": (40.60, -8.67), "Sines": (37.95, -8.87),
    "Ovar": (40.86, -8.62), "Esposende": (41.53, -8.78),
    "Póvoa De Varzim": (41.38, -8.76), "Penafiel": (41.20, -8.28),
    "Lagoa": (37.13, -8.45), "Tavira": (37.13, -7.65), "Mafra": (38.94, -9.33),
    "Peniche": (39.36, -9.38), "Vila Real De Santo António": (37.19, -7.42),
    "Vila Nova De Cerveira": (41.94, -8.74), "Aljezur": (37.32, -8.80),
    # --- ilhas (Madeira / Açores) ---
    "Ilha Da Madeira": (32.74, -16.96), "Madeira": (32.74, -16.96),
    "Ilha Do Madeira": (32.74, -16.96), "Funchal": (32.65, -16.91),
    "Câmara De Lobos": (32.65, -16.98), "Machico": (32.72, -16.77),
    "Porto Santo": (33.07, -16.34), "Ponta Do Sol": (32.68, -17.10),
    "Calheta": (32.72, -17.18), "Ilha De Porto Santo": (33.07, -16.34),
    "Azores": (37.74, -25.67), "Ilha De São Miguel": (37.74, -25.67),
    "Ilha São Miguel": (37.74, -25.67), "Ponta Delgada": (37.74, -25.67),
    "Ribeira Grande": (37.82, -25.52), "Povoação": (37.76, -25.24),
    "Vila Franca Do Campo": (37.72, -25.43), "Lagoa Açores": (37.74, -25.57),
    "Ilha Terceira": (38.66, -27.22), "Angra Do Heroísmo": (38.66, -27.22),
    "Praia Da Vitória": (38.73, -27.07), "Ilha Do Faial": (38.53, -28.63),
    "Horta": (38.53, -28.63), "Ilha Do Pico": (38.47, -28.32),
    "Madalena": (38.53, -28.52), "Ilha De Santa Maria": (36.97, -25.10),
    "Vila Do Porto": (36.94, -25.14), "Ilha Das Flores": (39.45, -31.13),
    "Ilha De São Jorge": (38.65, -28.10), "Ilha Do Corvo": (39.70, -31.11),
}

ILHAS = {k for k in COORDS if any(s in k for s in
         ["Ilha", "Madeira", "Açores", "Azores", "Funchal", "Porto Santo",
          "Câmara De Lobos", "Machico", "Ponta Do Sol", "Calheta",
          "Ponta Delgada", "Ribeira Grande", "Povoação", "Vila Franca Do Campo",
          "Angra", "Praia Da Vitória", "Horta", "Madalena", "Vila Do Porto"])}

# Tokens costeiros (continental) — sede junto/perto do litoral
COSTEIROS = {"Lisboa", "Porto", "Faro", "Setúbal", "Setubal", "Aveiro",
             "Viana Do Castelo", "Matosinhos", "Espinho", "Vila Do Conde",
             "Póvoa De Varzim", "Esposende", "Ovar", "Ílhavo", "Figueira Da Foz",
             "Peniche", "Cascais", "Oeiras", "Almada", "Seixal", "Barreiro",
             "Sesimbra", "Sines", "Odemira", "Albufeira", "Portimão", "Lagos",
             "Olhão", "Tavira", "Lagoa", "Vila Do Bispo", "Aljezur",
             "Vila Real De Santo António", "Vila Nova De Gaia", "Grândola",
             "Santiago Do Cacém", "Mafra", "Torres Vedras", "Loulé", "Silves",
             "Caldas Da Rainha", "Nazaré", "Montijo", "Moita", "Palmela"}


def geocode(token: str):
    return COORDS.get(token)


def is_ilha(token: str) -> bool:
    return token in ILHAS


def is_costeiro(token: str) -> bool:
    return token in COSTEIROS
