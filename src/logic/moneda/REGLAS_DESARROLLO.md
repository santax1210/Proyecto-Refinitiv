# 📚 Reglas y Buenas Prácticas para Scripts del Pipeline

Esta guía define las reglas de organización, factoría y logging para todos los scripts del pipeline de conciliación de allocations.

---

## 1. Organización y Factorización de Scripts

- **Un script, una responsabilidad:**
  - Cada archivo debe tener una función principal clara y única.
  - Ejemplo: `load_allocations.py` carga Y procesa allocations (procesamiento completo en un solo lugar).

- **Funciones puras y reutilizables:**
  - Cada función debe recibir y retornar datos explícitamente (preferir DataFrames como entrada/salida).
  - Evitar efectos secundarios (no modificar variables globales ni escribir archivos salvo en scripts de orquestación).

- **Separación de lógica y ejecución:**
  - La lógica de negocio debe estar en funciones/módulos, no en el bloque `if __name__ == "__main__"`.
  - El bloque principal solo debe orquestar y mostrar resultados.

- **Consistencia en el procesamiento:**
  - Si dos dataframes similares (ej: allocations nuevas y antiguas) producen resultados similares (ej: 1 fila por instrumento con dominancia calculada), deben procesarse de la MISMA manera.
  - Evitar separar lógica en múltiples archivos cuando puede estar en uno solo.

- **Nombres descriptivos:**
  - Los nombres de scripts, funciones y variables deben reflejar su propósito.
  - Ejemplo: `calcular_dominancia_nuevas`, `crear_df_final`, `filtrar_balanceados`.

- **Documentación en cada archivo:**
  - Cada script debe iniciar con un docstring que explique su objetivo y uso.
  - Cada función debe tener docstring con parámetros y retornos.
  - Usar secciones con comentarios `# ====` para separar visualmente el código.

---

## 2. Estructura Recomendada de Scripts

```python
"""
Breve descripción del propósito del script.
"""
import pandas as pd


# ============================================================================
# FUNCIONES AUXILIARES (privadas, prefijo _)
# ============================================================================

def _funcion_auxiliar(...):
    """Descripción breve."""
    ...


# ============================================================================
# FUNCIÓN PRINCIPAL (pública, sin prefijo)
# ============================================================================

def funcion_principal(...):
    """
    Descripción detallada del propósito.
    
    PROCESO COMPLETO:
    1. Paso 1
    2. Paso 2
    3. Paso 3
    
    Parámetros:
        param1: Descripción
        param2: Descripción
    
    Retorna:
        Descripción del retorno
    """
    # PASO 1: Descripción
    ...
    
    # PASO 2: Descripción
    ...
    
    return resultado


# ============================================================================
# BLOQUE DE TEST Y EJECUCIÓN MANUAL
# ============================================================================

if __name__ == "__main__":
    # Tests con logging estructurado
    ...
```

---

## 3. Logging y Salidas en Consola

- **Secciones claras:**
  - Usa separadores visuales (`=` o `─`) para dividir fases y subfases.
  - Ejemplo:
    ```python
    print("\n" + "="*70)
    print(" FASE 1: CARGA DE DATOS ".center(70, "="))
    print("="*70)
    ```

- **Mensajes informativos y progresivos:**
  - Indica el paso actual y el resultado (✓/✗/⚠️).
  - Ejemplo:
    ```python
    print("[1/4] Cargando instrumentos...")
    print("  ✓ 1200 instrumentos cargados")
    ```

- **Errores y advertencias:**
  - Usa prefijos claros: `❌ ERROR: ...`, `⚠️  ADVERTENCIA: ...`
  - Si ocurre una excepción, muestra el tipo y mensaje.

- **Resumen final:**
  - Al terminar, imprime un resumen ejecutivo con totales y estadísticas clave.
  - Ejemplo:
    ```python
    print("\n" + "="*70)
    print(" RESUMEN FINAL ".center(70, "="))
    print("="*70)
    print(f"Total instrumentos: {total}")
    print(f"Balanceados: {balanceados}")
    print(f"Con cambios: {con_cambios}")
    ```

- **Logs técnicos vs usuario:**
  - Los scripts de lógica deben ser silenciosos o solo mostrar logs de test.
  - El orquestador (`run_pipeline.py` o `clasificacion.py`) debe mostrar logs amigables y estructurados.

---

## 4. Ejemplo de Logging Estandarizado

```python
print("\n" + "="*70)
print(" FASE 2: CLASIFICACIÓN Y DOMINANCIA ".center(70, "="))
print("="*70)

try:
    ... # lógica principal
    print("  ✓ Dominancia calculada correctamente")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")
```

---

## 5. Principios de Refactorización

- **No duplicar código:**
  - Si una función se repite, muévela a un módulo común.
  - Si dos procesos similares están en archivos separados, unifícalos.

- **Evitar archivos intermedios innecesarios:**
  - Si un archivo solo tiene una función que se usa en un solo lugar, muévelo.
  - Ejemplo: `escalado.py` fue eliminado porque su función se usaba solo en `load_allocations.py`.

- **Consistencia entre procesadores similares:**
  - `load_allocations_nuevas()` y `load_allocations_antiguas()` deben retornar estructuras similares.
  - Ambas retornan: 1 fila por instrumento con dominancia calculada.

---

## 6. Otras Reglas

- **No escribir archivos fuera de los scripts de orquestación.**

- **Incluye tests mínimos en cada módulo:**
  - Usa el bloque `if __name__ == "__main__"` para ejemplos de uso y validación rápida.

- **Mantén los scripts cortos y enfocados:**
  - Si un archivo crece demasiado, divídelo en módulos más pequeños.
  - Pero NO dividas si crea duplicación o inconsistencia.

---

## 7. Resumen Visual de Logging

```
======================================================================
==================== FASE 1: CARGA DE DATOS ==========================
======================================================================
[1/3] Cargando instrumentos...
  ✓ 1200 instrumentos cargados
[2/3] Cargando allocations nuevas...
  ✓ 1100 instrumentos procesados (con dominancia calculada)
    - Balanceados: 700
    - No balanceados: 400
[3/3] Cargando allocations antiguas...
  ✓ 1050 instrumentos procesados (con Pct_dominancia calculada)
----------------------------------------------------------------------
================ FASE 2: CLASIFICACIÓN Y DOMINANCIA =================
----------------------------------------------------------------------
[1/2] Verificando allocations nuevas...
  ✓ Columnas de dominancia presentes
----------------------------------------------------------------------
======================= RESUMEN FINAL ===============================

---

## 8. Columnas del df_final

| Columna | Origen | Descripción |
|---------|--------|-------------|
| `Nombre` | df_instruments | Nombre del instrumento |
| `ID` | df_instruments | Identificador único |
| `Tipo instrumento` | df_instruments | Tipo/categoría del instrumento |
| `moneda_antigua` | df_instruments.SubMoneda | Clasificación de moneda vigente en el sistema |
| `moneda_nueva` | df_dominancia_nuevas | Clasificación calculada en el pipeline (puede ser moneda ISO o "Balanceado") |
| `pct_dominancia_nuevo` | df_dominancia_nuevas | Porcentaje de la moneda dominante en las nuevas allocations |
| `pct_escalado` | df_dominancia_nuevas | Porcentaje escalado al 100% (solo positivos) |
| `pct_original` | df_dominancia_nuevas | Porcentaje original antes de escalar |
| `pct_dominancia_antigua` | df_dominancia_antiguas.Pct_dominancia | Porcentaje dominante en allocations antiguas (formato "MONEDA XX.XX%") |
| `Cambio` | Calculado | "Sí" / "No" / "Sin datos" según si cambió la moneda |
| `Estado` | Calculado | Estado_1 / Estado_2 / Estado_3 (ver sección 9) |
| `nivel_variacion` | Calculado | "Alta" / "Baja" / None según umbrales por tipo de métrica |
| `distancia_hellinger` | Calculado | Distancia de Hellinger (0–1) entre distribuciones antiguas y nuevas |
| `variacion_balanceados` | Calculado | Métrica de variación solo para `moneda_nueva == "Balanceado"` |
| `variacion_no_balanceados` | Calculado | Métrica de variación para todos los instrumentos NO balanceados |

---

## 9. Estados de Clasificación

La columna `Estado` clasifica cada instrumento según la transición entre su moneda antigua y nueva.

| Estado | Condición | Descripción |
|--------|-----------|-------------|
| `Estado_1` | Moneda → Misma Moneda | La clasificación no cambió (o ambas son Balanceado) |
| `Estado_2` | Moneda → Balanceado / Balanceado → Moneda | Cambio entre moneda específica y distribución balanceada |
| `Estado_3` | Moneda → Otra Moneda | La moneda dominante cambió a una distinta |
| `""` (vacío) | Sin datos en alguna columna | No se puede calcular el estado |

**Reglas específicas para balanceados** (`moneda_nueva == "Balanceado"`):
- Si `Moneda:` es `"FALTA ALLOCATION"` → `Estado_3`
- Si `moneda_antigua == "Balanceado"` → `Estado_1`
- Si `moneda_antigua` es una moneda específica → `Estado_2`

**Reglas para no balanceados** (`moneda_nueva` es una moneda ISO):
- Si `moneda_antigua == "Balanceado"` → `Estado_2`
- Si `moneda_antigua == moneda_nueva` → `Estado_1`
- Si `moneda_antigua != moneda_nueva` → `Estado_3`

---

## 10. Métricas de Variación

Todas las métricas se calculan en `crear_df_final.py` y se guardan como columnas del df_final.

### 10.1 Distancia de Hellinger (`distancia_hellinger`)

**Aplica a:** Todos los instrumentos.

**Fórmula:**
```
H = (1/√2) × √(Σ(√p_i - √q_i)²)
```
Donde `p_i` y `q_i` son los porcentajes normalizados de cada moneda en las distribuciones antigua y nueva respectivamente.

**Proceso por instrumento:**
1. Se identifican las **top 5 monedas** de ese instrumento en allocations antiguas (excluyendo `Balanceado`, `Otros`, `N/A`, `Global`).
2. Se extrae la distribución de esas 5 monedas en allocations antiguas.
3. Se extrae la distribución de las **mismas** 5 monedas en allocations nuevas (0% si no aparece).
4. Ambas distribuciones se normalizan al 100%.
5. Se calcula H con la fórmula anterior.

**Rango:** 0.0 (sin cambio) – 1.0 (cambio máximo / sin datos nuevos).

**Funciones:** `obtener_top_monedas_por_instrumento`, `calcular_distancia_hellinger`, `calcular_hellinger_por_instrumento`.

---

### 10.2 Variación Balanceados (`variacion_balanceados`)

**Aplica a:** Solo instrumentos con `moneda_nueva == "Balanceado"`.

La métrica varía según el `Estado`:

| Estado | Fórmula | Descripción |
|--------|---------|-------------|
| `Estado_1` (Bal→Bal) | Distancia de Hellinger | Compara las dos distribuciones |
| `Estado_2` (Mon→Bal) | `\|pct_antiguo - pct_misma_moneda_en_nueva\| / 100` | Cuánto cayó la moneda dominante antigua en la nueva distribución |
| Otros / Sin datos | `None` | No aplica |

**Ejemplo Estado_2:** CLP 100% antigua → CLP 18.3% nueva → `variacion = 0.817`

**Función:** `calcular_variacion_balanceados`.

---

### 10.3 Variación No Balanceados (`variacion_no_balanceados`)

**Aplica a:** Todos los instrumentos con `moneda_nueva != "Balanceado"`.

**Fórmula (misma para todos los Estados):**
```
variacion = |pct_moneda_dominante_antigua - pct_misma_moneda_en_nueva| / 100
```

Los porcentajes de nuevas allocations se escalan al 100% (solo positivos) antes de comparar.

**Función:** `calcular_variacion_no_balanceados`.

---

### 10.4 Nivel de Variación (`nivel_variacion`)

Clasificación binaria calculada a partir de las métricas anteriores:

| Tipo de instrumento | Métrica usada | Umbral Baja | Umbral Alta |
|---------------------|---------------|-------------|-------------|
| Balanceado Estado_1 (Bal→Bal) | Hellinger | ≤ 0.30 | > 0.30 |
| Balanceado Estado_2 (Mon→Bal) | Variación % | ≤ 0.40 | > 0.40 |
| No balanceado (todos los Estados) | Variación % | ≤ 0.40 | > 0.40 |
| Sin métricas calculadas | — | — | `None` |

**Función:** `calcular_nivel_variacion`.
----------------------------------------------------------------------
Total instrumentos: 1050
Balanceados: 200
Con cambios: 50
======================================================================
```

---

**Última actualización:** Febrero 2026  
**Cambios recientes:** Unificación de procesamiento de allocations en `load_allocations.py`
