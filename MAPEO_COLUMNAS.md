# 🔄 Mapeo de Columnas: Backend ↔ Frontend

## ✅ Solución Implementada

Se agregó transformación de columnas en el backend (`api/app.py`) para que el frontend reciba los datos correctamente estructurados.

**IMPORTANTE:** NO se mapea directamente `moneda_nueva` → `estado`. En su lugar:
- `moneda_nueva` se mantiene con su valor real (USD, CLP, EUR, Balanceado, etc.)
- `estado` se CALCULA a partir de `moneda_nueva` con 3 categorías: "Balanceado", "No Balanceado", "Sin datos"

---

## 📋 Tabla de Mapeo

| Backend (Python CSV) | Frontend (React JSON) | Cálculo | Descripción |
|---------------------|----------------------|---------|-------------|
| `Nombre` | `instrumento` | Renombrar | Nombre del instrumento financiero |
| `ID` | `id_inst` | Renombrar | ID único del instrumento |
| - | `id` | Calcular | ID como string para selección en el frontend |
| `Tipo instrumento` | `tipo` | Renombrar | Tipo: Renta Fija, Renta Variable, ETF, etc. |
| `moneda_antigua` | `moneda_antigua` | Mantener | Moneda de la clasificación antigua (SubMoneda) |
| `moneda_nueva` | `moneda_nueva` | Mantener | Nueva clasificación: USD, CLP, EUR, Balanceado, etc. |
| `moneda_nueva` | **`estado`** | **CALCULAR** | **Categoría: "Balanceado", "No Balanceado", "Sin datos"** |
| `moneda_nueva` | `estado_idx` | Calcular | Índice numérico: 1=Balanceado, 2=No Balanceado, 3=Sin datos |
| `pct_dominancia_nuevo` | `pct_nuevo` | Renombrar | % de dominancia en la nueva clasificación |
| `pct_escalado` | `pct_escalado` | Mantener | % escalado del cálculo de dominancia |
| `pct_original` | `pct_original` | Mantener | % original antes del escalado |
| `pct_dominancia_antigua` | `pct_antiguo` | Renombrar | % de dominancia en la clasificación antigua |
| `Cambio` | `cambio` | Renombrar | Si hubo cambio entre clasificaciones (Sí/No/Sin datos) |

---

## 🔍 Diferencia entre `moneda_nueva` y `estado`

### ❌ ERROR COMÚN

**NO** mapear directamente `moneda_nueva` → `estado`. Son conceptos diferentes:

### ✅ CORRECTO

**`moneda_nueva`**: Clasificación específica del instrumento
- Valores: "Balanceado", "USD", "CLP", "EUR", "AUD", "JPY", etc.
- Representa la moneda dominante calculada por el pipeline

**`estado`**: Categoría simplificada para filtros en el UI
- Valores: SOLO "Balanceado", "No Balanceado", "Sin datos"
- Se CALCULA a partir de `moneda_nueva`:
  ```python
  def calcular_estado_categoria(moneda):
      moneda_str = str(moneda).strip().upper()
      if moneda_str == 'BALANCEADO':
          return 'Balanceado'
      elif moneda_str in ['', 'NAN', 'NONE', 'SIN DATOS']:
          return 'Sin datos'
      else:
          # Cualquier moneda específica (USD, CLP, EUR, etc.)
          return 'No Balanceado'
  ```

### ⚠️ Confusión con `Estado` de exports

En `generar_exports.py` existe una columna **`Estado`** con valores "Estado_1", "Estado_2", "Estado_3".

**PERO** esta columna:
- Solo existe en los archivos CSV de export (export_balanceados.csv, export_no_balanceados.csv)
- NO existe en `df_final.csv` que es lo que muestra la tabla de validación
- Representa el tipo de transición entre clasificaciones antigua y nueva

---

## 📂 Archivos Modificados

### 1. `api/app.py`

**Endpoint:** `/api/results/validation`

```python
# Se agregó mapeo de columnas
column_mapping = {
    'Nombre': 'instrumento',
    'ID': 'id_inst',
    'Tipo instrumento': 'tipo',
    'moneda_antigua': 'moneda_antigua',
    'moneda_nueva': 'estado',
    'pct_dominancia_nuevo': 'pct_nuevo',
    'pct_escalado': 'pct_escalado',
    'pct_original': 'pct_original',
    'pct_dominancia_antigua': 'pct_antiguo',
    'Cambio': 'cambio'
}

df = df.rename(columns=existing_columns)
```

**Endpoint:** `/api/results/exports/<tipo>`

```python
# Mismo mapeo para exports
df = df.rename(columns=existing_columns)
```

---

## 🔍 Ejemplo de Transformación

### Antes (CSV en backend - df_final.csv):

```csv
Nombre,ID,Tipo instrumento,moneda_antigua,moneda_nueva,pct_dominancia_nuevo,pct_dominancia_antigua,Cambio
FM BCI Gestión Global Dinámica 80,23,Renta Variable,CLP,Balanceado,98.5,100.0,Sí
Fondo Mutuo USD Agresivo,45,Renta Variable,CLP,USD,92.3,85.0,Sí
ETF Europeo Diversificado,67,ETF,USD,EUR,88.7,90.2,Sí
```

### Transformación en backend (api/app.py):

```python
# 1. Renombrar columnas
df = df.rename(columns={
    'Nombre': 'instrumento',
    'ID': 'id_inst',
    'Tipo instrumento': 'tipo',
    'moneda_nueva': 'moneda_nueva',  # Se mantiene
    'pct_dominancia_antigua': 'pct_antiguo',
    'pct_dominancia_nuevo': 'pct_nuevo'
})

# 2. CALCULAR la columna 'estado' a partir de 'moneda_nueva'
def calcular_estado_categoria(moneda):
    moneda_str = str(moneda).strip().upper()
    if moneda_str == 'BALANCEADO':
        return 'Balanceado'
    elif moneda_str in ['', 'NAN', 'NONE', 'SIN DATOS']:
        return 'Sin datos'
    else:
        return 'No Balanceado'  # USD, CLP, EUR, etc.

df['estado'] = df['moneda_nueva'].apply(calcular_estado_categoria)

# 3. Calcular estado_idx para filtros
df['estado_idx'] = df['estado'].apply(lambda x: 
    1 if x == 'Balanceado' 
    else 3 if x == 'Sin datos' 
    else 2
)

# 4. Agregar ID para selección
df['id'] = df['id_inst'].astype(str)
```

### Después (JSON al frontend):

```json
[
  {
    "instrumento": "FM BCI Gestión Global Dinámica 80",
    "id_inst": "23",
    "id": "23",
    "tipo": "Renta Variable",
    "moneda_antigua": "CLP",
    "moneda_nueva": "Balanceado",
    "estado": "Balanceado",
    "estado_idx": 1,
    "pct_nuevo": 98.5,
    "pct_antiguo": 100.0,
    "cambio": "Sí"
  },
  {
    "instrumento": "Fondo Mutuo USD Agresivo",
    "id_inst": "45",
    "id": "45",
    "tipo": "Renta Variable",
    "moneda_antigua": "CLP",
    "moneda_nueva": "USD",
    "estado": "No Balanceado",
    "estado_idx": 2,
    "pct_nuevo": 92.3,
    "pct_antiguo": 85.0,
    "cambio": "Sí"
  },
  {
    "instrumento": "ETF Europeo Diversificado",
    "id_inst": "67",
    "id": "67",
    "tipo": "ETF",
    "moneda_antigua": "USD",
    "moneda_nueva": "EUR",
    "estado": "No Balanceado",
    "estado_idx": 2,
    "pct_nuevo": 88.7,
    "pct_antiguo": 90.2,
    "cambio": "Sí"
  }
]
```

---

## 🎯 Uso en el Frontend

### ValidacionPage.jsx

```jsx
// Acceso a los datos mapeados:
<div>{row.instrumento}</div>              // ✅ "FM BCI Gestión Global Dinámica 80"
<div>{row.id_inst}</div>                  // ✅ "23"
<EstadoPill estado={row.estado} />        // ✅ "Balanceado" (NO "USD", "EUR", etc.)
<div>{row.moneda_nueva}</div>             // ✅ "USD" (valor específico de moneda)
<div>{row.moneda_antigua}</div>           // ✅ "CLP"
<div>{row.pct_antiguo}%</div>             // ✅ "100.0%"
```

### EstadoPill Component

El componente espera uno de estos 3 valores EXACTOS:

```jsx
const ESTADO_CFG = {
    'Balanceado': { dot: '#299D91', bg: '#EBF7F6', text: '#299D91' },
    'No Balanceado': { dot: '#F0A050', bg: '#FFF7ED', text: '#D97706' },
    'Sin datos': { dot: '#9F9F9F', bg: '#F3F4F6', text: '#71717A' },
};

// ❌ INCORRECTO: <EstadoPill estado={row.moneda_nueva} />  
//    Esto mostraría "USD", "EUR", etc. que NO están en ESTADO_CFG

// ✅ CORRECTO: <EstadoPill estado={row.estado} />
//    Esto muestra solo "Balanceado", "No Balanceado", "Sin datos"
```

### Filtros y Búsqueda

```jsx
// Filtro por estado usando estado_idx
const filtered = data.filter(r => 
    !filterEstadoIdx || r.estado_idx === filterEstadoIdx
);
// filterEstadoIdx: 1 = Balanceado, 2 = No Balanceado, 3 = Sin datos

// Búsqueda en múltiples campos
const matchSearch = !search ||
    r.instrumento.toLowerCase().includes(search.toLowerCase()) ||
    r.id_inst.toLowerCase().includes(search.toLowerCase()) ||
    r.moneda_antigua.toLowerCase().includes(search.toLowerCase()) ||
    r.moneda_nueva.toLowerCase().includes(search.toLowerCase());  // Buscar por moneda específica
```

---

## ✨ Campos Calculados en el Backend

### `estado` (NUEVO - Calculado)

**Cálculo:**
```python
def calcular_estado_categoria(moneda):
    moneda_str = str(moneda).strip().upper()
    if moneda_str == 'BALANCEADO':
        return 'Balanceado'
    elif moneda_str in ['', 'NAN', 'NONE', 'SIN DATOS']:
        return 'Sin datos'
    else:
        return 'No Balanceado'  # USD, CLP, EUR, AUD, etc.

df['estado'] = df['moneda_nueva'].apply(calcular_estado_categoria)
```

**Valores posibles:**
- `"Balanceado"` - Instrumento con clasificación balanceada
- `"No Balanceado"` - Instrumento con moneda específica (USD, CLP, EUR, etc.)
- `"Sin datos"` - Instrumento sin información de clasificación

**Uso en frontend:**
```jsx
// Para mostrar pill de estado
<EstadoPill estado={row.estado} />

// Para filtrar por categoría
if (row.estado === 'Balanceado') { /* ... */ }
```

### `estado_idx` (Calculado)

**Cálculo:**
```python
df['estado_idx'] = df['estado'].apply(lambda x: 
    1 if x == 'Balanceado' 
    else 3 if x == 'Sin datos' 
    else 2
)
```

**Valores:**
- `1` = Balanceado
- `2` = No Balanceado
- `3` = Sin datos

**Uso en frontend:**
```jsx
// Filtrar por tipo de estado usando índice numérico
if (filterEstadoIdx === 1) {
    // Mostrar solo balanceados
} else if (filterEstadoIdx === 2) {
    // Mostrar solo no balanceados (USD, CLP, EUR, etc.)
} else if (filterEstadoIdx === 3) {
    // Mostrar solo sin datos
}
```

### `id` (Calculado)

**Cálculo:**
```python
df['id'] = df['id_inst'].astype(str)
```

**Uso en frontend:**
```jsx
// Para selección de filas
const toggleRow = (id) =>
    setSelected(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id]);

// Para navegación
onClick={() => { onSelect(row.id); onNavigate('visualizacion'); }}
```

---

## 🧪 Testing

### 1. Verificar que el backend calcula correctamente:

```powershell
# Iniciar backend
python api/app.py

# En otra terminal, hacer request
$response = Invoke-WebRequest http://localhost:5000/api/results/validation | ConvertFrom-Json
$response.data | Select-Object -First 3 | Format-Table instrumento, id_inst, moneda_nueva, estado, estado_idx
```

**Debe mostrar:**
```
instrumento                           id_inst  moneda_nueva  estado         estado_idx
-----------                           -------  ------------  ------         ----------
FM BCI Gestión Global Dinámica 80    23       Balanceado    Balanceado     1
Fondo Mutuo USD Agresivo             45       USD           No Balanceado  2
ETF Europeo Diversificado            67       EUR           No Balanceado  2
```

### 2. Verificar en el frontend:

```javascript
// En DevTools Console (F12)
fetch('http://localhost:5000/api/results/validation')
    .then(r => r.json())
    .then(data => {
        console.log('Primera fila:', data.data[0]);
        console.log('Columnas:', Object.keys(data.data[0]));
        console.log('\nVerificar cálculo de estado:');
        data.data.slice(0, 5).forEach(row => {
            console.log(`${row.instrumento}: moneda_nueva="${row.moneda_nueva}" → estado="${row.estado}"`);
        });
    });
```

**Debe mostrar:**
```
Primera fila: {instrumento: "FM BCI...", moneda_nueva: "Balanceado", estado: "Balanceado", ...}
Columnas: ["instrumento", "id_inst", "tipo", "moneda_antigua", "moneda_nueva", "estado", ...]

Verificar cálculo de estado:
FM BCI Gestión...: moneda_nueva="Balanceado" → estado="Balanceado"
Fondo Mutuo USD...: moneda_nueva="USD" → estado="No Balanceado"
ETF Europeo...: moneda_nueva="EUR" → estado="No Balanceado"
```

### 3. Verificar EstadoPill en UI:

El pill debe mostrar SOLO estos valores:
- ✅ "Balanceado" (verde)
- ✅ "No Balanceado" (naranja) - para cualquier USD, CLP, EUR, etc.
- ✅ "Sin datos" (gris)

**❌ Si ves "USD", "EUR", "CLP" en el pill: el cálculo de `estado` tiene un error**

---

## 📊 Diagrama de Flujo Actualizado

```
┌──────────────────────────────────────────────────────────┐
│ Pipeline Python (crear_df_final)                         │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ df_final con columnas:                               │ │
│ │ Nombre, ID, Tipo instrumento                         │ │
│ │ moneda_antigua (SubMoneda renombrada)                │ │
│ │ moneda_nueva (USD, CLP, EUR, Balanceado...)          │ │
│ │ pct_dominancia_nueva, pct_dominancia_antigua         │ │
│ │ Cambio                                               │ │
│ └──────────────────────────────────────────────────────┘ │
└─────────────────────┬────────────────────────────────────┘
                      │ to_csv()
                      ▼
┌──────────────────────────────────────────────────────────┐
│ CSV guardado: data/processed/df_final.csv               │
│ Nombre,ID,moneda_nueva,moneda_antigua,Cambio...         │
└─────────────────────┬────────────────────────────────────┘
                      │ Flask lee CSV
                      ▼
┌──────────────────────────────────────────────────────────┐
│ Backend Flask (api/app.py)                               │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ 1. pd.read_csv('df_final.csv')                      │ │
│ │ 2. Renombrar columnas:                               │ │
│ │    Nombre → instrumento                              │ │
│ │    ID → id_inst                                      │ │
│ │    pct_dominancia_antigua → pct_antiguo              │ │
│ │ 3. CALCULAR 'estado' desde 'moneda_nueva':          │ │
│ │    'Balanceado' → 'Balanceado'                      │ │
│ │    'USD'/'CLP'/'EUR'/etc. → 'No Balanceado'         │ │
│ │    ''/'NaN' → 'Sin datos'                           │ │
│ │ 4. CALCULAR 'estado_idx' (1/2/3)                    │ │
│ │ 5. CALCULAR 'id' para selección                     │ │
│ │ 6. df.to_dict(orient='records')                     │ │
│ └──────────────────────────────────────────────────────┘ │
│ ✅ JSON con transformaciones aplicadas                   │
└─────────────────────┬────────────────────────────────────┘
                      │ HTTP Response
                      ▼
┌──────────────────────────────────────────────────────────┐
│ Frontend React                                           │
│ ┌──────────────────────────────────────────────────────┐ │
│ │ apiService.getValidationResults()                    │ │
│ │ ↓                                                    │ │
│ │ AppContext.setValidationData()                       │ │
│ │ ↓                                                    │ │
│ │ ValidacionPage renderiza tabla                       │ │
│ │ ✅ row.instrumento (renombrado)                     │ │
│ │ ✅ row.moneda_nueva (USD, CLP, EUR, Balanceado...)  │ │
│ │ ✅ row.estado (Balanceado, No Balanceado, Sin datos)│ │
│ │ ✅ <EstadoPill estado={row.estado} />               │ │
│ └──────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

---

## ✅ Resultado Final

Con estos cambios:

1. ✅ **`moneda_nueva`** se mantiene con su valor real (USD, CLP, EUR, Balanceado)
2. ✅ **`estado`** se CALCULA con solo 3 categorías (Balanceado, No Balanceado, Sin datos)
3. ✅ El backend transforma automáticamente las columnas antes de enviar al frontend
4. ✅ El frontend recibe datos con nombres correctos y categorías simplificadas
5. ✅ EstadoPill funciona correctamente con valores predefinidos
6. ✅ Los filtros pueden usar tanto `estado` (categoría) como `moneda_nueva` (valor específico)
7. ✅ No se confunde con el campo `Estado` de los exports (Estado_1, Estado_2, Estado_3)
8. ✅ No se requieren cambios en el pipeline de Python

---

**Estado:** ✅ Implementado correctamente en `api/app.py`
**Endpoint:** `/api/results/validation`
**Cálculo:** `estado` = FUNCIÓN(`moneda_nueva`), NO mapeo directo
