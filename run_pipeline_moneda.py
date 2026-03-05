"""
Pipeline de validación de Allocations de MONEDA.

Orquesta todo el flujo desde la carga de datos hasta la generación
de reportes finales para allocations de moneda (classif == 'currency').

Uso:
    python run_pipeline_moneda.py
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.extractors.moneda.load_instruments import load_df_instruments
from src.extractors.moneda.load_allocations import load_allocations_nuevas, load_allocations_antiguas
from src.logic.moneda.clasificacion import ejecutar_pipeline_completo

PROCESSED_DIR = 'data/processed/moneda'
EXPORTS_DIR = 'data/exports/moneda'


def main():
    print("\n" + "="*80)
    print(" PIPELINE DE VALIDACIÓN — ALLOCATIONS DE MONEDA ".center(80, "="))
    print(f" Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(80))
    print("="*80)

    pos_path      = 'data/raw/posiciones.csv'
    instr_path    = 'data/raw/instruments.csv'
    nuevas_path   = 'data/raw/allocations_nuevas.csv'
    antiguas_path = 'data/raw/allocations_currency.csv'

    archivos_requeridos = [pos_path, instr_path, nuevas_path, antiguas_path]
    archivos_faltantes = [f for f in archivos_requeridos if not os.path.exists(f)]

    if archivos_faltantes:
        print("\n[ERROR] No se encontraron los siguientes archivos:")
        for archivo in archivos_faltantes:
            print(f"  - {archivo}")
        print("\nAsegúrate de que los archivos raw están en data/raw/")
        return 1

    try:
        # FASE 1: CARGA DE DATOS
        print("\n" + "─"*80)
        print("FASE 1: CARGA Y FILTRADO DE DATOS")
        print("─"*80)

        print("\n[1.1] Cargando y filtrando instrumentos...")
        df_instruments = load_df_instruments(pos_path, instr_path)
        print(f"  [OK] {len(df_instruments)} instrumentos cargados")

        print("\n[1.2] Cargando allocations nuevas (moneda)...")
        df_nuevas = load_allocations_nuevas(df_instruments, nuevas_path, umbral=0.9)
        print(f"  [OK] {len(df_nuevas)} registros procesados")

        print("\n[1.3] Cargando allocations antiguas (moneda)...")
        df_antiguas = load_allocations_antiguas(df_instruments, antiguas_path)
        print(f"  [OK] {len(df_antiguas)} instrumentos con datos históricos")

        # FASE 2: CLASIFICACIÓN
        print("\n" + "─"*80)
        print("FASE 2: PROCESAMIENTO Y CLASIFICACIÓN")
        print("─"*80)

        resultados = ejecutar_pipeline_completo(
            df_instruments=df_instruments,
            df_nuevas=df_nuevas,
            df_antiguas=df_antiguas
        )

        # FASE 3: EXPORTACIÓN
        print("\n" + "─"*80)
        print("FASE 3: EXPORTACIÓN DE RESULTADOS")
        print("─"*80)

        os.makedirs(PROCESSED_DIR, exist_ok=True)
        os.makedirs(EXPORTS_DIR, exist_ok=True)

        print("\n[3.1] Guardando archivos procesados...")

        df_instruments.to_csv(
            f'{PROCESSED_DIR}/df_instruments.csv',
            index=False, sep=';', encoding='latin-1'
        )
        print(f"  [OK] {PROCESSED_DIR}/df_instruments.csv")

        df_nuevas.to_csv(
            f'{PROCESSED_DIR}/allocations_nuevas.csv',
            index=False, sep=';', encoding='latin-1'
        )
        print(f"  [OK] {PROCESSED_DIR}/allocations_nuevas.csv")

        resultados['df_final'].to_csv(
            f'{PROCESSED_DIR}/df_final.csv',
            index=False, sep=';', encoding='latin-1'
        )
        print(f"  [OK] {PROCESSED_DIR}/df_final.csv")

        resultados['df_antiguas'].to_csv(
            f'{PROCESSED_DIR}/allocations_antiguas.csv',
            index=False, sep=';', encoding='latin-1'
        )
        print(f"  [OK] {PROCESSED_DIR}/allocations_antiguas.csv")

        print("\n[3.2] Guardando archivos de exportación final...")

        for nombre, key in [
            ('export_balanceados.csv',    'balanceados'),
            ('export_no_balanceados.csv', 'no_balanceados'),
            ('export_con_cambios.csv',    'con_cambios'),
            ('export_sin_datos.csv',      'sin_datos'),
        ]:
            df = resultados['exports'][key]
            df.to_csv(f'{EXPORTS_DIR}/{nombre}', index=False, sep=';', encoding='latin-1')
            print(f"  [OK] {EXPORTS_DIR}/{nombre} ({len(df)} registros)")

        # RESUMEN FINAL
        print("\n" + "="*80)
        print(" RESUMEN EJECUTIVO — MONEDA ".center(80, "="))
        print("="*80)

        df_final = resultados['df_final']
        total         = len(df_final)
        balanceados   = len(resultados['exports']['balanceados'])
        no_balanceados = len(resultados['exports']['no_balanceados'])
        con_cambios   = len(resultados['exports']['con_cambios'])
        sin_datos     = len(resultados['exports']['sin_datos'])

        print(f"\n  Total instrumentos procesados:  {total}")
        print(f"  Balanceados:                    {balanceados} ({balanceados/total*100:.1f}%)")
        print(f"  No balanceados:                 {no_balanceados} ({no_balanceados/total*100:.1f}%)")
        print(f"  Con cambios:                    {con_cambios} ({con_cambios/total*100:.1f}%)")
        print(f"  Sin datos:                      {sin_datos}")

        if 'moneda_nueva' in df_final.columns:
            print("\n  Distribución de monedas nuevas (top 5):")
            dist = df_final[df_final['moneda_nueva'] != 'Balanceado']['moneda_nueva'].value_counts().head(5)
            for moneda, count in dist.items():
                print(f"    - {moneda}: {count} instrumentos")

        print("\n" + "="*80)
        print(" [EXITOSO] PIPELINE MONEDA COMPLETADO ".center(80, "="))
        print("="*80)
        print(f"\n  Archivos procesados: {PROCESSED_DIR}/")
        print(f"  Exports finales:     {EXPORTS_DIR}/")
        return 0

    except Exception as e:
        print(f"\n[ERROR] Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
