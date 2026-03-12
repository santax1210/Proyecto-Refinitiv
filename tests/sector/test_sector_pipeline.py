"""
Tests sintéticos del pipeline de SECTOR / INDUSTRIA.

No dependen de archivos raw del repo. Validan la lógica específica agregada para:
- filtro classif == 'industry'
- Estado_3 en balanceados con 'Sectores:' = 'FALTA ALLOCATION' o 'VACÍO'
- exports de balanceados y no balanceados
"""

import os
import sys
import tempfile

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.extractors.sector.load_allocations_sector import load_allocations_nuevas_sector
from src.logic.sector.crear_df_final_sector import crear_df_final_sector
from src.logic.sector.generar_exports_sector import (
    generar_export_balanceados_sector,
    generar_export_no_balanceados_sector,
)


def _print_section(title):
    print('\n' + '=' * 80)
    print(f' {title} '.center(80, '='))
    print('=' * 80)


def test_filtro_industry_en_allocations_nuevas_sector():
    _print_section('TEST 1: Filtro classif == industry')

    df_instruments = pd.DataFrame([
        {'ID': 1, 'Nombre': 'Instrumento A', 'RIC': 'RIC_A', 'Isin': 'ISIN_A', 'Cusip': 'CUSIP_A'},
    ])

    contenido = (
        ';instrument;date;class;percentage;Columna Fuente;classif\n'
        '0;RIC_A;2025-01-31;Technology;60,0;IndustryAllocation;industry\n'
        '1;RIC_A;2025-01-31;Healthcare;40,0;IndustryAllocation;industry\n'
        '2;RIC_A;2025-01-31;Chile;100,0;CountryAllocation;country\n'
    )

    with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, encoding='latin-1') as tmp:
        tmp.write(contenido)
        tmp_path = tmp.name

    try:
        df = load_allocations_nuevas_sector(df_instruments, tmp_path, umbral=0.9)
    finally:
        os.unlink(tmp_path)

    print(df[['ID', 'class', 'percentage', 'sector_nueva', 'pct_dominancia_nueva']].to_string(index=False))

    assert len(df) == 2, 'Deben quedar solo las filas de industry'
    assert set(df['class'].tolist()) == {'Technology', 'Healthcare'}
    assert df['sector_nueva'].iloc[0] == 'Balanceado', '60/40 no debe superar el umbral 0.9'
    print('\n[OK] Filtro industry validado correctamente')
    return True


def _build_datos_sinteticos():
    df_instruments = pd.DataFrame([
        {'ID': 1, 'Nombre': 'Fondo Balanceado', 'Tipo instrumento': 'C03', 'sectores': 'Technology'},
        {'ID': 2, 'Nombre': 'Fondo Concentrado', 'Tipo instrumento': 'C03', 'sectores': 'Balanceado'},
    ])

    df_nuevas = pd.DataFrame([
        {'ID': 1, 'Nombre': 'Fondo Balanceado', 'instrument': 'RIC1', 'class': 'Technology', 'percentage': 40.0, 'tipo_id': 'RIC', 'sector_nueva': 'Balanceado', 'pct_dominancia_nueva': 'Technology 40.00%', 'pct_escalado': 100.0, 'pct_original': 100.0},
        {'ID': 1, 'Nombre': 'Fondo Balanceado', 'instrument': 'RIC1', 'class': 'Healthcare', 'percentage': 30.0, 'tipo_id': 'RIC', 'sector_nueva': 'Balanceado', 'pct_dominancia_nueva': 'Technology 40.00%', 'pct_escalado': 100.0, 'pct_original': 100.0},
        {'ID': 1, 'Nombre': 'Fondo Balanceado', 'instrument': 'RIC1', 'class': 'Financials', 'percentage': 30.0, 'tipo_id': 'RIC', 'sector_nueva': 'Balanceado', 'pct_dominancia_nueva': 'Technology 40.00%', 'pct_escalado': 100.0, 'pct_original': 100.0},
        {'ID': 2, 'Nombre': 'Fondo Concentrado', 'instrument': 'RIC2', 'class': 'Utilities', 'percentage': 95.0, 'tipo_id': 'RIC', 'sector_nueva': 'Utilities', 'pct_dominancia_nueva': 'Utilities 95.00%', 'pct_escalado': 100.0, 'pct_original': 100.0},
        {'ID': 2, 'Nombre': 'Fondo Concentrado', 'instrument': 'RIC2', 'class': 'Energy', 'percentage': 5.0, 'tipo_id': 'RIC', 'sector_nueva': 'Utilities', 'pct_dominancia_nueva': 'Utilities 95.00%', 'pct_escalado': 100.0, 'pct_original': 100.0},
    ])

    df_antiguas = pd.DataFrame([
        {'ID': 1, 'Nombre': 'Fondo Balanceado', 'sectores': 'Technology', 'Technology': 100.0, 'Healthcare': 0.0, 'Financials': 0.0, 'Pct_dominancia': 'Technology 100.00%', 'Sectores:': 'VACÍO'},
        {'ID': 2, 'Nombre': 'Fondo Concentrado', 'sectores': 'Balanceado', 'Utilities': 60.0, 'Energy': 40.0, 'Pct_dominancia': 'Utilities 60.00%', 'Sectores:': 'ASIGNADO'},
    ])

    return df_instruments, df_nuevas, df_antiguas


def test_estado_y_exports_sector():
    _print_section('TEST 2: Estados especiales y exports sector')

    df_instruments, df_nuevas, df_antiguas = _build_datos_sinteticos()
    df_final = crear_df_final_sector(df_instruments, df_nuevas, df_antiguas)

    print(df_final[['ID', 'sector_antigua', 'sector_nueva', 'Cambio', 'Estado']].to_string(index=False))

    estado_id1 = df_final.loc[df_final['ID'] == 1, 'Estado'].iloc[0]
    estado_id2 = df_final.loc[df_final['ID'] == 2, 'Estado'].iloc[0]

    assert estado_id1 == 'Estado_3', 'VACÍO en Sectores: debe forzar Estado_3 para balanceados'
    assert estado_id2 == 'Estado_2', 'Balanceado -> Industria debe ser Estado_2'

    export_bal = generar_export_balanceados_sector(df_final, df_nuevas, df_instruments, df_antiguas)
    export_no_bal = generar_export_no_balanceados_sector(df_final)

    print('\nExport balanceados:')
    print(export_bal.to_string(index=False))
    print('\nExport no balanceados:')
    print(export_no_bal.to_string(index=False))

    assert len(export_bal) == 1
    assert export_bal['Estado'].iloc[0] == 'Estado_3'
    assert export_bal['Fecha'].iloc[0] == '31-12-2019'
    assert export_bal['Clasificacion'].iloc[0] == 'SubIndustria'

    assert len(export_no_bal) == 1
    assert list(export_no_bal.columns) == ['ID', 'Instrumento', 'SubIndustria', 'Industria Anterior', 'Estado', 'Sobreescribir']
    assert export_no_bal['Estado'].iloc[0] == 'Estado_2'
    print('\n[OK] Estados y exports de sector validados correctamente')
    return True


def test_estado3_variantes_sectores_col():
    """Verifica que VACÃO, FALTA ALLOCATIONS y variantes fuerzan Estado_3."""
    _print_section('TEST 3: Estado_3 con variantes de la columna Sectores:')

    variantes_estado3 = ['FALTA ALLOCATION', 'FALTA ALLOCATIONS', 'VACÃO', 'VACÍO', 'VACIO', 'vacão', 'vacío']
    variantes_ok = ['ASIGNADO', 'Technology', '']

    from src.logic.sector.crear_df_final_sector import (
        normalizar_estado_sector, ESTADOS_FALTA_ALLOCATION, calcular_estado_sector
    )
    import pandas as pd

    print('Variantes que DEBEN disparar Estado_3:')
    for v in variantes_estado3:
        norm = normalizar_estado_sector(v)
        en_set = norm in ESTADOS_FALTA_ALLOCATION
        print(f'  {repr(v):25} -> {repr(norm):25} -> Estado_3: {en_set}')
        assert en_set, f'Se esperaba Estado_3 para Sectores:={repr(v)}'

    print('\nVariantes que NO deben disparar Estado_3:')
    for v in variantes_ok:
        norm = normalizar_estado_sector(v)
        en_set = norm in ESTADOS_FALTA_ALLOCATION
        print(f'  {repr(v):25} -> {repr(norm):25} -> Estado_3: {en_set}')
        assert not en_set, f'NO se esperaba Estado_3 para Sectores:={repr(v)}'

    # Verifica a través de calcular_estado_sector con un row sintético
    row_falta = pd.Series({'sector_nueva': 'Balanceado', 'sector_antigua': 'Technology', 'Cambio': 'Sí', 'Sectores:': 'VACÃO'})
    estado = calcular_estado_sector(row_falta)
    assert estado == 'Estado_3', f'Esperado Estado_3, obtenido {estado}'

    row_falta2 = pd.Series({'sector_nueva': 'Balanceado', 'sector_antigua': 'Technology', 'Cambio': 'Sí', 'Sectores:': 'FALTA ALLOCATIONS'})
    estado2 = calcular_estado_sector(row_falta2)
    assert estado2 == 'Estado_3', f'Esperado Estado_3, obtenido {estado2}'

    print('\n[OK] Todas las variantes de Estado_3 validadas correctamente')
    return True


def main():
    ok1 = test_filtro_industry_en_allocations_nuevas_sector()
    ok2 = test_estado_y_exports_sector()
    ok3 = test_estado3_variantes_sectores_col()
    return ok1 and ok2 and ok3


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
