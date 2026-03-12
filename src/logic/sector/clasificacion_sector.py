import pandas as pd

from .crear_df_final_sector import (
    crear_df_final_sector,
    filtrar_balanceados_sector,
    filtrar_no_balanceados_sector,
    filtrar_cambios_sector,
)
from .generar_exports_sector import (
    generar_export_balanceados_sector,
    generar_export_no_balanceados_sector,
    generar_export_sin_datos_sector,
)


def ejecutar_pipeline_completo_sector(df_instruments, df_nuevas_sector, df_antiguas_sector):
    print('\n' + '=' * 70)
    print(' PIPELINE DE CLASIFICACIÓN Y COMPARACIÓN — SECTOR '.center(70, '='))
    print('=' * 70)

    print('\n[1/3] Verificando allocations nuevas (sector)...')
    print(f"  [OK] {len(df_nuevas_sector)} registros procesados (formato LONG)")
    if 'sector_nueva' in df_nuevas_sector.columns:
        df_dom = df_nuevas_sector.drop_duplicates(subset=['ID'])
        balanceados = (df_dom['sector_nueva'] == 'Balanceado').sum()
        print(f"    - Balanceados: {balanceados}")
        print(f"    - No balanceados: {len(df_dom) - balanceados}")

    print('\n[2/3] Verificando allocations antiguas (sector)...')
    print(f"  [OK] {len(df_antiguas_sector)} instrumentos procesados")
    if 'Pct_dominancia' in df_antiguas_sector.columns:
        sin_datos = (df_antiguas_sector['Pct_dominancia'] == 'Sin datos').sum()
        print(f"    - Con datos: {len(df_antiguas_sector) - sin_datos}")
        print(f"    - Sin datos: {sin_datos}")

    print('\n[3/3] Creando dataframe final consolidado (sector)...')
    df_final = crear_df_final_sector(df_instruments, df_nuevas_sector, df_antiguas_sector)
    print(f"  [OK] df_final_sector creado con {len(df_final)} registros")

    print('\n[Extra] Generando vistas filtradas...')
    df_balanceados = filtrar_balanceados_sector(df_final)
    df_no_balanceados = filtrar_no_balanceados_sector(df_final)
    df_con_cambios = filtrar_cambios_sector(df_final)
    print(f"  [OK] Balanceados: {len(df_balanceados)} registros")
    print(f"  [OK] No balanceados: {len(df_no_balanceados)} registros")
    print(f"  [OK] Con cambios: {len(df_con_cambios)} registros")

    print('\n[Extra] Generando exports con formatos específicos (sector)...')
    export_balanceados = generar_export_balanceados_sector(df_final, df_nuevas_sector, df_instruments, df_antiguas_sector)
    export_no_balanceados = generar_export_no_balanceados_sector(df_final)
    export_sin_datos = generar_export_sin_datos_sector(df_instruments, df_nuevas_sector)
    export_con_cambios = generar_export_no_balanceados_sector(df_con_cambios) if len(df_con_cambios) > 0 else pd.DataFrame()

    print(f"  [OK] Export balanceados: {len(export_balanceados)} registros")
    print(f"  [OK] Export no balanceados: {len(export_no_balanceados)} registros")
    print(f"  [OK] Export sin datos: {len(export_sin_datos)} registros")
    print(f"  [OK] Export con cambios: {len(export_con_cambios)} registros")

    return {
        'df_nuevas': df_nuevas_sector,
        'df_antiguas': df_antiguas_sector,
        'df_final': df_final,
        'df_balanceados': df_balanceados,
        'df_no_balanceados': df_no_balanceados,
        'df_con_cambios': df_con_cambios,
        'exports': {
            'balanceados': export_balanceados,
            'no_balanceados': export_no_balanceados,
            'con_cambios': export_con_cambios,
            'sin_datos': export_sin_datos,
        },
    }
