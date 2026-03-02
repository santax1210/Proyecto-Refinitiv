"""
Suite de Tests - Ejecutor Maestro
==================================
Ejecuta todos los tests del proyecto en secuencia.
"""

import sys
import os
import subprocess
from datetime import datetime

def print_header(texto):
    print("\n" + "="*80)
    print(f" {texto} ".center(80, "="))
    print("="*80)

def ejecutar_test(nombre_archivo, descripcion):
    """Ejecuta un test individual y retorna True si pasa."""
    print(f"\n{'-'*80}")
    print(f">> Ejecutando: {descripcion}")
    print(f"   Archivo: {nombre_archivo}")
    print(f"{'-'*80}\n")
    
    try:
        result = subprocess.run(
            ['python', f'tests/{nombre_archivo}'],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        # Mostrar salida
        print(result.stdout)
        
        if result.returncode == 0:
            print(f"\n[OK] {descripcion} - EXITOSO")
            return True
        else:
            print(f"\n[X] {descripcion} - FALLIDO (exit code {result.returncode})")
            if result.stderr:
                print("\nError output:")
                print(result.stderr)
            return False
    
    except subprocess.TimeoutExpired:
        print(f"\n❌ {descripcion} - TIMEOUT")
        return False
    
    except Exception as e:
        print(f"\n❌ {descripcion} - ERROR: {str(e)}")
        return False

def main():
    """Ejecuta toda la suite de tests."""
    
    print_header("SUITE DE TESTS - ALLOCATIONS VALIDATION")
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Directorio: {os.getcwd()}")
    
    # Definir tests a ejecutar
    tests = [
        ('test_carga_archivos.py', 'Test 1: Carga de Archivos Raw'),
        ('test_creacion_dataframes.py', 'Test 2: Creación de DataFrames'),
        ('test_mapeo_monedas.py', 'Test 3: Mapeo de Monedas (Refinitiv→ISO)'),
        ('test_dominancia.py', 'Test 4: Cálculos de Dominancia y Escalado'),
        ('test_formato_archivos.py', 'Test 5: Formato de Archivos (LONG/WIDE)'),
        ('test_exports.py', 'Test 6: Generación y Validación de Exports'),
        ('test_pipeline_completo.py', 'Test 7: Pipeline Completo (End-to-End)'),
    ]
    
    resultados = []
    
    print_header("EJECUTANDO TESTS")
    
    for archivo, descripcion in tests:
        exito = ejecutar_test(archivo, descripcion)
        resultados.append((descripcion, exito))
    
    # Resumen final
    print_header("RESUMEN DE RESULTADOS")
    
    print(f"\n{'Test':<55} | {'Resultado':>20}")
    print("─" * 80)
    
    exitosos = 0
    fallidos = 0
    
    for descripcion, exito in resultados:
        if exito:
            print(f"{descripcion:<55} | {'[OK] EXITOSO':>20}")
            exitosos += 1
        else:
            print(f"{descripcion:<55} | {'[X] FALLIDO':>20}")
            fallidos += 1
    
    print("-" * 80)
    print(f"\n{'Total tests:':<55} {len(resultados)}")
    print(f"{'Exitosos:':<55} {exitosos} ({exitosos/len(resultados)*100:.0f}%)")
    print(f"{'Fallidos:':<55} {fallidos}")
    
    # Resultado final
    if fallidos == 0:
        print_header("[OK] TODOS LOS TESTS PASARON")
        return 0
    else:
        print_header(f"[X] {fallidos} TEST(S) FALLARON")
        return 1

if __name__ == "__main__":
    codigo_salida = main()
    sys.exit(codigo_salida)
