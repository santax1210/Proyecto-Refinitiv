"""
Módulo para generar los exports finales de REGIÓN.

Equivalente a src/logic/moneda/generar_exports.py pero para el pipeline de región.

DIFERENCIAS clave vs moneda:
- Estado_3 para balanceados: 'Base Region:' == 'FALTA ALLOCATION' O 'SIN ASIGNAR'.
- Fecha: '31-12-2019' cuando 'Base Region:' es 'FALTA ALLOCATION' o 'SIN ASIGNAR'.
- Pivot usa columna 'region' (no 'class').
- Clasificacion = 'SubRegion' (en lugar de 'SubMoneda').
- No hay columna SubMoneda en df_instruments para región.
- Rename 'Moneda Anterior' → 'Region Anterior' en no balanceados.
"""
import pandas as pd


def _calcular_estado_balanceados_region(row):
    """
    Calcula el estado para el export de balanceados (región).

    Lógica:
    - Estado_3: 'Base Region:' == 'FALTA ALLOCATION' O 'SIN ASIGNAR'
    - Estado_1: Balanceado → Balanceado
    - Estado_2: Region → Balanceado
    """
    base_region = str(row.get('Base Region:', '')).strip()
    antigua = str(row.get('region_antigua', '')).strip().upper()
    nueva   = str(row.get('region_nueva', '')).strip().upper()

    # Estado_3: FALTA ALLOCATION o SIN ASIGNAR
    if base_region in ('FALTA ALLOCATION', 'SIN ASIGNAR'):
        return 'Estado_3'

    # Estado_1: Balanceado → Balanceado
    if antigua == 'BALANCEADO' and nueva == 'BALANCEADO':
        return 'Estado_1'

    # Estado_2: Region → Balanceado
    if antigua not in ['BALANCEADO', '', 'NAN', 'NONE'] and nueva == 'BALANCEADO':
        return 'Estado_2'

    return 'Estado_2'


def _calcular_estado_no_balanceados_region(row):
    """
    Calcula el estado para el export de no balanceados (región).

    Lógica:
    - Estado_1: Region → Misma Region
    - Estado_2: Balanceado → Region
    - Estado_3: Region → Otra Region
    """
    antigua = str(row.get('Region Anterior', '')).strip().upper()
    nueva   = str(row.get('SubRegion', '')).strip().upper()

    # Estado_2: Balanceado → Region
    if antigua == 'BALANCEADO' and nueva not in ['BALANCEADO', '', 'NAN', 'NONE']:
        return 'Estado_2'

    # Estado_1: Region → Misma Region
    if antigua == nueva and antigua not in ['BALANCEADO', '', 'NAN', 'NONE']:
        return 'Estado_1'

    # Estado_3: Region → Otra Region
    if (antigua not in ['BALANCEADO', '', 'NAN', 'NONE']
            and nueva not in ['BALANCEADO', '', 'NAN', 'NONE']
            and antigua != nueva):
        return 'Estado_3'

    return 'Estado_3'


def generar_export_balanceados_region(df_final, df_allocations_nuevas_region, df_instruments, df_allocations_antiguas_region):
    """
    Genera el export de instrumentos balanceados (región) en formato WIDE.

    Formato del export:
    - ID
    - Instrumento (Nombre)
    - Id_ti_valor (instrument de allocations_nuevas_region)
    - Id_ti (tipo_id)
    - Fecha (calculado desde 'Base Region:')
    - Clasificacion ('SubRegion')
    - Region Anterior (region_antigua de df_final)
    - Estado (calculado)
    - pct_original
    - [Regiones dinámicas en formato WIDE]
    """
    # 1. Filtrar solo balanceados
    df_bal = df_final[df_final['region_nueva'] == 'Balanceado'].copy()
    if df_bal.empty:
        print("ADVERTENCIA: No hay instrumentos balanceados para exportar (región).")
        return pd.DataFrame()

    ids_balanceados = df_bal['ID'].unique()

    # 2. Filtrar allocations para IDs balanceados
    df_alloc_bal = df_allocations_nuevas_region[
        df_allocations_nuevas_region['ID'].isin(ids_balanceados)
    ].copy()

    # 3. Pivot WIDE (por región)
    df_pivot = df_alloc_bal.pivot_table(
        index='ID',
        columns='region',
        values='percentage',
        aggfunc='first'
    ).reset_index()

    # 4. Info adicional de allocations nuevas (instrument, tipo_id → primera ocurrencia por ID)
    cols_info = [c for c in ['ID', 'instrument', 'tipo_id'] if c in df_alloc_bal.columns]
    df_info = df_alloc_bal[cols_info].drop_duplicates(subset=['ID'], keep='first')

    # 5. Merge base
    df_export = df_bal[['ID', 'Nombre', 'region_antigua', 'pct_original']].copy()
    df_export = pd.merge(df_export, df_info, on='ID', how='left')
    df_export = pd.merge(df_export, df_pivot, on='ID', how='left')

    # 6. Obtener 'Base Region:' desde antiguas para cálculo de Fecha y Estado
    if 'Base Region:' in df_allocations_antiguas_region.columns:
        df_export = pd.merge(
            df_export,
            df_allocations_antiguas_region[['ID', 'Base Region:']].drop_duplicates(subset=['ID']),
            on='ID',
            how='left'
        )
    else:
        df_export['Base Region:'] = ''

    # 7. Obtener region_nueva para calcular Estado
    df_export = pd.merge(
        df_export,
        df_final[['ID', 'region_nueva']].drop_duplicates(subset=['ID']),
        on='ID',
        how='left',
        suffixes=('', '_final')
    )

    # 8. Calcular campos ANTES de renombrar
    from datetime import datetime
    primer_dia_mes = datetime.now().replace(day=1).strftime('%d-%m-%Y')

    df_export['Fecha'] = df_export['Base Region:'].apply(
        lambda x: '31-12-2019' if str(x).strip() in ('FALTA ALLOCATION', 'SIN ASIGNAR') else primer_dia_mes
    )
    df_export['Clasificacion'] = 'SubRegion'
    df_export['Estado'] = df_export.apply(_calcular_estado_balanceados_region, axis=1)

    # 9. Renombrar columnas
    df_export.rename(columns={
        'Nombre': 'Instrumento',
        'instrument': 'Id_ti_valor',
        'tipo_id': 'Id_ti',
        'region_antigua': 'Region Anterior'
    }, inplace=True)

    # 10. Limpiar columnas temporales
    cols_drop = [c for c in ['Base Region:', 'region_nueva'] if c in df_export.columns]
    df_export.drop(columns=cols_drop, errors='ignore', inplace=True)

    # 11. Reordenar
    cols_fijas = ['ID', 'Instrumento', 'Id_ti_valor', 'Id_ti', 'Fecha',
                  'Clasificacion', 'Region Anterior', 'Estado', 'pct_original']
    cols_regiones = [c for c in df_export.columns if c not in cols_fijas]
    cols_finales = [c for c in cols_fijas if c in df_export.columns] + cols_regiones
    return df_export[cols_finales]


def generar_export_no_balanceados_region(df_final):
    """
    Genera el export de instrumentos NO balanceados (región).

    Formato del export:
    - ID
    - Instrumento (Nombre)
    - SubRegion (region_nueva)
    - Region Anterior (region_antigua)
    - Estado (calculado)
    - Sobreescribir ('Sí' si hay cambio, 'No' si no)
    """
    df_nobal = df_final[df_final['region_nueva'] != 'Balanceado'].copy()
    if df_nobal.empty:
        print("ADVERTENCIA: No hay instrumentos no balanceados para exportar (región).")
        return pd.DataFrame()

    df_export = df_nobal[['ID', 'Nombre', 'region_nueva', 'region_antigua', 'Cambio']].copy()
    df_export.rename(columns={
        'Nombre': 'Instrumento',
        'region_nueva': 'SubRegion',
        'region_antigua': 'Region Anterior'
    }, inplace=True)

    df_export['Estado'] = df_export.apply(_calcular_estado_no_balanceados_region, axis=1)
    df_export['Sobreescribir'] = df_export['Cambio'].apply(lambda x: 'Sí' if x == 'Sí' else 'No')

    return df_export[['ID', 'Instrumento', 'SubRegion', 'Region Anterior', 'Estado', 'Sobreescribir']]


def generar_export_sin_datos_region(df_instruments, df_allocations_nuevas_region):
    """
    Genera el export de instrumentos sin datos (región).

    Incluye:
    - Instrumentos no encontrados en allocations nuevas.
    - Instrumentos con TODAS las filas con percentage inválido.
    """
    ids_instruments = set(df_instruments['ID'].unique())
    ids_allocations = set(df_allocations_nuevas_region['ID'].unique())

    ids_sin_datos = ids_instruments - ids_allocations

    ids_invalidos = set()
    for id_inst in ids_allocations:
        grupo = df_allocations_nuevas_region[df_allocations_nuevas_region['ID'] == id_inst]
        validos = grupo['percentage'].dropna()
        validos = validos[validos > 0]
        if len(validos) == 0:
            ids_invalidos.add(id_inst)

    ids_sin_datos = ids_sin_datos | ids_invalidos

    print(f"  [INFO] Instrumentos sin datos (región):")
    print(f"    - No encontrados en allocations nuevas: {len(ids_sin_datos - ids_invalidos)}")
    print(f"    - Con TODAS las filas percentage=NA: {len(ids_invalidos)}")
    print(f"    - TOTAL sin datos: {len(ids_sin_datos)}")

    if not ids_sin_datos:
        print("ADVERTENCIA: No hay instrumentos sin datos (región).")
        return pd.DataFrame(columns=['ID', 'Instrumento'])

    df_sin_datos = df_instruments[df_instruments['ID'].isin(ids_sin_datos)][['ID', 'Nombre']].copy()
    df_sin_datos.rename(columns={'Nombre': 'Instrumento'}, inplace=True)
    return df_sin_datos


# ============================================================================
# TEST MANUAL
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from src.extractors.region.load_instruments_region import load_instruments_region
    from src.extractors.region.load_allocations_region import (
        load_allocations_nuevas_region, load_allocations_antiguas_region
    )
    from src.logic.region.crear_df_final_region import crear_df_final_region

    print("\n" + "="*70)
    print(" TEST: GENERACIÓN DE EXPORTS REGIÓN ".center(70, "="))
    print("="*70)

    df_instr = load_instruments_region()
    df_nuevas = load_allocations_nuevas_region(df_instr, 'data/raw/region/allocations_nuevas_region.csv')
    df_antiguas = load_allocations_antiguas_region(df_instr, 'data/raw/region/allocations_region.csv')
    df_final = crear_df_final_region(df_instr, df_nuevas, df_antiguas)

    exp_bal   = generar_export_balanceados_region(df_final, df_nuevas, df_instr, df_antiguas)
    exp_nobal = generar_export_no_balanceados_region(df_final)
    exp_sin   = generar_export_sin_datos_region(df_instr, df_nuevas)

    print(f"  [OK] Balanceados: {len(exp_bal)} filas | No balanceados: {len(exp_nobal)} filas | Sin datos: {len(exp_sin)} filas")
