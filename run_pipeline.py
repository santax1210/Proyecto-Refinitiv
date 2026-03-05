"""
Script principal para ejecutar el pipeline completo de validación de allocations.

Este script orquesta todo el flujo desde la carga de datos hasta la generación
de reportes finales.

Uso:
    python run_pipeline.py
"""

import sys
import os
from datetime import datetime

# Asegurar que el directorio raíz está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.extractors.moneda.load_instruments import load_df_instruments
from src.extractors.moneda.load_allocations import load_allocations_nuevas, load_allocations_antiguas
from src.logic.moneda.clasificacion import ejecutar_pipeline_completo


def main():
    """
    Ejecuta el pipeline completo de validación de allocations.
    """
    print("\n" + "="*80)
    print(f" PIPELINE DE VALIDACIÓN DE ALLOCATIONS ".center(80, "="))
    print(f" Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(80))
    print("="*80)
    
    # Rutas de archivos
    pos_path = 'data/raw/posiciones.csv'
    instr_path = 'data/raw/instruments.csv'
    nuevas_path = 'data/raw/allocations_nuevas.csv'
    antiguas_path = 'data/raw/allocations_currency.csv'
    
    # Verificar que los archivos existen
    archivos_requeridos = [pos_path, instr_path, nuevas_path, antiguas_path]
    archivos_faltantes = [f for f in archivos_requeridos if not os.path.exists(f)]
    
    if archivos_faltantes:
        print("\n[ERROR] ERROR: No se encontraron los siguientes archivos:")
        for archivo in archivos_faltantes:
            print(f"  - {archivo}")
        print("\nPor favor, asegúrate de que los archivos raw están en data/raw/")
        return 1
    
    try:
        # FASE 1: CARGA DE DATOS
        print("\n" + "─"*80)
        print("FASE 1: CARGA Y FILTRADO DE DATOS")
        print("─"*80)
        
        print("\n[1.1] Cargando y filtrando instrumentos...")
        df_instruments = load_df_instruments(pos_path, instr_path)
        print(f"  [OK] {len(df_instruments)} instrumentos cargados")
        print(f"    Columnas: {', '.join(df_instruments.columns.tolist())}")
        
        print("\n[1.2] Cargando allocations nuevas...")
        df_nuevas = load_allocations_nuevas(df_instruments, nuevas_path, umbral=0.9)
        print(f"  [OK] {len(df_nuevas)} registros procesados (formato long con dominancia)")
        if 'ID' in df_nuevas.columns:
            instrumentos_unicos = df_nuevas['ID'].nunique()
            print(f"  [OK] {instrumentos_unicos} instrumentos únicos")
        if 'moneda_nueva' in df_nuevas.columns:
            balanceados_nuevas = (df_nuevas['moneda_nueva'] == 'Balanceado').sum()
            no_balanceados_nuevas = len(df_nuevas) - balanceados_nuevas
            print(f"    - Filas con Balanceado: {balanceados_nuevas}")
            print(f"    - Filas con moneda específica: {no_balanceados_nuevas}")
        
        print("\n[1.3] Cargando allocations antiguas...")
        df_antiguas = load_allocations_antiguas(df_instruments, antiguas_path)
        print(f"  [OK] {len(df_antiguas)} instrumentos procesados (con Pct_dominancia calculada)")
        if 'Pct_dominancia' in df_antiguas.columns:
            sin_datos = (df_antiguas['Pct_dominancia'] == 'Sin datos').sum()
            print(f"    - Con datos: {len(df_antiguas) - sin_datos}")
            print(f"    - Sin datos: {sin_datos}")
        
        # FASE 2: PROCESAMIENTO Y CLASIFICACIÓN
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
        
        os.makedirs('data/processed', exist_ok=True)
        os.makedirs('data/exports', exist_ok=True)
        
        # Guardar en processed (para inspección técnica)
        print("\n[3.1] Guardando archivos procesados...")
        
        # Guardar df_instruments
        df_instruments.to_csv(
            'data/processed/df_instruments.csv',
            index=False,
            sep=';',
            encoding='latin-1'
        )
        print("  [OK] data/processed/df_instruments.csv")
        
        # Guardar allocations_nuevas (formato long con dominancia)
        df_nuevas.to_csv(
            'data/processed/allocations_nuevas.csv',
            index=False,
            sep=';',
            encoding='latin-1'
        )
        print("  [OK] data/processed/allocations_nuevas.csv (formato long con dominancia)")
        
        resultados['df_final'].to_csv(
            'data/processed/df_final.csv',
            index=False,
            sep=';',
            encoding='latin-1'
        )
        print("  [OK] data/processed/df_final.csv")
        
        resultados['df_antiguas'].to_csv(
            'data/processed/allocations_antiguas.csv',
            index=False,
            sep=';',
            encoding='latin-1'
        )
        print("  [OK] data/processed/allocations_antiguas.csv")
        
        # Guardar en exports (para usuario final)
        print("\n[3.2] Guardando archivos de exportación final...")
        
        resultados['exports']['balanceados'].to_csv(
            'data/exports/export_balanceados.csv',
            index=False,
            sep=';',
            encoding='latin-1'
        )
        print(f"  [OK] data/exports/export_balanceados.csv ({len(resultados['exports']['balanceados'])} registros)")
        
        resultados['exports']['no_balanceados'].to_csv(
            'data/exports/export_no_balanceados.csv',
            index=False,
            sep=';',
            encoding='latin-1'
        )
        print(f"  [OK] data/exports/export_no_balanceados.csv ({len(resultados['exports']['no_balanceados'])} registros)")
        
        resultados['exports']['con_cambios'].to_csv(
            'data/exports/export_con_cambios.csv',
            index=False,
            sep=';',
            encoding='latin-1'
        )
        print(f"  [OK] data/exports/export_con_cambios.csv ({len(resultados['exports']['con_cambios'])} registros)")
        
        resultados['exports']['sin_datos'].to_csv(
            'data/exports/export_sin_datos.csv',
            index=False,
            sep=';',
            encoding='latin-1'
        )
        print(f"  [OK] data/exports/export_sin_datos.csv ({len(resultados['exports']['sin_datos'])} registros)")
        
        # RESUMEN FINAL
        print("\n" + "="*80)
        print(" RESUMEN EJECUTIVO FINAL ".center(80, "="))
        print("="*80)
        
        df_final = resultados['df_final']
        total = len(df_final)
        balanceados = len(resultados['exports']['balanceados'])
        no_balanceados = len(resultados['exports']['no_balanceados'])
        con_cambios = len(resultados['exports']['con_cambios'])
        sin_datos = len(resultados['exports']['sin_datos'])
        
        print(f"\n📊 Total de instrumentos procesados:    {total}")
        print(f"⚖️  Instrumentos balanceados:            {balanceados} ({balanceados/total*100:.1f}%)")
        print(f"💱 Instrumentos no balanceados:         {no_balanceados} ({no_balanceados/total*100:.1f}%)")
        print(f"🔄 Instrumentos con cambios:            {con_cambios} ({con_cambios/total*100:.1f}%)")
        print(f"❓ Instrumentos sin datos:              {sin_datos}")
        
        if 'moneda_nueva' in df_final.columns:
            print("\n💰 Distribución de monedas nuevas (top 5):")
            dist = df_final[df_final['moneda_nueva'] != 'Balanceado']['moneda_nueva'].value_counts().head(5)
            for moneda, count in dist.items():
                print(f"  - {moneda}: {count} instrumentos")
        
        print("\n" + "="*80)
        print(" [EXITO] PIPELINE COMPLETADO EXITOSAMENTE ".center(80, "="))
        print("="*80)
        print("\n📁 Archivos generados:")
        print("  • data/processed/   → Archivos intermedios para análisis técnico")
        print("  • data/exports/     → Archivos finales para usuario")
        print("\n")
        
        return 0
        
    except Exception as e:
        print("\n" + "="*80)
        print(" [ERROR] ERROR EN LA EJECUCIÓN ".center(80, "="))
        print("="*80)
        print(f"\n{type(e).__name__}: {str(e)}")
        print("\nPor favor, revisa los logs y los datos de entrada.")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
