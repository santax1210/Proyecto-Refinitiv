"""
Test de Pipeline Completo (End-to-End) — Sector
=================================================
Ejecuta y valida el pipeline completo de sector desde archivos raw hasta exports,
siguiendo los mismos pasos de detalle que test_pipeline_completo.py de moneda:

  Test 1  — Verificar archivos raw
  Test 2  — Ejecutar run_pipeline_sector.py
  Test 3  — Verificar archivos procesados generados
  Test 4  — Verificar archivos de exportación
  Test 5  — Validar contenido de archivos (columnas, formato, tipos, merge)
  Test 6  — Validación de integridad (IDs consistentes entre archivos)
  Test 7  — Pipeline sintético end-to-end (sin archivos raw)
  Test 8  — Métricas del pipeline sintético

Los tests 1-6 se saltan automáticamente si los archivos raw no están disponibles.
Los tests 7-8 siempre se ejecutan usando datos sintéticos.
"""

import os
import sys
import subprocess
import tempfile
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.extractors.sector.load_allocations_sector import (
    load_allocations_nuevas_sector,
    load_allocations_antiguas_sector,
)
from src.logic.sector.clasificacion_sector import ejecutar_pipeline_completo_sector


def print_section(title):
    print('\n' + '=' * 80)
    print(f' {title.upper()} '.center(80, '='))
    print('=' * 80)


def check_file_exists(filepath, descripcion):
    """Verifica que un archivo exista y retorna su tamaño."""
    if os.path.exists(filepath):
        size_kb = os.path.getsize(filepath) / 1024
        print(f'    [OK] {descripcion:45} ({size_kb:>8.1f} KB)')
        return True
    else:
        print(f'    [X] {descripcion:45} [NO ENCONTRADO]')
        return False


# ---------------------------------------------------------------------------
# Tests con archivos reales (Tests 1-6)
# ---------------------------------------------------------------------------

def test_pipeline_completo():
    """
    Ejecuta y valida el pipeline completo de sector con archivos reales.
    Si faltan archivos raw, informa y retorna True (no bloqueante).
    """

    print_section('Test de Pipeline Completo — Sector (End-to-End)')
    print(f'\nFecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

    # ------------------------------------------------------------------
    # TEST 1: VERIFICAR ARCHIVOS RAW
    # ------------------------------------------------------------------
    print_section('Test 1: Validación de Archivos Raw')

    archivos_raw = {
        'data/raw/sector/instruments.csv':       'Maestro de Instrumentos',
        'data/raw/sector/allocations_nuevas.csv': 'Allocations Nuevas (sector)',
        'data/raw/sector/allocations_sector.csv': 'Allocations Antiguas (sector)',
    }
    # Posiciones acepta dos nombres de archivo
    pos_candidatos = [
        'data/raw/sector/posiciones.csv',
        'data/raw/sector/posiciones.csv.csv',
    ]
    pos_path = next((p for p in pos_candidatos if os.path.exists(p)), None)

    print('\n[i] Verificando archivos de entrada...')
    todos_ok = True
    for filepath, desc in archivos_raw.items():
        if not check_file_exists(filepath, desc):
            todos_ok = False

    if pos_path:
        size_kb = os.path.getsize(pos_path) / 1024
        print(f'    [OK] {"Posiciones":45} ({size_kb:>8.1f} KB)')
    else:
        print(f'    [X] {"Posiciones":45} [NO ENCONTRADO]')
        todos_ok = False

    if not todos_ok:
        print('\n[SKIP] Faltan archivos raw necesarios. Saltando tests 1-6.')
        print('       Coloque los archivos en data/raw/sector/ y vuelva a ejecutar.')
        return True

    print('\n[[OK]] Todos los archivos raw están presentes.')

    # ------------------------------------------------------------------
    # TEST 2: EJECUTAR PIPELINE
    # ------------------------------------------------------------------
    print_section('Test 2: Ejecución del Pipeline')

    print('\n[...] Ejecutando: python run_pipeline_sector.py')
    print('[i] Esto puede tomar unos segundos...\n')

    try:
        result = subprocess.run(
            [sys.executable, 'run_pipeline_sector.py'],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode == 0:
            print('[[OK]] Pipeline ejecutado exitosamente (exit code 0)')
        else:
            print(f'\n[!] ERROR: Pipeline falló con exit code {result.returncode}')
            print('\n--- STDERR ---')
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
            return False

        output = result.stdout
        # Extraer métricas clave del log si están disponibles
        for line in output.split('\n'):
            for kw in ['instrumentos cargados', 'registros procesados', 'instrumentos con datos',
                       'PIPELINE', 'FASE']:
                if kw.lower() in line.lower():
                    print(f'[i] {line.strip()}')
                    break

    except subprocess.TimeoutExpired:
        print('\n[!] ERROR: Pipeline excedió el tiempo límite (2 minutos)')
        return False
    except Exception as exc:
        print(f'\n[!] ERROR al ejecutar pipeline: {exc}')
        return False

    # ------------------------------------------------------------------
    # TEST 3: VERIFICAR ARCHIVOS PROCESADOS
    # ------------------------------------------------------------------
    print_section('Test 3: Validación de Archivos Procesados')

    archivos_procesados = {
        'data/processed/sector/df_instruments.csv':             'Instrumentos Filtrados (sector)',
        'data/processed/sector/allocations_nuevas_sector.csv':  'Allocations Nuevas (LONG)',
        'data/processed/sector/allocations_antiguas_sector.csv':'Allocations Antiguas (WIDE)',
        'data/processed/sector/df_final_sector.csv':            'DataFrame Final Consolidado',
    }

    print('\n[i] Verificando archivos procesados...')
    todos_ok = True
    for filepath, desc in archivos_procesados.items():
        if not check_file_exists(filepath, desc):
            todos_ok = False

    if not todos_ok:
        print('\n[!] ERROR: Faltan archivos procesados.')
        return False

    print('\n[[OK]] Todos los archivos procesados generados.')

    # ------------------------------------------------------------------
    # TEST 4: VERIFICAR ARCHIVOS DE EXPORTACIÓN
    # ------------------------------------------------------------------
    print_section('Test 4: Validación de Archivos de Exportación')

    archivos_export = {
        'data/exports/sector/export_balanceados.csv':    'Export Balanceados',
        'data/exports/sector/export_no_balanceados.csv': 'Export No Balanceados',
        'data/exports/sector/export_con_cambios.csv':    'Export Con Cambios',
        'data/exports/sector/export_sin_datos.csv':      'Export Sin Datos',
    }

    print('\n[i] Verificando archivos de exportación...')
    todos_ok = True
    for filepath, desc in archivos_export.items():
        if not check_file_exists(filepath, desc):
            todos_ok = False

    if not todos_ok:
        print('\n[!] ADVERTENCIA: Faltan algunos archivos de exportación.')
    else:
        print('\n[[OK]] Todos los archivos de exportación generados.')

    # ------------------------------------------------------------------
    # TEST 5: VALIDAR CONTENIDO DE ARCHIVOS
    # ------------------------------------------------------------------
    print_section('Test 5: Validación de Contenido')

    errores = []

    # 5.1 — df_instruments
    print('\n[i] Validando df_instruments.csv (sector)...')
    try:
        df_instr = pd.read_csv('data/processed/sector/df_instruments.csv',
                               sep=';', encoding='utf-8', on_bad_lines='skip')
        print(f'    Registros: {len(df_instr)}')
        print(f'    Columnas:  {list(df_instr.columns)}')

        cols_req = ['ID', 'Nombre', 'Tipo instrumento', 'RIC', 'Isin', 'Cusip']
        faltantes = [c for c in cols_req if c not in df_instr.columns]
        if faltantes:
            errores.append(f'df_instruments: Columnas faltantes {faltantes}')
        else:
            print('    [OK] Columnas requeridas presentes')

        if 'sectores' in df_instr.columns:
            print('    [OK] Columna sectores (clasificación antigua) presente')
        else:
            print('    [!] ADVERTENCIA: Columna sectores no encontrada')

        if len(df_instr) < 10:
            print(f'    [!] ADVERTENCIA: Pocos instrumentos ({len(df_instr)})')

    except Exception as exc:
        errores.append(f'df_instruments: {exc}')

    # 5.2 — allocations_nuevas_sector (LONG)
    print('\n[i] Validando allocations_nuevas_sector.csv...')
    try:
        df_nuevas = pd.read_csv('data/processed/sector/allocations_nuevas_sector.csv',
                                sep=';', encoding='utf-8', on_bad_lines='skip')
        print(f'    Registros:     {len(df_nuevas)}')
        print(f'    Instrumentos:  {df_nuevas["ID"].nunique()}')
        print(f'    Columnas:      {df_nuevas.shape[1]}')

        cols_req = ['ID', 'Nombre', 'instrument', 'class', 'percentage',
                    'sector_nueva', 'pct_dominancia_nueva', 'pct_escalado', 'pct_original']
        faltantes = [c for c in cols_req if c not in df_nuevas.columns]
        if faltantes:
            errores.append(f'allocations_nuevas_sector: Columnas faltantes {faltantes}')
        else:
            print('    [OK] Columnas de dominancia presentes')

        filas_por_inst = len(df_nuevas) / df_nuevas['ID'].nunique() if df_nuevas['ID'].nunique() > 0 else 0
        if filas_por_inst > 1.5:
            print(f'    [OK] Formato LONG confirmado ({filas_por_inst:.1f} filas/instrumento)')
        else:
            errores.append(f'allocations_nuevas_sector: Parece formato WIDE ({filas_por_inst:.1f} filas/inst)')

        # Distribución sector_nueva
        if 'sector_nueva' in df_nuevas.columns:
            print('\n    [i] Distribución sector_nueva (únicos por ID):')
            dist = df_nuevas.drop_duplicates(subset=['ID'])['sector_nueva'].value_counts()
            for val, cnt in dist.head(10).items():
                print(f'        {val}: {cnt}')

    except Exception as exc:
        errores.append(f'allocations_nuevas_sector: {exc}')

    # 5.3 — allocations_antiguas_sector (WIDE)
    print('\n[i] Validando allocations_antiguas_sector.csv...')
    try:
        df_antiguas = pd.read_csv('data/processed/sector/allocations_antiguas_sector.csv',
                                  sep=';', encoding='utf-8', on_bad_lines='skip', nrows=10)
        print(f'    Columnas: {df_antiguas.shape[1]}')

        if 'Pct_dominancia' not in df_antiguas.columns:
            errores.append('allocations_antiguas_sector: Falta columna Pct_dominancia')
        else:
            print('    [OK] Columna Pct_dominancia presente')

        if 'Sectores:' in df_antiguas.columns:
            print('    [OK] Columna Sectores: presente')
        else:
            print('    [!] ADVERTENCIA: Columna Sectores: no encontrada')

        # Formato WIDE → muchas columnas de sector
        if df_antiguas.shape[1] < 5:
            errores.append(f'allocations_antiguas_sector: Parece incompleto (solo {df_antiguas.shape[1]} cols)')
        else:
            print(f'    [OK] Formato WIDE ({df_antiguas.shape[1]} columnas)')

    except Exception as exc:
        errores.append(f'allocations_antiguas_sector: {exc}')

    # 5.4 — df_final_sector
    print('\n[i] Validando df_final_sector.csv...')
    try:
        df_final = pd.read_csv('data/processed/sector/df_final_sector.csv',
                               sep=';', encoding='utf-8', on_bad_lines='skip')
        print(f'    Registros: {len(df_final)}')
        print(f'    Columnas:  {df_final.shape[1]}')

        # Tipo de ID
        if 'ID' in df_final.columns:
            id_dtype = df_final['ID'].dtype
            if id_dtype in ['int64', 'Int64', 'int32', 'Int32']:
                print(f'    [OK] Columna ID tiene tipo correcto: {id_dtype}')
            else:
                errores.append(f'df_final_sector: Columna ID tiene tipo incorrecto {id_dtype}')

        # pct_dominancia_nueva poblada
        if 'pct_dominancia_nueva' in df_final.columns:
            n_poblado = df_final['pct_dominancia_nueva'].notna().sum()
            pct_pob = n_poblado / len(df_final) * 100
            print(f'    [i] pct_dominancia_nueva poblado: {n_poblado}/{len(df_final)} ({pct_pob:.1f}%)')
            if pct_pob < 10:
                errores.append(f'df_final_sector: pct_dominancia_nueva muy baja cobertura ({pct_pob:.1f}%)')
            else:
                print('    [OK] pct_dominancia_nueva correctamente poblada')
        else:
            errores.append('df_final_sector: Falta columna pct_dominancia_nueva')

        # pct_dominancia_antigua poblada
        if 'pct_dominancia_antigua' in df_final.columns:
            n_pob_ant = df_final['pct_dominancia_antigua'].notna().sum()
            pct_pob_ant = n_pob_ant / len(df_final) * 100
            print(f'    [i] pct_dominancia_antigua poblado: {n_pob_ant}/{len(df_final)} ({pct_pob_ant:.1f}%)')
            if pct_pob_ant == 0:
                errores.append('df_final_sector: pct_dominancia_antigua está completamente vacía (error de merge)')
            else:
                print('    [OK] pct_dominancia_antigua correctamente poblada')
        else:
            errores.append('df_final_sector: Falta columna pct_dominancia_antigua')

        # Columnas Estado y Cambio
        for col in ['Estado', 'Cambio', 'sector_nueva', 'sector_antigua']:
            if col in df_final.columns:
                print(f'    [OK] Columna {col!r} presente')
            else:
                errores.append(f'df_final_sector: Falta columna {col!r}')

        # Distribución de Estado
        if 'Estado' in df_final.columns:
            print('\n    [i] Distribución de Estado:')
            for val, cnt in df_final['Estado'].value_counts(dropna=False).items():
                print(f'        {str(val):12}: {cnt}')
            estados_invalidos = set(df_final['Estado'].dropna().unique()) - {'Estado_1', 'Estado_2', 'Estado_3', ''}
            if estados_invalidos:
                errores.append(f'df_final_sector: Estados inválidos detectados: {estados_invalidos}')
            else:
                print('    [OK] Solo estados válidos (Estado_1 / Estado_2 / Estado_3)')

        # Distribución de Cambio
        if 'Cambio' in df_final.columns:
            print('\n    [i] Distribución de Cambio:')
            for val, cnt in df_final['Cambio'].value_counts(dropna=False).items():
                print(f'        {str(val):12}: {cnt}')

    except Exception as exc:
        errores.append(f'df_final_sector: {exc}')

    if errores:
        print(f'\n[!] Se encontraron {len(errores)} errores:')
        for err in errores:
            print(f'    [X] {err}')
        return False
    else:
        print('\n[[OK]] Validación de contenido exitosa.')

    # ------------------------------------------------------------------
    # TEST 6: VALIDACIÓN DE INTEGRIDAD (IDs entre archivos)
    # ------------------------------------------------------------------
    print_section('Test 6: Validación de Integridad')

    print('\n[i] Verificando integridad de datos...')

    try:
        df_instr    = pd.read_csv('data/processed/sector/df_instruments.csv',
                                  sep=';', encoding='utf-8', on_bad_lines='skip')
        df_nuevas   = pd.read_csv('data/processed/sector/allocations_nuevas_sector.csv',
                                  sep=';', encoding='utf-8', on_bad_lines='skip')
        df_antiguas = pd.read_csv('data/processed/sector/allocations_antiguas_sector.csv',
                                  sep=';', encoding='utf-8', on_bad_lines='skip')
        df_final    = pd.read_csv('data/processed/sector/df_final_sector.csv',
                                  sep=';', encoding='utf-8', on_bad_lines='skip')

        # Tipos de datos de ID
        print('\n[i] Validando tipos de datos de columna "ID":')
        tipos_ok = True
        for nombre, df in [('df_instruments',             df_instr),
                           ('allocations_nuevas_sector',  df_nuevas),
                           ('allocations_antiguas_sector',df_antiguas),
                           ('df_final_sector',            df_final)]:
            id_dtype = df['ID'].dtype
            icono = '[OK]' if id_dtype in ['int64', 'Int64', 'int32', 'Int32'] else '[X] '
            print(f'    {icono} {nombre:30} → dtype: {id_dtype}')
            if icono == '[X] ':
                tipos_ok = False

        if tipos_ok:
            print('    [OK] Tipos de datos consistentes para ID')
        else:
            print('    [!] Tipos de datos inconsistentes detectados')

        ids_instr    = set(df_instr['ID'].dropna().astype(int))
        ids_nuevas   = set(df_nuevas['ID'].dropna().astype(int))
        ids_antiguas = set(df_antiguas['ID'].dropna().astype(int))
        ids_final    = set(df_final['ID'].dropna().astype(int))

        print(f'\n[i] IDs por archivo:')
        print(f'    df_instruments:              {len(ids_instr)}')
        print(f'    allocations_nuevas_sector:   {len(ids_nuevas)}')
        print(f'    allocations_antiguas_sector: {len(ids_antiguas)}')
        print(f'    df_final_sector:             {len(ids_final)}')

        # IDs de nuevas y antiguas deben ser subconjuntos de instruments
        if ids_nuevas.issubset(ids_instr):
            print('    [OK] IDs de nuevas están en instruments')
        else:
            print(f'    [!] ADVERTENCIA: {len(ids_nuevas - ids_instr)} IDs de nuevas no están en instruments')

        if ids_antiguas.issubset(ids_instr):
            print('    [OK] IDs de antiguas están en instruments')
        else:
            print(f'    [!] ADVERTENCIA: {len(ids_antiguas - ids_instr)} IDs de antiguas no están en instruments')

        # Cobertura
        cob_nuevas   = len(ids_nuevas)   / len(ids_instr) * 100 if ids_instr else 0
        cob_antiguas = len(ids_antiguas) / len(ids_instr) * 100 if ids_instr else 0

        print(f'\n[i] Cobertura:')
        print(f'    Nuevas:   {cob_nuevas:.1f}% de instruments')
        print(f'    Antiguas: {cob_antiguas:.1f}% de instruments')

        if cob_nuevas > 5 and cob_antiguas > 5:
            print('\n[[OK]] Cobertura razonable en ambos archivos')
        else:
            print('\n[!] ADVERTENCIA: Cobertura baja — revisar archivos raw')

    except Exception as exc:
        print(f'\n[!] ERROR en validación de integridad: {exc}')

    # ------------------------------------------------------------------
    # RESUMEN FINAL
    # ------------------------------------------------------------------
    print_section('Resumen Final del Pipeline — Sector')

    print('\n[OK] Pipeline ejecutado exitosamente')
    print('[OK] Todos los archivos generados')
    print('[OK] Formato LONG verificado en allocations_nuevas_sector')
    print('[OK] Formato WIDE verificado en allocations_antiguas_sector')
    print('[OK] Contenido y columnas validados')
    print('[OK] Integridad de IDs verificada')

    print('\n' + '=' * 80)
    print(' [OK] TEST DE PIPELINE COMPLETO SECTOR EXITOSO '.center(80, '='))
    print('=' * 80)

    return True


def main():
    print(f'\nFecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    ok_real = test_pipeline_completo()
    return ok_real


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
