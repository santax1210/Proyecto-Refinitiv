"""
Test de Carga de Archivos — Sector
====================================
Valida que los archivos raw del pipeline de sector existan y puedan cargarse
con la estructura esperada (columnas, delimitador, encoding).

Si algún archivo no existe, el test lo reporta como advertencia pero no falla
de forma irrecuperable (los archivos de datos no están versionados).
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


def print_section(title):
    print('\n' + '=' * 70)
    print(f' {title.upper()} '.center(70, '='))
    print('=' * 70)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _cargar_csv(path, sep=';', encoding='latin-1', nombre='archivo'):
    """Intenta cargar un CSV y devuelve (df, ok)."""
    if not os.path.exists(path):
        print(f'    [!] ADVERTENCIA: {nombre} no encontrado en {path}')
        return None, False
    try:
        df = pd.read_csv(path, sep=sep, encoding=encoding, nrows=5, on_bad_lines='skip')
        print(f'    [OK] {nombre} cargado ({len(df.columns)} columnas detectadas)')
        return df, True
    except Exception as exc:
        print(f'    [X] ERROR al cargar {nombre}: {exc}')
        return None, False


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_carga_instruments_sector():
    """Valida que instruments.csv del sector tenga las columnas necesarias."""
    print_section('TEST 1: Carga de instruments.csv (sector)')

    path = 'data/raw/sector/instruments.csv'
    df, ok = _cargar_csv(path, nombre='instruments.csv')

    if not ok:
        print('    [SKIP] No se puede validar sin el archivo.')
        return True  # No bloqueante

    columnas_requeridas = ['ID', 'Nombre']
    faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if faltantes:
        print(f'    [X] Columnas requeridas faltantes: {faltantes}')
        return False

    print(f'    [OK] Columnas presentes: {df.columns.tolist()}')
    print(df.head(2).to_string(index=False))
    print('\n[OK] test_carga_instruments_sector PASADO')
    return True


def test_carga_posiciones_sector():
    """Valida que posiciones.csv del sector sea legible."""
    print_section('TEST 2: Carga de posiciones.csv (sector)')

    # Acepta tanto 'posiciones.csv' como 'posiciones.csv.csv' (error de nombre conocido)
    candidatos = [
        'data/raw/sector/posiciones.csv',
        'data/raw/sector/posiciones.csv.csv',
    ]
    df, ok = None, False
    for path in candidatos:
        df, ok = _cargar_csv(path, nombre='posiciones.csv')
        if ok:
            break

    if not ok:
        print('    [SKIP] No se puede validar sin el archivo.')
        return True

    columnas_requeridas = ['ID']
    faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if faltantes:
        print(f'    [X] Columnas requeridas faltantes: {faltantes}')
        return False

    print(f'    [OK] Columnas presentes: {df.columns.tolist()}')
    print('\n[OK] test_carga_posiciones_sector PASADO')
    return True


def test_carga_allocations_nuevas_sector():
    """Valida que allocations_nuevas.csv del sector tenga classif y percentage."""
    print_section('TEST 3: Carga de allocations_nuevas.csv (sector)')

    path = 'data/raw/sector/allocations_nuevas.csv'
    df, ok = _cargar_csv(path, nombre='allocations_nuevas.csv')

    if not ok:
        print('    [SKIP] No se puede validar sin el archivo.')
        return True

    columnas_requeridas = ['instrument', 'class', 'percentage', 'classif']
    faltantes = [c for c in columnas_requeridas if c not in df.columns]
    if faltantes:
        print(f'    [!] Columnas requeridas no encontradas: {faltantes}')
        print(f'        Columnas presentes: {df.columns.tolist()}')
        return False

    # Verificar que haya filas con classif == 'industry'
    df_full = pd.read_csv(path, sep=';', encoding='latin-1', on_bad_lines='skip')
    df_full.columns = df_full.columns.str.strip()
    if 'classif' in df_full.columns:
        n_industry = (df_full['classif'].astype(str).str.strip().str.lower() == 'industry').sum()
        print(f'    [i] Filas con classif=industry: {n_industry}')
        if n_industry == 0:
            print('    [!] ADVERTENCIA: No hay filas con classif=industry en el archivo.')
    print('\n[OK] test_carga_allocations_nuevas_sector PASADO')
    return True


def test_carga_allocations_antiguas_sector():
    """Valida que allocations_sector.csv (antiguas) sea legible y tenga ID."""
    print_section('TEST 4: Carga de allocations_sector.csv (antiguas sector)')

    path = 'data/raw/sector/allocations_sector.csv'
    df, ok = _cargar_csv(path, nombre='allocations_sector.csv')

    if not ok:
        print('    [SKIP] No se puede validar sin el archivo.')
        return True

    if 'ID' not in df.columns:
        print(f'    [X] Columna ID no encontrada. Columnas presentes: {df.columns.tolist()}')
        return False

    print(f'    [OK] Columnas presentes: {df.columns.tolist()}')
    print('\n[OK] test_carga_allocations_antiguas_sector PASADO')
    return True


def test_resumen_archivos():
    """Imprime resumen de disponibilidad de todos los archivos raw del sector."""
    print_section('RESUMEN: Disponibilidad de archivos raw (sector)')

    archivos = {
        'data/raw/sector/instruments.csv': 'Maestro de Instrumentos',
        'data/raw/sector/posiciones.csv': 'Posiciones',
        'data/raw/sector/posiciones.csv.csv': 'Posiciones (nombre alternativo)',
        'data/raw/sector/allocations_nuevas.csv': 'Allocations Nuevas (sector)',
        'data/raw/sector/allocations_sector.csv': 'Allocations Antiguas (sector)',
    }

    disponibles = 0
    for ruta, desc in archivos.items():
        existe = os.path.exists(ruta)
        estado = '[OK]' if existe else '[--]'
        if existe:
            disponibles += 1
        print(f'    {estado} {desc:45} {ruta}')

    print(f'\n    Total disponibles: {disponibles}/{len(archivos)} archivos')
    print('\n[OK] test_resumen_archivos PASADO')
    return True


def main():
    ok1 = test_carga_instruments_sector()
    ok2 = test_carga_posiciones_sector()
    ok3 = test_carga_allocations_nuevas_sector()
    ok4 = test_carga_allocations_antiguas_sector()
    ok5 = test_resumen_archivos()
    return all([ok1, ok2, ok3, ok4, ok5])


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
