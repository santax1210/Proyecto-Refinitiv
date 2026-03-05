# Métrica de Variación para Instrumentos Balanceados

## 📊 Descripción

La columna `variacion_balanceados` es una métrica específica para instrumentos con `moneda_nueva = "Balanceado"` que utiliza diferentes cálculos según el **Estado** del instrumento.

### ¿Por qué una métrica específica?

La distancia de Hellinger por sí sola no es representativa para todos los casos de instrumentos balanceados:
- **Estado_1 (Bal→Bal)**: Compara dos distribuciones → Hellinger es apropiado
- **Estado_2 (Mon→Bal)**: Compara moneda única vs distribución → Hellinger no es representativo

## 🔍 Lógica de Cálculo

### Estado_1: Balanceado → Balanceado
**Métrica usada:** Distancia de Hellinger

Compara las distribuciones de las top 5 monedas en ambas allocations (antigua y nueva).

**Ejemplo:**
```
Instrumento: MFS European Value (ID: 33)
Antigua: EUR 48.19%, USD 28.11%, CHF 18.55%, GBP 0.75%, DKK 1.64%
Nueva:   EUR 52.02%, USD 27.50%, CHF 17.00%, GBP 1.00%, DKK 1.50%
→ variacion_balanceados = 0.0565 (Hellinger)
```

**Interpretación:**  
- 0 = Distribuciones idénticas
- 1 = Distribuciones completamente diferentes
- 0.0565 = Cambio leve en la distribución

---

### Estado_2: Moneda → Balanceado
**Métrica usada:** Diferencia entre el porcentaje de la moneda dominante antigua y el porcentaje de esa **misma moneda** en la nueva distribución

**Fórmula:**
```
variacion = |pct_moneda_antigua_en_antigua - pct_moneda_antigua_en_nueva| / 100
```

**Ejemplo:**
```
Instrumento: Fondo BCI Gestion Global (ID: 23)
Antigua: CLP 100% (moneda única)
Nueva:   USD 49.42%, CLP 18.30%, EUR 15.00%, ...  ← buscamos CLP
→ variacion_balanceados = |100 - 18.30| / 100 = 0.8170 (81.70% de diferencia)
```

**Interpretación:**  
- 0 = La moneda dominante antigua mantiene el mismo porcentaje en la nueva distribución
- 1 = La moneda dominante antigua desaparece por completo de la nueva distribución (0%)
- 0.8170 = La moneda original (CLP) pasó de representar 100% a solo 18.30%

**Casos especiales:**  
- Si la moneda antigua **no aparece** en la nueva distribución → su porcentaje nuevo es **0%**, variación = pct_antiguo / 100
- Si el instrumento no tiene allocations nuevas → `variacion_balanceados = None`

---

## 📈 Estadísticas del Dataset

Basado en el procesamiento actual:

- **Total instrumentos balanceados:** 403
- **Con variación calculada:** 377
  - **Estado_1 (Bal→Bal, Hellinger):** 135 instrumentos (35.8%)
  - **Estado_2 (Mon→Bal, Dif. %):** 242 instrumentos (64.2%)
- **Sin datos:** 26 (instrumentos sin allocations nuevas)

**Métricas de variación:**
- **Promedio:** 0.3122 (31.22% de variación)
- **Mediana:** 0.2542 (25.42% de variación)
- **Mínimo:** 0.0133 (1.33% de variación)
- **Máximo:** 0.8421 (84.21% de variación)

---

## 🎯 Casos de Uso

### 1. Identificar instrumentos con mayor variación en balanceados

```python
import pandas as pd

df = pd.read_csv('data/processed/df_final.csv', sep=';', encoding='latin-1')

# Filtrar balanceados con variación calculada
balanceados = df[(df['moneda_nueva'] == 'Balanceado') & (df['variacion_balanceados'].notna())]

# Ordenar por mayor variación
top_variacion = balanceados.nlargest(10, 'variacion_balanceados')
print(top_variacion[['Nombre', 'Estado', 'pct_dominancia_antigua', 'pct_dominancia_nuevo', 'variacion_balanceados']])
```

### 2. Comparar variación entre Estado_1 y Estado_2

```python
# Separar por Estado
estado1 = balanceados[balanceados['Estado'] == 'Estado_1']
estado2 = balanceados[balanceados['Estado'] == 'Estado_2']

print(f"Estado_1 (Bal→Bal):")
print(f"  Promedio variación: {estado1['variacion_balanceados'].mean():.4f}")
print(f"  Mediana variación: {estado1['variacion_balanceados'].median():.4f}")

print(f"\nEstado_2 (Mon→Bal):")
print(f"  Promedio variación: {estado2['variacion_balanceados'].mean():.4f}")
print(f"  Mediana variación: {estado2['variacion_balanceados'].median():.4f}")
```

### 3. Filtrar por nivel de variación

```python
# Instrumentos con variación baja (< 0.2)
variacion_baja = balanceados[balanceados['variacion_balanceados'] < 0.2]

# Instrumentos con variación moderada (0.2 - 0.5)
variacion_moderada = balanceados[(balanceados['variacion_balanceados'] >= 0.2) & 
                                  (balanceados['variacion_balanceados'] < 0.5)]

# Instrumentos con variación alta (>= 0.5)
variacion_alta = balanceados[balanceados['variacion_balanceados'] >= 0.5]

print(f"Variación baja (<20%): {len(variacion_baja)} instrumentos")
print(f"Variación moderada (20%-50%): {len(variacion_moderada)} instrumentos")
print(f"Variación alta (>=50%): {len(variacion_alta)} instrumentos")
```

---

## 📊 Ejemplos Reales del Dataset

### Estado_2: Mayor variación (Moneda → Balanceado)

| Nombre | Antigua | Nueva | Variación |
|--------|---------|-------|-----------|
| Fondo BCI Gestion Global | CLP 100% | USD 49.42% | 50.58% |
| MFS European Value Fund | USD 100% | EUR 52.02% | 47.98% |
| MFS Emerging Markets Debt | USD 100% | USD 86.61% | 13.39% |

### Estado_1: Variación en distribución (Bal → Bal)

| Nombre | Antigua | Nueva | Variación (Hellinger) |
|--------|---------|-------|----------------------|
| MFS European Value USD | EUR 48.19% | EUR 52.02% | 0.0565 |
| iShares MSCI ACWI | USD 59.19% | USD 69.81% | 0.1736 |

---

## ⚠️ Consideraciones Importantes

1. **Solo para balanceados:** Esta métrica solo se calcula para instrumentos con `moneda_nueva = "Balanceado"`.

2. **Métricas diferentes por Estado:**
   - No se pueden comparar directamente valores de Estado_1 vs Estado_2 ya que usan fórmulas diferentes
   - Estado_1: Hellinger (0-1, compara distribuciones)
   - Estado_2: Diferencia de porcentajes (0-1, compara porcentajes dominantes)

3. **Instrumentos sin datos:** Si `moneda_nueva` está vacía o el Estado no es válido, `variacion_balanceados` será `None`.

4. **Complemento de otras métricas:**
   - `distancia_hellinger`: Disponible para todos los instrumentos
   - `variacion_balanceados`: Solo para balanceados, con lógica específica por Estado

---

## 🔄 Diferencia con distancia_hellinger

| Métrica | Aplica a | Lógica |
|---------|----------|--------|
| `distancia_hellinger` | Todos los instrumentos | Compara distribuciones usando top 5 monedas del instrumento |
| `variacion_balanceados` | Solo balanceados | Estado_1: Hellinger / Estado_2: Diferencia de % |

**Ventaja de variacion_balanceados:**  
Proporciona una métrica más representativa para instrumentos balanceados Estado_2, donde pasar de una moneda única a una distribución balanceada tiene un significado específico.

---

## 📁 Ubicación en el Pipeline

- **Código:** [src/logic/crear_df_final.py](src/logic/crear_df_final.py)
- **Función:** `calcular_variacion_balanceados()`
- **Columna en df_final:** `variacion_balanceados`
- **Archivos generados:**
  - `data/processed/df_final.csv` (todos los instrumentos)
  - `data/processed/df_final_balanceados.csv` (solo balanceados)
  - `data/exports/export_balanceados.csv` (exportación para usuario)

---

**Fecha de implementación:** 2026-03-03  
**Autor:** Pipeline de validación de allocations
