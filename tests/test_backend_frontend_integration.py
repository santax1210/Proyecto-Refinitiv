"""
Test de integración Backend-Frontend
Valida que los datos se pasen correctamente desde Python (backend) a React (frontend).

Este test simula el flujo completo:
1. Backend procesa archivos y genera df_final y exports
2. Backend serializa a JSON (como lo haría el endpoint /api/results/validation)
3. Verifica que la estructura JSON sea correcta
4. Valida que todas las columnas esperadas estén presentes
"""

import sys
import os
import json
import pandas as pd

# Agregar src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.extractors.load_instruments import load_df_instruments
from src.extractors.load_allocations import load_allocations_nuevas, load_allocations_antiguas
from src.logic.clasificacion import ejecutar_pipeline_completo


def test_estructura_resultados():
    """
    TEST 1: Verificar que ejecutar_pipeline_completo retorna la estructura correcta
    """
    print("\n" + "="*70)
    print(" TEST 1: Estructura de resultados del pipeline ".center(70, "="))
    print("="*70)
    
    # Cargar datos
    df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
    df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
    
    # Ejecutar pipeline
    resultados = ejecutar_pipeline_completo(df_instr, df_nuevas, df_antiguas)
    
    # Verificar claves principales
    claves_esperadas = [
        'df_final', 'df_nuevas', 'df_antiguas',
        'df_balanceados', 'df_no_balanceados', 'df_con_cambios',
        'exports'
    ]
    
    print("\n[Verificando claves principales...]")
    for clave in claves_esperadas:
        if clave in resultados:
            print(f"  [OK] '{clave}' presente")
        else:
            print(f"  [ERROR] '{clave}' FALTA")
            return False
    
    # Verificar exports
    print("\n[Verificando estructura de exports...]")
    exports_esperados = ['balanceados', 'no_balanceados', 'con_cambios', 'sin_datos']
    
    if 'exports' not in resultados:
        print("  [ERROR] Clave 'exports' no encontrada")
        return False
    
    for export_key in exports_esperados:
        if export_key in resultados['exports']:
            print(f"  [OK] exports['{export_key}'] presente")
        else:
            print(f"  [ERROR] exports['{export_key}'] FALTA")
            return False
    
    print("\n[OK] Estructura de resultados correcta")
    return True


def test_columnas_df_final():
    """
    TEST 2: Verificar que df_final tiene todas las columnas esperadas por el frontend
    """
    print("\n" + "="*70)
    print(" TEST 2: Columnas de df_final (para tabla de validación) ".center(70, "="))
    print("="*70)
    
    # Cargar datos y ejecutar pipeline
    df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
    df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
    resultados = ejecutar_pipeline_completo(df_instr, df_nuevas, df_antiguas)
    
    df_final = resultados['df_final']
    
    # Columnas críticas que el frontend espera
    columnas_criticas = [
        'ID',
        'Nombre',
        'moneda_nueva',
        'Pct_dominancia',
        'Cambio',
        'Estado'
    ]
    
    print("\n[Verificando columnas críticas para el frontend...]")
    columnas_faltantes = []
    
    for col in columnas_criticas:
        if col in df_final.columns:
            print(f"  [OK] {col}")
        else:
            print(f"  [ERROR] {col} - FALTA")
            columnas_faltantes.append(col)
    
    if columnas_faltantes:
        print(f"\n[ERROR] Columnas faltantes: {columnas_faltantes}")
        return False
    
    print(f"\n[INFO] Total de columnas en df_final: {len(df_final.columns)}")
    print(f"[INFO] Columnas: {df_final.columns.tolist()}")
    
    print("\n[OK] Todas las columnas críticas presentes")
    return True


def test_serializacion_json():
    """
    TEST 3: Verificar que df_final puede serializarse a JSON correctamente
    """
    print("\n" + "="*70)
    print(" TEST 3: Serialización a JSON (backend -> frontend) ".center(70, "="))
    print("="*70)
    
    # Cargar datos y ejecutar pipeline
    df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
    df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
    resultados = ejecutar_pipeline_completo(df_instr, df_nuevas, df_antiguas)
    
    df_final = resultados['df_final']
    
    print("\n[Intentando serializar df_final a JSON...]")
    try:
        # Simular lo que hace el endpoint /api/results/validation
        df_final = df_final.astype(object).where(pd.notna(df_final), None)
        data = df_final.to_dict(orient='records')
        # Intentar serializar a JSON string
        json_string = json.dumps(data)
        print(f"  [OK] Serialización exitosa")
        print(f"  [INFO] Total de registros: {len(data)}")
        print(f"  [INFO] Tamaño del JSON: {len(json_string) / 1024:.2f} KB")
        # Verificar que se puede deserializar
        data_parsed = json.loads(json_string)
        print(f"  [OK] Deserialización exitosa")
        # Verificar estructura del primer registro
        if data_parsed and len(data_parsed) > 0:
            print(f"\n[INFO] Estructura del primer registro:")
            primer_registro = data_parsed[0]
            for key, value in list(primer_registro.items())[:10]:
                print(f"    {key}: {value} (tipo: {type(value).__name__})")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Fallo en serialización: {str(e)}")
        return False


def test_estructura_summary():
    """
    TEST 4: Verificar estructura del summary JSON
    """
    print("\n" + "="*70)
    print(" TEST 4: Estructura del summary.json ".center(70, "="))
    print("="*70)
    
    # Cargar datos y ejecutar pipeline
    df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
    df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
    resultados = ejecutar_pipeline_completo(df_instr, df_nuevas, df_antiguas)
    
    # Simular lo que hace el backend en app.py
    summary = {
        'total_instrumentos': len(resultados['df_final']),
        'balanceados': len(resultados['exports']['balanceados']),
        'no_balanceados': len(resultados['exports']['no_balanceados']),
        'con_cambios': len(resultados['exports']['con_cambios']),
        'sin_datos': len(resultados['exports']['sin_datos']),
    }
    
    print("\n[Verificando estructura del summary...]")
    claves_esperadas = ['total_instrumentos', 'balanceados', 'no_balanceados', 'con_cambios', 'sin_datos']
    
    for clave in claves_esperadas:
        if clave in summary:
            valor = summary[clave]
            print(f"  [OK] {clave}: {valor}")
        else:
            print(f"  [ERROR] {clave} FALTA en summary")
            return False
    
    # Verificar que se puede serializar a JSON
    try:
        json_string = json.dumps(summary)
        print(f"\n[OK] Summary serializable a JSON")
        print(f"[INFO] Tamaño: {len(json_string)} bytes")
        return True
    except Exception as e:
        print(f"\n[ERROR] No se puede serializar summary: {str(e)}")
        return False


def test_valores_estado():
    """
    TEST 5: Verificar que la columna Estado tiene valores válidos
    """
    print("\n" + "="*70)
    print(" TEST 5: Valores de la columna Estado ".center(70, "="))
    print("="*70)
    
    # Cargar datos y ejecutar pipeline
    df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
    df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
    resultados = ejecutar_pipeline_completo(df_instr, df_nuevas, df_antiguas)
    
    df_final = resultados['df_final']
    
    if 'Estado' not in df_final.columns:
        print("[ERROR] Columna 'Estado' no encontrada")
        return False
    
    # Valores válidos esperados
    valores_validos = ['Estado_1', 'Estado_2', 'Estado_3', '']
    
    estados_en_df = df_final['Estado'].unique()
    print(f"\n[INFO] Estados encontrados: {estados_en_df}")
    
    estados_invalidos = [e for e in estados_en_df if e not in valores_validos]
    
    if estados_invalidos:
        print(f"[ERROR] Estados inválidos encontrados: {estados_invalidos}")
        return False
    
    print("[OK] Todos los estados son válidos")
    
    # Mostrar distribución
    print("\n[INFO] Distribución de Estados:")
    dist = df_final['Estado'].value_counts()
    for estado, count in dist.items():
        estado_display = estado if estado else "(vacío)"
        print(f"  {estado_display}: {count}")
    
    return True


def test_valores_cambio():
    """
    TEST 6: Verificar que la columna Cambio tiene valores válidos
    """
    print("\n" + "="*70)
    print(" TEST 6: Valores de la columna Cambio ".center(70, "="))
    print("="*70)
    
    # Cargar datos y ejecutar pipeline
    df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
    df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
    df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
    resultados = ejecutar_pipeline_completo(df_instr, df_nuevas, df_antiguas)
    
    df_final = resultados['df_final']
    
    if 'Cambio' not in df_final.columns:
        print("[ERROR] Columna 'Cambio' no encontrada")
        return False
    
    # Valores válidos esperados
    valores_validos = ['Si', 'No', '']
    
    cambios_en_df = df_final['Cambio'].unique()
    print(f"\n[INFO] Valores de Cambio encontrados: {cambios_en_df}")
    
    cambios_invalidos = [c for c in cambios_en_df if c not in valores_validos]
    
    if cambios_invalidos:
        print(f"[ERROR] Valores de Cambio inválidos: {cambios_invalidos}")
        return False
    
    print("[OK] Todos los valores de Cambio son válidos")
    
    # Mostrar distribución
    print("\n[INFO] Distribución de Cambio:")
    dist = df_final['Cambio'].value_counts()
    for valor, count in dist.items():
        valor_display = valor if valor else "(vacío)"
        print(f"  {valor_display}: {count}")
    
    return True


# ============================================================================
# EJECUTAR TODOS LOS TESTS
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print(" TESTS DE INTEGRACION BACKEND-FRONTEND ".center(70, "="))
    print("="*70)
    print("\nEstos tests validan que los datos se pasen correctamente")
    print("desde el backend (Python/Flask) al frontend (React/JSON)")
    
    tests = [
        ("Estructura de resultados", test_estructura_resultados),
        ("Columnas de df_final", test_columnas_df_final),
        ("Serialización a JSON", test_serializacion_json),
        ("Estructura del summary", test_estructura_summary),
        ("Valores de Estado", test_valores_estado),
        ("Valores de Cambio", test_valores_cambio),
    ]
    
    resultados = []
    
    for nombre, test_func in tests:
        try:
            exito = test_func()
            resultados.append((nombre, exito))
        except Exception as e:
            print(f"\n[ERROR] Test '{nombre}' falló con excepción: {str(e)}")
            resultados.append((nombre, False))
    
    # Resumen final
    print("\n" + "="*70)
    print(" RESUMEN DE TESTS ".center(70, "="))
    print("="*70)
    
    tests_exitosos = sum(1 for _, exito in resultados if exito)
    tests_fallidos = len(resultados) - tests_exitosos
    
    for nombre, exito in resultados:
        status = "[OK]" if exito else "[FALLO]"
        print(f"{status} {nombre}")
    
    print("\n" + "-"*70)
    print(f"Total:    {len(resultados)} tests")
    print(f"Exitosos: {tests_exitosos}")
    print(f"Fallidos: {tests_fallidos}")
    print("="*70)
    
    if tests_fallidos > 0:
        print("\n[ATENCION] Algunos tests fallaron. Revisa los logs arriba.")
        sys.exit(1)
    else:
        print("\n[EXITO] Todos los tests pasaron correctamente!")
        sys.exit(0)
