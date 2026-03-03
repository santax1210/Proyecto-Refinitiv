# 🧪 Suite de Tests - Allocations Validation Pipeline

Conjunto completo de tests para validar el pipeline de procesamiento de allocations financieras.

## 📋 Índice de Tests

### 1. **test_carga_archivos.py** - Validación de Archivos Raw
**Objetivo:** Verificar que todos los archivos raw se puedan cargar correctamente.

**Valida:**
- ✅ Existencia de archivos en `data/raw/`
- ✅ Formato correcto (CSV con delimitador `;`)
- ✅ Encoding (latin-1)
- ✅ Columnas presentes en cada archivo
- ✅ Muestra de datos para inspección visual

**Uso:**
```bash
python tests/test_carga_archivos.py
```

---

### 2. **test_creacion_dataframes.py** - Creación de DataFrames
**Objetivo:** Validar que los extractores creen DataFrames correctamente.

**Valida:**
- ✅ `load_df_instruments()` - Cruce de posiciones + instrumentos
- ✅ `load_allocations_nuevas()` - Formato LONG con dominancia
- ✅ `load_allocations_antiguas()` - Formato WIDE con SubMoneda
- ✅ Todas las columnas requeridas están presentes
- ✅ Conteo de instrumentos únicos
- ✅ Mapeo de monedas a códigos ISO

**Uso:**
```bash
python tests/test_creacion_dataframes.py
```

**Nota:** Requiere que los archivos raw estén disponibles.

---

### 3. **test_mapeo_monedas.py** - Mapeo de Monedas (Refinitiv → ISO)
**Objetivo:** Validar que el mapeo de nombres de monedas funcione correctamente.

**Valida:**
- ✅ Diccionario `CURRENCY_MAP_REFINITIV_TO_ISO` (170+ mapeos)
- ✅ Monedas principales correctamente mapeadas (USD, EUR, JPY, CLP, etc.)
- ✅ Case-insensitivity (US Dollar = US DOLLAR = us dollar)
- ✅ Todos los nombres en archivos procesados son códigos ISO
- ✅ Formato de `pct_dominancia_nuevo` ("USD 49.42%")
- ✅ Consistencia entre allocations_nuevas y allocations_antiguas

**Uso:**
```bash
python tests/test_mapeo_monedas.py
```

**Requiere:** Pipeline ejecutado (archivos en `data/processed/`)

---

### 4. **test_dominancia.py** - Cálculos de Dominancia y Escalado
**Objetivo:** Validar cálculos matemáticos de dominancia y escalado de porcentajes.

**Valida:**
- ✅ Columnas de dominancia presentes (moneda_nueva, pct_dominancia_nuevo, etc.)
- ✅ `pct_escalado = 100.0` para cada instrumento (tolerancia 0.01%)
- ✅ `suma(percentage) = pct_original` (consistencia)
- ✅ Clasificación correcta: Balanceado vs Moneda dominante (umbral 90%)
- ✅ Formato de `pct_dominancia_nuevo` ("MONEDA XX.XX%")
- ✅ Estadísticas generales (distribución de clasificación)

**Uso:**
```bash
python tests/test_dominancia.py
```

**Requiere:** Pipeline ejecutado

---

### 5. **test_formato_archivos.py** - Formato de Archivos (LONG/WIDE)
**Objetivo:** Validar que los archivos tengan el formato correcto.

**Valida:**

#### allocations_nuevas.csv (LONG):
- ✅ Múltiples filas por instrumento
- ✅ Exactamente 10 columnas
- ✅ Columna `class` con moneda
- ✅ Columna `percentage` con porcentaje
- ✅ Sin columnas por moneda

#### allocations_antiguas.csv (WIDE):
- ✅ Una fila por instrumento
- ✅ ~80 columnas (variable)
- ✅ Columnas por moneda (USD, EUR, CLP, etc.)
- ✅ Columnas `SubMoneda` y `Pct_dominancia` presentes

#### Consistencia:
- ✅ IDs consistentes entre archivos
- ✅ Cobertura de instrumentos

**Uso:**
```bash
python tests/test_formato_archivos.py
```

**Requiere:** Pipeline ejecutado

---

### 6. **test_exports.py** - Generación y Validación de Exports
**Objetivo:** Validar la correcta generación y estructura de los archivos de exportación.

**Valida:**

#### Export Balanceados:
- ✅ Estructura correcta de columnas (ID, Instrumento, Id_ti_valor, Id_ti, Fecha, Clasificacion, Moneda Anterior, Estado, pct_original, [monedas])
- ✅ Formato WIDE: columnas dinámicas por moneda (USD, CLP, EUR, etc.)
- ✅ Lógica de Estado:
  - Estado_1: Balanceado → Balanceado
  - Estado_2: Moneda → Balanceado
  - Estado_3: Solo si SubMoneda es "unassigned"
- ✅ Lógica de Fecha:
  - "31-12-2019" si SubMoneda es "unassigned"
  - Primer día del mes actual en caso contrario
- ✅ Clasificacion = "SubMoneda" (literal)
- ✅ Id_ti contiene el tipo de identificador usado (RIC, Isin, Cusip)

#### Export No Balanceados:
- ✅ Estructura correcta de columnas (ID, Instrumento, SubMoneda, Moneda Anterior, Estado, Sobreescribir)
- ✅ Lógica de Estado:
  - Estado_1: Moneda → Misma Moneda
  - Estado_2: Balanceado → Moneda
  - Estado_3: Moneda → Otra Moneda
- ✅ Sobreescribir: "Sí" si hay cambio, "No" si no hay cambio

#### Integridad:
- ✅ Sin IDs duplicados en ningún export
- ✅ Cobertura completa de instrumentos entre ambos exports
- ✅ Solo valores válidos en columnas calculadas

**Uso:**
```bash
python tests/test_exports.py
```

**Requiere:** Pipeline ejecutado

---

### 7. **test_pipeline_completo.py** - Pipeline Completo (End-to-End)
**Objetivo:** Test de integración completo desde raw hasta exports.

**Valida:**
- ✅ Existencia de archivos raw
- ✅ Ejecución exitosa de `run_pipeline.py`
- ✅ Generación de archivos procesados:
  - `df_instruments.csv`
  - `allocations_nuevas.csv`
  - `allocations_antiguas.csv`
  - `df_final.csv`
- ✅ Generación de archivos de exportación:
  - `export_balanceados.csv`
  - `export_no_balanceados.csv`
  - `export_con_cambios.csv`
- ✅ Validación de contenido de cada archivo
- ✅ Integridad de datos (IDs, cobertura)

**Uso:**
```bash
python tests/test_pipeline_completo.py
```

**Nota:** Este test ejecuta el pipeline completo, puede tomar ~30-60 segundos.

---

### 8. **test_backend_frontend_integration.py** - Integración Backend-Frontend
**Objetivo:** Validar que los datos se pasen correctamente desde el backend (Python/Flask) al frontend (React/JSON).

**Valida:**

#### Estructura de Resultados:
- ✅ `ejecutar_pipeline_completo()` retorna todas las claves esperadas
- ✅ Clave `exports` contiene: balanceados, no_balanceados, con_cambios, sin_datos
- ✅ Estructura de resultados coincide con lo que el endpoint `/api/results/validation` espera

#### Columnas de df_final:
- ✅ Todas las columnas críticas presentes: ID, Nombre, moneda_nueva, Pct_dominancia, Cambio, Estado
- ✅ Columnas disponibles para la tabla de validación en el frontend

#### Serialización JSON:
- ✅ df_final se puede convertir a dict con `.to_dict(orient='records')`
- ✅ Los datos se pueden serializar a JSON string (sin errores de encoding)
- ✅ JSON deserializable correctamente
- ✅ Tamaño del JSON razonable para transferencia HTTP

#### Estructura del Summary:
- ✅ Summary contiene: total_instrumentos, balanceados, no_balanceados, con_cambios, sin_datos
- ✅ Summary serializable a JSON

#### Validación de Valores:
- ✅ Columna `Estado` tiene solo valores válidos: Estado_1, Estado_2, Estado_3, o vacío
- ✅ Columna `Cambio` tiene solo valores válidos: Si, No, o vacío

**Uso:**
```bash
python tests/test_backend_frontend_integration.py
```

**Requiere:** Pipeline ejecutado

**Propósito:** Este test es crítico para asegurar que no haya errores de serialización o incompatibilidades entre el backend Python y el frontend React. Valida el contrato de datos entre ambos sistemas.

---

## 🚀 Ejecutar Todos los Tests

### Opción 1: Script ejecutor maestro
```bash
python tests/run_all_tests.py
```

Este script ejecuta todos los tests en secuencia y muestra un resumen final.

### Opción 2: Manualmente (en orden)
```bash
python tests/test_carga_archivos.py
python tests/test_creacion_dataframes.py
python tests/test_mapeo_monedas.py
python tests/test_dominancia.py
python tests/test_formato_archivos.py
python tests/test_pipeline_completo.py
```

---

## 📊 Estructura de Salida

Cada test muestra:
- ✅ **Checks exitosos** - en verde
- ❌ **Errores** - en rojo con detalles
- ℹ️ **Información** - estadísticas y muestras de datos
- ⚠️ **Advertencias** - potenciales problemas pero no críticos

### Exit Codes:
- `0` - Test pasó exitosamente
- `1` - Test falló

---

## 🔧 Requisitos

### Archivos Raw Necesarios:
```
data/raw/
  ├── instruments.csv
  ├── posiciones.csv
  ├── allocations_nuevas.csv
  └── allocations_currency.csv
```

### Dependencias Python:
```
pandas >= 2.0.0
numpy >= 1.24.0
```

---

## 📝 Notas Importantes

1. **Orden de ejecución:**
   - `test_carga_archivos.py` y `test_creacion_dataframes.py` se pueden ejecutar con solo archivos raw
   - Los demás tests requieren que el pipeline se haya ejecutado primero

2. **Ejecución del pipeline:**
   ```bash
   python run_pipeline.py
   ```

3. **Tolerance levels:**
   - Escalado: 0.01% de tolerancia para errores de redondeo
   - Sumas: 0.1 unidades de tolerancia

4. **Performance:**
   - Tests de validación: < 5 segundos cada uno
   - Test completo (pipeline): 30-60 segundos

---

## 🐛 Solución de Problemas

### "FileNotFoundError: archivo no encontrado"
**Solución:** Ejecute `python run_pipeline.py` primero.

### "ImportError: No module named 'src'"
**Solución:** Ejecute desde el directorio raíz del proyecto.

### Tests fallan con formato incorrecto
**Solución:** Verifique que el pipeline se ejecutó correctamente y los archivos en `data/processed/` fueron generados.

---

## 📈 Métricas de Éxito

Un pipeline exitoso debe cumplir:
- ✅ 100% de tests pasando
- ✅ 4,500+ instrumentos procesados
- ✅ 97%+ de cobertura de mapeo de monedas
- ✅ pct_escalado = 100.0 en todos los casos
- ✅ Formato LONG con 10 columnas (nuevas)
- ✅ Formato WIDE con ~80 columnas (antiguas)

---

## 🔄 Actualización de Tests

Cuando se modifique el pipeline:
1. Actualice los tests afectados
2. Ejecute `run_all_tests.py` para verificar
3. Documente cambios en este README
4. Actualice umbral/tolerancias si es necesario

---

## 📧 Soporte

Para problemas con los tests, revise:
1. Logs de ejecución del test
2. Salida del pipeline (`run_pipeline.py`)
3. Estructura de archivos generados
4. Documentación en `REGLAS_DESARROLLO.md`

---

**Última actualización:** 2026-02-26
**Versión del pipeline:** 2.0 (Post-refactorización)
