import pandas as pd
import sys
import os

# Añadimos el root al path para poder importar src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extractors.load_instruments import load_df_instruments
from src.extractors.load_allocations import load_allocations_nuevas, load_allocations_antiguas

def print_section(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)

def test_creacion_dataframes():
    # Rutas raw
    pos_path = "data/raw/posiciones.csv"
    instr_path = "data/raw/instruments.csv"
    nuevas_path = "data/raw/allocations_nuevas.csv"
    antiguas_path = "data/raw/allocations_currency.csv"

    # --- SECCION 1: DF_INSTRUMENTS ---
    print_section("Paso 1: Creación de df_instruments")
    print("[...] Cruzando posiciones y maestro...")
    df_instr = load_df_instruments(pos_path, instr_path)
    
    print(f"\n[OK] df_instruments creado con éxito.")
    print(f"    - Filas totales: {len(df_instr)}")
    print(f"    - Columnas: {df_instr.columns.tolist()}")
    print("\nResumen por Tipo instrumento:")
    print(df_instr['Tipo instrumento'].value_counts().to_string())
    print("\nPrimeras 5 filas:")
    print(df_instr.head().to_string(index=False))

    # --- SECCION 2: ALLOCATIONS NUEVAS ---
    print_section("Paso 2: Cruce con Allocations Nuevas")
    print("[...] Realizando cruce por RIC/Isin/Cusip...")
    print("[...] Aplicando cálculo de dominancia y mapeo de monedas...")
    df_nuevas = load_allocations_nuevas(df_instr, nuevas_path)
    
    print(f"\n[OK] allocations_nuevas creado (formato LONG con dominancia).")
    print(f"    - Filas totales: {len(df_nuevas)}")
    print(f"    - Instrumentos únicos: {df_nuevas['ID'].nunique()}")
    print(f"    - Columnas: {list(df_nuevas.columns)}")
    
    # Validar columnas requeridas
    columnas_requeridas = ['ID', 'Nombre', 'instrument', 'class', 'percentage', 'date',
                          'moneda_nueva', 'pct_dominancia_nuevo', 'pct_escalado', 'pct_original']
    columnas_faltantes = [c for c in columnas_requeridas if c not in df_nuevas.columns]
    if columnas_faltantes:
        print(f"\n[!] ADVERTENCIA: Columnas faltantes: {columnas_faltantes}")
    else:
        print(f"\n[[OK]] Todas las columnas requeridas presentes.")
    
    # Distribución de clasificación
    if 'moneda_nueva' in df_nuevas.columns:
        print("\n[i] Distribución de clasificación (Top 10):")
        print(df_nuevas['moneda_nueva'].value_counts().head(10).to_string())
    
    # Validar monedas están en código ISO
    if 'class' in df_nuevas.columns:
        monedas_unicas = df_nuevas['class'].unique()
        print(f"\n[i] Monedas únicas detectadas: {len(monedas_unicas)}")
        print(f"    Ejemplos: {', '.join([str(m) for m in monedas_unicas[:10]])}")
        
        # Verificar que no haya nombres largos (deberían ser códigos ISO de 3 letras)
        nombres_largos = [m for m in monedas_unicas if pd.notna(m) and len(str(m)) > 10]
        if nombres_largos:
            print(f"\n[!] ADVERTENCIA: Monedas sin mapear detectadas ({len(nombres_largos)}):")
            print(f"    {', '.join(nombres_largos[:5])}")
        else:
            print(f"\n[[OK]] Todas las monedas están mapeadas a códigos ISO.")
    
    print("\n[i] Muestra de datos (primeras 10 filas):")
    cols_mostrar = ['ID', 'Nombre', 'class', 'percentage', 'moneda_nueva', 'pct_dominancia_nuevo']
    print(df_nuevas[cols_mostrar].head(10).to_string(index=False))

    # --- SECCION 3: ALLOCATIONS ANTIGUAS ---
    print_section("Paso 3: Cruce con Allocations Antiguas")
    print("[...] Cruzando por ID...")
    df_antiguas = load_allocations_antiguas(df_instr, antiguas_path)
    
    print(f"\n[OK] allocations_antiguas_merged creado.")
    print(f"    - Filas totales: {len(df_antiguas)}")
    print(f"    - Instrumentos únicos con match: {df_antiguas['ID'].nunique()}")
    
    # Identificar columnas que son monedas y tienen algún valor > 0
    # Suponemos que las monedas son columnas después de la 10
    subset_potential = df_antiguas.columns[9:]
    cols_con_datos = []
    for col in subset_potential:
        # Intentamos convertir a numerico por si acaso
        val_sum = pd.to_numeric(df_antiguas[col].astype(str).str.replace(',', '.'), errors='coerce').sum()
        if val_sum > 0:
            cols_con_datos.append(col)
    
    print(f"\n[i] Monedas detectadas con datos en antiguas ({len(cols_con_datos)}):")
    print(f"    {', '.join(cols_con_datos[:15])}{'...' if len(cols_con_datos) > 15 else ''}")

    print("\nMuestra de cruce (ID + Monedas principales):")
    cols_to_show = ['ID', 'Nombre'] + cols_con_datos[:5]
    # Aseguramos que existan las columnas en el df (Nombre puede ser Nombre_x o Nombre_y si hubo colisión)
    actual_cols = [c for c in cols_to_show if c in df_antiguas.columns]
    print(df_antiguas[actual_cols].head(10).to_string(index=False))

    # --- RESUMEN FINAL ---
    print_section("Resumen Final del Pipeline de Datos")
    summary_data = {
        "Dataframe": ["df_instruments", "allocations_nuevas", "allocations_antiguas"],
        "Registros": [len(df_instr), len(df_nuevas), len(df_antiguas)],
        "Instrumentos Únicos": [df_instr['ID'].nunique(), df_nuevas['ID'].nunique(), df_antiguas['ID'].nunique()]
    }
    df_summary = pd.DataFrame(summary_data)
    print(df_summary.to_string(index=False))
    print("\nValidación de Pipeline completada.")

if __name__ == "__main__":
    test_creacion_dataframes()
