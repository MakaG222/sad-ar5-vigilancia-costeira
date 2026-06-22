# SAD AR5 — Plataforma operacional

Protótipo web quasi-tempo-real para apoio à vigilância costeira com o UAV TEKEVER AR5:
mapa de risco, meteo, AIS, rotas de patrulha, plano 24 h, dimensionamento de frota e alertas.

**Repositório:** https://github.com/MakaG222/sad-ar5-vigilancia-costeira

## Arranque rápido (macOS)

```bash
cd plataforma
chmod +x setup-mac.sh start-mac.sh stop-mac.sh
./setup-mac.sh
./start-mac.sh
```

→ http://localhost:5173 · API: http://127.0.0.1:8080/docs

Windows: ver [`plataforma/README.md`](plataforma/README.md).

## Estrutura

```
├── plataforma/          # API FastAPI + interface React (Vite)
├── src/                 # Núcleo geoespacial (config, geo, risco, otimização, rotas)
├── dados/               # Fontes e intensidades processadas (grelha PT)
├── resultados/          # JSON de validação e camadas para a API
└── requirements.txt     # Dependências Python do núcleo + API
```

## Documentação

- [`plataforma/README.md`](plataforma/README.md) — instalação, URLs, funcionalidades
- [`plataforma/APRESENTACAO.md`](plataforma/APRESENTACAO.md) — roteiro de demo (5 min)

## Nota

O relatório académico (Word/PDF) **não** faz parte deste repositório; mantém-se apenas o código e dados necessários para executar a plataforma.
