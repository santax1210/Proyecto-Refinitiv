"""
Pipeline de validación de Allocations de SECTOR / INDUSTRIA.

Orquesta todo el flujo desde la carga de datos hasta la generación
de reportes finales para allocations de sector (classif == 'industry').
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.extractors.sector.load_instruments_sector import load_instruments_sector
from src.extractors.sector.load_allocations_sector import (
    load_allocations_nuevas_sector,
    load_allocations_antiguas_sector,
)
from src.logic.sector.clasificacion_sector import ejecutar_pipeline_completo_sector

PROCESSED_DIR = 'data/processed/sector'
EXPORTS_DIR = 'data/exports/sector'


def main():
    print('\n' + '=' * 80)
    print(' PIPELINE DE VALIDACIÓN — ALLOCATIONS DE SECTOR '.center(80, '='))
    print(f" Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(80))
    print('=' * 80)

    pos_path = 'data/raw/sector/posiciones.csv'
    instr_path = 'data/raw/sector/instruments.csv'
    nuevas_path = 'data/raw/sector/allocations_nuevas.csv'
    antiguas_path = 'data/raw/sector/allocations_sector.csv'

    archivos_requeridos = [pos_path, instr_path, nuevas_path, antiguas_path]
    archivos_faltantes = [f for f in archivos_requeridos if not os.path.exists(f)]
    if archivos_faltantes:
        print('\n[ERROR] No se encontraron los siguientes archivos:')
        for archivo in archivos_faltantes:
            print(f"  - {archivo}")
        print('\nAsegúrate de que los archivos raw están en data/raw/')
        return 1

    try:
        print('\n' + '─' * 80)
        print('FASE 1: CARGA Y FILTRADO DE DATOS')
        print('─' * 80)

        print('\n[1.1] Cargando y filtrando instrumentos...')
        df_instruments = load_instruments_sector(pos_path, instr_path)
        print(f"  [OK] {len(df_instruments)} instrumentos cargados")

        print('\n[1.2] Cargando allocations nuevas (sector/industria)...')
        df_nuevas = load_allocations_nuevas_sector(df_instruments, nuevas_path, umbral=0.9)
        print(f"  [OK] {len(df_nuevas)} registros procesados")

        print('\n[1.3] Cargando allocations antiguas (sector)...')
        df_antiguas = load_allocations_antiguas_sector(df_instruments, antiguas_path)
        print(f"  [OK] {len(df_antiguas)} instrumentos con datos históricos")

        print('\n' + '─' * 80)
        print('FASE 2: PROCESAMIENTO Y CLASIFICACIÓN')
        print('─' * 80)
        resultados = ejecutar_pipeline_completo_sector(df_instruments, df_nuevas, df_antiguas)

        print('\n' + '─' * 80)
        print('FASE 3: EXPORTACIÓN DE RESULTADOS')
        print('─' * 80)

        os.makedirs(PROCESSED_DIR, exist_ok=True)
        os.makedirs(EXPORTS_DIR, exist_ok=True)

        df_instruments.to_csv(f'{PROCESSED_DIR}/df_instruments.csv', index=False, sep=';', encoding='utf-8')
        df_nuevas.to_csv(f'{PROCESSED_DIR}/allocations_nuevas_sector.csv', index=False, sep=';', encoding='utf-8')
        resultados['df_final'].to_csv(f'{PROCESSED_DIR}/df_final_sector.csv', index=False, sep=';', encoding='utf-8')
        resultados['df_antiguas'].to_csv(f'{PROCESSED_DIR}/allocations_antiguas_sector.csv', index=False, sep=';', encoding='utf-8')

        for nombre, key in [
            ('export_balanceados.csv', 'balanceados'),
            ('export_no_balanceados.csv', 'no_balanceados'),
            ('export_con_cambios.csv', 'con_cambios'),
            ('export_sin_datos.csv', 'sin_datos'),
        ]:
            resultados['exports'][key].to_csv(
                f'{EXPORTS_DIR}/{nombre}', index=False, sep=';', encoding='utf-8'
            )

        df_final = resultados['df_final']
        total = len(df_final)
        n_balanceados = len(resultados['exports']['balanceados'])
        n_no_balanceados = len(resultados['exports']['no_balanceados'])
        n_cambios = len(resultados['exports']['con_cambios'])
        n_sin_datos = len(resultados['exports']['sin_datos'])

        print('\n' + '=' * 80)
        print(' RESUMEN EJECUTIVO — SECTOR '.center(80, '='))
        print('=' * 80)
        print(f"Total instrumentos procesados:  {total}")
        if total > 0:
            print(f"Instrumentos balanceados:       {n_balanceados} ({n_balanceados / total * 100:.1f}%)")
            print(f"Instrumentos no balanceados:    {n_no_balanceados} ({n_no_balanceados / total * 100:.1f}%)")
            print(f"Instrumentos con cambios:       {n_cambios} ({n_cambios / total * 100:.1f}%)")
            print(f"Instrumentos sin datos:         {n_sin_datos}")
        print('=' * 80)

        print(f"\n  Archivos procesados: {PROCESSED_DIR}/")
        print(f"  Exports finales:     {EXPORTS_DIR}/")
        print('\n  [EXITOSO] Pipeline de sector completado.')
        return 0

    except Exception as exc:
        print(f"\n[ERROR] Error durante la ejecución: {exc}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())