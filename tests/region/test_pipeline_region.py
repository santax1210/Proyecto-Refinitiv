"""
Runner unificado — Tests pipeline de REGIÓN
=============================================
Ejecuta todos los tests de región en secuencia y reporta el resultado global.

Tests incluidos:
  1. test_carga_archivos      — Existencia y lectura de archivos raw
  2. test_formato_archivos    — Formato WIDE (raw nuevas) y LONG (procesado nuevas)
  3. test_creacion_dataframes — DataFrames del pipeline (instruments, nuevas, antiguas, final)
  4. test_dominancia          — Dominancia, escalado y clasificación Balanceado/Región
  5. test_exports             — Estructura y lógica de todos los exports
  6. test_pipeline_completo   — End-to-end: ejecuta run_pipeline_region.py y valida archivos
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from tests.region.test_carga_archivos      import test_carga_archivos_region
from tests.region.test_formato_archivos    import test_formato_archivos_region
from tests.region.test_creacion_dataframes import test_creacion_dataframes_region
from tests.region.test_dominancia          import test_dominancia_y_escalado_region
from tests.region.test_exports             import run_all as test_exports_region
from tests.region.test_pipeline_completo   import test_pipeline_completo_region


def main():
    print("\n" + "="*80)
    print(" SUITE COMPLETA DE TESTS — PIPELINE DE REGIÓN ".center(80, "="))
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(80))
    print("="*80)

    suite = [
        ("Carga de Archivos",      test_carga_archivos_region),
        ("Formato de Archivos",    test_formato_archivos_region),
        ("Creación de DataFrames", test_creacion_dataframes_region),
        ("Dominancia y Escalado",  test_dominancia_y_escalado_region),
        ("Exports",                test_exports_region),
        ("Pipeline Completo",      test_pipeline_completo_region),
    ]

    resultados = {}
    for nombre, fn in suite:
        print(f"\n{'─'*80}")
        print(f"  ▶  {nombre}")
        print(f"{'─'*80}")
        try:
            ok = fn()
            resultados[nombre] = bool(ok)
        except Exception as e:
            print(f"\n  [!] EXCEPCIÓN durante '{nombre}': {e}")
            import traceback
            traceback.print_exc()
            resultados[nombre] = False

    # ------------------------------------------------------------------ #
    print("\n" + "="*80)
    print(" RESULTADO FINAL ".center(80, "="))
    print("="*80)

    pasados  = sum(1 for v in resultados.values() if v)
    fallados = len(resultados) - pasados

    for nombre, ok in resultados.items():
        icono = "✅" if ok else "❌"
        print(f"  {icono}  {nombre}")

    print(f"\n  {'='*40}")
    print(f"  Total: {pasados}/{len(resultados)} pasados  |  {fallados} fallados")
    print(f"  {'='*40}")

    return fallados == 0


if __name__ == "__main__":
    exito = main()
    sys.exit(0 if exito else 1)

