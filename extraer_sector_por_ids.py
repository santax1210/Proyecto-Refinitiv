"""
extraer_sector_por_ids.py
=========================
Script de recuperación: dado el Excel del export de MONEDA descargado por error
(que contiene los IDs correctos que se debían validar), filtra los exports del
pipeline de SECTOR por esos IDs y genera archivos listos para usar.

Uso:
    python extraer_sector_por_ids.py <ruta_excel_moneda>

Ejemplo:
    python extraer_sector_por_ids.py export_moneda_incorrecto.xlsx

Salida:
    data/exports/sector/recuperados/
        export_balanceados_filtrado.xlsx
        export_no_balanceados_filtrado.xlsx
        export_con_cambios_filtrado.xlsx
        export_sin_datos_filtrado.xlsx
        resumen.txt
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

import pandas as pd

EXPORTS_DIR = 'data/exports/sector'
OUTPUT_DIR  = 'data/exports/sector/recuperados'

EXPORTS = [
    ('export_balanceados.xlsx',    'export_balanceados_filtrado.xlsx'),
    ('export_no_balanceados.xlsx', 'export_no_balanceados_filtrado.xlsx'),
    ('export_con_cambios.xlsx',    'export_con_cambios_filtrado.xlsx'),
    ('export_sin_datos.xlsx',      'export_sin_datos_filtrado.xlsx'),
]


def main():
    print('\n' + '=' * 70)
    print(' RECUPERACIÓN DE EXPORTS DE SECTOR POR IDs '.center(70, '='))
    print(f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(70))
    print('=' * 70)

    # ── Argumento: ruta del Excel ──────────────────────────────────────────
    if len(sys.argv) < 2:
        print('\n[ERROR] Debés pasar la ruta del Excel de moneda como argumento.')
        print('  Uso: python extraer_sector_por_ids.py <ruta_excel>')
        return 1

    excel_path = sys.argv[1]
    if not os.path.exists(excel_path):
        print(f'\n[ERROR] No se encontró el archivo: {excel_path}')
        return 1

    # ── PASO 1: Leer IDs del Excel ─────────────────────────────────────────
    print(f'\n[1] Leyendo IDs desde: {excel_path}')
    try:
        df_excel = pd.read_excel(excel_path)
    except Exception as e:
        print(f'[ERROR] No se pudo leer el Excel: {e}')
        return 1

    if 'ID' not in df_excel.columns and 'instrument_id' not in df_excel.columns:
        print(f'[ERROR] El Excel no tiene columna "ID" ni "instrument_id". Columnas encontradas: {list(df_excel.columns)}')
        return 1

    id_col_excel = 'instrument_id' if 'instrument_id' in df_excel.columns else 'ID'
    ids_validos = set(df_excel[id_col_excel].dropna().astype(str).str.strip())
    print(f'  [OK] {len(ids_validos)} IDs únicos encontrados en el Excel')

    # ── PASO 2: Verificar exports de sector ───────────────────────────────
    print(f'\n[2] Verificando exports de sector en: {EXPORTS_DIR}/')
    faltantes = []
    for nombre_src, _ in EXPORTS:
        ruta = os.path.join(EXPORTS_DIR, nombre_src)
        if not os.path.exists(ruta):
            faltantes.append(nombre_src)

    if faltantes:
        print('\n  [!] Faltan los siguientes exports de sector:')
        for f in faltantes:
            print(f'      - {EXPORTS_DIR}/{f}')
        print('\n  Ejecutá primero el pipeline de sector:')
        print('      python run_pipeline_sector.py')
        return 1

    print('  [OK] Todos los exports de sector están presentes')

    # ── PASO 3: Filtrar y guardar ─────────────────────────────────────────
    print(f'\n[3] Filtrando exports y guardando en: {OUTPUT_DIR}/')
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    resumen_lineas = [
        f'Recuperación de exports de sector',
        f'Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'Excel fuente: {excel_path}',
        f'IDs en el Excel: {len(ids_validos)}',
        '',
    ]

    total_encontrados = 0
    total_no_encontrados = 0

    for nombre_src, nombre_dst in EXPORTS:
        ruta_src = os.path.join(EXPORTS_DIR, nombre_src)
        ruta_dst = os.path.join(OUTPUT_DIR, nombre_dst)

        try:
            df = pd.read_excel(ruta_src, dtype=str)
        except Exception as e:
            print(f'  [ERROR] No se pudo leer {nombre_src}: {e}')
            resumen_lineas.append(f'{nombre_src}: ERROR al leer - {e}')
            continue

        id_col = 'instrument_id' if 'instrument_id' in df.columns else 'ID'
        if id_col not in df.columns:
            print(f'  [WARN] {nombre_src} no tiene columna "instrument_id" ni "ID" — se copia sin filtrar')
            df.to_excel(ruta_dst, index=False)
            resumen_lineas.append(f'{nombre_dst}: sin columna ID, copiado completo ({len(df)} filas)')
            continue

        ids_en_export = set(df[id_col].astype(str).str.strip())
        df_filtrado = df[df[id_col].astype(str).str.strip().isin(ids_validos)].copy()

        ids_faltantes_en_sector = ids_validos - ids_en_export
        n_encontrados = len(df_filtrado)
        total_encontrados += n_encontrados

        df_filtrado.to_excel(ruta_dst, index=False)

        # Loggear IDs del Excel y del export para depuración
        ruta_log_ids = os.path.join(OUTPUT_DIR, f'log_ids_{nombre_dst}.txt')
        with open(ruta_log_ids, 'w', encoding='utf-8') as log_file:
            log_file.write('IDs en el Excel:\n')
            log_file.write('\n'.join(sorted(ids_validos)))
            log_file.write('\n\nIDs en el export:\n')
            log_file.write('\n'.join(sorted(ids_en_export)))

        # Loggear IDs que no coinciden
        ids_no_encontrados = ids_validos - ids_en_export
        ruta_log_no_match = os.path.join(OUTPUT_DIR, f'log_no_match_{nombre_dst}.txt')
        with open(ruta_log_no_match, 'w', encoding='utf-8') as log_file:
            log_file.write('IDs en el Excel que no están en el export:\n')
            log_file.write('\n'.join(sorted(ids_no_encontrados)))

        linea = f'{nombre_dst}: {n_encontrados} filas filtradas (de {len(df)} totales en sector)'
        print(f'  [OK] {nombre_src} -> {nombre_dst}  ({n_encontrados} registros)')
        resumen_lineas.append(linea)

        if ids_faltantes_en_sector:
            total_no_encontrados += len(ids_faltantes_en_sector)
            aviso = f'       {len(ids_faltantes_en_sector)} IDs del Excel no estaban en este export'
            print(f'  [i] {aviso.strip()}')
            resumen_lineas.append(aviso)

    # ── PASO 4: Resumen final ─────────────────────────────────────────────
    print('\n' + '=' * 70)
    print(' RESUMEN '.center(70, '='))
    print('=' * 70)
    print(f'  IDs en el Excel:          {len(ids_validos)}')
    print(f'  Registros exportados:     {total_encontrados}')
    if total_no_encontrados:
        print(f'  IDs no hallados (total):  {total_no_encontrados} (pueden estar en otros exports)')

    resumen_lineas += [
        '',
        f'Total registros exportados: {total_encontrados}',
        f'IDs sin match (acum.):      {total_no_encontrados}',
    ]

    ruta_resumen = os.path.join(OUTPUT_DIR, 'resumen.txt')
    with open(ruta_resumen, 'w', encoding='utf-8') as f:
        f.write('\n'.join(resumen_lineas))

    print(f'\n  Archivos guardados en: {OUTPUT_DIR}/')
    print(f'  Resumen: {ruta_resumen}')
    print('\n  [EXITOSO] Recuperación completada.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
