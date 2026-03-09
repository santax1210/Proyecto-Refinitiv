"""
Test de Formato de Archivos — REGIÓN
=======================================
Valida formato de allocations_nuevas_region (WIDE raw → LONG procesado)
y allocations_region (WIDE antiguas).

Diferencias clave vs moneda:
- nuevas raw: WIDE (una fila por instrumento, columnas = regiones)
- nuevas procesadas: LONG (una fila por instrumento-región)
- antiguas: WIDE (igual que moneda pero con 'Base Region:' en lugar de 'Moneda:')
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def print_section(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)


def test_formato_archivos_region():
    todos_ok = True

    print_section("Test de Formato de Archivos — REGIÓN")

    # ------------------------------------------------------------------ #
    # TEST 1: ALLOCATIONS NUEVAS RAW (debe ser WIDE)
    # ------------------------------------------------------------------ #
    print_section("Test 1: allocations_nuevas_region.csv raw (Formato WIDE)")

    try:
        df_nuevas_raw = pd.read_csv(
            'data/raw/region/allocations_nuevas_region.csv',
            sep=';', encoding='latin-1', on_bad_lines='skip'
        )

        print(f"\n[[OK]] Archivo cargado: {df_nuevas_raw.shape[0]} filas × {df_nuevas_raw.shape[1]} columnas")

        # Formato WIDE: 1 fila por instrumento
        ids_unicos = df_nuevas_raw.iloc[:, 0].nunique()
        total_filas = len(df_nuevas_raw)

        print(f"\n[i] Análisis de formato:")
        print(f"    Instrumentos únicos (col 0): {ids_unicos}")
        print(f"    Total filas:                 {total_filas}")

        if total_filas == ids_unicos:
            print(f"\n[[OK]] FORMATO WIDE CONFIRMADO (1 fila por instrumento)")
        else:
            print(f"\n[!] ADVERTENCIA: Filas ({total_filas}) ≠ únicos ({ids_unicos}). Posibles duplicados.")

        # Columnas de región (todas excepto la primera = identificador)
        cols_region = df_nuevas_raw.columns[1:].tolist()
        print(f"\n[i] Columnas de región detectadas ({len(cols_region)}):")
        for col in cols_region[:10]:
            print(f"    - {col}")
        if len(cols_region) > 10:
            print(f"    ... y {len(cols_region) - 10} más")

        if len(cols_region) > 5:
            print(f"\n[[OK]] Múltiples columnas de región (formato WIDE correcto)")
        else:
            print(f"\n[!] ADVERTENCIA: Pocas columnas de región ({len(cols_region)})")
            todos_ok = False

        # Verificar que los valores tienen coma como separador decimal
        sample_val = df_nuevas_raw.iloc[0, 1]
        val_str = str(sample_val).strip()
        if ',' in val_str:
            print(f"\n[[OK]] Separador decimal detectado: coma (ej: '{val_str}')")
        elif '.' in val_str:
            print(f"\n[i] Separador decimal: punto (ej: '{val_str}')")
        else:
            print(f"\n[i] Valor de muestra: '{val_str}'")

    except FileNotFoundError:
        print(f"\n[!] ERROR: Archivo no encontrado. Verificar data/raw/region/")
        todos_ok = False

    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
        todos_ok = False

    # ------------------------------------------------------------------ #
    # TEST 2: ALLOCATIONS NUEVAS PROCESADAS (debe ser LONG)
    # ------------------------------------------------------------------ #
    print_section("Test 2: allocations_nuevas_region.csv procesado (Formato LONG)")

    try:
        df_nuevas = pd.read_csv(
            'data/processed/region/allocations_nuevas_region.csv',
            sep=';', encoding='utf-8'
        )

        print(f"\n[[OK]] Archivo cargado: {df_nuevas.shape[0]} filas × {df_nuevas.shape[1]} columnas")
        print(f"\n[i] Columnas presentes:")
        for col in df_nuevas.columns:
            print(f"    - {col}")

        # Validar estructura LONG (múltiples filas por instrumento)
        total_instr = df_nuevas['ID'].nunique()
        total_filas = len(df_nuevas)
        filas_por_instr = total_filas / total_instr if total_instr > 0 else 0

        print(f"\n[i] Análisis de formato:")
        print(f"    Instrumentos únicos: {total_instr}")
        print(f"    Total filas:         {total_filas}")
        print(f"    Filas/instrumento:   {filas_por_instr:.2f}")

        if filas_por_instr > 1.5:
            print(f"\n[[OK]] FORMATO LONG CONFIRMADO (múltiples filas por instrumento)")
        else:
            print(f"\n[!] ADVERTENCIA: Parece formato WIDE (pocas filas por instrumento)")
            todos_ok = False

        # Columnas requeridas
        cols_requeridas = ['ID', 'Nombre', 'instrument', 'region', 'percentage',
                           'tipo_id', 'region_nueva', 'pct_dominancia_nueva',
                           'pct_escalado', 'pct_original']
        faltantes = [c for c in cols_requeridas if c not in df_nuevas.columns]
        if faltantes:
            print(f"\n[!] Columnas faltantes: {faltantes}")
            todos_ok = False
        else:
            print(f"\n[[OK]] Todas las columnas requeridas presentes")

        # Muestra de un instrumento (múltiples regiones)
        sample_id = df_nuevas['ID'].iloc[0]
        df_sample = df_nuevas[df_nuevas['ID'] == sample_id]
        print(f"\n[i] Muestra — instrumento {sample_id} ({len(df_sample)} regiones):")
        for _, row in df_sample.head(5).iterrows():
            pct = row.get('percentage', 'N/A')
            print(f"    {str(row.get('region', '?')):25} : {pct}")

    except FileNotFoundError:
        print(f"\n[!] ERROR: Archivo procesado no encontrado.")
        print(f"    Ejecute primero: python run_pipeline_region.py")
        todos_ok = False

    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
        todos_ok = False

    # ------------------------------------------------------------------ #
    # TEST 3: ALLOCATIONS ANTIGUAS PROCESADAS (WIDE con Base Region:)
    # ------------------------------------------------------------------ #
    print_section("Test 3: allocations_antiguas_region.csv procesado (Formato WIDE + Base Region:)")

    try:
        df_antiguas = pd.read_csv(
            'data/processed/region/allocations_antiguas_region.csv',
            sep=';', encoding='utf-8'
        )

        print(f"\n[[OK]] Archivo cargado: {df_antiguas.shape[0]} filas × {df_antiguas.shape[1]} columnas")

        # 1 fila por instrumento
        total_instr = df_antiguas['ID'].nunique()
        total_filas = len(df_antiguas)
        print(f"\n[i] Instrumentos únicos: {total_instr} | Total filas: {total_filas}")

        if total_instr == total_filas:
            print(f"[[OK]] FORMATO WIDE CONFIRMADO (1 fila por instrumento)")
        else:
            print(f"[!] ADVERTENCIA: Filas ({total_filas}) ≠ únicos ({total_instr})")

        # Columna Base Region: (normalizada, sin acento)
        if 'Base Region:' in df_antiguas.columns:
            print(f"\n[[OK]] Columna 'Base Region:' normalizada presente")
            valores = df_antiguas['Base Region:'].value_counts().head(5)
            print(f"[i] Valores frecuentes en 'Base Region:':")
            for val, cnt in valores.items():
                print(f"    '{val}' : {cnt} instrumentos")
        else:
            print(f"\n[!] ERROR: Columna 'Base Region:' no encontrada")
            print(f"    Columnas: {df_antiguas.columns.tolist()}")
            todos_ok = False

        # Columna Pct_dominancia
        if 'Pct_dominancia' in df_antiguas.columns:
            print(f"\n[[OK]] Columna 'Pct_dominancia' presente")
            sample_vals = df_antiguas['Pct_dominancia'].dropna().head(5).tolist()
            print(f"[i] Ejemplos de Pct_dominancia: {sample_vals}")
        else:
            print(f"\n[!] ERROR: Columna 'Pct_dominancia' faltante")
            todos_ok = False

        # Columnas de región (excluir metadata)
        cols_meta = {'ID', 'Nombre', 'Pct_dominancia', 'Base Region:'}
        cols_region = [c for c in df_antiguas.columns if c not in cols_meta]
        print(f"\n[i] Columnas de región en antiguas ({len(cols_region)}):")
        for col in cols_region[:10]:
            print(f"    - {col}")

        if len(cols_region) > 5:
            print(f"\n[[OK]] Múltiples columnas de región detectadas")
        else:
            print(f"\n[!] ADVERTENCIA: Pocas columnas de región ({len(cols_region)})")

    except FileNotFoundError:
        print(f"\n[!] ERROR: Archivo procesado no encontrado.")
        print(f"    Ejecute primero: python run_pipeline_region.py")
        todos_ok = False

    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
        todos_ok = False

    # ------------------------------------------------------------------ #
    # TEST 4: COMPARACIÓN RESUMEN
    # ------------------------------------------------------------------ #
    print_section("Test 4: Resumen de Formatos")
    try:
        df_nuevas = pd.read_csv('data/processed/region/allocations_nuevas_region.csv', sep=';', encoding='utf-8')
        df_antiguas = pd.read_csv('data/processed/region/allocations_antiguas_region.csv', sep=';', encoding='utf-8')

        print(f"\n{'Archivo':40} | {'Formato':8} | {'Filas':8} | {'Cols':6} | {'Instrum':8}")
        print("-" * 80)
        print(f"{'allocations_nuevas_region.csv':40} | {'LONG':8} | {len(df_nuevas):8} | {df_nuevas.shape[1]:6} | {df_nuevas['ID'].nunique():8}")
        print(f"{'allocations_antiguas_region.csv':40} | {'WIDE':8} | {len(df_antiguas):8} | {df_antiguas.shape[1]:6} | {df_antiguas['ID'].nunique():8}")
    except Exception:
        pass  # Ya reportado arriba

    print_section("Resultado Final")
    if todos_ok:
        print("[OK] Todos los formatos de archivos de región son correctos.")
    else:
        print("[!] Algunos formatos presentaron problemas. Revisar más arriba.")

    return todos_ok


if __name__ == "__main__":
    exito = test_formato_archivos_region()
    sys.exit(0 if exito else 1)
