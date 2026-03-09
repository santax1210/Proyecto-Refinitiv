"""
Pipeline de validación de Allocations de REGIÓN.

Orquesta todo el flujo desde la carga de datos hasta la generación
de reportes finales para allocations de región.

Uso:
    python run_pipeline_region.py
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.extractors.region.load_instruments_region import load_instruments_region
from src.extractors.region.load_allocations_region import (
    load_allocations_nuevas_region,
    load_allocations_antiguas_region,
)
from src.logic.region.clasificacion_region import ejecutar_pipeline_completo_region

PROCESSED_DIR = 'data/processed/region'
EXPORTS_DIR   = 'data/exports/region'


def main():
    print("\n" + "="*80)
    print(" PIPELINE DE VALIDACIÓN — ALLOCATIONS DE REGIÓN ".center(80, "="))
    print(f" Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(80))
    print("="*80)

    # Archivos raw específicos de región
    pos_path      = 'data/raw/posiciones.csv'
    instr_path    = 'data/raw/instruments.csv'
    nuevas_path   = 'data/raw/region/allocations_nuevas_region.csv'
    antiguas_path = 'data/raw/region/allocations_region.csv'

    archivos_requeridos = [pos_path, instr_path, nuevas_path, antiguas_path]
    archivos_faltantes = [f for f in archivos_requeridos if not os.path.exists(f)]

    if archivos_faltantes:
        print("\n[ERROR] No se encontraron los siguientes archivos:")
        for archivo in archivos_faltantes:
            print(f"  - {archivo}")
        print("\nAsegúrate de que los archivos raw están en data/raw/ y data/raw/region/")
        return 1

    try:
        # FASE 1: CARGA DE DATOS
        print("\n" + "─"*80)
        print("FASE 1: CARGA Y FILTRADO DE DATOS")
        print("─"*80)

        print("\n[1.1] Cargando y filtrando instrumentos...")
        df_instruments = load_instruments_region(pos_path, instr_path)
        print(f"  [OK] {len(df_instruments)} instrumentos cargados")

        print("\n[1.2] Cargando allocations nuevas de región (formato WIDE → LONG)...")
        df_nuevas = load_allocations_nuevas_region(df_instruments, nuevas_path, umbral=0.9)
        print(f"  [OK] {len(df_nuevas)} registros procesados (formato LONG)")

        print("\n[1.3] Cargando allocations antiguas de región...")
        df_antiguas = load_allocations_antiguas_region(df_instruments, antiguas_path)
        print(f"  [OK] {len(df_antiguas)} instrumentos con datos históricos")

        # FASE 2: CLASIFICACIÓN
        print("\n" + "─"*80)
        print("FASE 2: PROCESAMIENTO Y CLASIFICACIÓN")
        print("─"*80)

        resultados = ejecutar_pipeline_completo_region(
            df_instruments=df_instruments,
            df_nuevas_region=df_nuevas,
            df_antiguas_region=df_antiguas,
        )

        # FASE 3: EXPORTACIÓN
        print("\n" + "─"*80)
        print("FASE 3: EXPORTACIÓN DE RESULTADOS")
        print("─"*80)

        os.makedirs(PROCESSED_DIR, exist_ok=True)
        os.makedirs(EXPORTS_DIR,   exist_ok=True)

        print("\n[3.1] Guardando archivos procesados...")

        df_instruments.to_csv(
            f'{PROCESSED_DIR}/df_instruments.csv',
            index=False, sep=';', encoding='utf-8'
        )
        print(f"  [OK] {PROCESSED_DIR}/df_instruments.csv")

        df_nuevas.to_csv(
            f'{PROCESSED_DIR}/allocations_nuevas_region.csv',
            index=False, sep=';', encoding='utf-8'
        )
        print(f"  [OK] {PROCESSED_DIR}/allocations_nuevas_region.csv")

        resultados['df_final'].to_csv(
            f'{PROCESSED_DIR}/df_final_region.csv',
            index=False, sep=';', encoding='utf-8'
        )
        print(f"  [OK] {PROCESSED_DIR}/df_final_region.csv")

        resultados['df_antiguas'].to_csv(
            f'{PROCESSED_DIR}/allocations_antiguas_region.csv',
            index=False, sep=';', encoding='utf-8'
        )
        print(f"  [OK] {PROCESSED_DIR}/allocations_antiguas_region.csv")

        print("\n[3.2] Guardando archivos de exportación final...")

        for nombre, key in [
            ('export_balanceados.csv',    'balanceados'),
            ('export_no_balanceados.csv', 'no_balanceados'),
            ('export_con_cambios.csv',    'con_cambios'),
            ('export_sin_datos.csv',      'sin_datos'),
        ]:
            df = resultados['exports'][key]
            df.to_csv(f'{EXPORTS_DIR}/{nombre}', index=False, sep=';', encoding='utf-8')
            print(f"  [OK] {EXPORTS_DIR}/{nombre} ({len(df)} registros)")

        # RESUMEN FINAL
        print("\n" + "="*80)
        print(" RESUMEN EJECUTIVO — REGIÓN ".center(80, "="))
        print("="*80)

        df_final = resultados['df_final']
        total          = len(df_final)
        n_balanceados  = len(resultados['exports']['balanceados'])
        n_no_bal       = len(resultados['exports']['no_balanceados'])
        n_cambios      = len(resultados['exports']['con_cambios'])
        n_sin_datos    = len(resultados['exports']['sin_datos'])

        print(f"Total instrumentos procesados:  {total}")
        if total > 0:
            print(f"Instrumentos balanceados:       {n_balanceados} ({n_balanceados/total*100:.1f}%)")
            print(f"Instrumentos no balanceados:    {n_no_bal} ({n_no_bal/total*100:.1f}%)")
            print(f"Instrumentos con cambios:       {n_cambios} ({n_cambios/total*100:.1f}%)")
            print(f"Instrumentos sin datos:         {n_sin_datos}")
        print("="*80)

        print(f"\n  Archivos procesados: {PROCESSED_DIR}/")
        print(f"  Exports finales:     {EXPORTS_DIR}/")
        print("\n  [EXITOSO] Pipeline de región completado.")
        return 0

    except Exception as e:
        print(f"\n[ERROR] Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

