# Reglas de Desarrollo — Pipeline de Región

> Este documento extiende las reglas generales de `src/logic/moneda/REGLAS_DESARROLLO.md`.
> Aplican todas las mismas reglas de organización, logging y factorización; aquí se documentan
> únicamente las diferencias y especificidades del pipeline de región.

---

## 1. Objetivo

Validar y generar allocations de **región** para instrumentos financieros,
siguiendo el mismo enfoque que el pipeline de moneda pero aplicado a la clasificación geográfica.

---

## 2. Módulos del Pipeline

| Módulo | Responsabilidad |
|--------|----------------|
| `src/extractors/region/load_allocations_region.py` | Carga, cruce y cálculo de dominancia por región |
| `src/logic/region/clasificacion_region.py` | Orquestador principal |
| `src/logic/region/crear_df_final_region.py` | Ensamblaje del df_final y cálculo de métricas |
| `src/logic/region/generar_exports_region.py` | Exportación de archivos finales |

El maestro de instrumentos (`load_instruments_region`) es compartido con moneda — usa el mismo archivo fuente.

---

## 3. Estructura de Archivos

### Inputs esperados
- `data/raw/instruments.csv` — Maestro de instrumentos (compartido con moneda)
- `data/raw/posiciones.csv` — Posiciones (compartido con moneda)
- `data/raw/region/allocations_nuevas_region.csv` — Nuevas allocations filtradas por `classif == 'region'`
- `data/raw/region/allocations_region.csv` — Allocations antiguas de región

### Outputs generados
- `data/processed/region/` — DataFrames intermedios (df_final_region, allocations_nuevas_region, etc.)
- `data/exports/region/` — Archivos finales para importar al sistema externo

---

## 4. Diferencias Clave vs Pipeline de Moneda

| Aspecto | Moneda | Región |
|---------|--------|--------|
| Columna de clasificación antigua | `SubMoneda` (de df_instruments) | `Pct_dominancia` de antiguas (se extrae el nombre de región) |
| Columna de estado en antiguas | `Moneda:` | `Base Region:` |
| Trigger de Estado_3 en balanceados | `Moneda: == "FALTA ALLOCATION"` | `Base Region: == "FALTA ALLOCATION"` o `"SIN ASIGNAR"` |
| Columna de clasificación en nuevas | `class` | `region` |
| Columna en df_final | `moneda_nueva`, `moneda_antigua` | `region_nueva`, `region_antigua` |
| Subcarpeta datos | `data/raw/`, `data/processed/` | `data/raw/region/`, `data/processed/region/` |
| Nombre de export no balanceados | columna "Moneda Anterior" | columna "Region Anterior" |
| Fecha en balanceados Estado_3 | `"31-12-2019"` | `"31-12-2019"` (igual) |
| Normalización | Códigos ISO de moneda | `normalizar_nombre_region()` (nombres geográficos) |

---

## 5. Columnas del df_final_region

| Columna | Origen | Descripción |
|---------|--------|-------------|
| `Nombre` | df_instruments | Nombre del instrumento |
| `ID` | df_instruments | Identificador único |
| `Tipo instrumento` | df_instruments | Tipo/categoría del instrumento |
| `region_antigua` | Extraída de df_dominancia_antiguas.Pct_dominancia | Región dominante vigente en el sistema |
| `region_nueva` | df_dominancia_nuevas_region | Clasificación de región calculada (puede ser nombre o "Balanceado") |
| `pct_dominancia_nuevo` | df_dominancia_nuevas_region | Porcentaje de la región dominante en las nuevas allocations |
| `pct_escalado` | df_dominancia_nuevas_region | Porcentaje escalado al 100% (solo positivos) |
| `pct_original` | df_dominancia_nuevas_region | Porcentaje original antes de escalar |
| `pct_dominancia_antigua` | df_dominancia_antiguas.Pct_dominancia | Porcentaje dominante en allocations antiguas (formato "REGION XX.XX%") |
| `Base Region:` | df_dominancia_antiguas | Estado de la región en el sistema antiguo |
| `Cambio` | Calculado | "Sí" / "No" / "Sin datos" |
| `Estado` | Calculado | Estado_1 / Estado_2 / Estado_3 (ver sección 6) |
| `nivel_variacion` | Calculado | "Alta" / "Baja" / None según umbrales |
| `distancia_hellinger` | Calculado | Distancia de Hellinger (0–1) entre distribuciones |
| `variacion_balanceados` | Calculado | Métrica solo para `region_nueva == "Balanceado"` |
| `variacion_no_balanceados` | Calculado | Métrica para todos los instrumentos NO balanceados |

---

## 6. Estados de Clasificación

| Estado | Condición | Descripción |
|--------|-----------|-------------|
| `Estado_1` | Región → Misma Región (o Balanceado → Balanceado) | Sin cambio de clasificación |
| `Estado_2` | Región → Balanceado / Balanceado → Región | Cambio entre región específica y distribución balanceada |
| `Estado_3` | Región → Otra Región, o `Base Region:` es `"FALTA ALLOCATION"` / `"SIN ASIGNAR"` | Cambio de región o sin datos de sistema |
| `""` (vacío) | Sin datos en alguna columna | No calculable |

**Reglas específicas para balanceados** (`region_nueva == "Balanceado"`):
- `Base Region:` == `"FALTA ALLOCATION"` o `"SIN ASIGNAR"` → `Estado_3`
- `region_antigua == "Balanceado"` → `Estado_1`
- `region_antigua` es una región específica → `Estado_2`

**Normalización de nombres:** se usa `normalizar_nombre_region()` para comparar regiones (elimina tildes, unifica mayúsculas/minúsculas y variantes de nombres).

---

## 7. Métricas de Variación

Implementadas en `crear_df_final_region.py`. La lógica es idéntica a moneda, adaptada para regiones.

### 7.1 Distancia de Hellinger (`distancia_hellinger`)

**Aplica a:** Todos los instrumentos.

**Proceso por instrumento:**
1. Se identifican las **top 5 regiones** del instrumento en allocations antiguas, excluyendo: `N/A`, `Otros`, `World`, `Globales`, `Global Des.`, `Global Eme.`, `Temáticos`.
2. Se extrae la distribución de esas 5 regiones en allocations antiguas.
3. Se extrae la distribución de las **mismas** 5 regiones en allocations nuevas (0% si no aparece).
4. Ambas se normalizan al 100% y se calcula H.

**Fórmula:** `H = (1/√2) × √(Σ(√p_i - √q_i)²)` — igual que moneda.

**Rango:** 0.0 (sin cambio) – 1.0 (cambio máximo / sin datos nuevos).

**Funciones:** `obtener_top_regiones_por_instrumento`, `calcular_distancia_hellinger_region`, `calcular_hellinger_por_instrumento_region`.

---

### 7.2 Variación Balanceados (`variacion_balanceados`)

**Aplica a:** Solo instrumentos con `region_nueva == "Balanceado"`.

| Estado | Fórmula | Descripción |
|--------|---------|-------------|
| `Estado_1` (Bal→Bal) | Distancia de Hellinger | Compara las dos distribuciones de regiones |
| `Estado_2` (Región→Bal) | `\|pct_antiguo - pct_misma_region_en_nueva\| / 100` | Cuánto cayó la región dominante antigua en la nueva distribución |
| Otros | `None` | No aplica |

El porcentaje de nuevas allocations se escala al 100% antes de comparar.

**Función:** `calcular_variacion_balanceados_region`.

---

### 7.3 Variación No Balanceados (`variacion_no_balanceados`)

**Aplica a:** Todos los instrumentos con `region_nueva != "Balanceado"`.

**Fórmula:**
```
variacion = |pct_region_dominante_antigua - pct_misma_region_en_nueva| / 100
```

La comparación usa `normalizar_nombre_region()` para hacer match correcto entre variantes de nombre.

**Función:** `calcular_variacion_no_balanceados_region`.

---

### 7.4 Nivel de Variación (`nivel_variacion`)

Umbrales idénticos a moneda:

| Tipo de instrumento | Métrica | Umbral Baja | Umbral Alta |
|---------------------|---------|-------------|-------------|
| Balanceado Estado_1 (Bal→Bal) | Hellinger | ≤ 0.30 | > 0.30 |
| Balanceado Estado_2 (Región→Bal) | Variación % | ≤ 0.40 | > 0.40 |
| No balanceado (todos los Estados) | Variación % | ≤ 0.40 | > 0.40 |
| Sin métricas calculadas | — | — | `None` |

**Función:** `calcular_nivel_variacion_region`.
