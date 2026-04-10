"""
Utilidad para normalizar el export_balanceados a base 1.

Cada columna de clase se divide por la suma de clases de su propia fila,
garantizando que pct_carga = 1.0 exacto por instrumento.

Se aplica SOLO en la fase final de guardado a CSV, sin afectar
la lógica interna ni la visualización en la UI.
"""

# Columnas fijas del export_balanceados (no son clases, no se tocan)
COLS_METADATA_EXPORT = {
    'ID', 'Instrumento', 'Id_ti_valor', 'Id_ti', 'Fecha',
    'Clasificacion', 'Estado', 'pct_original', 'pct_carga',
    'Industria Anterior', 'Moneda Anterior', 'Region Anterior',
}


def convertir_export_a_base1(df):
    """
    Devuelve una copia del DataFrame de export_balanceados con las columnas
    de clases normalizadas a base 1 (cada clase / suma de clases de su fila).

    Además agrega la columna 'pct_carga' (suma de clases en base 1)
    justo a la derecha de 'pct_original'.

    Retorna:
        DataFrame con columnas de clases en base 1 y columna pct_carga
    """
    if df is None or df.empty:
        return df

    df_out = df.copy()

    # Columnas de clase: numéricas que no son metadata
    cols_clase = [
        col for col in df_out.columns
        if col not in COLS_METADATA_EXPORT
        and df_out[col].dtype in ('float64', 'float32', 'int64', 'int32')
    ]

    # Normalizar por fila: cada clase / suma de clases de su fila
    suma_fila = df_out[cols_clase].sum(axis=1)
    df_out[cols_clase] = df_out[cols_clase].div(suma_fila, axis=0).round(6)

    # Corregir errores de redondeo: ajustar la última clase para que la suma sea exactamente 1.0
    for idx in df_out.index:
        diff = round(1.0 - df_out.loc[idx, cols_clase].sum(), 6)
        if diff != 0:
            ultima_col = df_out.loc[idx, cols_clase].last_valid_index()
            if ultima_col is not None:
                df_out.loc[idx, ultima_col] = round(df_out.loc[idx, ultima_col] + diff, 6)

    # Agregar pct_carga justo después de pct_original
    df_out['pct_carga'] = df_out[cols_clase].sum(axis=1).round(6)
    if 'pct_original' in df_out.columns:
        cols = list(df_out.columns)
        cols.remove('pct_carga')
        idx_col = cols.index('pct_original')
        cols.insert(idx_col + 1, 'pct_carga')
        df_out = df_out[cols]

    return df_out
