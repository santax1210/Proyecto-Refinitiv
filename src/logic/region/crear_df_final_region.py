"""
Módulo para crear el dataframe final consolidado de REGIÓN.

Equivalente a src/logic/moneda/crear_df_final.py pero para el pipeline de región.

DIFERENCIAS clave vs moneda:
- region_antigua se deriva de Pct_dominancia_antigua (no viene de df_instruments.SubMoneda).
- La columna de estado se llama 'Base Region:' (en lugar de 'Moneda:').
- Estado_3 en balanceados se activa con 'FALTA ALLOCATION' O 'SIN ASIGNAR'.
- Las columnas de distribución son regiones (no monedas).
"""
import pandas as pd
import numpy as np
import re
from src.extractors.region.load_allocations_region import normalizar_nombre_region


# ============================================================================
# EXTRACCIÓN DE NOMBRE DE REGIÓN DESDE Pct_dominancia
# ============================================================================

def extraer_nombre_region(pct_str):
    """
    Extrae el nombre de la región dominante desde un string tipo 'Chile 100.00%'.
    Maneja regiones con espacios ('Europa Des.', 'M. Oriente Front.', etc.)
    """
    if pd.isna(pct_str) or str(pct_str).strip().upper() in ('', 'SIN DATOS', 'NAN', 'NONE'):
        return 'Sin datos'
    valor = str(pct_str).strip()
    # Formato: "REGION NAME XX.XX%" → separar por último número+%
    match = re.match(r'^(.+)\s+(\d+\.?\d*)\s*%$', valor)
    if match:
        return match.group(1).strip()
    return valor


def _extraer_region_antigua_con_umbral(pct_str, umbral=90.0):
    """
    Extrae region_antigua aplicando el mismo umbral de dominancia que se usa
    en las nuevas (90% por defecto). Si el porcentaje del region max es menor
    al umbral, retorna 'Balanceado' — igual que _calcular_dominancia_region
    hace con pct_escalado >= 0.9 para las nuevas.
    """
    nombre = extraer_nombre_region(pct_str)
    if nombre in ('Sin datos', ''):
        return nombre
    match = re.search(r'(\d+\.?\d*)\s*%$', str(pct_str).strip())
    if match:
        pct = float(match.group(1))
        if pct < umbral:
            return 'Balanceado'
    return nombre


# ============================================================================
# HELLINGER Y MÉTRICAS DE VARIACIÓN (adaptadas para regiones)
# ============================================================================

def obtener_top_regiones_por_instrumento(row_antigua, cols_region, top_n=5):
    """
    Obtiene las N regiones con mayor peso para un instrumento en allocations antiguas.
    Excluye categorías no geográficas: N/A, otros, world, Globales, etc.
    """
    excluir = {'n/a', 'otros', 'world', 'globales', 'global des.', 'global eme.', 'temáticos', 'tematicos'}

    regiones_valores = {}
    for col in cols_region:
        if col.lower().strip() in excluir:
            continue
        valor = pd.to_numeric(row_antigua.get(col), errors='coerce')
        if pd.notna(valor) and valor > 0:
            regiones_valores[col] = valor

    if not regiones_valores:
        return []

    top = sorted(regiones_valores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [r for r, _ in top]


def extraer_distribucion_antigua_region(row, top_regiones):
    distribucion = {}
    for reg in top_regiones:
        if reg in row.index:
            valor = pd.to_numeric(row[reg], errors='coerce')
            distribucion[reg] = valor if pd.notna(valor) else 0.0
        else:
            distribucion[reg] = 0.0
    return distribucion


def extraer_distribucion_nueva_region(df_nuevas_region, instrument_id, top_regiones):
    df_inst = df_nuevas_region[df_nuevas_region['ID'] == instrument_id]
    if df_inst.empty:
        return {r: 0.0 for r in top_regiones}

    distribucion = {r: 0.0 for r in top_regiones}
    for _, row in df_inst.iterrows():
        if 'region' in row:
            reg = str(row['region']).strip()
            if reg in top_regiones:
                pct = pd.to_numeric(row.get('percentage'), errors='coerce')
                if pd.notna(pct):
                    distribucion[reg] = pct
    return distribucion


def calcular_distancia_hellinger_region(dist1, dist2):
    if not dist1 or not dist2:
        return None
    monedas = set(dist1.keys()) | set(dist2.keys())
    suma1 = sum(dist1.values())
    suma2 = sum(dist2.values())
    if suma1 == 0 and suma2 == 0:
        return 0.0
    if suma1 == 0 or suma2 == 0:
        return 1.0
    suma_raices = sum(
        (np.sqrt(max(0, dist1.get(m, 0) / suma1)) - np.sqrt(max(0, dist2.get(m, 0) / suma2))) ** 2
        for m in monedas
    )
    hellinger = min(1.0, max(0.0, (1 / np.sqrt(2)) * np.sqrt(suma_raices)))
    return round(hellinger, 4)


def calcular_hellinger_por_instrumento_region(row, df_dominancia_antiguas, df_dominancia_nuevas):
    if 'ID' not in row:
        return None

    fila_antigua = df_dominancia_antiguas[df_dominancia_antiguas['ID'] == row['ID']]
    if fila_antigua.empty:
        return None

    # Columnas de región en antiguas (excluir metadata)
    cols_meta = {'ID', 'Nombre', 'Pct_dominancia', 'Base Region:'}
    cols_region = [c for c in fila_antigua.columns if c not in cols_meta]

    top_regiones = obtener_top_regiones_por_instrumento(fila_antigua.iloc[0], cols_region)
    if not top_regiones:
        return None

    dist_antigua = extraer_distribucion_antigua_region(fila_antigua.iloc[0], top_regiones)
    dist_nueva = extraer_distribucion_nueva_region(df_dominancia_nuevas, row['ID'], top_regiones)

    return calcular_distancia_hellinger_region(dist_antigua, dist_nueva)


def extraer_porcentaje_dominante_region(row, columna):
    if columna not in row or pd.isna(row[columna]):
        return None
    valor = str(row[columna]).strip()
    if valor == '' or valor.upper() == 'SIN DATOS':
        return None
    match = re.search(r'(\d+\.?\d*)\s*%', valor)
    if match:
        return float(match.group(1))
    try:
        return float(valor)
    except Exception:
        return None


def obtener_pct_region_en_nuevas(df_nuevas_region, instrument_id, region):
    df_inst = df_nuevas_region[df_nuevas_region['ID'] == instrument_id]
    if df_inst.empty:
        return None

    pct_series = pd.to_numeric(df_inst['percentage'], errors='coerce')
    total = pct_series[pct_series > 0].sum()

    for _, fila in df_inst.iterrows():
        if 'region' in fila:
            reg = str(fila['region']).strip()
            if normalizar_nombre_region(reg) == normalizar_nombre_region(region):
                pct = pd.to_numeric(fila.get('percentage'), errors='coerce')
                if pd.notna(pct) and total > 0:
                    return round(pct / total * 100, 4)

    return 0.0


def calcular_variacion_balanceados_region(row, df_dominancia_antiguas, df_dominancia_nuevas):
    if 'region_nueva' not in row or str(row['region_nueva']).strip().upper() != 'BALANCEADO':
        return None
    if 'Estado' not in row or pd.isna(row['Estado']) or row['Estado'] == '':
        return None

    estado = str(row['Estado']).strip()

    if estado == 'Estado_1':
        return calcular_hellinger_por_instrumento_region(row, df_dominancia_antiguas, df_dominancia_nuevas)
    elif estado == 'Estado_2':
        pct_antiguo = extraer_porcentaje_dominante_region(row, 'pct_dominancia_antigua')
        region_antigua = _extraer_region_antigua_con_umbral(row.get('pct_dominancia_antigua', ''))
        if pct_antiguo is not None and region_antigua not in ('Sin datos', '') and 'ID' in row:
            pct_misma = obtener_pct_region_en_nuevas(df_dominancia_nuevas, row['ID'], region_antigua)
            if pct_misma is None:
                return None
            return round(abs(pct_antiguo - pct_misma) / 100.0, 4)
    return None


def calcular_variacion_no_balanceados_region(row, df_dominancia_nuevas):
    if 'region_nueva' not in row or str(row['region_nueva']).strip().upper() == 'BALANCEADO':
        return None
    if 'Estado' not in row or pd.isna(row['Estado']) or row['Estado'] == '':
        return None
    if 'ID' not in row:
        return None

    pct_antiguo = extraer_porcentaje_dominante_region(row, 'pct_dominancia_antigua')
    region_antigua = _extraer_region_antigua_con_umbral(row.get('pct_dominancia_antigua', ''))
    if pct_antiguo is None or region_antigua in ('Sin datos', ''):
        return None

    pct_misma = obtener_pct_region_en_nuevas(df_dominancia_nuevas, row['ID'], region_antigua)
    if pct_misma is None:
        return None

    return round(abs(pct_antiguo - pct_misma) / 100.0, 4)


# ============================================================================
# DETECCIÓN DE CAMBIO Y ESTADO
# ============================================================================

def detectar_cambio_region(row):
    """
    Compara region_nueva vs region_antigua (con normalización de nombres).
    Retorna "Sí", "No" o "Sin datos".
    """
    if 'region_nueva' not in row or 'region_antigua' not in row:
        return "Sin datos"

    nueva = str(row['region_nueva']).strip()
    antigua = str(row['region_antigua']).strip()

    if nueva.upper() in ('', 'NAN', 'NONE') or antigua.upper() in ('', 'NAN', 'NONE', 'SIN DATOS'):
        return "Sin datos"

    if normalizar_nombre_region(nueva) == normalizar_nombre_region(antigua):
        return "No"
    return "Sí"


def calcular_estado_region(row):
    """
    Calcula Estado_1 / Estado_2 / Estado_3 para región.

    DIFERENCIAS vs moneda:
    - Estado_3 para balanceados: 'Base Region:' == 'FALTA ALLOCATION' O 'SIN ASIGNAR'
    """
    if 'Cambio' in row and str(row['Cambio']).strip() == "Sin datos":
        return ""

    if 'region_nueva' not in row or 'region_antigua' not in row:
        return ""

    nueva = str(row['region_nueva']).strip().upper()
    antigua = str(row['region_antigua']).strip().upper()

    if nueva in ('', 'NAN', 'NONE') or antigua in ('', 'NAN', 'NONE'):
        return ""

    if nueva == 'BALANCEADO':
        base_region = str(row.get('Base Region:', '')).strip()
        if base_region in ('FALTA ALLOCATION', 'SIN ASIGNAR'):
            return 'Estado_3'
        if antigua == 'BALANCEADO':
            return 'Estado_1'
        return 'Estado_2'
    else:
        if antigua == 'BALANCEADO':
            return 'Estado_2'
        if normalizar_nombre_region(antigua) == normalizar_nombre_region(nueva):
            return 'Estado_1'
        return 'Estado_3'


def calcular_nivel_variacion_region(row):
    val_bal   = row.get('variacion_balanceados')
    val_nobal = row.get('variacion_no_balanceados')
    estado    = str(row.get('Estado', '')).strip()

    if pd.notna(val_bal) and val_bal is not None:
        val = float(val_bal)
        if estado == 'Estado_1':
            return 'Baja' if val <= 0.30 else 'Alta'
        else:
            return 'Baja' if val <= 0.40 else 'Alta'
    elif pd.notna(val_nobal) and val_nobal is not None:
        return 'Baja' if float(val_nobal) <= 0.40 else 'Alta'
    return None


# ============================================================================
# FILTROS
# ============================================================================

def filtrar_balanceados_region(df_final):
    return df_final[df_final['region_nueva'] == 'Balanceado'].copy()


def filtrar_no_balanceados_region(df_final):
    return df_final[df_final['region_nueva'] != 'Balanceado'].copy()


def filtrar_cambios_region(df_final):
    return df_final[df_final['Cambio'] == 'Sí'].copy()


# ============================================================================
# FUNCIÓN PRINCIPAL: CREAR DF_FINAL_REGION
# ============================================================================

def crear_df_final_region(df_instruments, df_dominancia_nuevas_region, df_dominancia_antiguas_region):
    """
    Crea el dataframe final consolidado para análisis de REGIÓN.

    DIFERENCIAS vs crear_df_final (moneda):
    - region_antigua se extrae de Pct_dominancia (antiguas) en lugar de SubMoneda (instruments).
    - Columnas: region_nueva, region_antigua, pct_dominancia_nueva, pct_dominancia_antigua.
    - Estado_3 en balanceados: 'Base Region:' == 'FALTA ALLOCATION' O 'SIN ASIGNAR'.
    """
    # 1. Base con info de instrumentos
    cols_base = [c for c in ['ID', 'Nombre', 'Tipo instrumento'] if c in df_instruments.columns]
    df_base = df_instruments[cols_base].copy()

    # 2. Merge con dominancia nuevas (1 fila por ID)
    cols_nuevas = [c for c in ['ID', 'region_nueva', 'pct_dominancia_nueva', 'pct_escalado', 'pct_original']
                   if c in df_dominancia_nuevas_region.columns]
    df_nuevas_ded = df_dominancia_nuevas_region[cols_nuevas].drop_duplicates(subset=['ID'], keep='first')

    df_final = pd.merge(df_base, df_nuevas_ded, on='ID', how='left')

    # 3. Merge con dominancia antiguas (Pct_dominancia + Base Region:)
    cols_antiguas = [c for c in ['ID', 'Pct_dominancia', 'Base Region:']
                     if c in df_dominancia_antiguas_region.columns]
    df_final = pd.merge(df_final, df_dominancia_antiguas_region[cols_antiguas], on='ID', how='left')

    if 'Pct_dominancia' in df_final.columns:
        df_final.rename(columns={'Pct_dominancia': 'pct_dominancia_antigua'}, inplace=True)

    # 4. Derivar region_antigua desde pct_dominancia_antigua aplicando umbral de dominancia (90%)
    # Esto es equivalente a lo que hace _calcular_dominancia_region para las nuevas:
    # si la región máxima no supera el 90%, el instrumento se considera Balanceado en antiguas también.
    df_final['region_antigua'] = df_final['pct_dominancia_antigua'].apply(_extraer_region_antigua_con_umbral)

    # 5. Columna Cambio
    df_final['Cambio'] = df_final.apply(detectar_cambio_region, axis=1)

    # 6. Columna Estado
    df_final['Estado'] = df_final.apply(calcular_estado_region, axis=1)

    # 7. Distancia de Hellinger
    print("  [INFO] Calculando distancia de Hellinger por instrumento (región)...")
    df_final['distancia_hellinger'] = df_final.apply(
        lambda row: calcular_hellinger_por_instrumento_region(
            row, df_dominancia_antiguas_region, df_dominancia_nuevas_region),
        axis=1
    )

    # 8. Variación balanceados
    print("  [INFO] Calculando variación para balanceados (región)...")
    df_final['variacion_balanceados'] = df_final.apply(
        lambda row: calcular_variacion_balanceados_region(
            row, df_dominancia_antiguas_region, df_dominancia_nuevas_region),
        axis=1
    )

    # 9. Variación no balanceados
    print("  [INFO] Calculando variación para no balanceados (región)...")
    df_final['variacion_no_balanceados'] = df_final.apply(
        lambda row: calcular_variacion_no_balanceados_region(row, df_dominancia_nuevas_region),
        axis=1
    )

    # 10. Nivel de variación
    df_final['nivel_variacion'] = df_final.apply(calcular_nivel_variacion_region, axis=1)

    # 11. Alertas de dominancia
    from src.logic.utils.alertas_dominancia import calcular_alerta_dominancia, COLS_META_REGION
    print("  [INFO] Calculando alertas de dominancia (región)...")
    df_final['alerta_dominancia'] = df_final.apply(
        lambda row: calcular_alerta_dominancia(
            row,
            df_dominancia_nuevas_region,
            df_dominancia_antiguas_region,
            col_pct_antigua='pct_dominancia_antigua',
            col_pct_nueva='pct_dominancia_nueva',
            col_clase_nuevas='region',
            col_pct_nuevas='percentage',
            cols_meta_antiguas=COLS_META_REGION,
        ),
        axis=1
    )
    n_alertas = df_final['alerta_dominancia'].notna().sum()
    print(f"  [OK] Alertas detectadas: {n_alertas} instrumentos")

    # 12. Reordenar columnas
    cols_orden = [
        'Nombre', 'ID', 'Tipo instrumento',
        'region_antigua', 'region_nueva',
        'pct_dominancia_nueva', 'pct_escalado', 'pct_original',
        'pct_dominancia_antigua', 'Cambio', 'Estado', 'nivel_variacion',
        'distancia_hellinger', 'variacion_balanceados', 'variacion_no_balanceados',
        'alerta_dominancia',
    ]
    cols_finales = [c for c in cols_orden if c in df_final.columns]
    return df_final[cols_finales]


# ============================================================================
# BLOQUE DE TEST Y EJECUCIÓN MANUAL
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from src.extractors.region.load_instruments_region import load_instruments_region
    from src.extractors.region.load_allocations_region import (
        load_allocations_nuevas_region, load_allocations_antiguas_region
    )

    print("\n" + "="*70)
    print(" TEST: CREAR DF_FINAL REGIÓN ".center(70, "="))
    print("="*70)

    df_instr = load_instruments_region()
    df_nuevas = load_allocations_nuevas_region(df_instr, 'data/raw/region/allocations_nuevas_region.csv')
    df_antiguas = load_allocations_antiguas_region(df_instr, 'data/raw/region/allocations_region.csv')

    df_final = crear_df_final_region(df_instr, df_nuevas, df_antiguas)
    print(f"  [OK] df_final_region creado con {len(df_final)} registros")
    print(f"  Columnas: {df_final.columns.tolist()}")
    print(df_final.head(3))

