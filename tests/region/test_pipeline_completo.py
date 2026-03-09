"""
Test de Pipeline Completo (End-to-End) — REGIÓN
==================================================
Ejecuta y valida el pipeline completo de región desde archivos raw hasta exports.
"""

import pandas as pd
import sys
import os
import subprocess
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def print_section(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)


def check_file(filepath, descripcion):
    if os.path.exists(filepath):
        size_kb = os.path.getsize(filepath) / 1024
        print(f"    [OK] {descripcion:45} ({size_kb:>8.1f} KB)")
        return True
    else:
        print(f"    [X] {descripcion:45} [NO ENCONTRADO]")
        return False


def test_pipeline_completo_region():
    print_section("Test de Pipeline Completo (End-to-End) — REGIÓN")
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # ------------------------------------------------------------------ #
    # TEST 1: ARCHIVOS RAW
    # ------------------------------------------------------------------ #
    print_section("Test 1: Validación de Archivos Raw")

    archivos_raw = {
        'data/raw/instruments.csv':                        'Maestro de Instrumentos',
        'data/raw/posiciones.csv':                         'Posiciones',
        'data/raw/region/allocations_nuevas_region.csv':   'Allocations Nuevas (WIDE)',
        'data/raw/region/allocations_region.csv':          'Allocations Antiguas (región)',
    }

    print("\n[i] Verificando archivos de entrada...")
    todos_ok = all(check_file(fp, desc) for fp, desc in archivos_raw.items())

    if not todos_ok:
        print("\n[!] ERROR: Faltan archivos raw necesarios.")
        return False

    print("\n[[OK]] Todos los archivos raw están presentes.")

    # ------------------------------------------------------------------ #
    # TEST 2: EJECUCIÓN DEL PIPELINE
    # ------------------------------------------------------------------ #
    print_section("Test 2: Ejecución del Pipeline de Región")
    print("\n[...] Ejecutando: python run_pipeline_region.py")

    try:
        result = subprocess.run(
            [sys.executable, 'run_pipeline_region.py'],
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode == 0:
            print("[[OK]] Pipeline ejecutado exitosamente (exit code 0)")
        else:
            print(f"\n[!] ERROR: Pipeline falló con exit code {result.returncode}")
            stderr = result.stderr[-1000:] if len(result.stderr) > 1000 else result.stderr
            print("\n--- STDERR ---")
            print(stderr)
            return False

        # Buscar mensajes clave
        output = result.stdout
        if "Pipeline de región completado" in output or "EXITOSO" in output:
            print("[[OK]] Pipeline completado según logs")

        # Extraer estadísticas
        for line in output.split('\n'):
            if any(kw in line for kw in ('Total instrumentos', 'Balanceados', 'No balanceados', 'Con cambios')):
                print(f"[i] {line.strip()}")

    except subprocess.TimeoutExpired:
        print("\n[!] ERROR: Pipeline excedió el tiempo límite (3 minutos)")
        return False

    except Exception as e:
        print(f"\n[!] ERROR al ejecutar pipeline: {e}")
        return False

    # ------------------------------------------------------------------ #
    # TEST 3: ARCHIVOS PROCESADOS
    # ------------------------------------------------------------------ #
    print_section("Test 3: Validación de Archivos Procesados")

    archivos_proc = {
        'data/processed/region/df_instruments.csv':               'Instrumentos Filtrados',
        'data/processed/region/allocations_nuevas_region.csv':    'Allocations Nuevas (LONG)',
        'data/processed/region/allocations_antiguas_region.csv':  'Allocations Antiguas',
        'data/processed/region/df_final_region.csv':              'DataFrame Final Consolidado',
    }

    print("\n[i] Verificando archivos procesados...")
    proc_ok = all(check_file(fp, desc) for fp, desc in archivos_proc.items())

    if not proc_ok:
        print("\n[!] ERROR: Faltan archivos procesados.")
        return False

    print("\n[[OK]] Todos los archivos procesados generados.")

    # ------------------------------------------------------------------ #
    # TEST 4: ARCHIVOS DE EXPORTACIÓN
    # ------------------------------------------------------------------ #
    print_section("Test 4: Validación de Archivos de Exportación")

    archivos_exp = {
        'data/exports/region/export_balanceados.csv':    'Export Balanceados',
        'data/exports/region/export_no_balanceados.csv': 'Export No Balanceados',
        'data/exports/region/export_con_cambios.csv':    'Export Con Cambios',
        'data/exports/region/export_sin_datos.csv':      'Export Sin Datos',
    }

    print("\n[i] Verificando archivos de exportación...")
    exp_ok = all(check_file(fp, desc) for fp, desc in archivos_exp.items())

    if not exp_ok:
        print("\n[!] ADVERTENCIA: Faltan algunos archivos de exportación.")
    else:
        print("\n[[OK]] Todos los archivos de exportación generados.")

    # ------------------------------------------------------------------ #
    # TEST 5: CONTENIDO DEL df_final_region
    # ------------------------------------------------------------------ #
    print_section("Test 5: Validación de Contenido — df_final_region")

    try:
        df_final = pd.read_csv('data/processed/region/df_final_region.csv',
                               sep=';', encoding='utf-8')
        print(f"\n[i] df_final_region: {len(df_final)} filas, {df_final.shape[1]} columnas")

        # Columnas obligatorias
        cols_oblig = ['ID', 'Nombre', 'region_antigua', 'region_nueva',
                      'pct_dominancia_nueva', 'pct_dominancia_antigua', 'Cambio', 'Estado']
        faltantes = [c for c in cols_oblig if c not in df_final.columns]
        if faltantes:
            print(f"\n[!] Columnas faltantes en df_final: {faltantes}")
            return False
        else:
            print(f"[[OK]] Todas las columnas obligatorias presentes")

        # Distribución de Cambio
        if 'Cambio' in df_final.columns:
            print(f"\n[i] Distribución de Cambio:")
            print(df_final['Cambio'].value_counts().to_string())

        # Distribución de Estado
        if 'Estado' in df_final.columns:
            print(f"\n[i] Distribución de Estado:")
            print(df_final['Estado'].value_counts().to_string())

        # Instrumentos balance y no balance
        if 'region_nueva' in df_final.columns:
            n_bal = (df_final['region_nueva'] == 'Balanceado').sum()
            print(f"\n[i] Balanceados: {n_bal} | No balanceados: {len(df_final) - n_bal}")

    except Exception as e:
        print(f"\n[!] ERROR al leer df_final_region: {e}")
        return False

    # ------------------------------------------------------------------ #
    # TEST 6: CONTENIDO DE EXPORTS
    # ------------------------------------------------------------------ #
    print_section("Test 6: Validación de Contenido — Exports")

    errores_exp = []

    # Export balanceados
    try:
        df_bal = pd.read_csv('data/exports/region/export_balanceados.csv', sep=';', encoding='utf-8')
        print(f"\n  Export balanceados:    {len(df_bal)} filas")
        for col in ['Clasificacion', 'Estado', 'Fecha', 'Region Anterior']:
            if col not in df_bal.columns:
                errores_exp.append(f"Balanceados: columna '{col}' faltante")
        # Clasificacion debe ser 'SubRegion'
        if 'Clasificacion' in df_bal.columns:
            vals = df_bal['Clasificacion'].unique()
            if not all(v == 'SubRegion' for v in vals):
                errores_exp.append(f"Balanceados: Clasificacion esperada 'SubRegion', encontrada {vals}")
            else:
                print(f"  [[OK]] Clasificacion = 'SubRegion'")
    except Exception as e:
        errores_exp.append(f"Error al leer export_balanceados: {e}")

    # Export no balanceados
    try:
        df_nobal = pd.read_csv('data/exports/region/export_no_balanceados.csv', sep=';', encoding='utf-8')
        print(f"  Export no balanceados: {len(df_nobal)} filas")
        for col in ['SubRegion', 'Region Anterior', 'Estado', 'Sobreescribir']:
            if col not in df_nobal.columns:
                errores_exp.append(f"No balanceados: columna '{col}' faltante")
        # Verificar que no hay 'SubMoneda' ni 'Moneda Anterior'
        cols_moneda = [c for c in df_nobal.columns if c in ('SubMoneda', 'Moneda Anterior')]
        if cols_moneda:
            errores_exp.append(f"No balanceados: columnas de moneda inesperadas: {cols_moneda}")
        else:
            print(f"  [[OK]] No hay columnas de moneda en no balanceados")
    except Exception as e:
        errores_exp.append(f"Error al leer export_no_balanceados: {e}")

    # Export sin datos
    try:
        df_sin = pd.read_csv('data/exports/region/export_sin_datos.csv', sep=';', encoding='utf-8')
        print(f"  Export sin datos:      {len(df_sin)} filas")
        for col in ['ID', 'Instrumento']:
            if col not in df_sin.columns:
                errores_exp.append(f"Sin datos: columna '{col}' faltante")
    except Exception as e:
        errores_exp.append(f"Error al leer export_sin_datos: {e}")

    if errores_exp:
        print(f"\n[!] Errores en exports:")
        for err in errores_exp:
            print(f"    {err}")
        return False
    else:
        print(f"\n[[OK]] Todos los exports son correctos")

    # ------------------------------------------------------------------ #
    # RESUMEN
    # ------------------------------------------------------------------ #
    print_section("Resumen Ejecutivo")

    try:
        df_final = pd.read_csv('data/processed/region/df_final_region.csv', sep=';', encoding='utf-8')
        df_bal   = pd.read_csv('data/exports/region/export_balanceados.csv', sep=';', encoding='utf-8')
        df_nobal = pd.read_csv('data/exports/region/export_no_balanceados.csv', sep=';', encoding='utf-8')
        df_cam   = pd.read_csv('data/exports/region/export_con_cambios.csv', sep=';', encoding='utf-8')
        df_sin   = pd.read_csv('data/exports/region/export_sin_datos.csv', sep=';', encoding='utf-8')

        total = len(df_final)
        print(f"\n  Total instrumentos procesados: {total}")
        if total > 0:
            print(f"  Balanceados:                   {len(df_bal)} ({len(df_bal)/total*100:.1f}%)")
            print(f"  No balanceados:                {len(df_nobal)} ({len(df_nobal)/total*100:.1f}%)")
            print(f"  Con cambios:                   {len(df_cam)}")
            print(f"  Sin datos:                     {len(df_sin)}")
    except Exception:
        pass

    print("\n  [[EXITOSO]] Pipeline de región completado y validado.")
    return True


# ------------------------------------------------------------------ #
# TEST 7: INTEGRACIÓN API — run_pipeline_background
# ------------------------------------------------------------------ #
def test_api_run_pipeline_background():
    """
    Llama directamente a run_pipeline_background('region') — el mismo código
    que ejecuta la API cuando el usuario hace click en 'Procesar Validación'.
    Esto garantiza que los argumentos y las llamadas internas son correctos.
    """
    print_section("Test 7: Integración API — run_pipeline_background('region')")

    # Importar la función de la API (misma ruta que usa Flask)
    api_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sys.path.insert(0, api_root)

    try:
        import importlib, types

        # Necesitamos un app context mínimo para que app.config esté disponible
        # Cargamos app.py pero sin arrancar el servidor
        import api.app as api_app

        # Asginar UPLOAD_FOLDER correcto (raw)
        api_app.app.config['UPLOAD_FOLDER']    = os.path.join(api_root, 'data', 'raw')
        api_app.app.config['PROCESSED_FOLDER'] = os.path.join(api_root, 'data', 'processed')
        api_app.app.config['EXPORTS_FOLDER']   = os.path.join(api_root, 'data', 'exports')

        # Verificar archivos raw antes de ejecutar
        file_config = api_app.get_file_config('region', api_app.app.config['UPLOAD_FOLDER'])
        faltantes = [k for k, v in file_config.items() if not os.path.exists(v)]
        if faltantes:
            print(f"  [!] Archivos raw faltantes: {faltantes}")
            print("  [!] Ejecutar run_pipeline_region.py primero")
            return False

        print("  [i] Archivos raw presentes — ejecutando run_pipeline_background('region')...")

        # Ejecutar la función de background (bloqueante aquí, igual que en producción)
        api_app.run_pipeline_background('region')

        estado = api_app.processing_state
        print(f"  [i] Estado final: {estado['status']}")

        if estado['status'] == 'error':
            print(f"  [!] Error en pipeline: {estado.get('error')}")
            return False

        if estado['status'] == 'completed':
            print("  [[OK]] run_pipeline_background('region') completó sin errores")

            # Verificar archivos de salida
            exp_folder = os.path.join(api_root, 'data', 'exports', 'region')
            for export in ('balanceados', 'no_balanceados', 'con_cambios', 'sin_datos'):
                path = os.path.join(exp_folder, f'export_{export}.csv')
                if os.path.exists(path):
                    print(f"  [OK] export_{export}.csv")
                else:
                    print(f"  [!] Falta export_{export}.csv")
                    return False
            return True
        else:
            print(f"  [!] Estado inesperado: {estado['status']}")
            return False

    except Exception as e:
        print(f"  [!] Excepción: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ok1 = test_pipeline_completo_region()
    print()
    ok2 = test_api_run_pipeline_background()
    print()
    print_section("Resultado Final")
    print(f"  Pipeline completo (run_pipeline_region.py): {'✅' if ok1 else '❌'}")
    print(f"  Integración API (run_pipeline_background): {'✅' if ok2 else '❌'}")
    exito = ok1 and ok2
    sys.exit(0 if exito else 1)
