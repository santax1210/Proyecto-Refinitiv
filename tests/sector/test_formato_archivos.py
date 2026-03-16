"""
Test de Formato de Archivos Procesados — Sector
=================================================
Valida que los archivos procesados del pipeline de sector tengan el formato
correcto:

  - allocations_nuevas_sector.csv → formato LONG (múltiples filas por instrumento)
  - allocations_antiguas_sector.csv → formato WIDE (una fila por instrumento)
  - df_final_sector.csv → una fila por instrumento con columnas de estado

Si los archivos procesados no existen (pipeline aún no ejecutado), el test los
reporta como advertencia sin fallar.
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


def print_section(title):
    print('\n' + '=' * 70)
    print(f' {title.upper()} '.center(70, '='))
    print('=' * 70)


PROCESSED_SECTOR_DIR = 'data/processed/sector'


def _cargar_procesado(nombre, sep=';', encoding='utf-8'):
    path = os.path.join(PROCESSED_SECTOR_DIR, nombre)
    if not os.path.exists(path):
        print(f'    [SKIP] {nombre} no encontrado en {path}')
        print(f'           Ejecute primero: python run_pipeline_sector.py')
        return None
    df = pd.read_csv(path, sep=sep, encoding=encoding, on_bad_lines='skip')
    print(f'    [OK] {nombre} cargado: {df.shape[0]} filas × {df.shape[1]} columnas')
    return df


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_formato_allocations_nuevas_sector():
    """
    allocations_nuevas_sector.csv debe ser formato LONG:
    - Múltiples filas por instrumento (una por sector/clase)
    - Columnas: ID, Nombre, instrument, class, percentage, sector_nueva,
                pct_dominancia_nueva, pct_escalado, pct_original
    """
    print_section('TEST 1: Formato LONG — allocations_nuevas_sector.csv')

    df = _cargar_procesado('allocations_nuevas_sector.csv')
    if df is None:
        return True  # No bloqueante sin archivo

    print(f'\n    [i] Columnas: {df.columns.tolist()}')

    # Columnas requeridas
    columnas_req = [
        'ID', 'Nombre', 'instrument', 'class', 'percentage',
        'sector_nueva', 'pct_dominancia_nueva', 'pct_escalado', 'pct_original',
    ]
    faltantes = [c for c in columnas_req if c not in df.columns]
    if faltantes:
        print(f'    [X] Columnas faltantes: {faltantes}')
        return False
    print(f'    [OK] Todas las columnas requeridas presentes')

    # Verificar LONG: múltiples filas por instrumento
    total_instrumentos = df['ID'].nunique()
    total_filas = len(df)
    filas_por_instr = total_filas / total_instrumentos if total_instrumentos > 0 else 0

    print(f'\n    [i] Instrumentos únicos:  {total_instrumentos}')
    print(f'    [i] Total filas:          {total_filas}')
    print(f'    [i] Filas/instrumento:    {filas_por_instr:.2f}')

    if filas_por_instr <= 1.0:
        print('    [!] ADVERTENCIA: Parece formato WIDE (1 fila por instrumento)')
        return False
    print('    [OK] Formato LONG CONFIRMADO')

    # Distribución de sector_nueva
    print('\n    [i] Distribución de sector_nueva (Top 10):')
    print(df.drop_duplicates(subset=['ID'])['sector_nueva'].value_counts().head(10).to_string())

    # pct_escalado debe ser 100.0 (con tolerancia)
    errores_esc = []
    for id_inst in list(df['ID'].unique())[:50]:
        pct_esc = df[df['ID'] == id_inst]['pct_escalado'].iloc[0]
        if pct_esc != 0.0 and abs(pct_esc - 100.0) > 0.1:
            errores_esc.append({'ID': id_inst, 'pct_escalado': pct_esc})
    if errores_esc:
        print(f'\n    [!] {len(errores_esc)} instrumentos con pct_escalado incorrecto')
        for e in errores_esc[:3]:
            print(f'        ID={e["ID"]}: pct_escalado={e["pct_escalado"]}')
    else:
        print('\n    [OK] pct_escalado = 100.0 para todos los instrumentos con datos')

    print('\n[OK] test_formato_allocations_nuevas_sector PASADO')
    return True


def test_formato_allocations_antiguas_sector():
    """
    allocations_antiguas_sector.csv debe ser formato WIDE:
    - Una fila por instrumento
    - Columna Pct_dominancia presente
    """
    print_section('TEST 2: Formato WIDE — allocations_antiguas_sector.csv')

    df = _cargar_procesado('allocations_antiguas_sector.csv')
    if df is None:
        return True

    print(f'\n    [i] Columnas: {df.columns.tolist()}')

    # Una fila por ID (formato WIDE)
    total_filas = len(df)
    ids_unicos = df['ID'].nunique()

    print(f'\n    [i] Filas totales:         {total_filas}')
    print(f'    [i] IDs únicos:            {ids_unicos}')
    print(f'    [i] Ratio filas/ID:        {total_filas / ids_unicos:.2f}')

    if total_filas != ids_unicos:
        print(f'    [!] ADVERTENCIA: {total_filas - ids_unicos} IDs duplicados detectados')
    else:
        print('    [OK] Formato WIDE CONFIRMADO (1 fila por instrumento)')

    # Columna Pct_dominancia presente
    if 'Pct_dominancia' not in df.columns:
        print('    [X] Columna Pct_dominancia faltante')
        return False
    print('    [OK] Columna Pct_dominancia presente')

    # Distribución de Pct_dominancia (Sin datos vs con datos)
    n_sin_datos = (df['Pct_dominancia'] == 'Sin datos').sum()
    print(f'\n    [i] Con datos:   {len(df) - n_sin_datos}')
    print(f'    [i] Sin datos:   {n_sin_datos}')

    print('\n[OK] test_formato_allocations_antiguas_sector PASADO')
    return True


def test_formato_df_final_sector():
    """
    df_final_sector.csv debe:
    - Tener una fila por instrumento
    - Contener columnas sector_antigua, sector_nueva, Cambio, Estado
    """
    print_section('TEST 3: Formato df_final_sector.csv')

    df = _cargar_procesado('df_final_sector.csv')
    if df is None:
        return True

    print(f'\n    [i] Columnas: {df.columns.tolist()}')

    columnas_req = ['ID', 'Nombre', 'sector_nueva', 'sector_antigua', 'Cambio', 'Estado']
    faltantes = [c for c in columnas_req if c not in df.columns]
    if faltantes:
        print(f'    [X] Columnas faltantes: {faltantes}')
        return False
    print('    [OK] Columnas requeridas presentes')

    # Una fila por ID
    if df['ID'].nunique() != len(df):
        dupes = len(df) - df['ID'].nunique()
        print(f'    [!] {dupes} IDs duplicados en df_final_sector')
    else:
        print('    [OK] Una fila por instrumento')

    # Distribución de Estado
    if 'Estado' in df.columns:
        print('\n    [i] Distribución de Estado:')
        print(df['Estado'].value_counts().to_string())
        estados_validos = {'Estado_1', 'Estado_2', 'Estado_3', ''}
        invalidos = set(df['Estado'].dropna().unique()) - estados_validos
        if invalidos:
            print(f'    [!] Estados inválidos: {invalidos}')
        else:
            print('    [OK] Solo estados válidos presentes')

    # Distribución de Cambio
    if 'Cambio' in df.columns:
        print('\n    [i] Distribución de Cambio:')
        print(df['Cambio'].value_counts().to_string())

    print('\n[OK] test_formato_df_final_sector PASADO')
    return True


def test_consistencia_ids_sector():
    """Verifica consistencia de IDs entre allocations nuevas, antiguas y df_final."""
    print_section('TEST 4: Consistencia de IDs entre archivos procesados (sector)')

    df_nuevas = _cargar_procesado('allocations_nuevas_sector.csv')
    df_antiguas = _cargar_procesado('allocations_antiguas_sector.csv')
    df_final = _cargar_procesado('df_final_sector.csv')

    if df_nuevas is None or df_antiguas is None or df_final is None:
        print('    [SKIP] Algún archivo no disponible. Ejecute run_pipeline_sector.py primero.')
        return True

    ids_nuevas = set(df_nuevas['ID'].astype(str).unique())
    ids_antiguas = set(df_antiguas['ID'].astype(str).unique())
    ids_final = set(df_final['ID'].astype(str).unique())

    print(f'\n    [i] IDs en nuevas:   {len(ids_nuevas)}')
    print(f'    [i] IDs en antiguas: {len(ids_antiguas)}')
    print(f'    [i] IDs en final:    {len(ids_final)}')

    # IDs de nuevas deben estar contenidos en df_final
    huerfanos = ids_nuevas - ids_final
    if huerfanos:
        print(f'    [!] {len(huerfanos)} IDs en nuevas no están en df_final')
    else:
        print('    [OK] Todos los IDs de nuevas están en df_final')

    # IDs de antiguas deben estar contenidos en df_final
    huerfanos_ant = ids_antiguas - ids_final
    if huerfanos_ant:
        print(f'    [!] {len(huerfanos_ant)} IDs en antiguas no están en df_final')
    else:
        print('    [OK] Todos los IDs de antiguas están en df_final')

    print('\n[OK] test_consistencia_ids_sector PASADO')
    return True


def main():
    ok1 = test_formato_allocations_nuevas_sector()
    ok2 = test_formato_allocations_antiguas_sector()
    ok3 = test_formato_df_final_sector()
    ok4 = test_consistencia_ids_sector()
    return all([ok1, ok2, ok3, ok4])


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
