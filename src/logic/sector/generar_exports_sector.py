from datetime import datetime

import pandas as pd

from .crear_df_final_sector import ESTADOS_FALTA_ALLOCATION, normalizar_estado_sector


def _calcular_estado_balanceados_sector(row):
    antigua = str(row.get('sector_antigua', '')).strip().upper()
    nueva = str(row.get('sector_nueva', '')).strip().upper()
    sector_col = normalizar_estado_sector(row.get('Sectores:', ''))

    if sector_col in ESTADOS_FALTA_ALLOCATION:
        return 'Estado_3'
    if antigua == 'BALANCEADO' and nueva == 'BALANCEADO':
        return 'Estado_1'
    if antigua not in ['BALANCEADO', '', 'NAN', 'NONE'] and nueva == 'BALANCEADO':
        return 'Estado_2'
    return 'Estado_2'


def _calcular_estado_no_balanceados_sector(row):
    antigua = str(row.get('Industria Anterior', '')).strip().upper()
    nueva = str(row.get('SubIndustria', '')).strip().upper()

    if antigua == 'BALANCEADO' and nueva not in ['BALANCEADO', '', 'NAN', 'NONE']:
        return 'Estado_2'
    if antigua == nueva and antigua not in ['BALANCEADO', '', 'NAN', 'NONE']:
        return 'Estado_1'
    if antigua not in ['BALANCEADO', '', 'NAN', 'NONE'] and nueva not in ['BALANCEADO', '', 'NAN', 'NONE']:
        return 'Estado_3'
    return 'Estado_3'


def generar_export_balanceados_sector(df_final, df_allocations_nuevas_sector, df_instruments, df_allocations_antiguas_sector):
    df_balanceados = df_final[df_final['sector_nueva'] == 'Balanceado'].copy()
    if df_balanceados.empty:
        print('ADVERTENCIA: No hay instrumentos balanceados para exportar (sector).')
        return pd.DataFrame()

    ids_balanceados = df_balanceados['ID'].unique()
    df_alloc_balanceados = df_allocations_nuevas_sector[
        df_allocations_nuevas_sector['ID'].isin(ids_balanceados)
    ].copy()

    df_pivot = df_alloc_balanceados.pivot_table(
        index='ID',
        columns='class',
        values='percentage',
        aggfunc='first'
    ).reset_index()

    cols_info = [c for c in ['ID', 'instrument', 'tipo_id'] if c in df_alloc_balanceados.columns]
    df_info = df_alloc_balanceados[cols_info].drop_duplicates(subset=['ID'], keep='first')

    df_export = df_balanceados[['ID', 'Nombre', 'sector_antigua', 'pct_original']].copy()
    df_export = pd.merge(df_export, df_info, on='ID', how='left')
    df_export = pd.merge(df_export, df_pivot, on='ID', how='left')

    if 'Sectores:' in df_allocations_antiguas_sector.columns:
        df_export = pd.merge(
            df_export,
            df_allocations_antiguas_sector[['ID', 'Sectores:']].drop_duplicates(subset=['ID']),
            on='ID',
            how='left'
        )
    else:
        df_export['Sectores:'] = ''

    df_export = pd.merge(
        df_export,
        df_final[['ID', 'sector_nueva']].drop_duplicates(subset=['ID']),
        on='ID',
        how='left'
    )

    primer_dia_mes = datetime.now().replace(day=1).strftime('%d-%m-%Y')
    df_export['Fecha'] = df_export['Sectores:'].apply(
        lambda x: '31-12-2019' if normalizar_estado_sector(x) in ESTADOS_FALTA_ALLOCATION else primer_dia_mes
    )
    df_export['Clasificacion'] = 'SubIndustria'
    df_export['Estado'] = df_export.apply(_calcular_estado_balanceados_sector, axis=1)

    df_export = df_export.rename(columns={
        'Nombre': 'Instrumento',
        'instrument': 'Id_ti_valor',
        'tipo_id': 'Id_ti',
        'sector_antigua': 'Industria Anterior',
    })

    df_export = df_export.drop(columns=[c for c in ['Sectores:', 'sector_nueva'] if c in df_export.columns])

    cols_fijas = [
        'ID', 'Instrumento', 'Id_ti_valor', 'Id_ti', 'Fecha',
        'Clasificacion', 'Industria Anterior', 'Estado', 'pct_original',
    ]
    cols_sector = [c for c in df_export.columns if c not in cols_fijas]
    return df_export[[c for c in cols_fijas if c in df_export.columns] + cols_sector]


def generar_export_no_balanceados_sector(df_final):
    df_no_balanceados = df_final[df_final['sector_nueva'] != 'Balanceado'].copy()
    if df_no_balanceados.empty:
        print('ADVERTENCIA: No hay instrumentos no balanceados para exportar (sector).')
        return pd.DataFrame()

    df_export = df_no_balanceados[['ID', 'Nombre', 'sector_nueva', 'sector_antigua', 'Cambio']].copy()
    df_export = df_export.rename(columns={
        'Nombre': 'Instrumento',
        'sector_nueva': 'SubIndustria',
        'sector_antigua': 'Industria Anterior',
    })

    df_export['Estado'] = df_export.apply(_calcular_estado_no_balanceados_sector, axis=1)
    df_export['Sobreescribir'] = df_export['Cambio'].apply(lambda x: 'Sí' if x == 'Sí' else 'No')

    return df_export[['ID', 'Instrumento', 'SubIndustria', 'Industria Anterior', 'Estado', 'Sobreescribir']]


def generar_export_sin_datos_sector(df_instruments, df_allocations_nuevas_sector):
    ids_instruments = set(df_instruments['ID'].unique())
    ids_allocations = set(df_allocations_nuevas_sector['ID'].unique())
    ids_sin_datos = ids_instruments - ids_allocations

    ids_invalidos = set()
    for id_inst in ids_allocations:
        grupo = df_allocations_nuevas_sector[df_allocations_nuevas_sector['ID'] == id_inst]
        validos = grupo['percentage'].dropna()
        validos = validos[validos > 0]
        if len(validos) == 0:
            ids_invalidos.add(id_inst)

    ids_sin_datos = ids_sin_datos | ids_invalidos

    print('  [INFO] Instrumentos sin datos (sector):')
    print(f"    - No encontrados en allocations nuevas: {len(ids_sin_datos - ids_invalidos)}")
    print(f"    - Con TODAS las filas percentage=NA: {len(ids_invalidos)}")
    print(f"    - TOTAL sin datos: {len(ids_sin_datos)}")

    if not ids_sin_datos:
        print('ADVERTENCIA: No hay instrumentos sin datos (sector).')
        return pd.DataFrame(columns=['ID', 'Instrumento'])

    df_sin_datos = df_instruments[df_instruments['ID'].isin(ids_sin_datos)][['ID', 'Nombre']].copy()
    df_sin_datos = df_sin_datos.rename(columns={'Nombre': 'Instrumento'})
    return df_sin_datos
