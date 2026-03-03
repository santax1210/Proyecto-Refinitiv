"""
Módulo orquestador principal del pipeline de clasificación.
Integra todos los módulos especializados para generar el df_final.
"""
import pandas as pd
from .crear_df_final import (
    crear_df_final, 
    filtrar_balanceados, 
    filtrar_no_balanceados, 
    filtrar_cambios
)
from .generar_exports import (
    generar_export_balanceados,
    generar_export_no_balanceados,
    generar_export_sin_datos
)


def ejecutar_pipeline_completo(df_instruments, df_nuevas, df_antiguas):
    """
    Ejecuta el pipeline completo de clasificación y comparación.
    
    IMPORTANTE: Los DataFrames de entrada deben venir ya procesados:
    - df_nuevas: Con columnas de dominancia calculadas (de load_allocations_nuevas)
    - df_antiguas: Con Pct_dominancia calculada (de load_allocations_antiguas)
    
    Parámetros:
        df_instruments: DataFrame base con instrumentos filtrados
        df_nuevas: DataFrame con allocations nuevas procesadas (1 fila/instrumento)
        df_antiguas: DataFrame con allocations antiguas procesadas (1 fila/instrumento)
    
    Retorna:
        dict con todos los dataframes generados:
            - 'df_nuevas': Allocations nuevas con dominancia
            - 'df_antiguas': Allocations antiguas con Pct_dominancia
            - 'df_final': DataFrame final consolidado
            - 'df_balanceados': Solo instrumentos balanceados
            - 'df_no_balanceados': Solo instrumentos no balanceados
            - 'df_con_cambios': Solo instrumentos con cambios
    """
    print("\n" + "="*70)
    print(" PIPELINE DE CLASIFICACIÓN Y COMPARACIÓN ".center(70, "="))
    print("="*70)
    
    # 1. Verificar allocations nuevas
    print("\n[1/3] Verificando allocations nuevas...")
    print(f"  [OK] {len(df_nuevas)} instrumentos procesados")
    
    if 'moneda_nueva' in df_nuevas.columns:
        balanceados = (df_nuevas['moneda_nueva'] == 'Balanceado').sum()
        print(f"    - Balanceados: {balanceados}")
        print(f"    - No balanceados: {len(df_nuevas) - balanceados}")
    else:
        print("  [WARN] ADVERTENCIA: Columna 'moneda_nueva' no encontrada")
    
    # 2. Verificar allocations antiguas
    print("\n[2/3] Verificando allocations antiguas...")
    print(f"  [OK] {len(df_antiguas)} instrumentos procesados")
    
    if 'Pct_dominancia' in df_antiguas.columns:
        sin_datos = (df_antiguas['Pct_dominancia'] == 'Sin datos').sum()
        print(f"    - Con datos: {len(df_antiguas) - sin_datos}")
        print(f"    - Sin datos: {sin_datos}")
    else:
        print("  [WARN] ADVERTENCIA: Columna 'Pct_dominancia' no encontrada")
    
    # 3. Crear df_final consolidado
    print("\n[3/3] Creando dataframe final consolidado...")
    df_final = crear_df_final(df_instruments, df_nuevas, df_antiguas)
    print(f"  [OK] df_final creado con {len(df_final)} registros")
    
    # 4. Generar vistas filtradas
    print("\n[Extra] Generando vistas filtradas...")
    df_balanceados = filtrar_balanceados(df_final)
    df_no_balanceados = filtrar_no_balanceados(df_final)
    df_con_cambios = filtrar_cambios(df_final)
    
    print(f"  [OK] Balanceados: {len(df_balanceados)} registros")
    print(f"  [OK] No balanceados: {len(df_no_balanceados)} registros")
    print(f"  [OK] Con cambios: {len(df_con_cambios)} registros")
    
    # 5. Generar exports con formatos específicos
    print("\n[Extra] Generando exports con formatos específicos...")
    export_balanceados = generar_export_balanceados(df_final, df_nuevas, df_instruments, df_antiguas)
    export_no_balanceados = generar_export_no_balanceados(df_final)
    export_sin_datos = generar_export_sin_datos(df_instruments, df_nuevas)
    
    print(f"  [OK] Export balanceados: {len(export_balanceados)} registros")
    print(f"  [OK] Export no balanceados: {len(export_no_balanceados)} registros")
    print(f"  [OK] Export sin datos: {len(export_sin_datos)} registros")
    
    # 6. Generar export de con_cambios (mismo formato que no_balanceados)
    export_con_cambios = generar_export_no_balanceados(df_con_cambios) if len(df_con_cambios) > 0 else pd.DataFrame()
    print(f"  [OK] Export con cambios: {len(export_con_cambios)} registros")
    
    # Resumen final
    print("\n" + "="*70)
    print(" RESUMEN EJECUTIVO ".center(70, "="))
    print("="*70)
    print(f"Total instrumentos procesados:  {len(df_final)}")
    if len(df_final) > 0:
        print(f"Instrumentos balanceados:       {len(df_balanceados)} ({len(df_balanceados)/len(df_final)*100:.1f}%)")
        print(f"Instrumentos con cambios:       {len(df_con_cambios)} ({len(df_con_cambios)/len(df_final)*100:.1f}%)")
    print("="*70)
    
    return {
        'df_nuevas': df_nuevas,
        'df_antiguas': df_antiguas,
        'df_final': df_final,
        'df_balanceados': df_balanceados,
        'df_no_balanceados': df_no_balanceados,
        'df_con_cambios': df_con_cambios,
        'exports': {
            'balanceados': export_balanceados,
            'no_balanceados': export_no_balanceados,
            'con_cambios': export_con_cambios,
            'sin_datos': export_sin_datos
        }
    }


# ============================================================================
# BLOQUE DE TEST Y EJECUCIÓN MANUAL
# ============================================================================

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, '.')
    from src.extractors.load_instruments import load_df_instruments
    from src.extractors.load_allocations import load_allocations_nuevas, load_allocations_antiguas

    print("\n" + "="*70)
    print(" INICIO DEL PIPELINE DE CLASIFICACIÓN ".center(70, "="))
    print("="*70)
    
    # FASE 1: CARGAR DATOS BASE
    print("\n[Fase 1/3] Cargando datos base...")
    df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
    print(f"  [OK] df_instruments: {len(df_instr)} instrumentos")
    
    # FASE 2: CARGAR ALLOCATIONS (YA PROCESADAS CON DOMINANCIA)
    print("\n[Fase 2/3] Cargando allocations (con dominancia calculada)...")
    df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
    print(f"  [OK] Allocations nuevas: {len(df_nuevas)} registros (formato long)")
    
    df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
    print(f"  [OK] Allocations antiguas: {len(df_antiguas)} instrumentos")
    
    # FASE 3: EJECUTAR PIPELINE COMPLETO
    print("\n[Fase 3/3] Ejecutando pipeline de clasificación...")
    resultados = ejecutar_pipeline_completo(
        df_instruments=df_instr,
        df_nuevas=df_nuevas,
        df_antiguas=df_antiguas
    )
    
    # GUARDAR RESULTADOS
    print("\n" + "="*70)
    print(" GUARDANDO RESULTADOS ".center(70, "="))
    print("="*70)
    
    os.makedirs('data/processed', exist_ok=True)
    
    # Guardar df_final principal
    resultados['df_final'].to_csv(
        'data/processed/df_final.csv',
        index=False,
        sep=';',
        encoding='latin-1'
    )
    print("  💾 df_final.csv")
    
    # Guardar vistas filtradas
    resultados['df_balanceados'].to_csv(
        'data/processed/df_final_balanceados.csv',
        index=False,
        sep=';',
        encoding='latin-1'
    )
    print("  💾 df_final_balanceados.csv")
    
    resultados['df_no_balanceados'].to_csv(
        'data/processed/df_final_no_balanceados.csv',
        index=False,
        sep=';',
        encoding='latin-1'
    )
    print("  💾 df_final_no_balanceados.csv")
    
    resultados['df_con_cambios'].to_csv(
        'data/processed/df_final_con_cambios.csv',
        index=False,
        sep=';',
        encoding='latin-1'
    )
    print("  💾 df_final_con_cambios.csv")
    
    # PREVIEW DEL DF_FINAL
    print("\n" + "="*70)
    print(" PREVIEW DEL DF_FINAL ".center(70, "="))
    print("="*70)
    
    cols_preview = ['Nombre', 'ID', 'moneda_nueva', 'moneda_antigua', 'Cambio']
    cols_disponibles = [c for c in cols_preview if c in resultados['df_final'].columns]
    
    if cols_disponibles:
        print("\nPrimeros 10 registros:")
        print(resultados['df_final'][cols_disponibles].head(10).to_string(index=False))
    
    print("\n" + "="*70)
    print(" PIPELINE COMPLETADO EXITOSAMENTE ".center(70, "="))
    print("="*70)
