# Plataforma SAD AR5 — versão apresentação (v0.4)

Versão optimizada para **defesa do projecto** e demo em sala.

## Novidades desta versão

1. **Modo apresentação** (activo por defeito) — mapa leve: bases, clusters, corredor, AIS e rota.
2. **Demo offline** — meteo/IPMA/RSS com fallback local se não houver rede.
3. **Feedback de rotas** — botão «A calcular…» + toast com distância, pontos e zona.

## Arranque

```bash
cd plataforma
./setup-mac.sh    # 1.ª vez
./start-mac.sh
```

Abrir: http://localhost:5173

## Roteiro de demo (5 min)

1. Mostrar barra de estado (frota 9 AR5, alto risco 274, ganho 2,13×).
2. Separador **Operação** → escolher base Portimão → **Calcular rota** (sortie).
3. Apontar zona k-means no mapa e rota laranja.
4. **Sim. spoofing** → alerta em tempo real.
5. Separador **Camadas** → ligar Apreensões ou EMODnet se o júri perguntar.
6. Botão **Modo completo** se quiserem ver todas as camadas.

## Sem internet

A plataforma continua a funcionar: grelha SAD, frota, rotas, clusters e camadas locais.
O indicador **Offline OK** aparece no topo quando meteo/IPMA/RSS estão em cache.

## Parar

```bash
./stop-mac.sh
```
