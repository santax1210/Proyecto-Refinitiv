import os

import pandas as pd


def _resolver_columna_sector(df_instr):
    """Devuelve la columna del maestro que representa la clasificación de sector."""
    candidatos = ['sectores', 'sectores-2', 'sector-categoria']
    for columna in candidatos:
        if columna in df_instr.columns:
            return columna
    return None


def load_instruments_sector(pos_path, instr_path):
    """
    Carga el dataframe base de instrumentos para el pipeline de Sector.

    Replica la lógica de moneda pero incorporando la clasificación antigua desde
    la columna `sectores` del maestro de instrumentos.
    """
    df_pos = pd.read_csv(pos_path, sep=';', encoding='latin-1', on_bad_lines='skip')
    df_instr = pd.read_csv(instr_path, sep=';', encoding='latin-1', on_bad_lines='skip')

    df_pos.columns = df_pos.columns.str.strip()
    df_instr.columns = df_instr.columns.str.strip()

    with open('debug_cols_runtime.txt', 'w') as f:
        f.write("\n".join(df_instr.columns.tolist()))

    col_fecha = 'F. Proceso'
    df_pos[col_fecha] = pd.to_datetime(df_pos[col_fecha], dayfirst=True, errors='coerce')
    df_pos = df_pos[df_pos[col_fecha] > pd.Timestamp(2025, 6, 1)]

    df_merged = pd.merge(df_pos[['ID', col_fecha]], df_instr, on='ID', how='inner')

    col_tipo = 'Tipo instrumento'
    tipos_interes = ['C02', 'C14', 'C04', 'C03', 'C09', 'C10']
    df_merged = df_merged[df_merged[col_tipo].isin(tipos_interes)]

    col_sector = _resolver_columna_sector(df_merged)
    cols_map = {
        'ID': 'ID',
        'Nombre': 'Nombre',
        'País': 'Pais',
        'Tipo instrumento': 'Tipo instrumento',
        'RIC': 'RIC',
        'Isin': 'Isin',
        'Cusip': 'Cusip',
    }
    if col_sector:
        cols_map[col_sector] = 'sectores'

    existing_cols = [c for c in cols_map.keys() if c in df_merged.columns]
    df_result = df_merged[existing_cols].copy()
    df_result = df_result.rename(columns={k: v for k, v in cols_map.items() if k in existing_cols})
    df_result = df_result.drop_duplicates(subset=['ID'])

    return df_result


if __name__ == '__main__':
    pos = 'data/raw/posiciones.csv'
    instr = 'data/raw/instruments.csv'
    df = load_instruments_sector(pos, instr)
    print(f"df_instruments_sector cargado con {len(df)} registros.")
    print("Columnas actuales:", df.columns.tolist())
    print(df.head())

    os.makedirs('data/processed/sector', exist_ok=True)
    df.to_csv('data/processed/sector/df_instruments.csv', index=False, sep=';', encoding='utf-8')
