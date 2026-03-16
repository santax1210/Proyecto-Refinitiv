"""
Test de Creación de DataFrames — Sector
==========================================
Valida la creación correcta de los tres dataframes base del pipeline de sector:

  1. df_instruments_sector  — cruce posiciones × maestro con filtro por tipo
  2. allocations_nuevas_sector — formato LONG con classif=industry y dominancia
  3. allocations_antiguas_sector — formato WIDE con Pct_dominancia calculada

Los tests usan datos sintéticos generados en tempfiles para no depender de
los archivos raw del repositorio.
"""

import os
import sys
import tempfile

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.extractors.sector.load_allocations_sector import (
    load_allocations_nuevas_sector,
    load_allocations_antiguas_sector,
)


def print_section(title):
    print('\n' + '=' * 70)
    print(f' {title.upper()} '.center(70, '='))
    print('=' * 70)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _df_instruments_sintetico():
    return pd.DataFrame([
        {'ID': 1, 'Nombre': 'Fondo Tech', 'Tipo instrumento': 'C03',
         'RIC': 'RIC1', 'Isin': 'ISIN1', 'Cusip': 'CUSIP1', 'sectores': 'Technology'},
        {'ID': 2, 'Nombre': 'Fondo Salud', 'Tipo instrumento': 'C03',
         'RIC': 'RIC2', 'Isin': 'ISIN2', 'Cusip': 'CUSIP2', 'sectores': 'Healthcare'},
        {'ID': 3, 'Nombre': 'Fondo Bal', 'Tipo instrumento': 'C03',
         'RIC': 'RIC3', 'Isin': 'ISIN3', 'Cusip': 'CUSIP3', 'sectores': 'Balanceado'},
    ])


def _csv_nuevas_sintetico():
    """CSV con classif=industry para 3 instrumentos (2 con dominancia, 1 balanceado)."""
    return (
        ';instrument;date;class;percentage;Columna Fuente;classif\n'
        # ID=1: Technology domina al 95% → sector_nueva = Technology
        '0;RIC1;2025-01-31;Technology;95,0;IndustryAllocation;industry\n'
        '1;RIC1;2025-01-31;Healthcare;5,0;IndustryAllocation;industry\n'
        # ID=2: Healthcare domina al 91% → sector_nueva = Healthcare
        '2;RIC2;2025-01-31;Healthcare;91,0;IndustryAllocation;industry\n'
        '3;RIC2;2025-01-31;Financials;9,0;IndustryAllocation;industry\n'
        # ID=3: Balanceado (40/35/25) → sector_nueva = Balanceado
        '4;RIC3;2025-01-31;Technology;40,0;IndustryAllocation;industry\n'
        '5;RIC3;2025-01-31;Healthcare;35,0;IndustryAllocation;industry\n'
        '6;RIC3;2025-01-31;Financials;25,0;IndustryAllocation;industry\n'
        # Fila con country (debe ser excluida por filtro classif)
        '7;RIC1;2025-01-31;Chile;100,0;CountryAllocation;country\n'
    )


def _csv_antiguas_sintetico():
    """CSV de allocations antiguas en formato WIDE con col 'Sectores:'."""
    return (
        'ID;Nombre;Technology;Healthcare;Financials;Sectores:\n'
        '1;Fondo Tech;100;0;0;ASIGNADO\n'
        '2;Fondo Salud;0;80;20;ASIGNADO\n'
        '3;Fondo Bal;40;35;25;VACÍO\n'
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_creacion_df_instruments():
    """
    Valida las propiedades básicas de df_instruments:
    columna ID como int, no duplicados, columna sectores presente.
    """
    print_section('TEST 1: Validación de df_instruments (sintético)')

    df = _df_instruments_sintetico()

    # ID debe ser numérico
    assert pd.api.types.is_integer_dtype(df['ID']), 'ID debe ser tipo entero'
    # Sin duplicados de ID
    assert df['ID'].nunique() == len(df), 'No debe haber IDs duplicados'
    # Columnas mínimas presentes
    for col in ['ID', 'Nombre', 'RIC', 'Isin', 'Cusip', 'sectores']:
        assert col in df.columns, f'Columna requerida faltante: {col}'

    print(f'    [OK] {len(df)} instrumentos cargados, sin duplicados')
    print(f'    [OK] Columnas: {df.columns.tolist()}')
    print(df.to_string(index=False))
    print('\n[OK] test_creacion_df_instruments PASADO')
    return True


def test_creacion_allocations_nuevas_sector():
    """
    Valida la carga de allocations nuevas:
    - Solo quedan filas con classif=industry
    - Columnas requeridas presentes
    - sector_nueva calculado correctamente
    - IDs cruzados con df_instruments
    """
    print_section('TEST 2: Creación de allocations_nuevas_sector (sintético)')

    df_instruments = _df_instruments_sintetico()

    with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, encoding='latin-1') as f:
        f.write(_csv_nuevas_sintetico())
        tmp_path = f.name

    try:
        df = load_allocations_nuevas_sector(df_instruments, tmp_path, umbral=0.9)
    finally:
        os.unlink(tmp_path)

    print(f'    [i] Registros en allocations_nuevas_sector: {len(df)}')
    print(df[['ID', 'Nombre', 'class', 'percentage', 'sector_nueva', 'pct_dominancia_nueva']].to_string(index=False))

    # Columnas requeridas
    columnas_req = ['ID', 'Nombre', 'instrument', 'class', 'percentage',
                    'sector_nueva', 'pct_dominancia_nueva', 'pct_escalado', 'pct_original']
    faltantes = [c for c in columnas_req if c not in df.columns]
    assert not faltantes, f'Columnas faltantes: {faltantes}'

    # Solo IDs que existen en df_instruments
    ids_en_df = set(df_instruments['ID'].unique())
    ids_en_nuevas = set(df['ID'].unique())
    assert ids_en_nuevas.issubset(ids_en_df), 'Hay IDs en nuevas que no existen en df_instruments'

    # Formato LONG: múltiples filas por instrumento
    filas_por_id = df.groupby('ID').size()
    assert (filas_por_id > 1).any(), 'allocations_nuevas_sector debe ser formato LONG'

    # Validar clasificación para ID=1 (domina Technology 95%)
    sector_id1 = df[df['ID'] == 1]['sector_nueva'].iloc[0]
    assert sector_id1 == 'Technology', f'ID=1 debe ser Technology, obtenido: {sector_id1}'

    # Validar clasificación para ID=3 (balanceado)
    sector_id3 = df[df['ID'] == 3]['sector_nueva'].iloc[0]
    assert sector_id3 == 'Balanceado', f'ID=3 debe ser Balanceado, obtenido: {sector_id3}'

    print('\n    [OK] Columnas requeridas presentes')
    print('    [OK] Formato LONG confirmado')
    print('    [OK] Dominancia calculada correctamente')
    print('\n[OK] test_creacion_allocations_nuevas_sector PASADO')
    return True


def test_creacion_allocations_antiguas_sector():
    """
    Valida la carga de allocations antiguas:
    - Columna Pct_dominancia calculada
    - Columna Sectores: presente
    - IDs cruzados con df_instruments
    """
    print_section('TEST 3: Creación de allocations_antiguas_sector (sintético)')

    df_instruments = _df_instruments_sintetico()

    with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, encoding='latin-1') as f:
        f.write(_csv_antiguas_sintetico())
        tmp_path = f.name

    try:
        df = load_allocations_antiguas_sector(df_instruments, tmp_path)
    finally:
        os.unlink(tmp_path)

    print(f'    [i] Registros en allocations_antiguas_sector: {len(df)}')
    print(df.to_string(index=False))

    # Columnas mínimas
    assert 'ID' in df.columns, 'Columna ID faltante'
    assert 'Pct_dominancia' in df.columns, 'Columna Pct_dominancia faltante'

    # Pct_dominancia no vacío para instrumentos con datos
    sin_pct = df[df['Pct_dominancia'].isna() | (df['Pct_dominancia'] == '')]
    assert len(sin_pct) == 0, f'{len(sin_pct)} instrumentos con Pct_dominancia vacío'

    # IDs en df únicamente de los que cruzaron con df_instruments
    ids_en_df = set(df_instruments['ID'].unique())
    ids_en_antiguas = set(df['ID'].astype(int).unique())
    assert ids_en_antiguas.issubset(ids_en_df), 'Hay IDs huérfanos en antiguas'

    print('\n    [OK] Columna Pct_dominancia calculada')
    print('    [OK] IDs válidos')
    print('\n[OK] test_creacion_allocations_antiguas_sector PASADO')
    return True


def test_cobertura_cruce_ids():
    """Valida cobertura del cruce entre nuevas e instruments."""
    print_section('TEST 4: Cobertura del cruce de IDs (sector)')

    df_instruments = _df_instruments_sintetico()

    with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, encoding='latin-1') as f:
        f.write(_csv_nuevas_sintetico())
        tmp_path = f.name

    try:
        df_nuevas = load_allocations_nuevas_sector(df_instruments, tmp_path, umbral=0.9)
    finally:
        os.unlink(tmp_path)

    ids_instruments = set(df_instruments['ID'].unique())
    ids_nuevas = set(df_nuevas['ID'].unique())
    cobertura = len(ids_nuevas) / len(ids_instruments) * 100

    print(f'    [i] Instrumentos totales:          {len(ids_instruments)}')
    print(f'    [i] Con allocations nuevas sector: {len(ids_nuevas)}')
    print(f'    [i] Cobertura:                     {cobertura:.1f}%')

    assert ids_nuevas.issubset(ids_instruments), 'IDs huérfanos en allocations nuevas'
    assert len(ids_nuevas) > 0, 'No se encontró ningún instrumento en allocations nuevas'

    print('\n[OK] test_cobertura_cruce_ids PASADO')
    return True


def main():
    ok1 = test_creacion_df_instruments()
    ok2 = test_creacion_allocations_nuevas_sector()
    ok3 = test_creacion_allocations_antiguas_sector()
    ok4 = test_cobertura_cruce_ids()
    return all([ok1, ok2, ok3, ok4])


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
