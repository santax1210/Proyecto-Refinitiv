# Métrica de Distancia de Hellinger

## 📊 ¿Qué es la Distancia de Hellinger?

La distancia de Hellinger es una métrica estadística que mide la diferencia entre dos distribuciones de probabilidad. En nuestro caso, la usamos para comparar cómo cambia la distribución de monedas de un instrumento entre las allocations antiguas y las nuevas.

### Valor de la métrica
- **0.0**: Sin cambio (distribuciones idénticas)
- **1.0**: Cambio máximo (distribuciones completamente diferentes)

## 🎯 ¿Por qué usar Distancia de Hellinger?

Comparada con otras métricas como la diferencia absoluta, la distancia de Hellinger:
- ✅ Es menos sensible a cambios pequeños en monedas poco relevantes
- ✅ Es más robusta cuando hay muchas monedas con pesos bajos
- ✅ Da más importancia a cambios en monedas principales
- ✅ Está normalizada entre 0 y 1, facilitando la interpretación

## 🔍 Implementación en tu Pipeline

### Selección de monedas (POR INSTRUMENTO)
El cálculo es **específico para cada instrumento**. Para cada uno:
1. Se identifican sus **top 5 monedas** con mayor peso en allocations antiguas
2. Se **excluyen** categorías especiales que no son monedas reales:
   - **Balanceado**: No es moneda, indica distribución balanceada
   - **Otros**: Agrupación de monedas pequeñas, no útil para comparación
   - **N/A**, **Global**: Otras categorías especiales
3. Esas 5 monedas específicas se usan para comparar con allocations nuevas

**Ejemplo:**
- Instrumento A (fondo USA): Top 5 = [USD, EUR, JPY, GBP, CAD]
- Instrumento B (fondo LATAM): Top 5 = [BRL, CLP, MXN, COP, USD]
- Cada uno se evalúa con sus propias monedas principales

### Alineamiento de distribuciones
Para cada instrumento:
1. Se identifican sus top 5 monedas en allocations antiguas (excluyendo Balanceado/Otros)
2. Se extrae la distribución de esas 5 monedas en allocations antiguas
3. Se extrae la distribución de las MISMAS 5 monedas en allocations nuevas
4. Si una moneda no existe en la nueva distribución, se asigna 0%
5. Ambas distribuciones se normalizan (deben sumar 100%)
6. Se calcula la distancia de Hellinger entre ambas

**Ventaja:** Cada instrumento se compara usando sus monedas más relevantes, no un set global

### Fórmula matemática
```
H = (1/√2) × √(Σ(√p_i - √q_i)²)
```
Donde:
- `p_i` = porcentaje de la moneda i en distribución antigua
- `q_i` = porcentaje de la moneda i en distribución nueva

## 📈 Ejemplos de interpretación

### Ejemplo 1: Sin cambio (H = 0.0)
```
Instrumento: Fondo USA
Top 5 monedas del instrumento: [USD, EUR, JPY, GBP, CAD]

Antigua: USD 100%, EUR 0%, JPY 0%, GBP 0%, CAD 0%
Nueva:   USD 100%, EUR 0%, JPY 0%, GBP 0%, CAD 0%
→ Distancia: 0.0 (sin cambio)
```

### Ejemplo 2: Cambio parcial (H = 0.1973)
```
Instrumento: Fondo Global
Top 5 monedas del instrumento: [USD, EUR, JPY, GBP, CHF]

Antigua: USD 100%, EUR 0%, JPY 0%, GBP 0%, CHF 0%
Nueva:   USD 86.61%, EUR 10%, JPY 3.39%, GBP 0%, CHF 0%
→ Distancia: 0.1973 (cambio leve, USD sigue dominante)
```

### Ejemplo 3: Cambio significativo (H = 0.7051)
```
Instrumento: Fondo Diversificado
Top 5 monedas del instrumento: [CLP, USD, EUR, BRL, JPY]

Antigua: CLP 100%, USD 0%, EUR 0%, BRL 0%, JPY 0%
Nueva:   CLP 20.58%, USD 49.42%, EUR 30%, BRL 0%, JPY 0%
→ Distancia: 0.7051 (cambio significativo en la distribución)
```

### Ejemplo 4: Cambio completo (H = 1.0)
```
Instrumento: Fondo sin datos nuevos
Top 5 monedas del instrumento: [CLP, USD, EUR, JPY, GBP]

Antigua: CLP 100%, USD 0%, EUR 0%, JPY 0%, GBP 0%
Nueva:   Sin datos (0% en todas las monedas)
→ Distancia: 1.0 (cambio máximo / sin datos)
```

## 📊 Estadísticas del dataset actual

Basado en el procesamiento reciente:
- **Total instrumentos**: 4,361
- **Instrumentos con datos**: 4,324 (algunos no tienen monedas válidas)
- **Promedio de distancia**: ~0.81
- **Mediana de distancia**: 1.0000
- **Mínimo**: 0.0000 (sin cambio)
- **Máximo**: 1.0000 (cambio completo)

### Interpretación general
- La mediana de 1.0 indica que más del 50% de los instrumentos tienen cambios máximos
- Esto se debe principalmente a que ~3,454 instrumentos no tienen datos en allocations nuevas
- Para instrumentos con datos completos, la distancia promedio es menor
- **Importante:** Cada instrumento usa sus propias top 5 monedas para el cálculo

## 🔧 Uso en análisis

### Filtrar instrumentos por nivel de cambio

```python
import pandas as pd

df = pd.read_csv('data/processed/df_final.csv', sep=';', encoding='latin-1')

# Instrumentos sin cambio (H = 0)
sin_cambio = df[df['distancia_hellinger'] == 0.0]

# Instrumentos con cambio leve (0 < H < 0.3)
cambio_leve = df[(df['distancia_hellinger'] > 0) & (df['distancia_hellinger'] < 0.3)]

# Instrumentos con cambio moderado (0.3 <= H < 0.7)
cambio_moderado = df[(df['distancia_hellinger'] >= 0.3) & (df['distancia_hellinger'] < 0.7)]

# Instrumentos con cambio significativo (H >= 0.7)
cambio_significativo = df[df['distancia_hellinger'] >= 0.7]
```

### Análisis por tipo de instrumento

```python
# Promedio de distancia por tipo de instrumento
df.groupby('Tipo instrumento')['distancia_hellinger'].describe()

# Instrumentos con mayor cambio
top_cambios = df.nlargest(10, 'distancia_hellinger')[['Nombre', 'moneda_antigua', 'moneda_nueva', 'distancia_hellinger']]
```

## 📝 Integración con otras columnas

La columna `distancia_hellinger` complementa las demás columnas del df_final:
- **Cambio**: Indica si hubo cambio (Sí/No/Sin datos)
- **Estado**: Clasifica el tipo de cambio (Estado_1, Estado_2, Estado_3)
- **distancia_hellinger**: Cuantifica la magnitud del cambio (0 a 1)

Ejemplo:
```
Instrumento A:
  - Cambio: "Sí"
  - Estado: "Estado_2" (Moneda → Balanceado)
  - distancia_hellinger: 0.7051
  → Hubo un cambio y es significativo (70.51% de distancia máxima)
```

## 🎓 Referencias

- **Hellinger Distance**: Mide la similitud entre dos distribuciones de probabilidad
- **Ventajas**: Simétrica, acotada [0,1], robusta a valores pequeños
- **Uso común**: Análisis de portafolios, comparación de distribuciones financieras, machine learning

---

**Fecha de implementación**: 2026-03-03  
**Ubicación en código**: `src/logic/crear_df_final.py`
