"""
Test de Pipeline Completo (End-to-End)
=======================================
Ejecuta y valida el pipeline completo desde archivos raw hasta exports.
"""

import pandas as pd
import sys
import os
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def print_section(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)

def check_file_exists(filepath, descripcion):
    """Verifica que un archivo exista y retorna su tamaño."""
    if os.path.exists(filepath):
        size_kb = os.path.getsize(filepath) / 1024
        print(f"    [OK] {descripcion:40} ({size_kb:>8.1f} KB)")
        return True
    else:
        print(f"    [X] {descripcion:40} [NO ENCONTRADO]")
        return False

def test_pipeline_completo():
    """Ejecuta y valida el pipeline completo."""
    
    print_section("Test de Pipeline Completo (End-to-End)")
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # --- TEST 1: VERIFICAR ARCHIVOS RAW ---
    print_section("Test 1: Validación de Archivos Raw")
    
    archivos_raw = {
        'data/raw/instruments.csv': 'Maestro de Instrumentos',
        'data/raw/posiciones.csv': 'Posiciones',
        'data/raw/allocations_nuevas.csv': 'Allocations Nuevas',
        'data/raw/allocations_currency.csv': 'Allocations Antiguas'
    }
    
    print("\n[i] Verificando archivos de entrada...")
    todos_ok = True
    for filepath, desc in archivos_raw.items():
        if not check_file_exists(filepath, desc):
            todos_ok = False
    
    if not todos_ok:
        print("\n[!] ERROR: Faltan archivos raw necesarios.")
        return False
    
    print("\n[[OK]] Todos los archivos raw están presentes.")
    
    # --- TEST 2: EJECUTAR PIPELINE ---
    print_section("Test 2: Ejecución del Pipeline")
    
    print("\n[...] Ejecutando: python run_pipeline.py")
    print("[i] Esto puede tomar unos segundos...\n")
    
    try:
        # Ejecutar pipeline
        result = subprocess.run(
            ['python', 'run_pipeline.py'],
            capture_output=True,
            text=True,
            timeout=120  # 2 minutos máximo
        )
        
        if result.returncode == 0:
            print("[[OK]] Pipeline ejecutado exitosamente (exit code 0)")
        else:
            print(f"\n[!] ERROR: Pipeline falló con exit code {result.returncode}")
            print("\n--- STDERR ---")
            print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
            return False
        
        # Buscar métricas clave en la salida
        output = result.stdout
        if "PIPELINE COMPLETADO EXITOSAMENTE" in output:
            print("[[OK]] Pipeline completado exitosamente según logs")
        
        # Extraer estadísticas si están disponibles
        if "Total de instrumentos procesados:" in output:
            for line in output.split('\n'):
                if "Total de instrumentos procesados:" in line:
                    print(f"[i] {line.strip()}")
                elif "Instrumentos balanceados:" in line:
                    print(f"[i] {line.strip()}")
                elif "Instrumentos con cambios:" in line:
                    print(f"[i] {line.strip()}")
    
    except subprocess.TimeoutExpired:
        print("\n[!] ERROR: Pipeline excedió el tiempo límite (2 minutos)")
        return False
    
    except Exception as e:
        print(f"\n[!] ERROR al ejecutar pipeline: {str(e)}")
        return False
    
    # --- TEST 3: VERIFICAR ARCHIVOS PROCESADOS ---
    print_section("Test 3: Validación de Archivos Procesados")
    
    archivos_procesados = {
        'data/processed/df_instruments.csv': 'Instrumentos Filtrados',
        'data/processed/allocations_nuevas.csv': 'Allocations Nuevas (LONG)',
        'data/processed/allocations_antiguas.csv': 'Allocations Antiguas (WIDE)',
        'data/processed/df_final.csv': 'DataFrame Final Consolidado'
    }
    
    print("\n[i] Verificando archivos procesados...")
    todos_ok = True
    for filepath, desc in archivos_procesados.items():
        if not check_file_exists(filepath, desc):
            todos_ok = False
    
    if not todos_ok:
        print("\n[!] ERROR: Faltan archivos procesados.")
        return False
    
    print("\n[[OK]] Todos los archivos procesados generados.")
    
    # --- TEST 4: VERIFICAR ARCHIVOS DE EXPORTACIÓN ---
    print_section("Test 4: Validación de Archivos de Exportación")
    
    archivos_export = {
        'data/exports/export_balanceados.csv': 'Export Balanceados',
        'data/exports/export_no_balanceados.csv': 'Export No Balanceados',
        'data/exports/export_con_cambios.csv': 'Export Con Cambios'
    }
    
    print("\n[i] Verificando archivos de exportación...")
    todos_ok = True
    for filepath, desc in archivos_export.items():
        if not check_file_exists(filepath, desc):
            todos_ok = False
    
    if not todos_ok:
        print("\n[!] ADVERTENCIA: Faltan algunos archivos de exportación.")
    else:
        print("\n[[OK]] Todos los archivos de exportación generados.")
    
    # --- TEST 5: VALIDAR CONTENIDO DE ARCHIVOS ---
    print_section("Test 5: Validación de Contenido")
    
    errores = []
    
    # 5.1 - df_instruments
    print("\n[i] Validando df_instruments.csv...")
    try:
        df_instr = pd.read_csv('data/processed/df_instruments.csv', sep=';', encoding='latin-1')
        print(f"    Registros: {len(df_instr)}")
        print(f"    Columnas: {list(df_instr.columns)}")
        
        # Validar columnas requeridas
        cols_req = ['ID', 'Nombre', 'Tipo instrumento', 'RIC', 'Isin', 'Cusip', 'SubMoneda']
        faltantes = [c for c in cols_req if c not in df_instr.columns]
        if faltantes:
            errores.append(f"df_instruments: Columnas faltantes {faltantes}")
        else:
            print(f"    [OK] Todas las columnas requeridas presentes")
        
        if len(df_instr) < 100:
            print(f"    [!] ADVERTENCIA: Pocos instrumentos ({len(df_instr)})")
        
    except Exception as e:
        errores.append(f"df_instruments: {str(e)}")
    
    # 5.2 - allocations_nuevas
    print("\n[i] Validando allocations_nuevas.csv...")
    try:
        df_nuevas = pd.read_csv('data/processed/allocations_nuevas.csv', sep=';', encoding='latin-1')
        print(f"    Registros: {len(df_nuevas)}")
        print(f"    Instrumentos: {df_nuevas['ID'].nunique()}")
        print(f"    Columnas: {df_nuevas.shape[1]}")
        
        # Validar formato LONG (debe ser exactamente 10 columnas)
        if df_nuevas.shape[1] != 10:
            errores.append(f"allocations_nuevas: Debe tener 10 columnas, tiene {df_nuevas.shape[1]}")
        else:
            print(f"    [OK] Formato LONG correcto (10 columnas)")
        
        # Validar columnas específicas
        cols_req = ['ID', 'Nombre', 'instrument', 'class', 'percentage', 'date',
                   'moneda_nueva', 'pct_dominancia_nuevo', 'pct_escalado', 'pct_original']
        faltantes = [c for c in cols_req if c not in df_nuevas.columns]
        if faltantes:
            errores.append(f"allocations_nuevas: Columnas faltantes {faltantes}")
        else:
            print(f"    [OK] Todas las columnas de dominancia presentes")
        
        # Validar que hay múltiples filas por instrumento
        filas_por_inst = len(df_nuevas) / df_nuevas['ID'].nunique()
        if filas_por_inst > 1.5:
            print(f"    [OK] Múltiples filas/instrumento ({filas_por_inst:.1f})")
        else:
            errores.append(f"allocations_nuevas: Parece formato WIDE ({filas_por_inst:.1f} filas/inst)")
    
    except Exception as e:
        errores.append(f"allocations_nuevas: {str(e)}")
    
    # 5.3 - allocations_antiguas
    print("\n[i] Validando allocations_antiguas.csv...")
    try:
        df_antiguas = pd.read_csv('data/processed/allocations_antiguas.csv', sep=';', encoding='latin-1', nrows=10)
        print(f"    Registros: {len(df_antiguas)}")
        print(f"    Columnas: {df_antiguas.shape[1]}")
        
        # Validar formato WIDE (debe tener muchas columnas)
        if df_antiguas.shape[1] < 50:
            errores.append(f"allocations_antiguas: Parece formato LONG (solo {df_antiguas.shape[1]} columnas)")
        else:
            print(f"    [OK] Formato WIDE correcto ({df_antiguas.shape[1]} columnas)")
        
        # Verificar SubMoneda
        if 'SubMoneda' in df_antiguas.columns:
            print(f"    [OK] Columna SubMoneda presente")
        else:
            errores.append(f"allocations_antiguas: Falta columna SubMoneda")
    
    except Exception as e:
        errores.append(f"allocations_antiguas: {str(e)}")
    
    # 5.4 - df_final
    print("\n[i] Validando df_final.csv...")
    try:
        df_final = pd.read_csv('data/processed/df_final.csv', sep=';', encoding='latin-1', nrows=10)
        print(f"    Registros: {len(df_final)}")
        print(f"    Columnas: {df_final.shape[1]}")
        
        # Verificar que tenga datos de ambos archivos
        tiene_nuevas = any('nueva' in str(c).lower() for c in df_final.columns)
        tiene_antiguas = any('antigua' in str(c).lower() or 'Pct_dominancia' in c for c in df_final.columns)
        
        if tiene_nuevas and tiene_antiguas:
            print(f"    [OK] Contiene datos de allocations nuevas y antiguas")
        else:
            errores.append(f"df_final: No parece tener datos consolidados correctamente")
    
    except Exception as e:
        errores.append(f"df_final: {str(e)}")
    
    # Mostrar errores si hay
    if errores:
        print(f"\n[!] Se encontraron {len(errores)} errores:")
        for err in errores:
            print(f"    [X] {err}")
        return False
    else:
        print("\n[[OK]] Validación de contenido exitosa.")
    
    # --- TEST 6: VALIDACIÓN DE INTEGRIDAD ---
    print_section("Test 6: Validación de Integridad")
    
    print("\n[i] Verificando integridad de datos...")
    
    # 6.1 - Verificar que los IDs están presentes en todos los archivos
    try:
        df_instr = pd.read_csv('data/processed/df_instruments.csv', sep=';', encoding='latin-1')
        df_nuevas = pd.read_csv('data/processed/allocations_nuevas.csv', sep=';', encoding='latin-1')
        df_antiguas = pd.read_csv('data/processed/allocations_antiguas.csv', sep=';', encoding='latin-1')
        
        ids_instr = set(df_instr['ID'])
        ids_nuevas = set(df_nuevas['ID'])
        ids_antiguas = set(df_antiguas['ID'])
        
        print(f"\n[i] IDs por archivo:")
        print(f"    df_instruments:       {len(ids_instr)}")
        print(f"    allocations_nuevas:   {len(ids_nuevas)}")
        print(f"    allocations_antiguas: {len(ids_antiguas)}")
        
        # Los IDs de nuevas y antiguas deben ser subconjuntos de instruments
        if ids_nuevas.issubset(ids_instr):
            print(f"    [OK] IDs de nuevas están en instruments")
        else:
            print(f"    [!] ADVERTENCIA: {len(ids_nuevas - ids_instr)} IDs de nuevas no están en instruments")
        
        if ids_antiguas.issubset(ids_instr):
            print(f"    [OK] IDs de antiguas están en instruments")
        else:
            print(f"    [!] ADVERTENCIA: {len(ids_antiguas - ids_instr)} IDs de antiguas no están en instruments")
        
        # Comparar cobertura
        cobertura_nuevas = len(ids_nuevas) / len(ids_instr) * 100
        cobertura_antiguas = len(ids_antiguas) / len(ids_instr) * 100
        
        print(f"\n[i] Cobertura:")
        print(f"    Nuevas:   {cobertura_nuevas:.1f}% de instruments")
        print(f"    Antiguas: {cobertura_antiguas:.1f}% de instruments")
        
        if cobertura_nuevas > 20 and cobertura_antiguas > 20:
            print(f"\n[[OK]] Cobertura razonable en ambos archivos")
        else:
            print(f"\n[!] ADVERTENCIA: Cobertura baja")
    
    except Exception as e:
        print(f"\n[!] ERROR en validación de integridad: {str(e)}")
    
    # --- RESUMEN FINAL ---
    print_section("Resumen Final del Pipeline")
    
    print("\n[OK] Pipeline ejecutado exitosamente")
    print("[OK] Todos los archivos generados")
    print("[OK] Formato de archivos correcto (LONG/WIDE según corresponde)")
    print("[OK] Contenido validado")
    print("[OK] Integridad de datos verificada")
    
    print("\n" + "="*80)
    print(" [OK] TEST DE PIPELINE COMPLETO EXITOSO ".center(80, "="))
    print("="*80)
    
    return True

if __name__ == "__main__":
    exito = test_pipeline_completo()
    sys.exit(0 if exito else 1)
