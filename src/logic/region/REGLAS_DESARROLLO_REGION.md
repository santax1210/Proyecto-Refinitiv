# Reglas de Desarrollo — Pipeline de Región

## Objetivo
Validar y generar allocations de **región** para instrumentos financieros,
siguiendo el mismo enfoque que el pipeline de moneda pero aplicado a la clasificación geográfica.

## Clasificación de Instrumentos por Región
- **Balanceado**: Ninguna región supera el umbral de dominancia (por definir)
- **Región específica**: Una región supera el umbral → se clasifica con esa región

## Estructura de Archivos

### Inputs esperados (data/raw/region/)
- `allocations_nuevas_region.csv` → Nuevas allocations filtradas por classif == 'region'
- `allocations_antiguas_region.csv` → Allocations actuales de región en el sistema

### Outputs generados
- `data/processed/region/` → DataFrames intermedios para análisis técnico
- `data/exports/region/` → Archivos finales para importar al sistema externo

## Reglas de Dominancia (por definir)
- Umbral de dominancia: TBD (referencia moneda: 90%)
- Lógica de escalado: Igual que moneda (proporcional al 100%)

## Módulos del Pipeline
1. `src/extractors/region/load_allocations_region.py` — Carga y cruce de datos
2. `src/logic/region/clasificacion_region.py` — Orquestador principal
3. `src/logic/region/crear_df_final_region.py` — Ensamblaje final
4. `src/logic/region/generar_exports_region.py` — Exportación

## Notas
- El maestro de instrumentos (`load_instruments`) es compartido con moneda
- Las rutas de datos están separadas en `data/raw/region/`, `data/processed/region/`, `data/exports/region/`
