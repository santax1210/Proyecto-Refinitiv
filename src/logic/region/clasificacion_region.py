"""
Módulo orquestador principal del pipeline de clasificación de REGIÓN.

Equivalente a src/logic/moneda/clasificacion.py pero para el pipeline de región.
"""
import pandas as pd
from .crear_df_final_region import (
    crear_df_final_region,
    filtrar_balanceados_region,
    filtrar_no_balanceados_region,
    filtrar_cambios_region,
)
from .generar_exports_region import (
    generar_export_balanceados_region,
    generar_export_no_balanceados_region,
    generar_export_sin_datos_region,
)


def ejecutar_pipeline_completo_region(df_instruments, df_nuevas_region, df_antiguas_region):
    """
    Ejecuta el pipeline completo de clasificación y comparación para REGIÓN.

    IMPORTANTE: Los DataFrames de entrada deben venir ya procesados:
    - df_nuevas_region: Con columnas de dominancia calculadas (de load_allocations_nuevas_region)
    - df_antiguas_region: Con Pct_dominancia calculada (de load_allocations_antiguas_region)

    Parámetros:
        df_instruments: DataFrame base con instrumentos filtrados
        df_nuevas_region: DataFrame con allocations nuevas de región procesadas
        df_antiguas_region: DataFrame con allocations antiguas de región procesadas

    Retorna:
        dict con todos los dataframes generados:
            - 'df_nuevas': Allocations nuevas con dominancia
            - 'df_antiguas': Allocations antiguas con Pct_dominancia
            - 'df_final': DataFrame final consolidado
            - 'df_balanceados': Solo instrumentos balanceados
            - 'df_no_balanceados': Solo instrumentos no balanceados
            - 'df_con_cambios': Solo instrumentos con cambios
            - 'exports': dict con los DataFrames de exportación
    """
    print("\n" + "="*70)
    print(" PIPELINE DE CLASIFICACIÓN Y COMPARACIÓN — REGIÓN ".center(70, "="))
    print("="*70)

    # 1. Verificar allocations nuevas
    print("\n[1/3] Verificando allocations nuevas (región)...")
    print(f"  [OK] {len(df_nuevas_region)} registros procesados (formato LONG)")

    if 'region_nueva' in df_nuevas_region.columns:
        # Contar IDs únicos con region_nueva = Balanceado
        df_dom = df_nuevas_region.drop_duplicates(subset=['ID'])
        balanceados = (df_dom['region_nueva'] == 'Balanceado').sum()
        print(f"    - Balanceados: {balanceados}")
        print(f"    - No balanceados: {len(df_dom) - balanceados}")
    else:
        print("  [WARN] Columna 'region_nueva' no encontrada")

    # 2. Verificar allocations antiguas
    print("\n[2/3] Verificando allocations antiguas (región)...")
    print(f"  [OK] {len(df_antiguas_region)} instrumentos procesados")

    if 'Pct_dominancia' in df_antiguas_region.columns:
        sin_datos = (df_antiguas_region['Pct_dominancia'] == 'Sin datos').sum()
        print(f"    - Con datos: {len(df_antiguas_region) - sin_datos}")
        print(f"    - Sin datos: {sin_datos}")
    else:
        print("  [WARN] Columna 'Pct_dominancia' no encontrada")

    # 3. Crear df_final consolidado
    print("\n[3/3] Creando dataframe final consolidado (región)...")
    df_final = crear_df_final_region(df_instruments, df_nuevas_region, df_antiguas_region)
    print(f"  [OK] df_final_region creado con {len(df_final)} registros")

    # 4. Generar vistas filtradas
    print("\n[Extra] Generando vistas filtradas...")
    df_balanceados    = filtrar_balanceados_region(df_final)
    df_no_balanceados = filtrar_no_balanceados_region(df_final)
    df_con_cambios    = filtrar_cambios_region(df_final)

    print(f"  [OK] Balanceados: {len(df_balanceados)} registros")
    print(f"  [OK] No balanceados: {len(df_no_balanceados)} registros")
    print(f"  [OK] Con cambios: {len(df_con_cambios)} registros")

    # 5. Generar exports
    print("\n[Extra] Generando exports con formatos específicos (región)...")
    export_balanceados    = generar_export_balanceados_region(df_final, df_nuevas_region, df_instruments, df_antiguas_region)
    export_no_balanceados = generar_export_no_balanceados_region(df_final)
    export_sin_datos      = generar_export_sin_datos_region(df_instruments, df_nuevas_region)
    export_con_cambios    = generar_export_no_balanceados_region(df_con_cambios) if len(df_con_cambios) > 0 else pd.DataFrame()

    print(f"  [OK] Export balanceados: {len(export_balanceados)} registros")
    print(f"  [OK] Export no balanceados: {len(export_no_balanceados)} registros")
    print(f"  [OK] Export sin datos: {len(export_sin_datos)} registros")
    print(f"  [OK] Export con cambios: {len(export_con_cambios)} registros")

    # Resumen final
    print("\n" + "="*70)
    print(" RESUMEN EJECUTIVO — REGIÓN ".center(70, "="))
    print("="*70)
    print(f"Total instrumentos procesados:  {len(df_final)}")
    if len(df_final) > 0:
        print(f"Instrumentos balanceados:       {len(df_balanceados)} ({len(df_balanceados)/len(df_final)*100:.1f}%)")
        print(f"Instrumentos con cambios:       {len(df_con_cambios)} ({len(df_con_cambios)/len(df_final)*100:.1f}%)")
    print("="*70)

    return {
        'df_nuevas': df_nuevas_region,
        'df_antiguas': df_antiguas_region,
        'df_final': df_final,
        'df_balanceados': df_balanceados,
        'df_no_balanceados': df_no_balanceados,
        'df_con_cambios': df_con_cambios,
        'exports': {
            'balanceados': export_balanceados,
            'no_balanceados': export_no_balanceados,
            'con_cambios': export_con_cambios,
            'sin_datos': export_sin_datos,
        }
    }


# ============================================================================
# TEST MANUAL
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from src.extractors.region.load_instruments_region import load_instruments_region
    from src.extractors.region.load_allocations_region import (
        load_allocations_nuevas_region, load_allocations_antiguas_region
    )

    print("\n" + "="*70)
    print(" TEST: PIPELINE COMPLETO REGIÓN ".center(70, "="))
    print("="*70)

    df_instr   = load_instruments_region()
    df_nuevas  = load_allocations_nuevas_region(df_instr, 'data/raw/region/allocations_nuevas_region.csv')
    df_antiguas = load_allocations_antiguas_region(df_instr, 'data/raw/region/allocations_region.csv')

    resultado = ejecutar_pipeline_completo_region(df_instr, df_nuevas, df_antiguas)
    print(f"\n  [OK] Pipeline completado. df_final: {len(resultado['df_final'])} filas")
