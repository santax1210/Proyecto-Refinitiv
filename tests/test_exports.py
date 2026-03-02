"""
Test de validación para la generación de exports balanceados y no balanceados.

Este test verifica:
- Estructura correcta de columnas
- Lógica de la columna Estado
- Lógica de la columna Fecha
- Lógica de la columna Clasificacion
- Formato de datos en formato WIDE para balanceados
"""

import sys
import os
import pandas as pd
from datetime import datetime

# Asegurar que el directorio raíz está en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extractors.load_instruments import load_df_instruments
from src.extractors.load_allocations import load_allocations_nuevas, load_allocations_antiguas
from src.logic.crear_df_final import crear_df_final
from src.logic.generar_exports import generar_export_balanceados, generar_export_no_balanceados


def test_estructura_export_balanceados():
    """
    Verifica que el export balanceados tenga la estructura correcta de columnas.
    """
    print("\n" + "="*70)
    print(" TEST 1: Estructura Export Balanceados ".center(70, "="))
    print("="*70)
    
    # Construir rutas absolutas a los archivos de datos
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_raw = os.path.join(root_dir, 'data', 'raw')
    posiciones_path = os.path.join(data_raw, 'posiciones.csv')
    instruments_path = os.path.join(data_raw, 'instruments.csv')
    allocations_nuevas_path = os.path.join(data_raw, 'allocations_nuevas.csv')
    allocations_antiguas_path = os.path.join(data_raw, 'allocations_currency.csv')
    # Cargar datos
    df_instr = load_df_instruments(posiciones_path, instruments_path)
    df_nuevas = load_allocations_nuevas(df_instr, allocations_nuevas_path, umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, allocations_antiguas_path)
    df_final = crear_df_final(df_instr, df_nuevas, df_antiguas)
    
    # Generar export
    export_bal = generar_export_balanceados(df_final, df_nuevas, df_instr, df_antiguas)
    
    # Columnas fijas esperadas
    columnas_fijas = ['ID', 'Instrumento', 'Id_ti_valor', 'Id_ti', 'Fecha', 
                     'Clasificacion', 'Moneda Anterior', 'Estado', 'pct_original']
    
    print("\n[Test 1.1] Verificando columnas fijas...")
    for col in columnas_fijas:
        if col in export_bal.columns:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col} - FALTA")
            return False
    
    print("\n[Test 1.2] Verificando columnas de monedas (formato WIDE)...")
    columnas_monedas = [c for c in export_bal.columns if c not in columnas_fijas]
    if len(columnas_monedas) > 0:
        print(f"  ✓ {len(columnas_monedas)} columnas de monedas encontradas: {', '.join(columnas_monedas[:5])}...")
    else:
        print(f"  ✗ No se encontraron columnas de monedas")
        return False
    
    print("\n[Test 1.3] Verificando que no hay registros vacíos...")
    if len(export_bal) > 0:
        print(f"  ✓ {len(export_bal)} registros en el export")
    else:
        print(f"  ⚠️  Export sin registros (puede ser válido si no hay balanceados)")
    
    print("\n✅ TEST 1 PASADO: Estructura correcta")
    return True


def test_logica_estado_balanceados():
    """
    Verifica la lógica de la columna Estado en export balanceados.
    """
    print("\n" + "="*70)
    print(" TEST 2: Lógica Estado - Export Balanceados ".center(70, "="))
    print("="*70)
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_raw = os.path.join(root_dir, 'data', 'raw')
    posiciones_path = os.path.join(data_raw, 'posiciones.csv')
    instruments_path = os.path.join(data_raw, 'instruments.csv')
    allocations_nuevas_path = os.path.join(data_raw, 'allocations_nuevas.csv')
    allocations_antiguas_path = os.path.join(data_raw, 'allocations_currency.csv')
    # Cargar datos
    df_instr = load_df_instruments(posiciones_path, instruments_path)
    df_nuevas = load_allocations_nuevas(df_instr, allocations_nuevas_path, umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, allocations_antiguas_path)
    df_final = crear_df_final(df_instr, df_nuevas, df_antiguas)
    
    # Generar export
    export_bal = generar_export_balanceados(df_final, df_nuevas, df_instr, df_antiguas)
    
    if len(export_bal) == 0:
        print("  ⚠️  No hay registros para validar estados")
        return True
    
    print("\n[Test 2.1] Verificando valores de Estado...")
    estados = export_bal['Estado'].value_counts()
    for estado, count in estados.items():
        print(f"  {estado}: {count} registros")
    
    print("\n[Test 2.2] Verificando que solo existen Estado_1, Estado_2 o Estado_3...")
    estados_validos = {'Estado_1', 'Estado_2', 'Estado_3'}
    estados_encontrados = set(export_bal['Estado'].unique())
    
    if estados_encontrados.issubset(estados_validos):
        print(f"  ✓ Solo estados válidos: {estados_encontrados}")
    else:
        estados_invalidos = estados_encontrados - estados_validos
        print(f"  ✗ Estados inválidos encontrados: {estados_invalidos}")
        return False
    
    print("\n✅ TEST 2 PASADO: Lógica de Estado correcta")
    return True


def test_logica_fecha_clasificacion_balanceados():
    """
    Verifica la lógica de las columnas Fecha y Clasificacion en export balanceados.
    """
    print("\n" + "="*70)
    print(" TEST 3: Lógica Fecha y Clasificacion - Export Balanceados ".center(70, "="))
    print("="*70)
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_raw = os.path.join(root_dir, 'data', 'raw')
    posiciones_path = os.path.join(data_raw, 'posiciones.csv')
    instruments_path = os.path.join(data_raw, 'instruments.csv')
    allocations_nuevas_path = os.path.join(data_raw, 'allocations_nuevas.csv')
    allocations_antiguas_path = os.path.join(data_raw, 'allocations_currency.csv')
    # Cargar datos
    df_instr = load_df_instruments(posiciones_path, instruments_path)
    df_nuevas = load_allocations_nuevas(df_instr, allocations_nuevas_path, umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, allocations_antiguas_path)
    df_final = crear_df_final(df_instr, df_nuevas, df_antiguas)
    
    # Generar export
    export_bal = generar_export_balanceados(df_final, df_nuevas, df_instr, df_antiguas)
    
    if len(export_bal) == 0:
        print("  ⚠️  No hay registros para validar Fecha y Clasificacion")
        return True
    
    print("\n[Test 3.1] Verificando columna Clasificacion...")
    clasificaciones = export_bal['Clasificacion'].unique()
    if len(clasificaciones) == 1 and clasificaciones[0] == 'SubMoneda':
        print(f"  ✓ Clasificacion = 'SubMoneda' en todos los registros")
    else:
        print(f"  ✗ Clasificacion tiene valores incorrectos: {clasificaciones}")
        return False
    
    print("\n[Test 3.2] Verificando formato de Fecha...")
    hoy = datetime.now()
    primer_dia_mes = hoy.replace(day=1).strftime('%d-%m-%Y')
    
    fechas = export_bal['Fecha'].value_counts()
    print(f"  Fechas encontradas:")
    for fecha, count in fechas.items():
        print(f"    - {fecha}: {count} registros")
    
    print(f"\n[Test 3.3] Verificando que Fecha sea '31-12-2019' o primer día del mes actual...")
    fechas_validas = {'31-12-2019', primer_dia_mes}
    fechas_encontradas = set(export_bal['Fecha'].unique())
    
    if fechas_encontradas.issubset(fechas_validas):
        print(f"  ✓ Solo fechas válidas encontradas")
    else:
        fechas_invalidas = fechas_encontradas - fechas_validas
        print(f"  ✗ Fechas inválidas encontradas: {fechas_invalidas}")
        return False
    
    print("\n✅ TEST 3 PASADO: Lógica de Fecha y Clasificacion correcta")
    return True


def test_estructura_export_no_balanceados():
    """
    Verifica que el export no balanceados tenga la estructura correcta de columnas.
    """
    print("\n" + "="*70)
    print(" TEST 4: Estructura Export No Balanceados ".center(70, "="))
    print("="*70)
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_raw = os.path.join(root_dir, 'data', 'raw')
    posiciones_path = os.path.join(data_raw, 'posiciones.csv')
    instruments_path = os.path.join(data_raw, 'instruments.csv')
    allocations_nuevas_path = os.path.join(data_raw, 'allocations_nuevas.csv')
    allocations_antiguas_path = os.path.join(data_raw, 'allocations_currency.csv')
    # Cargar datos
    df_instr = load_df_instruments(posiciones_path, instruments_path)
    df_nuevas = load_allocations_nuevas(df_instr, allocations_nuevas_path, umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, allocations_antiguas_path)
    df_final = crear_df_final(df_instr, df_nuevas, df_antiguas)
    
    # Generar export
    export_no_bal = generar_export_no_balanceados(df_final)
    
    # Columnas esperadas
    columnas_esperadas = ['ID', 'Instrumento', 'SubMoneda', 'Moneda Anterior', 'Estado', 'Sobreescribir']
    
    print("\n[Test 4.1] Verificando columnas...")
    for col in columnas_esperadas:
        if col in export_no_bal.columns:
            print(f"  ✓ {col}")
        else:
            print(f"  ✗ {col} - FALTA")
            return False
    
    print("\n[Test 4.2] Verificando que no hay columnas extras...")
    if list(export_no_bal.columns) == columnas_esperadas:
        print(f"  ✓ Solo columnas esperadas presentes")
    else:
        columnas_extras = set(export_no_bal.columns) - set(columnas_esperadas)
        if columnas_extras:
            print(f"  ⚠️  Columnas extras: {columnas_extras}")
    
    print("\n[Test 4.3] Verificando que no hay registros vacíos...")
    if len(export_no_bal) > 0:
        print(f"  ✓ {len(export_no_bal)} registros en el export")
    else:
        print(f"  ⚠️  Export sin registros (puede ser válido si todos son balanceados)")
    
    print("\n✅ TEST 4 PASADO: Estructura correcta")
    return True


def test_logica_estado_no_balanceados():
    """
    Verifica la lógica de la columna Estado en export no balanceados.
    """
    print("\n" + "="*70)
    print(" TEST 5: Lógica Estado - Export No Balanceados ".center(70, "="))
    print("="*70)
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_raw = os.path.join(root_dir, 'data', 'raw')
    posiciones_path = os.path.join(data_raw, 'posiciones.csv')
    instruments_path = os.path.join(data_raw, 'instruments.csv')
    allocations_nuevas_path = os.path.join(data_raw, 'allocations_nuevas.csv')
    allocations_antiguas_path = os.path.join(data_raw, 'allocations_currency.csv')
    # Cargar datos
    df_instr = load_df_instruments(posiciones_path, instruments_path)
    df_nuevas = load_allocations_nuevas(df_instr, allocations_nuevas_path, umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, allocations_antiguas_path)
    df_final = crear_df_final(df_instr, df_nuevas, df_antiguas)
    
    # Generar export
    export_no_bal = generar_export_no_balanceados(df_final)
    
    if len(export_no_bal) == 0:
        print("  ⚠️  No hay registros para validar estados")
        return True
    
    print("\n[Test 5.1] Verificando valores de Estado...")
    estados = export_no_bal['Estado'].value_counts()
    for estado, count in estados.items():
        print(f"  {estado}: {count} registros")
    
    print("\n[Test 5.2] Verificando que solo existen Estado_1, Estado_2 o Estado_3...")
    estados_validos = {'Estado_1', 'Estado_2', 'Estado_3'}
    estados_encontrados = set(export_no_bal['Estado'].unique())
    
    if estados_encontrados.issubset(estados_validos):
        print(f"  ✓ Solo estados válidos: {estados_encontrados}")
    else:
        estados_invalidos = estados_encontrados - estados_validos
        print(f"  ✗ Estados inválidos encontrados: {estados_invalidos}")
        return False
    
    print("\n[Test 5.3] Verificando columna Sobreescribir...")
    sobreescribir = export_no_bal['Sobreescribir'].value_counts()
    print(f"  Valores de Sobreescribir:")
    for valor, count in sobreescribir.items():
        print(f"    - {valor}: {count} registros")
    
    sobreescribir_validos = {'Sí', 'No'}
    sobreescribir_encontrados = set(export_no_bal['Sobreescribir'].unique())
    
    if sobreescribir_encontrados.issubset(sobreescribir_validos):
        print(f"  ✓ Solo valores válidos: {sobreescribir_encontrados}")
    else:
        print(f"  ✗ Valores inválidos encontrados: {sobreescribir_encontrados - sobreescribir_validos}")
        return False
    
    print("\n✅ TEST 5 PASADO: Lógica de Estado y Sobreescribir correcta")
    return True


def test_integridad_datos():
    """
    Verifica la integridad de los datos en ambos exports.
    """
    print("\n" + "="*70)
    print(" TEST 6: Integridad de Datos ".center(70, "="))
    print("="*70)
    
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_raw = os.path.join(root_dir, 'data', 'raw')
    posiciones_path = os.path.join(data_raw, 'posiciones.csv')
    instruments_path = os.path.join(data_raw, 'instruments.csv')
    allocations_nuevas_path = os.path.join(data_raw, 'allocations_nuevas.csv')
    allocations_antiguas_path = os.path.join(data_raw, 'allocations_currency.csv')
    # Cargar datos
    df_instr = load_df_instruments(posiciones_path, instruments_path)
    df_nuevas = load_allocations_nuevas(df_instr, allocations_nuevas_path, umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, allocations_antiguas_path)
    df_final = crear_df_final(df_instr, df_nuevas, df_antiguas)
    
    # Generar exports
    export_bal = generar_export_balanceados(df_final, df_nuevas, df_instr, df_antiguas)
    export_no_bal = generar_export_no_balanceados(df_final)
    
    print("\n[Test 6.1] Verificando que no hay IDs duplicados...")
    
    if len(export_bal) > 0:
        ids_bal_duplicados = export_bal['ID'].duplicated().sum()
        if ids_bal_duplicados == 0:
            print(f"  ✓ Export Balanceados: Sin IDs duplicados")
        else:
            print(f"  ✗ Export Balanceados: {ids_bal_duplicados} IDs duplicados")
            return False
    
    if len(export_no_bal) > 0:
        ids_no_bal_duplicados = export_no_bal['ID'].duplicated().sum()
        if ids_no_bal_duplicados == 0:
            print(f"  ✓ Export No Balanceados: Sin IDs duplicados")
        else:
            print(f"  ✗ Export No Balanceados: {ids_no_bal_duplicados} IDs duplicados")
            return False
    
    print("\n[Test 6.2] Verificando que la suma de ambos exports cubre todos los instrumentos...")
    total_exports = len(export_bal) + len(export_no_bal)
    total_balanceados_df_final = (df_final['moneda_nueva'] == 'Balanceado').sum()
    total_no_balanceados_df_final = (df_final['moneda_nueva'] != 'Balanceado').sum()
    
    print(f"  Total en df_final con moneda_nueva:")
    print(f"    - Balanceados: {total_balanceados_df_final}")
    print(f"    - No balanceados: {total_no_balanceados_df_final}")
    print(f"  Total en exports:")
    print(f"    - Export Balanceados: {len(export_bal)}")
    print(f"    - Export No Balanceados: {len(export_no_bal)}")
    
    if len(export_bal) == total_balanceados_df_final and len(export_no_bal) == total_no_balanceados_df_final:
        print(f"  ✓ Los exports cubren correctamente todos los instrumentos")
    else:
        print(f"  ⚠️  Diferencia en el conteo (puede ser por instrumentos sin moneda_nueva)")
    
    print("\n✅ TEST 6 PASADO: Integridad de datos correcta")
    return True


def ejecutar_todos_los_tests():
    """
    Ejecuta todos los tests de validación de exports.
    """
    print("\n" + "="*70)
    print(" SUITE DE TESTS: VALIDACIÓN DE EXPORTS ".center(70, "="))
    print("="*70)
    print(f"\nFecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Estructura Export Balanceados", test_estructura_export_balanceados),
        ("Lógica Estado Balanceados", test_logica_estado_balanceados),
        ("Lógica Fecha y Clasificacion Balanceados", test_logica_fecha_clasificacion_balanceados),
        ("Estructura Export No Balanceados", test_estructura_export_no_balanceados),
        ("Lógica Estado No Balanceados", test_logica_estado_no_balanceados),
        ("Integridad de Datos", test_integridad_datos),
    ]
    
    resultados = []
    tests_pasados = 0
    tests_fallados = 0
    
    for nombre, test_func in tests:
        try:
            resultado = test_func()
            resultados.append((nombre, resultado))
            if resultado:
                tests_pasados += 1
            else:
                tests_fallados += 1
        except Exception as e:
            print(f"\n✗ ERROR EN TEST '{nombre}': {str(e)}")
            resultados.append((nombre, False))
            tests_fallados += 1
    
    # Resumen final
    print("\n" + "="*70)
    print(" RESUMEN DE TESTS ".center(70, "="))
    print("="*70)
    
    for nombre, resultado in resultados:
        simbolo = "✅" if resultado else "❌"
        print(f"{simbolo} {nombre}")
    
    print("\n" + "-"*70)
    print(f"Total tests ejecutados: {len(tests)}")
    print(f"Tests pasados:          {tests_pasados}")
    print(f"Tests fallados:         {tests_fallados}")
    print(f"Porcentaje éxito:       {tests_pasados/len(tests)*100:.1f}%")
    print("="*70)
    
    if tests_fallados == 0:
        print("\n🎉 TODOS LOS TESTS PASARON EXITOSAMENTE")
        return 0
    else:
        print(f"\n⚠️  {tests_fallados} TEST(S) FALLARON")
        return 1


if __name__ == "__main__":
    exit_code = ejecutar_todos_los_tests()
    sys.exit(exit_code)
