import csv

import pandas as pd

from src.logic.sector.mapeo_sectores import MAPEO_SECTORES_INDUSTRY

def _escalar_porcentajes_sector(grupo_classes):
    grupo = grupo_classes.copy()
    mask_positivos = grupo['percentage'] > 0
    total_original = grupo.loc[mask_positivos, 'percentage'].sum()

    if total_original == 0:
        grupo['pct_escalado'] = 0.0
    else:
        grupo['pct_escalado'] = 0.0
        grupo.loc[mask_positivos, 'pct_escalado'] = (
            grupo.loc[mask_positivos, 'percentage'] / total_original
        )

    return grupo, total_original


def _cargar_archivo_nuevas_sector(nuevas_path):
    """
    Carga allocations nuevas y filtra exclusivamente classif == 'industry'.
    """
    rows = []
    with open(nuevas_path, 'r', encoding='latin-1', newline='') as f:
        reader = csv.reader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
        headers = next(reader)
        headers = [h.strip() for h in headers]
        for row in reader:
            if len(row) == len(headers):
                rows.append(row)

    df = pd.DataFrame(rows, columns=headers)
    df.columns = df.columns.str.strip()

    # Eliminar la columna de índice sin nombre que genera el CSV (evita romper el groupby)
    df = df.loc[:, df.columns != '']

    if 'classif' in df.columns:
        df = df[df['classif'].astype(str).str.strip().str.lower() == 'industry'].copy()
    else:
        print("  [WARN] ADVERTENCIA: columna 'classif' no encontrada, se incluyen todos los registros.")

    if 'percentage' in df.columns:
        df['percentage'] = (
            df['percentage']
            .astype(str)
            .str.replace(',', '.', regex=False)
        )
        df['percentage'] = pd.to_numeric(df['percentage'], errors='coerce')

    if 'class' in df.columns:
        df['class'] = df['class'].astype(str).str.strip()
        # Normalizar a minúsculas con guiones bajos para coincidir con las claves del mapeo
        # Los datos raw vienen en MAYÚSCULAS con espacios (ej: "FINANCIALS", "CONSUMER CYCLICALS")
        # mientras que MAPEO_SECTORES_INDUSTRY usa claves en minúsculas con guiones bajos
        df['class'] = df['class'].map(
            lambda x: MAPEO_SECTORES_INDUSTRY.get(x.lower().replace(' ', '_'), 'Otros')
        )

    if 'percentage' in df.columns and 'class' in df.columns:
        cols_agrupar = [c for c in df.columns if c != 'percentage']
        df = df.groupby(cols_agrupar, dropna=False, as_index=False)['percentage'].sum()

    return df


def _cruzar_con_instruments_sector(df_instruments, df_nuevas):
    resultados = []
    matched_ids = set()

    for key_instr, key_nuevas in [('RIC', 'instrument'), ('Isin', 'instrument'), ('Cusip', 'instrument')]:
        pendientes = df_instruments[~df_instruments['ID'].isin(matched_ids)]
        if pendientes.empty:
            break

        df_merge = pd.merge(
            pendientes[['ID', 'Nombre', key_instr]],
            df_nuevas,
            left_on=key_instr,
            right_on=key_nuevas,
            how='inner'
        )

        if not df_merge.empty:
            df_merge['tipo_id'] = key_instr
            resultados.append(df_merge)
            matched_ids.update(df_merge['ID'].tolist())

    if not resultados:
        return pd.DataFrame(columns=['ID', 'Nombre', 'instrument', 'class', 'percentage', 'tipo_id'])

    df_merged = pd.concat(resultados, ignore_index=True)
    cols_to_keep = [
        c for c in ['ID', 'Nombre', 'instrument', 'class', 'percentage', 'date', 'tipo_id']
        if c in df_merged.columns
    ]
    df_merged = df_merged[cols_to_keep].drop_duplicates(subset=['ID', 'class'])

    ids_validos = set()
    ids_invalidos = set()
    for id_instrumento, grupo in df_merged.groupby('ID'):
        percentages_validos = grupo['percentage'].dropna()
        percentages_validos = percentages_validos[percentages_validos > 0]
        if len(percentages_validos) > 0:
            ids_validos.add(id_instrumento)
        else:
            ids_invalidos.add(id_instrumento)

    if ids_invalidos:
        print(f"  [INFO] Excluidos {len(ids_invalidos)} instrumentos con TODAS las filas percentage=NA")

    return df_merged[df_merged['ID'].isin(ids_validos)].copy()


def _calcular_dominancia_sector(df_nuevas_merged, umbral=0.9):
    resultados = []

    for instrumento_id, grupo in df_nuevas_merged.groupby('ID'):
        nombre = grupo['Nombre'].iloc[0] if 'Nombre' in grupo.columns else None
        instrument = grupo['instrument'].iloc[0] if 'instrument' in grupo.columns else None
        date = grupo['date'].iloc[0] if 'date' in grupo.columns else None

        pct_original = grupo['percentage'].sum()
        grupo_escalado, _ = _escalar_porcentajes_sector(grupo[['class', 'percentage']])
        pct_escalado = grupo_escalado['pct_escalado'].sum()

        idx_max = grupo_escalado['pct_escalado'].idxmax()
        sector_max = grupo_escalado.loc[idx_max, 'class']
        pct_max = grupo_escalado.loc[idx_max, 'pct_escalado']

        sector_nueva = sector_max if pct_max >= umbral else 'Balanceado'
        pct_dominancia_nueva = f"{sector_max} {pct_max * 100:.2f}%"

        resultados.append({
            'ID': instrumento_id,
            'Nombre': nombre,
            'instrument': instrument,
            'date': date,
            'sector_nueva': sector_nueva,
            'pct_dominancia_nueva': pct_dominancia_nueva,
            'pct_escalado': round(pct_escalado * 100, 2),
            'pct_original': round(pct_original, 2),
        })

    return pd.DataFrame(resultados)


def _enriquecer_allocations_sector(df_nuevas_merged, umbral=0.9):
    """
    Enriquece el DataFrame LONG con columnas de dominancia
    y ASEGURA que la columna 'percentage' esté escalada al 100% total.
    """
    # 1. Aplicar escalado individual a cada fila (prorrateo)
    df_list = []
    for _, grupo in df_nuevas_merged.groupby('ID'):
        grupo_escalado, _ = _escalar_porcentajes_sector(grupo[['class', 'percentage']])
        # Reemplazar percentage con la versión escalada (multiplicada por 100)
        # Nota: recuperamos el 'class' original del grupo para mantener consistencia
        grupo_result = grupo.copy()
        grupo_result['percentage'] = (grupo_escalado['pct_escalado'] * 100).round(4)
        df_list.append(grupo_result)
    
    df_final_long = pd.concat(df_list, ignore_index=True)

    # 2. Calcular dominancia por instrumento (resumen)
    df_dominancia = _calcular_dominancia_sector(df_nuevas_merged, umbral)
    
    # 3. Merge con el resumen de dominancia
    df_enriquecido = pd.merge(
        df_final_long,
        df_dominancia[['ID', 'sector_nueva', 'pct_dominancia_nueva', 'pct_escalado', 'pct_original']],
        on='ID',
        how='left'
    )
    
    # Eliminar columna auxiliar de escalado si quedó duplicada por el merge
    if 'pct_escalado_x' in df_enriquecido.columns:
        df_enriquecido = df_enriquecido.drop(columns=['pct_escalado_x'])
    if 'pct_escalado_y' in df_enriquecido.columns:
        df_enriquecido = df_enriquecido.rename(columns={'pct_escalado_y': 'pct_escalado'})

    return df_enriquecido


def load_allocations_nuevas_sector(df_instruments, nuevas_path, umbral=0.9):
    df_nuevas = _cargar_archivo_nuevas_sector(nuevas_path)

    if df_nuevas.empty:
        print("  [WARN] ADVERTENCIA: No se pudieron cargar allocations nuevas de sector.")
        return pd.DataFrame(columns=[
            'ID', 'Nombre', 'instrument', 'class', 'percentage', 'date',
            'sector_nueva', 'pct_dominancia_nueva', 'pct_escalado', 'pct_original',
        ])

    df_merged = _cruzar_con_instruments_sector(df_instruments, df_nuevas)
    if df_merged.empty:
        print("  [WARN] ADVERTENCIA: No se encontraron matches en allocations nuevas de sector.")
        return pd.DataFrame(columns=[
            'ID', 'Nombre', 'instrument', 'class', 'percentage', 'date',
            'sector_nueva', 'pct_dominancia_nueva', 'pct_escalado', 'pct_original',
        ])

    return _enriquecer_allocations_sector(df_merged, umbral)


def _detectar_columna_sectores(df):
    for col in df.columns:
        col_norm = str(col).strip().lower()
        if 'sector' in col_norm and col_norm.endswith(':'):
            return col
    return 'Sectores:' if 'Sectores:' in df.columns else None


def _identificar_columnas_sector(df_antiguas, base_cols, col_base_sector=None):
    cols_metadata = [
        'ID', 'Nombre', 'Creado', 'Tipo Instrumento', 'Tipo instrumento',
        'RIC', 'Isin', 'Cusip', 'sectores', 'Moneda', 'Pais', 'País',
        'Nemo', 'Ticker_BB', 'Currency',
    ]

    cols_sector = []
    for col in df_antiguas.columns:
        if col in cols_metadata or col in base_cols:
            continue
        if col_base_sector and col == col_base_sector:
            continue
        if len(str(col).strip()) <= 60:
            cols_sector.append(col)

    return cols_sector


def _calcular_pct_dominancia_antiguas_sector(row, cols_sector):
    sector_max = None
    pct_max = 0.0

    for col in cols_sector:
        try:
            val_num = float(str(row[col]).strip().replace(',', '.'))
            if val_num > pct_max:
                pct_max = val_num
                sector_max = str(col).strip()
        except (ValueError, TypeError):
            continue

    if sector_max and pct_max > 0:
        return f"{sector_max} {pct_max:.2f}%"
    return 'Sin datos'


def load_allocations_antiguas_sector(df_instruments, antiguas_path):
    df_antiguas = pd.read_csv(antiguas_path, sep=';', encoding='latin-1', on_bad_lines='skip')
    df_antiguas.columns = df_antiguas.columns.str.strip()

    if 'ID' in df_antiguas.columns:
        df_antiguas['ID'] = pd.to_numeric(df_antiguas['ID'], errors='coerce').astype('Int64')
        df_antiguas = df_antiguas.dropna(subset=['ID'])

    base_cols = ['ID', 'Nombre']
    if 'sectores' in df_instruments.columns:
        base_cols.append('sectores')

    df_result = pd.merge(
        df_instruments[base_cols],
        df_antiguas,
        on='ID',
        how='inner',
        suffixes=('', '_drop')
    )

    cols_drop = [col for col in df_result.columns if col.endswith('_drop')]
    if cols_drop:
        df_result = df_result.drop(columns=cols_drop)

    col_base_sector = _detectar_columna_sectores(df_result)
    cols_sector = _identificar_columnas_sector(df_result, base_cols, col_base_sector)

    if not cols_sector:
        print("  [WARN] ADVERTENCIA: No se encontraron columnas de sector en allocations antiguas.")
        df_result['Pct_dominancia'] = 'Sin datos'
        return df_result[base_cols + ['Pct_dominancia']]

    df_result['Pct_dominancia'] = df_result.apply(
        lambda row: _calcular_pct_dominancia_antiguas_sector(row, cols_sector),
        axis=1
    )

    if col_base_sector and col_base_sector != 'Sectores:':
        df_result = df_result.rename(columns={col_base_sector: 'Sectores:'})
        col_base_sector = 'Sectores:'

    cols_finales = base_cols + cols_sector + ['Pct_dominancia']
    if col_base_sector and col_base_sector in df_result.columns:
        cols_finales.append(col_base_sector)

    cols_finales = [col for col in cols_finales if col in df_result.columns]
    return df_result[cols_finales]
