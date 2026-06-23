# Dados de entrada — SAD AR5

Fontes usadas pelo núcleo (`src/`) e pela API em runtime.

## Estrutura

| Pasta / ficheiro | Origem | Uso |
|------------------|--------|-----|
| `fontes/apreensoes_droga_PT.xlsx` | SICAD / relatórios públicos | KDE droga, mapa de apreensões |
| `fontes/imigracao_pt_costa.csv` | SEF / Frontex (agregado) | Risco imigração costeira PT |
| `fontes/iom_missing_migrants.csv` | IOM Missing Migrants | Incidentes marítimos (camada IOM) |
| `fontes/emodnet/*.tif` | [EMODnet Human Activities](https://emodnet.ec.europa.eu/) | Densidade de embarcações (pesca, carga, etc.) |
| `processados/intensidades_reais.csv` | Gerado a partir dos rasters | Campo de risco pesca/poluição na grelha |

## Regenerar intensidades

Requer Python com `rasterio` (não incluído no runtime da plataforma):

```bash
pip install rasterio numpy pandas
python -c "from src.risco import ..."  # pipeline analítico completo fora do repo Docker
```

Em runtime Docker/local, a API lê `processados/intensidades_reais.csv` já pré-calculado.

## Licenças

- **EMODnet:** dados europeus de atividades humanas no mar — consultar termos EMODnet.
- **IOM:** dados abertos com atribuição à IOM Missing Migrants Project.
- **Apreensões / imigração:** agregações para fins académicos (CT302); não redistribuir dados brutos sem verificar restrições das fontes.
