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
----------------------------------------------------------------------
Total instrumentos: 1050
Balanceados: 200
Con cambios: 50
======================================================================
```

---

**Última actualización:** Febrero 2026  
**Cambios recientes:** Unificación de procesamiento de allocations en `load_allocations.py`
