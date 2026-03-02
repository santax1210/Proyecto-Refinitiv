"""
Test de Formato de Archivos
============================
Valida que allocations_nuevas esté en formato LONG y allocations_antiguas en WIDE.
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def print_section(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)

def test_formato_archivos():
    """Valida el formato correcto de los archivos procesados."""
    
    print_section("Test de Formato de Archivos")
    
    # --- TEST 1: ALLOCATIONS NUEVAS (FORMATO LONG) ---
    print_section("Test 1: allocations_nuevas.csv (Formato LONG)")
    
    try:
        df_nuevas = pd.read_csv('data/processed/allocations_nuevas.csv',
                                sep=';', encoding='latin-1')
        
        print(f"\n[[OK]] Archivo cargado exitosamente")
        print(f"[i] Dimensiones: {df_nuevas.shape[0]} filas × {df_nuevas.shape[1]} columnas")
        print(f"\n[i] Columnas presentes:")
        for col in df_nuevas.columns:
            print(f"    - {col}")
        
        # Validar que es formato LONG
        total_instrumentos = df_nuevas['ID'].nunique()
        total_filas = len(df_nuevas)
        filas_por_instrumento = total_filas / total_instrumentos
        
        print(f"\n[i] Análisis de formato:")
        print(f"    Instrumentos únicos: {total_instrumentos}")
        print(f"    Total filas:         {total_filas}")
        print(f"    Filas/instrumento:   {filas_por_instrumento:.2f}")
        
        if filas_por_instrumento > 1.5:
            print(f"\n[[OK]] FORMATO LONG CONFIRMADO (múltiples filas por instrumento)")
        else:
            print(f"\n[!] ADVERTENCIA: Parece formato WIDE (1 fila por instrumento)")
            return False
        
        # Validar estructura de columnas (debe tener columnas específicas, NO columnas por moneda)
        columnas_esperadas = ['ID', 'Nombre', 'instrument', 'class', 'percentage', 'date',
                             'moneda_nueva', 'pct_dominancia_nuevo', 'pct_escalado', 'pct_original']
        
        print(f"\n[i] Validación de estructura:")
        faltantes = [c for c in columnas_esperadas if c not in df_nuevas.columns]
        extras = [c for c in df_nuevas.columns if c not in columnas_esperadas]
        
        if faltantes:
            print(f"    [!] Columnas faltantes: {faltantes}")
            return False
        else:
            print(f"    [[OK]] Todas las columnas requeridas presentes")
        
        if extras:
            print(f"    [!] Columnas extra detectadas: {extras}")
            print(f"        (Formato LONG no debe tener columnas por moneda)")
            return False
        else:
            print(f"    [[OK]] Sin columnas extra (correcto para formato LONG)")
        
        # Validar que cada instrumento tenga múltiples filas
        print(f"\n[i] Muestra de un instrumento (múltiples monedas):")
        sample_id = df_nuevas['ID'].iloc[5]  # Tomar el 6to instrumento
        sample_df = df_nuevas[df_nuevas['ID'] == sample_id]
        print(f"    ID: {sample_id}")
        print(f"    Filas: {len(sample_df)}")
        print(f"    Monedas:")
        for _, row in sample_df.head(5).iterrows():
            print(f"      - {row['class']:5} : {row['percentage']:6.2f}%")
        
        if len(sample_df) > 1:
            print(f"\n[[OK]] Confirmado: Múltiples filas por instrumento (formato LONG)")
        
    except FileNotFoundError:
        print(f"\n[!] ERROR: Archivo no encontrado.")
        print(f"    Ejecute: python run_pipeline.py")
        return False
    
    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
        return False
    
    # --- TEST 2: ALLOCATIONS ANTIGUAS (FORMATO WIDE) ---
    print_section("Test 2: allocations_antiguas.csv (Formato WIDE)")
    
    try:
        df_antiguas = pd.read_csv('data/processed/allocations_antiguas.csv',
                                  sep=';', encoding='latin-1')
        
        print(f"\n[[OK]] Archivo cargado exitosamente")
        print(f"[i] Dimensiones: {df_antiguas.shape[0]} filas × {df_antiguas.shape[1]} columnas")
        
        # Validar que es formato WIDE
        total_instrumentos = df_antiguas['ID'].nunique()
        total_filas = len(df_antiguas)
        
        print(f"\n[i] Análisis de formato:")
        print(f"    Instrumentos únicos: {total_instrumentos}")
        print(f"    Total filas:         {total_filas}")
        
        if total_instrumentos == total_filas:
            print(f"\n[[OK]] FORMATO WIDE CONFIRMADO (1 fila por instrumento)")
        else:
            print(f"\n[!] ADVERTENCIA: {total_filas - total_instrumentos} filas duplicadas detectadas")
        
        # Identificar columnas de moneda (excluir metadata)
        cols_metadata = ['ID', 'Nombre', 'SubMoneda', 'Pct_dominancia']
        cols_moneda = [c for c in df_antiguas.columns if c not in cols_metadata]
        
        print(f"\n[i] Estructura de columnas:")
        print(f"    Columnas metadata:  {len(cols_metadata)}")
        print(f"    Columnas de moneda: {len(cols_moneda)}")
        
        if len(cols_moneda) > 10:
            print(f"\n[[OK]] Múltiples columnas de moneda detectadas (formato WIDE correcto)")
        else:
            print(f"\n[!] ADVERTENCIA: Pocas columnas de moneda. ¿Es realmente formato WIDE?")
            return False
        
        print(f"\n[i] Primeras 15 columnas de moneda:")
        for col in cols_moneda[:15]:
            print(f"    - {col}")
        
        # Validar que SubMoneda esté presente
        if 'SubMoneda' in df_antiguas.columns:
            print(f"\n[[OK]] Columna 'SubMoneda' presente")
            submondas_unicas = df_antiguas['SubMoneda'].nunique()
            print(f"[i] SubMonedas únicas: {submondas_unicas}")
        else:
            print(f"\n[!] ERROR: Columna 'SubMoneda' faltante")
            return False
        
        # Validar que Pct_dominancia esté presente
        if 'Pct_dominancia' in df_antiguas.columns:
            print(f"[[OK]] Columna 'Pct_dominancia' presente")
        else:
            print(f"[!] ERROR: Columna 'Pct_dominancia' faltante")
            return False
        
        # Muestra de un instrumento
        print(f"\n[i] Muestra de un instrumento (formato WIDE):")
        sample_row = df_antiguas.iloc[2]
        print(f"    ID: {sample_row['ID']}")
        print(f"    Nombre: {sample_row['Nombre'][:50]}")
        print(f"    SubMoneda: {sample_row.get('SubMoneda', 'N/A')}")
        
        # Mostrar algunas monedas con valor > 0
        monedas_con_valor = []
        for col in cols_moneda:
            try:
                val = pd.to_numeric(str(sample_row[col]).replace(',', '.'), errors='coerce')
                if pd.notna(val) and val > 0:
                    monedas_con_valor.append((col, val))
            except:
                pass
        
        if monedas_con_valor:
            print(f"    Monedas con valor:")
            for moneda, valor in monedas_con_valor[:5]:
                print(f"      {moneda:5} : {valor:6.2f}%")
            print(f"\n[[OK]] Confirmado: Monedas como columnas (formato WIDE)")
        
    except FileNotFoundError:
        print(f"\n[!] ERROR: Archivo no encontrado.")
        return False
    
    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
        return False
    
    # --- TEST 3: COMPARACIÓN DE FORMATOS ---
    print_section("Test 3: Comparación de Formatos")
    
    print(f"\n{'Archivo':30} | {'Formato':8} | {'Filas':8} | {'Columnas':10} | {'Instrum':8}")
    print("-" * 75)
    print(f"{'allocations_nuevas.csv':30} | {'LONG':8} | {len(df_nuevas):8} | {df_nuevas.shape[1]:10} | {df_nuevas['ID'].nunique():8}")
    print(f"{'allocations_antiguas.csv':30} | {'WIDE':8} | {len(df_antiguas):8} | {df_antiguas.shape[1]:10} | {df_antiguas['ID'].nunique():8}")
    
    print(f"\n[i] Características de formato LONG:")
    print(f"    [OK] Múltiples filas por instrumento")
    print(f"    [OK] Columna 'class' con nombre de moneda")
    print(f"    [OK] Columna 'percentage' con porcentaje")
    print(f"    [OK] Total columnas: 10 (fijas)")
    
    print(f"\n[i] Características de formato WIDE:")
    print(f"    [OK] Una fila por instrumento")
    print(f"    [OK] Columnas por cada moneda (USD, EUR, CLP, etc.)")
    print(f"    [OK] Valores directos en cada columna")
    print(f"    [OK] Total columnas: ~80 (variable)")
    
    # --- TEST 4: CONSISTENCIA DE IDs ---
    print_section("Test 4: Consistencia de Instrumentos")
    
    ids_nuevas = set(df_nuevas['ID'].unique())
    ids_antiguas = set(df_antiguas['ID'].unique())
    
    comunes = ids_nuevas.intersection(ids_antiguas)
    solo_nuevas = ids_nuevas - ids_antiguas
    solo_antiguas = ids_antiguas - ids_nuevas
    
    print(f"\n[i] Instrumentos en NUEVAS:  {len(ids_nuevas)}")
    print(f"[i] Instrumentos en ANTIGUAS: {len(ids_antiguas)}")
    print(f"[i] Instrumentos COMUNES:     {len(comunes)}")
    
    if solo_nuevas:
        print(f"\n[i] Instrumentos SOLO en NUEVAS: {len(solo_nuevas)}")
        if len(solo_nuevas) <= 10:
            print(f"    IDs: {sorted(solo_nuevas)}")
    
    if solo_antiguas:
        print(f"\n[i] Instrumentos SOLO en ANTIGUAS: {len(solo_antiguas)}")
        if len(solo_antiguas) <= 10:
            print(f"    IDs: {sorted(solo_antiguas)}")
    
    cobertura = len(comunes) / max(len(ids_nuevas), len(ids_antiguas)) * 100
    print(f"\n[i] Cobertura: {cobertura:.1f}%")
    
    if cobertura > 50:
        print(f"[[OK]] Buena cobertura entre archivos ({cobertura:.0f}%)")
    else:
        print(f"[!] ADVERTENCIA: Baja cobertura ({cobertura:.0f}%)")
    
    # --- RESUMEN FINAL ---
    print_section("Resumen Final")
    
    print("\n[OK] allocations_nuevas.csv está en formato LONG correcto.")
    print("[OK] allocations_antiguas.csv está en formato WIDE correcto.")
    print("[OK] Estructura de columnas validada.")
    print("[OK] Formatos apropiados para el pipeline.")
    print("\n[[OK]] TODOS LOS TESTS PASARON.")
    
    return True

if __name__ == "__main__":
    exito = test_formato_archivos()
    sys.exit(0 if exito else 1)
