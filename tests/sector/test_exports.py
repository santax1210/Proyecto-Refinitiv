"""
Test de Exports — Sector
==========================
Valida la generación de los exports del pipeline de sector:

  1. Export balanceados  — formato WIDE con columnas de sector en %, Fecha, Estado
  2. Export no balanceados — formato tabulado con Estado y Sobreescribir
  3. Export sin datos    — instrumentos sin cobertura en allocations nuevas

Todos los tests usan datos sintéticos para no depender de archivos raw.
"""

import os
import sys
from datetime import datetime

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.logic.sector.crear_df_final_sector import crear_df_final_sector
from src.logic.sector.generar_exports_sector import (
    generar_export_balanceados_sector,
    generar_export_no_balanceados_sector,
    generar_export_sin_datos_sector,
)


def print_section(title):
    print('\n' + '=' * 70)
    print(f' {title.upper()} '.center(70, '='))
    print('=' * 70)


# ---------------------------------------------------------------------------
# Datos sintéticos compartidos
# ---------------------------------------------------------------------------

def _datos_sinteticos():
    df_instruments = pd.DataFrame([
        {'ID': 1, 'Nombre': 'Fondo Balanceado',   'Tipo instrumento': 'C03', 'sectores': 'Technology'},
        {'ID': 2, 'Nombre': 'Fondo Concentrado',  'Tipo instrumento': 'C03', 'sectores': 'Balanceado'},
        {'ID': 3, 'Nombre': 'Fondo Sin Datos',    'Tipo instrumento': 'C03', 'sectores': 'Energy'},
    ])

    df_nuevas = pd.DataFrame([
        # ID=1: Balanceado en nuevas (40/35/25)
        {'ID': 1, 'Nombre': 'Fondo Balanceado',  'instrument': 'R1', 'class': 'Technology',
         'percentage': 40.0, 'tipo_id': 'RIC', 'sector_nueva': 'Balanceado',
         'pct_dominancia_nueva': 'Technology 40.00%', 'pct_escalado': 100.0, 'pct_original': 100.0},
        {'ID': 1, 'Nombre': 'Fondo Balanceado',  'instrument': 'R1', 'class': 'Healthcare',
         'percentage': 35.0, 'tipo_id': 'RIC', 'sector_nueva': 'Balanceado',
         'pct_dominancia_nueva': 'Technology 40.00%', 'pct_escalado': 100.0, 'pct_original': 100.0},
        {'ID': 1, 'Nombre': 'Fondo Balanceado',  'instrument': 'R1', 'class': 'Financials',
         'percentage': 25.0, 'tipo_id': 'RIC', 'sector_nueva': 'Balanceado',
         'pct_dominancia_nueva': 'Technology 40.00%', 'pct_escalado': 100.0, 'pct_original': 100.0},
        # ID=2: Utilities domina al 95%
        {'ID': 2, 'Nombre': 'Fondo Concentrado', 'instrument': 'R2', 'class': 'Utilities',
         'percentage': 95.0, 'tipo_id': 'RIC', 'sector_nueva': 'Utilities',
         'pct_dominancia_nueva': 'Utilities 95.00%', 'pct_escalado': 100.0, 'pct_original': 100.0},
        {'ID': 2, 'Nombre': 'Fondo Concentrado', 'instrument': 'R2', 'class': 'Energy',
         'percentage': 5.0,  'tipo_id': 'RIC', 'sector_nueva': 'Utilities',
         'pct_dominancia_nueva': 'Utilities 95.00%', 'pct_escalado': 100.0, 'pct_original': 100.0},
        # ID=3 no tiene allocations nuevas (sin datos)
    ])

    # ID=1: Sectores:=VACÍO para forzar Estado_3
    # ID=2: Sectores:=ASIGNADO (viene de Balanceado en antiguas → Utilities en nuevas → Estado_2)
    df_antiguas = pd.DataFrame([
        {'ID': 1, 'Nombre': 'Fondo Balanceado',  'sectores': 'Technology',
         'Technology': 100.0, 'Healthcare': 0.0, 'Financials': 0.0,
         'Pct_dominancia': 'Technology 100.00%', 'Sectores:': 'VACÍO'},
        {'ID': 2, 'Nombre': 'Fondo Concentrado', 'sectores': 'Balanceado',
         'Utilities': 60.0, 'Energy': 40.0,
         'Pct_dominancia': 'Utilities 60.00%', 'Sectores:': 'ASIGNADO'},
    ])

    df_final = crear_df_final_sector(df_instruments, df_nuevas, df_antiguas)
    return df_instruments, df_nuevas, df_antiguas, df_final


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_estructura_export_balanceados():
    """Verifica columnas fijas y presencia de columnas de sector (formato WIDE)."""
    print_section('TEST 1: Estructura export balanceados (sector)')

    df_instruments, df_nuevas, df_antiguas, df_final = _datos_sinteticos()
    export = generar_export_balanceados_sector(df_final, df_nuevas, df_instruments, df_antiguas)

    print(export.to_string(index=False))

    assert len(export) > 0, 'El export de balanceados no debe estar vacío'

    columnas_fijas = ['ID', 'Instrumento', 'Id_ti_valor', 'Id_ti',
                      'Fecha', 'Clasificacion', 'Industria Anterior', 'Estado', 'pct_original']
    faltantes = [c for c in columnas_fijas if c not in export.columns]
    assert not faltantes, f'Columnas fijas faltantes: {faltantes}'

    # Debe tener columnas de sector en formato WIDE
    cols_sector = [c for c in export.columns if c not in columnas_fijas]
    assert len(cols_sector) > 0, 'Deben existir columnas de sector (formato WIDE)'
    print(f'\n    [OK] {len(cols_sector)} columnas de sector en WIDE: {cols_sector}')

    # Clasificacion debe ser SubIndustria
    assert (export['Clasificacion'] == 'SubIndustria').all(), \
        "Clasificacion debe ser 'SubIndustria'"

    print('\n[OK] test_estructura_export_balanceados PASADO')
    return True


def test_logica_estado_export_balanceados():
    """Verifica que Estado en export balanceados sea Estado_1, Estado_2 o Estado_3."""
    print_section('TEST 2: Lógica Estado — export balanceados')

    df_instruments, df_nuevas, df_antiguas, df_final = _datos_sinteticos()
    export = generar_export_balanceados_sector(df_final, df_nuevas, df_instruments, df_antiguas)

    print(export[['ID', 'Instrumento', 'Estado', 'Fecha']].to_string(index=False))

    estados_validos = {'Estado_1', 'Estado_2', 'Estado_3'}
    estados_encontrados = set(export['Estado'].unique())
    invalidos = estados_encontrados - estados_validos
    assert not invalidos, f'Estados inválidos en export balanceados: {invalidos}'

    # ID=1 tiene Sectores:=VACÍO → debe ser Estado_3
    estado_id1 = export[export['ID'] == 1]['Estado'].iloc[0]
    assert estado_id1 == 'Estado_3', f'ID=1 esperado Estado_3, obtenido {estado_id1}'

    print(f'\n    [OK] Estados encontrados: {estados_encontrados}')
    print('\n[OK] test_logica_estado_export_balanceados PASADO')
    return True


def test_logica_fecha_export_balanceados():
    """
    Verifica la lógica de Fecha en export balanceados:
      - Sectores: en ESTADOS_FALTA_ALLOCATION → Fecha = '31-12-2019'
      - Otros → Fecha = primer día del mes actual
    """
    print_section('TEST 3: Lógica Fecha — export balanceados')

    df_instruments, df_nuevas, df_antiguas, df_final = _datos_sinteticos()
    export = generar_export_balanceados_sector(df_final, df_nuevas, df_instruments, df_antiguas)

    print(export[['ID', 'Instrumento', 'Fecha', 'Estado']].to_string(index=False))

    # ID=1 tiene Sectores:=VACÍO → fecha histórica
    fecha_id1 = export[export['ID'] == 1]['Fecha'].iloc[0]
    assert fecha_id1 == '31-12-2019', f'ID=1 esperado 31-12-2019, obtenido {fecha_id1}'

    # Formato de fecha válido para todas las filas (DD-MM-YYYY)
    for _, fila in export.iterrows():
        try:
            datetime.strptime(fila['Fecha'], '%d-%m-%Y')
        except ValueError:
            assert False, f'Fecha con formato inválido: {fila["Fecha"]}'

    print('\n    [OK] Fecha 31-12-2019 para VACÍO/FALTA ALLOCATION')
    print('    [OK] Formato DD-MM-YYYY para todas las fechas')
    print('\n[OK] test_logica_fecha_export_balanceados PASADO')
    return True


def test_estructura_export_no_balanceados():
    """Verifica columnas del export no balanceados y lógica de Estado."""
    print_section('TEST 4: Estructura export no balanceados (sector)')

    df_instruments, df_nuevas, df_antiguas, df_final = _datos_sinteticos()
    export = generar_export_no_balanceados_sector(df_final)

    print(export.to_string(index=False))

    assert len(export) > 0, 'El export de no balanceados no debe estar vacío'

    columnas_esperadas = ['ID', 'Instrumento', 'SubIndustria', 'Industria Anterior', 'Estado', 'Sobreescribir']
    assert list(export.columns) == columnas_esperadas, \
        f'Columnas esperadas: {columnas_esperadas}, obtenidas: {list(export.columns)}'

    # ID=2: Balanceado → Utilities → Estado_2
    estado_id2 = export[export['ID'] == 2]['Estado'].iloc[0]
    assert estado_id2 == 'Estado_2', f'ID=2 esperado Estado_2, obtenido {estado_id2}'

    # Sobreescribir solo puede ser Sí o No
    sobreescribir_invalido = set(export['Sobreescribir'].unique()) - {'Sí', 'No'}
    assert not sobreescribir_invalido, f'Valores inválidos en Sobreescribir: {sobreescribir_invalido}'

    print('\n    [OK] Columnas exactas')
    print(f'    [OK] Estado_2 para Balanceado → Utilities (ID=2)')
    print('\n[OK] test_estructura_export_no_balanceados PASADO')
    return True


def test_export_sin_datos():
    """Verifica que generar_export_sin_datos_sector detecte instrumentos sin cobertura."""
    print_section('TEST 5: Export sin datos (sector)')

    df_instruments, df_nuevas, df_antiguas, df_final = _datos_sinteticos()
    export = generar_export_sin_datos_sector(df_instruments, df_nuevas)

    print(export.to_string(index=False))

    # ID=3 no tiene allocations nuevas → debe aparecer en sin_datos
    assert 'ID' in export.columns, "Columna 'ID' faltante"
    assert 'Instrumento' in export.columns, "Columna 'Instrumento' faltante"
    assert 3 in export['ID'].values, 'ID=3 (sin datos) debe estar en el export sin_datos'

    # IDs con datos no deben aparecer
    ids_con_datos = {1, 2}
    ids_sin_datos = set(export['ID'].values)
    intersection = ids_con_datos & ids_sin_datos
    assert not intersection, f'IDs con datos encontrados en export sin_datos: {intersection}'

    print(f'\n    [OK] {len(export)} instrumento/s sin datos detectado/s correctamente')
    print('\n[OK] test_export_sin_datos PASADO')
    return True


def test_export_balanceados_pivote_sector():
    """Verifica que el pivote de clases en export balanceados sea correcto."""
    print_section('TEST 6: Pivote de sectores en export balanceados')

    df_instruments, df_nuevas, df_antiguas, df_final = _datos_sinteticos()
    export = generar_export_balanceados_sector(df_final, df_nuevas, df_instruments, df_antiguas)

    print(export.to_string(index=False))

    # Las columnas de sector (Technology, Healthcare, Financials) deben estar presentes
    sectores_esperados = {'Technology', 'Healthcare', 'Financials'}
    cols_sector = set(export.columns) - {'ID', 'Instrumento', 'Id_ti_valor', 'Id_ti',
                                          'Fecha', 'Clasificacion', 'Industria Anterior',
                                          'Estado', 'pct_original'}
    assert sectores_esperados.issubset(cols_sector), \
        f'Columnas de sector faltantes: {sectores_esperados - cols_sector}'

    # Valores de porcentaje del ID=1 deben ser correctos
    fila_id1 = export[export['ID'] == 1].iloc[0]
    assert abs(fila_id1['Technology'] - 40.0) < 0.01, f'Technology esperado 40.0, obtenido {fila_id1["Technology"]}'
    assert abs(fila_id1['Healthcare'] - 35.0) < 0.01, f'Healthcare esperado 35.0, obtenido {fila_id1["Healthcare"]}'
    assert abs(fila_id1['Financials'] - 25.0) < 0.01, f'Financials esperado 25.0, obtenido {fila_id1["Financials"]}'

    print('\n    [OK] Pivote de sectores correcto')
    print('\n[OK] test_export_balanceados_pivote_sector PASADO')
    return True


def main():
    ok1 = test_estructura_export_balanceados()
    ok2 = test_logica_estado_export_balanceados()
    ok3 = test_logica_fecha_export_balanceados()
    ok4 = test_estructura_export_no_balanceados()
    ok5 = test_export_sin_datos()
    ok6 = test_export_balanceados_pivote_sector()
    return all([ok1, ok2, ok3, ok4, ok5, ok6])


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
