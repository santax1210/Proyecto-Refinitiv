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
    # VALIDACIÓN DE TIPOS DE DATOS Y MERGES (unificado)
    print("\n[i] Validando tipos de datos y merges...")
    dataframes = {
        'df_instruments': df_instr
    }
    tipos_correctos = True
    for nombre, df in dataframes.items():
        if 'ID' in df.columns:
            id_dtype = df['ID'].dtype
            print(f"  {nombre:25} → dtype: {id_dtype}")
            if id_dtype not in ['int64', 'Int64', 'int32', 'Int32']:
                print(f"      [X] ERROR: Tipo incorrecto (debe ser int64)")
                tipos_correctos = False
            else:
                print(f"      [OK] Tipo correcto")
        else:
            print(f"  [X] ERROR: {nombre} no tiene columna 'ID'")
            tipos_correctos = False
    if not tipos_correctos:
        return False
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
    # VALIDACIÓN DE TIPOS DE DATOS Y MERGES (unificado)
    print("\n[i] Validando tipos de datos y merges...")
    dataframes['allocations_nuevas'] = df_nuevas
    tipos_correctos = True
    for nombre, df in dataframes.items():
        if 'ID' in df.columns:
            id_dtype = df['ID'].dtype
            print(f"  {nombre:25} → dtype: {id_dtype}")
            if id_dtype not in ['int64', 'Int64', 'int32', 'Int32']:
                print(f"      [X] ERROR: Tipo incorrecto (debe ser int64)")
                tipos_correctos = False
            else:
                print(f"      [OK] Tipo correcto")
        else:
            print(f"  [X] ERROR: {nombre} no tiene columna 'ID'")
            tipos_correctos = False
    if not tipos_correctos:
        return False
    # VALIDACIÓN DE MERGE/CRUCE
    ids_instruments = set(df_instr['ID'].unique())
    ids_nuevas = set(df_nuevas['ID'].unique())
    if ids_nuevas.issubset(ids_instruments):
        print(f"    [OK] Todos los IDs de allocations_nuevas están en df_instruments")
        print(f"    [OK] Cobertura: {len(ids_nuevas)}/{len(ids_instruments)} instrumentos ({len(ids_nuevas)/len(ids_instruments)*100:.1f}%)")
    else:
        ids_huerfanos = ids_nuevas - ids_instruments
        print(f"    [!] ERROR: {len(ids_huerfanos)} IDs de allocations_nuevas no están en df_instruments")
        return False
    
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
    # VALIDACIÓN DE TIPOS DE DATOS Y MERGES (unificado)
    dataframes['allocations_antiguas'] = df_antiguas
    tipos_correctos = True
    for nombre, df in dataframes.items():
        if 'ID' in df.columns:
            id_dtype = df['ID'].dtype
            print(f"  {nombre:25} → dtype: {id_dtype}")
            if id_dtype not in ['int64', 'Int64', 'int32', 'Int32']:
                print(f"      [X] ERROR: Tipo incorrecto (debe ser int64)")
                tipos_correctos = False
            else:
                print(f"      [OK] Tipo correcto")
        else:
            print(f"  [X] ERROR: {nombre} no tiene columna 'ID'")
            tipos_correctos = False
    if not tipos_correctos:
        return False
    # VALIDACIÓN DE MERGE/CRUCE
    ids_instruments = set(df_instr['ID'].unique())
    ids_antiguas = set(df_antiguas['ID'].unique())
    if ids_antiguas.issubset(ids_instruments):
        print(f"    [OK] Todos los IDs de allocations_antiguas están en df_instruments")
        print(f"    [OK] Cobertura: {len(ids_antiguas)}/{len(ids_instruments)} instrumentos ({len(ids_antiguas)/len(ids_instruments)*100:.1f}%)")
    else:
        ids_huerfanos = ids_antiguas - ids_instruments
        print(f"    [!] ERROR: {len(ids_huerfanos)} IDs de allocations_antiguas no están en df_instruments")
        return False
    # VALIDACIÓN DE PCT_DOMINANCIA
    print("\n[i] Validando columna Pct_dominancia...")
    if 'Pct_dominancia' in df_antiguas.columns:
        valores_validos = df_antiguas['Pct_dominancia'].notna().sum()
        valores_sin_datos = (df_antiguas['Pct_dominancia'] == 'Sin datos').sum()
        valores_con_formato = df_antiguas['Pct_dominancia'].str.contains(r'^[A-Z]{3} \d+\.\d+%$', na=False, regex=True).sum()
        print(f"    [OK] Columna 'Pct_dominancia' existe")
        print(f"    [OK] Valores válidos: {valores_validos}/{len(df_antiguas)}")
        print(f"    [OK] Con formato correcto (MONEDA XX.XX%): {valores_con_formato}")
        print(f"    [i] Sin datos: {valores_sin_datos}")
        if valores_validos == 0:
            print(f"    [!] ERROR: Pct_dominancia está completamente vacía")
            return False
    else:
        print(f"    [!] ERROR: Columna 'Pct_dominancia' no existe")
        return False
    
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
    print("\n[[OK]] Validación de Pipeline completada exitosamente.")
    return True

if __name__ == "__main__":
    exito = test_creacion_dataframes()
    sys.exit(0 if exito else 1)
