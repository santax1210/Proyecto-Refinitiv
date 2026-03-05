"""
Pipeline de validación de Allocations de REGIÓN.

Orquesta todo el flujo desde la carga de datos hasta la generación
de reportes finales para allocations de región (classif == 'region').

Uso:
    python run_pipeline_region.py

TODO: Implementar los módulos de extracción y lógica de región antes de ejecutar.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PROCESSED_DIR = 'data/processed/region'
EXPORTS_DIR   = 'data/exports/region'


def main():
    print("\n" + "="*80)
    print(" PIPELINE DE VALIDACIÓN — ALLOCATIONS DE REGIÓN ".center(80, "="))
    print(f" Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(80))
    print("="*80)

    # Archivos raw: los compartidos con moneda + específicos de región
    pos_path      = 'data/raw/posiciones.csv'
    instr_path    = 'data/raw/instruments.csv'
    nuevas_path   = 'data/raw/allocations_nuevas.csv'
    antiguas_path = 'data/raw/region/allocations_region.csv'  # archivo específico de región

    archivos_requeridos = [pos_path, instr_path, nuevas_path, antiguas_path]
    archivos_faltantes = [f for f in archivos_requeridos if not os.path.exists(f)]

    if archivos_faltantes:
        print("\n[ERROR] No se encontraron los siguientes archivos:")
        for archivo in archivos_faltantes:
            print(f"  - {archivo}")
        print("\nAsegúrate de que los archivos raw están en data/raw/ y data/raw/region/")
        return 1

    try:
        from src.extractors.region.load_instruments_region import load_instruments_region
        from src.extractors.region.load_allocations_region import load_allocations_region
        from src.logic.region.clasificacion_region import ejecutar_clasificacion_region
        from src.logic.region.crear_df_final_region import crear_df_final_region
        from src.logic.region.generar_exports_region import generar_exports_region

        # FASE 1: CARGA DE DATOS
        print("\n" + "─"*80)
        print("FASE 1: CARGA Y FILTRADO DE DATOS")
        print("─"*80)

        print("\n[1.1] Cargando instrumentos...")
        df_instruments = load_instruments_region()
        print(f"  [OK] {len(df_instruments)} instrumentos cargados")

        print("\n[1.2] Cargando allocations nuevas (región)...")
        allocations_nuevas_region, allocations_antiguas_region = load_allocations_region(df_instruments)
        print(f"  [OK] allocations de región cargadas")

        # FASE 2: CLASIFICACIÓN
        print("\n" + "─"*80)
        print("FASE 2: PROCESAMIENTO Y CLASIFICACIÓN")
        print("─"*80)

        df_final_region = ejecutar_clasificacion_region(
            df_instruments,
            allocations_nuevas_region,
            allocations_antiguas_region
        )

        # FASE 3: EXPORTACIÓN
        print("\n" + "─"*80)
        print("FASE 3: EXPORTACIÓN DE RESULTADOS")
        print("─"*80)

        os.makedirs(PROCESSED_DIR, exist_ok=True)
        os.makedirs(EXPORTS_DIR, exist_ok=True)

        generar_exports_region(df_final_region)

        print("\n" + "="*80)
        print(" [EXITOSO] PIPELINE REGIÓN COMPLETADO ".center(80, "="))
        print("="*80)
        print(f"\n  Archivos procesados: {PROCESSED_DIR}/")
        print(f"  Exports finales:     {EXPORTS_DIR}/")
        return 0

    except NotImplementedError as e:
        print(f"\n[PENDIENTE] Módulo no implementado aún: {e}")
        print("  Implementa los módulos en src/extractors/region/ y src/logic/region/")
        return 1

    except Exception as e:
        print(f"\n[ERROR] Error durante la ejecución: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
