"""
Test de Creación de DataFrames — REGIÓN
=========================================
Valida la creación y estructura de todos los DataFrames del pipeline de región:
  - df_instruments
  - allocations_nuevas_region (LONG con dominancia)
  - allocations_antiguas_region (WIDE con Pct_dominancia + Base Region:)
  - df_final_region (consolidado)

Diferencias vs moneda:
- No hay columna 'class', sino 'region'
- No hay mapeo ISO (regiones se mantienen tal cual normalizado)
- 'Base Region:' en lugar de 'Moneda:'
- region_antigua derivada de Pct_dominancia (no de SubMoneda)
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.extractors.region.load_instruments_region import load_instruments_region
from src.extractors.region.load_allocations_region import (
    load_allocations_nuevas_region,
    load_allocations_antiguas_region,
)
from src.logic.region.crear_df_final_region import crear_df_final_region


def print_section(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)


def test_creacion_dataframes_region():
    pos_path      = "data/raw/posiciones.csv"
    instr_path    = "data/raw/instruments.csv"
    nuevas_path   = "data/raw/region/allocations_nuevas_region.csv"
    antiguas_path = "data/raw/region/allocations_region.csv"

    # ------------------------------------------------------------------ #
    # PASO 1: df_instruments
    # ------------------------------------------------------------------ #
    print_section("Paso 1: Creación de df_instruments (región)")
    print("[...] Cargando instrumentos...")

    df_instr = load_instruments_region(pos_path, instr_path)

    print(f"\n[OK] df_instruments creado: {len(df_instr)} filas")
    print(f"    Columnas: {df_instr.columns.tolist()}")

    # Validar columna ID
    assert 'ID' in df_instr.columns, "[!] ERROR: Columna 'ID' faltante en df_instruments"
    id_dtype = df_instr['ID'].dtype
    print(f"\n[i] Tipo de dato de 'ID': {id_dtype}")
    if id_dtype in ('int64', 'Int64', 'int32'):
        print(f"    [OK] Tipo correcto (int)")
    else:
        print(f"    [!] ADVERTENCIA: Tipo de ID es '{id_dtype}' (esperado int)")

    print("\n[i] Distribución por Tipo instrumento:")
    print(df_instr['Tipo instrumento'].value_counts().to_string())
    print("\n[i] Primeras 5 filas:")
    print(df_instr.head().to_string(index=False))

    # ------------------------------------------------------------------ #
    # PASO 2: allocations nuevas (región) — LONG con dominancia
    # ------------------------------------------------------------------ #
    print_section("Paso 2: Allocations Nuevas Región (WIDE → LONG + dominancia)")
    print("[...] Cargando y procesando allocations nuevas...")

    df_nuevas = load_allocations_nuevas_region(df_instr, nuevas_path, umbral=0.9)

    print(f"\n[OK] allocations_nuevas_region creado (LONG).")
    print(f"    Filas:                {len(df_nuevas)}")
    print(f"    Instrumentos únicos:  {df_nuevas['ID'].nunique()}")
    print(f"    Columnas:             {list(df_nuevas.columns)}")

    # Columnas requeridas
    cols_requeridas = ['ID', 'Nombre', 'instrument', 'region', 'percentage',
                       'tipo_id', 'region_nueva', 'pct_dominancia_nueva',
                       'pct_escalado', 'pct_original']
    faltantes = [c for c in cols_requeridas if c not in df_nuevas.columns]
    if faltantes:
        print(f"\n[!] Columnas faltantes en nuevas: {faltantes}")
    else:
        print(f"\n[[OK]] Todas las columnas requeridas presentes")

    # Validar que IDs son subconjunto de instruments
    ids_instr = set(df_instr['ID'].unique())
    ids_nuevas = set(df_nuevas['ID'].unique())
    orphans = ids_nuevas - ids_instr
    if orphans:
        print(f"\n[!] ERROR: {len(orphans)} IDs de nuevas no existen en df_instruments")
    else:
        cobertura = len(ids_nuevas) / len(ids_instr) * 100 if ids_instr else 0
        print(f"    [OK] Cobertura: {len(ids_nuevas)}/{len(ids_instr)} instrumentos ({cobertura:.1f}%)")

    # Distribución de clasificación
    if 'region_nueva' in df_nuevas.columns:
        distrib = df_nuevas.drop_duplicates('ID')['region_nueva'].value_counts()
        print(f"\n[i] Distribución de region_nueva (Top 10):")
        print(distrib.head(10).to_string())

    # Muestra de datos
    print("\n[i] Muestra (primeras 10 filas):")
    cols_show = [c for c in ['ID', 'Nombre', 'region', 'percentage', 'region_nueva', 'pct_dominancia_nueva'] if c in df_nuevas.columns]
    print(df_nuevas[cols_show].head(10).to_string(index=False))

    # ------------------------------------------------------------------ #
    # PASO 3: allocations antiguas (región) — WIDE con Base Region:
    # ------------------------------------------------------------------ #
    print_section("Paso 3: Allocations Antiguas Región (WIDE + Base Region:)")
    print("[...] Cargando y procesando allocations antiguas...")

    df_antiguas = load_allocations_antiguas_region(df_instr, antiguas_path)

    print(f"\n[OK] allocations_antiguas_region creado.")
    print(f"    Filas:                {len(df_antiguas)}")
    print(f"    Instrumentos únicos:  {df_antiguas['ID'].nunique()}")
    print(f"    Columnas:             {df_antiguas.columns.tolist()}")

    # Validar IDs
    ids_antiguas = set(df_antiguas['ID'].unique())
    orphans_ant = ids_antiguas - ids_instr
    if orphans_ant:
        print(f"\n[!] ERROR: {len(orphans_ant)} IDs de antiguas no existen en df_instruments")
    else:
        cobertura_ant = len(ids_antiguas) / len(ids_instr) * 100 if ids_instr else 0
        print(f"    [OK] Cobertura: {len(ids_antiguas)}/{len(ids_instr)} ({cobertura_ant:.1f}%)")

    # Columna Base Region:
    if 'Base Region:' in df_antiguas.columns:
        print(f"\n[[OK]] Columna 'Base Region:' presente")
        print(f"[i] Valores únicos en 'Base Region:': {df_antiguas['Base Region:'].value_counts().head(5).to_dict()}")
    else:
        print(f"\n[!] ERROR: Columna 'Base Region:' no encontrada")

    # Validar Pct_dominancia
    if 'Pct_dominancia' in df_antiguas.columns:
        sin_datos = (df_antiguas['Pct_dominancia'] == 'Sin datos').sum()
        con_datos = len(df_antiguas) - sin_datos
        print(f"[[OK]] Columna 'Pct_dominancia' presente: {con_datos} con datos, {sin_datos} sin datos")
        sample = df_antiguas['Pct_dominancia'].dropna().head(5).tolist()
        print(f"[i] Ejemplos: {sample}")
    else:
        print(f"\n[!] ERROR: 'Pct_dominancia' faltante")

    # ------------------------------------------------------------------ #
    # PASO 4: df_final_region
    # ------------------------------------------------------------------ #
    print_section("Paso 4: Creación de df_final_region")
    print("[...] Consolidando dataframes...")

    df_final = crear_df_final_region(df_instr, df_nuevas, df_antiguas)

    print(f"\n[OK] df_final_region creado: {len(df_final)} filas")
    print(f"    Columnas: {df_final.columns.tolist()}")

    # Columnas requeridas
    cols_final = ['ID', 'Nombre', 'Tipo instrumento', 'region_antigua', 'region_nueva',
                  'pct_dominancia_nueva', 'pct_dominancia_antigua', 'Cambio', 'Estado']
    faltantes_final = [c for c in cols_final if c not in df_final.columns]
    if faltantes_final:
        print(f"\n[!] Columnas faltantes en df_final: {faltantes_final}")
    else:
        print(f"\n[[OK]] Todas las columnas requeridas en df_final")

    # Validar Cambio
    if 'Cambio' in df_final.columns:
        dist_cambio = df_final['Cambio'].value_counts()
        print(f"\n[i] Distribución de Cambio:")
        print(dist_cambio.to_string())

    # Validar Estado
    if 'Estado' in df_final.columns:
        dist_estado = df_final['Estado'].value_counts()
        print(f"\n[i] Distribución de Estado:")
        print(dist_estado.to_string())

    # Validar Hellinger
    if 'distancia_hellinger' in df_final.columns:
        n_non_null = df_final['distancia_hellinger'].notna().sum()
        print(f"\n[i] Distancia Hellinger: {n_non_null}/{len(df_final)} valores calculados")

    # ------------------------------------------------------------------ #
    # RESUMEN
    # ------------------------------------------------------------------ #
    print_section("Resumen Final del Pipeline de Datos — REGIÓN")

    summary = {
        "DataFrame":            ["df_instruments", "allocations_nuevas_region", "allocations_antiguas_region", "df_final_region"],
        "Registros":            [len(df_instr), len(df_nuevas), len(df_antiguas), len(df_final)],
        "Instrumentos Únicos":  [df_instr['ID'].nunique(), df_nuevas['ID'].nunique(),
                                  df_antiguas['ID'].nunique(), df_final['ID'].nunique()],
    }
    print(pd.DataFrame(summary).to_string(index=False))
    print("\n[[OK]] Validación de pipeline de región completada.")
    return True


if __name__ == "__main__":
    exito = test_creacion_dataframes_region()
    sys.exit(0 if exito else 1)
