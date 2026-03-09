"""
Test de Carga de Archivos — REGIÓN
====================================
Valida que los archivos raw de región existan y puedan cargarse correctamente.
"""

import pandas as pd
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def print_section(title):
    print("\n" + "="*60)
    print(f" {title.upper()} ".center(60, "="))
    print("="*60)


def test_carga_archivos_region():
    files = {
        "Maestro Instrumentos":          "data/raw/instruments.csv",
        "Posiciones":                    "data/raw/posiciones.csv",
        "Nuevas Allocations (WIDE)":     "data/raw/region/allocations_nuevas_region.csv",
        "Antiguas Allocations (región)": "data/raw/region/allocations_region.csv",
    }

    print_section("Validación de Carga de Archivos — REGIÓN")

    todos_ok = True

    for name, path in files.items():
        print(f"\n[+] Analizando: {name}")
        print(f"    Ruta: {path}")

        if not os.path.exists(path):
            print(f"    [!] ERROR: El archivo no existe.")
            todos_ok = False
            continue

        try:
            df = pd.read_csv(path, sep=';', encoding='latin-1', nrows=5, on_bad_lines='skip')
            print(f"    [OK] Archivo cargado correctamente.")
            print(f"    [i] Columnas detectadas ({len(df.columns)}):")
            for col in df.columns.tolist():
                print(f"        - {col}")
            print(f"    [i] Muestra de datos (primeras 2 filas):")
            print(df.head(2).to_string(index=False))

        except Exception as e:
            print(f"    [!] ERROR al cargar: {str(e)}")
            todos_ok = False

    print_section("Validación Extra — columnas clave de región")

    # Verificar columna Base Región en antiguas
    try:
        df_ant = pd.read_csv("data/raw/region/allocations_region.csv",
                             sep=';', encoding='latin-1', nrows=3, on_bad_lines='skip')
        cols_lower = [c.lower() for c in df_ant.columns]
        tiene_base_region = any('base' in c and 'regi' in c for c in cols_lower)
        if tiene_base_region:
            col_found = [c for c in df_ant.columns if 'base' in c.lower() and 'regi' in c.lower()][0]
            print(f"\n    [OK] Columna 'Base Región:' detectada: '{col_found}'")
        else:
            print(f"\n    [!] ADVERTENCIA: No se detectó columna 'Base Región:' en antiguas.")
            print(f"         Columnas presentes: {df_ant.columns.tolist()}")
            todos_ok = False
    except Exception as e:
        print(f"\n    [!] ERROR al verificar columna Base Región: {e}")
        todos_ok = False

    # Verificar que nuevas tiene formato WIDE (muchas columnas)
    try:
        df_nue = pd.read_csv("data/raw/region/allocations_nuevas_region.csv",
                             sep=';', encoding='latin-1', nrows=3, on_bad_lines='skip')
        print(f"\n    [i] Nuevas - número de columnas: {len(df_nue.columns)}")
        if len(df_nue.columns) > 5:
            print(f"    [OK] Formato WIDE confirmado (> 5 columnas)")
        else:
            print(f"    [!] ADVERTENCIA: Pocas columnas — ¿es realmente formato WIDE?")
    except Exception as e:
        print(f"\n    [!] ERROR: {e}")

    print_section("Resumen Final")
    if todos_ok:
        print("[OK] Todos los archivos de región cargaron correctamente.")
    else:
        print("[!] Algunos archivos presentaron problemas. Revisar más arriba.")

    return todos_ok


if __name__ == "__main__":
    exito = test_carga_archivos_region()
    sys.exit(0 if exito else 1)
