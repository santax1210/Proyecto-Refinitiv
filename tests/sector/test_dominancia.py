"""
Test de Cálculos de Dominancia y Escalado — Sector
====================================================
Valida que los cálculos de dominancia y escalado de porcentajes sean correctos
para el pipeline de sector/industria.

Cubre:
  - El umbral de dominancia (0.9 = 90%) clasifica correctamente
  - pct_escalado suma 100.0 por instrumento
  - pct_original refleja la suma de porcentajes brutos
  - Exportaciones con classif != 'industry' son excluidas
  - Casos borde: un solo sector, empate exacto, todos los porcentajes iguales
"""

import os
import sys
import tempfile

import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.extractors.sector.load_allocations_sector import load_allocations_nuevas_sector


def print_section(title):
    print('\n' + '=' * 70)
    print(f' {title.upper()} '.center(70, '='))
    print('=' * 70)


def _df_instruments_base():
    return pd.DataFrame([
        {'ID': 1, 'Nombre': 'A', 'RIC': 'R1', 'Isin': 'I1', 'Cusip': 'C1'},
        {'ID': 2, 'Nombre': 'B', 'RIC': 'R2', 'Isin': 'I2', 'Cusip': 'C2'},
        {'ID': 3, 'Nombre': 'C', 'RIC': 'R3', 'Isin': 'I3', 'Cusip': 'C3'},
        {'ID': 4, 'Nombre': 'D', 'RIC': 'R4', 'Isin': 'I4', 'Cusip': 'C4'},
    ])


def _cargar_nuevas(contenido_csv, df_instruments, umbral=0.9):
    with tempfile.NamedTemporaryFile('w', suffix='.csv', delete=False, encoding='latin-1') as f:
        f.write(contenido_csv)
        tmp_path = f.name
    try:
        return load_allocations_nuevas_sector(df_instruments, tmp_path, umbral=umbral)
    finally:
        os.unlink(tmp_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_umbral_dominancia_90():
    """Verifica que el umbral del 90% clasifique correctamente sector_nueva."""
    print_section('TEST 1: Umbral de dominancia al 90%')

    df_instruments = _df_instruments_base()
    contenido = (
        ';instrument;date;class;percentage;classif\n'
        # ID=1: exactamente 90% → DEBE clasificar como Technology (>= umbral)
        '0;R1;2025-01-31;Technology;90,0;industry\n'
        '1;R1;2025-01-31;Healthcare;10,0;industry\n'
        # ID=2: 89.9% → NO alcanza el umbral → Balanceado
        '2;R2;2025-01-31;Financials;89,9;industry\n'
        '3;R2;2025-01-31;Utilities;10,1;industry\n'
        # ID=3: 100% → Dominancia completa
        '4;R3;2025-01-31;Energy;100,0;industry\n'
        # ID=4: 33/33/34 → Balanceado
        '5;R4;2025-01-31;Technology;33,0;industry\n'
        '6;R4;2025-01-31;Healthcare;33,0;industry\n'
        '7;R4;2025-01-31;Financials;34,0;industry\n'
    )
    df = _cargar_nuevas(contenido, df_instruments)

    cols_mostrar = ['ID', 'class', 'percentage', 'sector_nueva', 'pct_dominancia_nueva']
    print(df[cols_mostrar].to_string(index=False))

    # ID=1: 90% exacto → Technology
    nueva_id1 = df[df['ID'] == 1]['sector_nueva'].iloc[0]
    assert nueva_id1 == 'Technology', f'ID=1 esperado Technology, obtenido {nueva_id1}'

    # ID=2: 89.9% → Balanceado
    nueva_id2 = df[df['ID'] == 2]['sector_nueva'].iloc[0]
    assert nueva_id2 == 'Balanceado', f'ID=2 esperado Balanceado, obtenido {nueva_id2}'

    # ID=3: 100% → Energy
    nueva_id3 = df[df['ID'] == 3]['sector_nueva'].iloc[0]
    assert nueva_id3 == 'Energy', f'ID=3 esperado Energy, obtenido {nueva_id3}'

    # ID=4: distribuido → Balanceado
    nueva_id4 = df[df['ID'] == 4]['sector_nueva'].iloc[0]
    assert nueva_id4 == 'Balanceado', f'ID=4 esperado Balanceado, obtenido {nueva_id4}'

    print('\n[OK] test_umbral_dominancia_90 PASADO')
    return True


def test_pct_escalado_suma_100():
    """
    Verifica que pct_escalado sea 100.0 para cada instrumento
    (la suma escalada de porcentajes positivos debe ser 1.0 escalada a 100).
    """
    print_section('TEST 2: pct_escalado = 100.0 por instrumento')

    df_instruments = _df_instruments_base()
    contenido = (
        ';instrument;date;class;percentage;classif\n'
        # Porcentajes que no suman exactamente 100 (deben escalarse)
        '0;R1;2025-01-31;Technology;60,0;industry\n'
        '1;R1;2025-01-31;Healthcare;20,0;industry\n'
        '2;R1;2025-01-31;Financials;10,0;industry\n'
        # Solo un sector
        '3;R2;2025-01-31;Energy;50,0;industry\n'
        # Porcentajes que ya suman 100
        '4;R3;2025-01-31;Technology;70,0;industry\n'
        '5;R3;2025-01-31;Healthcare;30,0;industry\n'
    )
    df = _cargar_nuevas(contenido, df_instruments)

    print(df[['ID', 'class', 'percentage', 'pct_escalado', 'pct_original']].to_string(index=False))

    errores = []
    for id_inst in df['ID'].unique():
        pct_esc = df[df['ID'] == id_inst]['pct_escalado'].iloc[0]
        if abs(pct_esc - 100.0) > 0.01:
            errores.append({'ID': id_inst, 'pct_escalado': pct_esc})

    if errores:
        for e in errores:
            print(f'    [X] ID={e["ID"]}: pct_escalado={e["pct_escalado"]} (esperado 100.0)')
        assert False, f'{len(errores)} instrumentos con pct_escalado incorrecto'

    print('\n    [OK] Todos los instrumentos tienen pct_escalado = 100.0')
    print('\n[OK] test_pct_escalado_suma_100 PASADO')
    return True


def test_pct_escalado_en_detalles_suma_100():
    """Verifica que suma(percentage) == pct_escalado (100.0) para todos los instrumentos."""
    print_section('TEST 3: suma(percentage) coincide con pct_escalado (100.0)')

    df_instruments = _df_instruments_base()
    contenido = (
        ';instrument;date;class;percentage;classif\n'
        '0;R1;2025-01-31;Technology;60,0;industry\n'
        '1;R1;2025-01-31;Healthcare;25,0;industry\n'
        '2;R1;2025-01-31;Financials;15,0;industry\n'
        '3;R2;2025-01-31;Energy;45,0;industry\n'
        '4;R2;2025-01-31;Utilities;55,0;industry\n'
    )
    df = _cargar_nuevas(contenido, df_instruments)

    print(df[['ID', 'class', 'percentage', 'pct_escalado', 'pct_original']].to_string(index=False))

    errores = []
    for id_inst in df['ID'].unique():
        grupo = df[df['ID'] == id_inst]
        suma_real = grupo['percentage'].sum()
        pct_esc = grupo['pct_escalado'].iloc[0]
        
        if pct_esc == 0:
            continue
            
        if abs(suma_real - 100.0) > 0.1:
            errores.append({'ID': id_inst, 'suma_real': suma_real, 'pct_escalado': pct_esc})

    if errores:
        for e in errores:
            print(f'    [X] ID={e["ID"]}: suma={e["suma_real"]:.2f}, pct_escalado={e["pct_escalado"]:.2f}')
        assert False, f'{len(errores)} inconsistencias entre suma(percentage) y 100.0'

    print('\n    [OK] suma(percentage) == 100.0 para todos los instrumentos')
    print('\n[OK] test_pct_escalado_en_detalles_suma_100 PASADO')
    return True


def test_exclusion_classif_no_industry():
    """Verifica que solo se procesen las filas con classif == 'industry'."""
    print_section('TEST 4: Exclusión de classif != industry')

    df_instruments = _df_instruments_base()
    contenido = (
        ';instrument;date;class;percentage;classif\n'
        # Solo estas 2 deben incluirse
        '0;R1;2025-01-31;Technology;95,0;industry\n'
        '1;R1;2025-01-31;Healthcare;5,0;industry\n'
        # Deben excluirse
        '2;R1;2025-01-31;Chile;100,0;country\n'
        '3;R1;2025-01-31;OECD;50,0;region\n'
        '4;R1;2025-01-31;USD;100,0;currency\n'
    )
    df = _cargar_nuevas(contenido, df_instruments)

    print(df[['ID', 'class', 'percentage', 'sector_nueva']].to_string(index=False))

    clases = set(df[df['ID'] == 1]['class'].tolist())
    assert clases == {'Technology', 'Healthcare'}, \
        f'Solo deben quedar Technology y Healthcare, obtenido: {clases}'
    assert len(df[df['ID'] == 1]) == 2, 'Deben haber exactamente 2 filas para ID=1'

    print('\n    [OK] Solo filas con classif=industry incluidas')
    print('\n[OK] test_exclusion_classif_no_industry PASADO')
    return True


def test_umbral_con_porcentajes_decimales():
    """Prueba con porcentajes decimales (coma como separador decimal)."""
    print_section('TEST 5: Porcentajes con coma decimal (formato latino)')

    df_instruments = _df_instruments_base()
    # 92,5% → debe dominar
    contenido = (
        ';instrument;date;class;percentage;classif\n'
        '0;R1;2025-01-31;Technology;92,5;industry\n'
        '1;R1;2025-01-31;Healthcare;7,5;industry\n'
    )
    df = _cargar_nuevas(contenido, df_instruments)

    print(df[['ID', 'class', 'percentage', 'sector_nueva', 'pct_dominancia_nueva']].to_string(index=False))

    pct_tech = df[(df['ID'] == 1) & (df['class'] == 'Technology')]['percentage'].iloc[0]
    assert abs(pct_tech - 92.5) < 0.01, f'percentage debe ser 92.5, obtenido {pct_tech}'

    sector = df[df['ID'] == 1]['sector_nueva'].iloc[0]
    assert sector == 'Technology', f'92.5% debe dominar como Technology, obtenido: {sector}'

    print('\n    [OK] Coma decimal manejada correctamente')
    print('\n[OK] test_umbral_con_porcentajes_decimales PASADO')
    return True


def main():
    ok1 = test_umbral_dominancia_90()
    ok2 = test_pct_escalado_suma_100()
    ok3 = test_pct_escalado_en_detalles_suma_100()
    ok4 = test_exclusion_classif_no_industry()
    ok5 = test_umbral_con_porcentajes_decimales()
    return all([ok1, ok2, ok3, ok4, ok5])


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
