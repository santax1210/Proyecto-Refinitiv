"""
Test de Generación de Exports — REGIÓN
==========================================
Valida la estructura y lógica de todos los exports del pipeline de región.

Diferencias clave vs moneda:
- Export balanceados: columna pivot = 'region' (no 'class')
  Clasificacion = 'SubRegion' (no 'SubMoneda')
  Fecha '31-12-2019' cuando Base Region: in ('FALTA ALLOCATION', 'SIN ASIGNAR')
  Columna 'Region Anterior' (no 'Moneda Anterior')
- Export no balanceados: columnas 'SubRegion' y 'Region Anterior' (no 'SubMoneda'/'Moneda Anterior')
- Estado_3 en balanceados: 'Base Region:' == 'FALTA ALLOCATION' O 'SIN ASIGNAR'
"""

import sys
import os
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.extractors.region.load_instruments_region import load_instruments_region
from src.extractors.region.load_allocations_region import (
    load_allocations_nuevas_region,
    load_allocations_antiguas_region,
)
from src.logic.region.crear_df_final_region import crear_df_final_region
from src.logic.region.generar_exports_region import (
    generar_export_balanceados_region,
    generar_export_no_balanceados_region,
    generar_export_sin_datos_region,
)


def _cargar_datos():
    """Carga todos los DataFrames necesarios para los tests de exports."""
    ROOT    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    raw_dir = os.path.join(ROOT, 'data', 'raw')

    df_instr    = load_instruments_region(
        os.path.join(raw_dir, 'posiciones.csv'),
        os.path.join(raw_dir, 'instruments.csv'),
    )
    df_nuevas   = load_allocations_nuevas_region(
        df_instr, os.path.join(raw_dir, 'region', 'allocations_nuevas_region.csv'), umbral=0.9
    )
    df_antiguas = load_allocations_antiguas_region(
        df_instr, os.path.join(raw_dir, 'region', 'allocations_region.csv')
    )
    df_final = crear_df_final_region(df_instr, df_nuevas, df_antiguas)
    return df_instr, df_nuevas, df_antiguas, df_final


def print_section(title):
    print("\n" + "="*70)
    print(f" {title} ".center(70, "="))
    print("="*70)


# ============================================================================
# TEST 1: Estructura Export Balanceados Región
# ============================================================================
def test_estructura_export_balanceados_region():
    print_section("TEST 1: Estructura Export Balanceados — REGIÓN")

    df_instr, df_nuevas, df_antiguas, df_final = _cargar_datos()
    exp = generar_export_balanceados_region(df_final, df_nuevas, df_instr, df_antiguas)

    cols_fijas = ['ID', 'Instrumento', 'Id_ti_valor', 'Id_ti', 'Fecha',
                  'Clasificacion', 'Region Anterior', 'Estado', 'pct_original']

    print("\n[Test 1.1] Verificando columnas fijas...")
    ok = True
    for col in cols_fijas:
        if col in exp.columns:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col} — FALTA")
            ok = False

    print("\n[Test 1.2] Verificando columnas de regiones (WIDE)...")
    cols_regiones = [c for c in exp.columns if c not in cols_fijas]
    if cols_regiones:
        print(f"  ✓ {len(cols_regiones)} columnas de región: {', '.join(cols_regiones[:5])}...")
    else:
        print(f"  ⚠  No se encontraron columnas de región (puede ser válido si todos son Estado_3)")

    print(f"\n[Test 1.3] Registros: {len(exp)}")

    if ok:
        print("\n✅ TEST 1 PASADO")
    else:
        print("\n❌ TEST 1 FALLADO")
    return ok


# ============================================================================
# TEST 2: Lógica Estado — Export Balanceados Región
# ============================================================================
def test_logica_estado_balanceados_region():
    print_section("TEST 2: Lógica Estado — Export Balanceados REGIÓN")

    df_instr, df_nuevas, df_antiguas, df_final = _cargar_datos()
    exp = generar_export_balanceados_region(df_final, df_nuevas, df_instr, df_antiguas)

    if len(exp) == 0:
        print("  ⚠  No hay registros balanceados para validar.")
        return True

    print("\n[Test 2.1] Distribución de Estado:")
    estados = exp['Estado'].value_counts()
    for estado, cnt in estados.items():
        print(f"  {estado}: {cnt} registros")

    print("\n[Test 2.2] Solo valores válidos (Estado_1, Estado_2, Estado_3)...")
    validos = {'Estado_1', 'Estado_2', 'Estado_3'}
    encontrados = set(exp['Estado'].unique())
    invalidos = encontrados - validos

    if invalidos:
        print(f"  ✗ Estados inválidos: {invalidos}")
        return False
    else:
        print(f"  ✓ Solo estados válidos: {encontrados}")

    print("\n✅ TEST 2 PASADO")
    return True


# ============================================================================
# TEST 3: Lógica Fecha y Clasificacion — Export Balanceados Región
# ============================================================================
def test_logica_fecha_clasificacion_region():
    print_section("TEST 3: Lógica Fecha y Clasificacion — REGIÓN")

    df_instr, df_nuevas, df_antiguas, df_final = _cargar_datos()
    exp = generar_export_balanceados_region(df_final, df_nuevas, df_instr, df_antiguas)

    if len(exp) == 0:
        print("  ⚠  Sin registros para validar.")
        return True

    # Clasificacion debe ser 'SubRegion'
    print("\n[Test 3.1] Verificando Clasificacion = 'SubRegion'...")
    vals_clasif = exp['Clasificacion'].unique()
    if list(vals_clasif) == ['SubRegion']:
        print(f"  ✓ Clasificacion = 'SubRegion' en todos los registros")
    else:
        print(f"  ✗ Valores de Clasificacion: {vals_clasif} (esperado: ['SubRegion'])")
        return False

    # Fecha
    primer_dia = datetime.now().replace(day=1).strftime('%d-%m-%Y')
    fechas_validas = {'31-12-2019', primer_dia}

    print(f"\n[Test 3.2] Verificando Fecha (esperado: '31-12-2019' o '{primer_dia}')...")
    fechas = exp['Fecha'].value_counts()
    for fecha, cnt in fechas.items():
        print(f"  {fecha}: {cnt} registros")

    invalidas = set(exp['Fecha'].unique()) - fechas_validas
    if invalidas:
        print(f"  ✗ Fechas inválidas: {invalidas}")
        return False
    else:
        print(f"  ✓ Solo fechas válidas encontradas")

    # Estado_3 debe tener Fecha = '31-12-2019'
    if 'Estado_3' in exp['Estado'].values:
        df_est3 = exp[exp['Estado'] == 'Estado_3']
        fechas_est3 = df_est3['Fecha'].unique()
        print(f"\n[Test 3.3] Estado_3 → Fecha debe ser '31-12-2019': {fechas_est3}")
        if all(f == '31-12-2019' for f in fechas_est3):
            print(f"  ✓ Correcto")
        else:
            print(f"  ✗ Estado_3 tiene fechas incorrectas: {fechas_est3}")
            return False

    print("\n✅ TEST 3 PASADO")
    return True


# ============================================================================
# TEST 4: Estructura Export No Balanceados Región
# ============================================================================
def test_estructura_export_no_balanceados_region():
    print_section("TEST 4: Estructura Export No Balanceados — REGIÓN")

    df_instr, df_nuevas, df_antiguas, df_final = _cargar_datos()
    exp = generar_export_no_balanceados_region(df_final)

    # Columnas esperadas — región usa SubRegion y Region Anterior
    cols_esperadas = ['ID', 'Instrumento', 'SubRegion', 'Region Anterior', 'Estado', 'Sobreescribir']

    print("\n[Test 4.1] Verificando columnas...")
    ok = True
    for col in cols_esperadas:
        if col in exp.columns:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col} — FALTA")
            ok = False

    print("\n[Test 4.2] Verificando que NO existan columnas de moneda ('SubMoneda', 'Moneda Anterior')...")
    cols_moneda_restantes = [c for c in exp.columns if c in ('SubMoneda', 'Moneda Anterior')]
    if cols_moneda_restantes:
        print(f"  ✗ Columnas de moneda encontradas: {cols_moneda_restantes}")
        ok = False
    else:
        print(f"  ✓ No hay columnas de moneda (correcto para región)")

    print(f"\n[Test 4.3] Registros: {len(exp)}")
    if len(exp) > 0:
        print(exp.head(3).to_string(index=False))

    if ok:
        print("\n✅ TEST 4 PASADO")
    else:
        print("\n❌ TEST 4 FALLADO")
    return ok


# ============================================================================
# TEST 5: Lógica Estado — Export No Balanceados Región
# ============================================================================
def test_logica_estado_no_balanceados_region():
    print_section("TEST 5: Lógica Estado — No Balanceados REGIÓN")

    df_instr, df_nuevas, df_antiguas, df_final = _cargar_datos()
    exp = generar_export_no_balanceados_region(df_final)

    if len(exp) == 0:
        print("  ⚠  Sin registros para validar.")
        return True

    print("\n[Test 5.1] Distribución de Estado:")
    for estado, cnt in exp['Estado'].value_counts().items():
        print(f"  {estado}: {cnt}")

    validos = {'Estado_1', 'Estado_2', 'Estado_3'}
    invalidos = set(exp['Estado'].unique()) - validos
    if invalidos:
        print(f"  ✗ Estados inválidos: {invalidos}")
        return False
    else:
        print(f"  ✓ Solo estados válidos")

    print("\n[Test 5.2] Distribución de Sobreescribir:")
    for val, cnt in exp['Sobreescribir'].value_counts().items():
        print(f"  {val}: {cnt}")

    validos_sob = {'Sí', 'No'}
    invalidos_sob = set(exp['Sobreescribir'].unique()) - validos_sob
    if invalidos_sob:
        print(f"  ✗ Valores inválidos en Sobreescribir: {invalidos_sob}")
        return False
    else:
        print(f"  ✓ Sobreescribir = 'Sí'/'No' únicamente")

    print("\n✅ TEST 5 PASADO")
    return True


# ============================================================================
# TEST 6: Export Sin Datos Región
# ============================================================================
def test_export_sin_datos_region():
    print_section("TEST 6: Export Sin Datos — REGIÓN")

    df_instr, df_nuevas, df_antiguas, df_final = _cargar_datos()
    exp = generar_export_sin_datos_region(df_instr, df_nuevas)

    cols_esperadas = ['ID', 'Instrumento']
    ok = True

    print("\n[Test 6.1] Verificando columnas...")
    for col in cols_esperadas:
        if col in exp.columns:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col} — FALTA")
            ok = False

    print(f"\n[Test 6.2] Registros sin datos: {len(exp)}")

    ids_instr = set(df_instr['ID'].unique())
    ids_exp   = set(exp['ID'].unique())
    orphans   = ids_exp - ids_instr
    if orphans:
        print(f"  ✗ {len(orphans)} IDs no existen en df_instruments")
        ok = False
    else:
        print(f"  ✓ Todos los IDs existen en df_instruments")

    if ok:
        print("\n✅ TEST 6 PASADO")
    else:
        print("\n❌ TEST 6 FALLADO")
    return ok


# ============================================================================
# RUNNER
# ============================================================================
def run_all():
    print("\n" + "="*70)
    print(" TESTS DE EXPORTS — REGIÓN ".center(70, "="))
    print("="*70)

    resultados = {
        "Test 1 — Estructura balanceados":         test_estructura_export_balanceados_region(),
        "Test 2 — Estado balanceados":             test_logica_estado_balanceados_region(),
        "Test 3 — Fecha y Clasificacion":          test_logica_fecha_clasificacion_region(),
        "Test 4 — Estructura no balanceados":      test_estructura_export_no_balanceados_region(),
        "Test 5 — Estado no balanceados":          test_logica_estado_no_balanceados_region(),
        "Test 6 — Sin datos":                      test_export_sin_datos_region(),
    }

    print("\n" + "="*70)
    print(" RESUMEN ".center(70, "="))
    print("="*70)
    pasados  = sum(1 for v in resultados.values() if v)
    fallados = len(resultados) - pasados

    for nombre, resultado in resultados.items():
        icono = "✅" if resultado else "❌"
        print(f"  {icono} {nombre}")

    print(f"\n  Total: {pasados}/{len(resultados)} pasados, {fallados} fallados")
    return fallados == 0


if __name__ == "__main__":
    exito = run_all()
    sys.exit(0 if exito else 1)
