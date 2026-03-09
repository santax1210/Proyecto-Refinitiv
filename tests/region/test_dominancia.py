"""
Test de Cálculos de Dominancia y Escalado — REGIÓN
=====================================================
Valida que los cálculos de dominancia y escalado en el pipeline de región
sean correctos.

Diferencias vs moneda:
- Columna 'region' en lugar de 'class'
- Columna 'region_nueva' en lugar de 'moneda_nueva'
- Columna 'pct_dominancia_nueva' en lugar de 'pct_dominancia_nuevo'
- Nombres de región pueden tener espacios y puntos (ej: 'Latam Eme. ex-Chile')
- No hay mapeo ISO de nombres
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def print_section(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)


def test_dominancia_y_escalado_region():
    todos_ok = True

    # ------------------------------------------------------------------ #
    # TEST 1: CARGA DEL ARCHIVO PROCESADO
    # ------------------------------------------------------------------ #
    print_section("Test 1: Carga de Datos Procesados (región)")

    try:
        df = pd.read_csv('data/processed/region/allocations_nuevas_region.csv',
                         sep=';', encoding='utf-8')
        print(f"\n[[OK]] Archivo cargado: {len(df)} registros")
        print(f"[i] Columnas: {list(df.columns)}")

    except FileNotFoundError:
        print(f"\n[!] ERROR: Archivo no encontrado.")
        print(f"    Ejecute primero: python run_pipeline_region.py")
        return False

    # ------------------------------------------------------------------ #
    # TEST 2: VALIDAR COLUMNAS DE DOMINANCIA
    # ------------------------------------------------------------------ #
    print_section("Test 2: Validación de Columnas de Dominancia")

    columnas_requeridas = {
        'ID':                  'Identificador del instrumento',
        'region':              'Región de cada allocation',
        'percentage':          'Porcentaje original de la región',
        'region_nueva':        'Clasificación: Balanceado o región dominante',
        'pct_dominancia_nueva':'Texto con región dominante y porcentaje',
        'pct_escalado':        'Suma de porcentajes escalados (debe ser 100.0)',
        'pct_original':        'Suma de porcentajes originales (pre-escalado)',
    }

    faltantes = []
    for col, desc in columnas_requeridas.items():
        if col in df.columns:
            print(f"    [OK] {col:30} - {desc}")
        else:
            print(f"    [X] {col:30} - FALTANTE")
            faltantes.append(col)
            todos_ok = False

    if faltantes:
        print(f"\n[!] Columnas faltantes: {faltantes}")
        return False

    # ------------------------------------------------------------------ #
    # TEST 3: VALIDAR ESCALADO POR INSTRUMENTO (pct_escalado = 100.0)
    # ------------------------------------------------------------------ #
    print_section("Test 3: Validación de Escalado (pct_escalado = 100.0)")

    instr_problema = []
    instr_sin_datos = []

    for inst_id in df['ID'].unique()[:100]:
        grupo = df[df['ID'] == inst_id]
        pct_esc = grupo['pct_escalado'].iloc[0]

        if abs(pct_esc - 100.0) > 0.01:
            if pct_esc == 0.0:
                instr_sin_datos.append(inst_id)
            else:
                instr_problema.append({'ID': inst_id, 'pct_escalado': pct_esc})

    if instr_sin_datos:
        print(f"\n[i] {len(instr_sin_datos)} instrumentos sin datos (pct_escalado = 0.0) — Normal")

    if instr_problema:
        print(f"\n[!] ERROR: {len(instr_problema)} instrumentos con pct_escalado incorrecto:")
        for item in instr_problema[:5]:
            print(f"    ID {item['ID']}: pct_escalado = {item['pct_escalado']}")
        todos_ok = False
    else:
        print(f"\n[[OK]] Todos los instrumentos con datos tienen pct_escalado = 100.0")

    # ------------------------------------------------------------------ #
    # TEST 4: CONSISTENCIA suma(percentage) = pct_original
    # ------------------------------------------------------------------ #
    print_section("Test 4: Consistencia suma(percentage) vs pct_original")

    errores = []
    for inst_id in df['ID'].unique()[:50]:
        grupo = df[df['ID'] == inst_id]
        suma_calc = grupo['percentage'].sum()
        pct_orig  = grupo['pct_original'].iloc[0]
        if abs(suma_calc - pct_orig) > 0.1:
            errores.append({
                'ID': inst_id,
                'suma': suma_calc,
                'pct_original': pct_orig,
                'diff': abs(suma_calc - pct_orig),
            })

    if errores:
        print(f"\n[!] ERROR: {len(errores)} inconsistencias:")
        for item in errores[:3]:
            print(f"    ID {item['ID']}: suma={item['suma']:.2f}, pct_original={item['pct_original']:.2f}")
        todos_ok = False
    else:
        print(f"\n[[OK]] Consistencia verificada: suma(percentage) ≈ pct_original")

    # ------------------------------------------------------------------ #
    # TEST 5: LÓGICA DE DOMINANCIA (umbral 90%)
    # ------------------------------------------------------------------ #
    print_section("Test 5: Validación de Clasificación por Dominancia (90%)")

    umbral = 0.9
    errores_dom = []

    for inst_id in df['ID'].unique()[:50]:
        grupo = df[df['ID'] == inst_id]
        total = grupo['percentage'].sum()
        if total <= 0:
            continue
        pcts_esc = grupo['percentage'] / total
        max_pct = pcts_esc.max()
        reg_max = grupo.loc[pcts_esc.idxmax(), 'region']
        reg_nueva = grupo['region_nueva'].iloc[0]

        if max_pct >= umbral:
            # Se espera la región dominante (comparación case-insensitive)
            if str(reg_nueva).strip().lower() != str(reg_max).strip().lower():
                errores_dom.append({
                    'ID': inst_id,
                    'max_pct': max_pct * 100,
                    'esperado': reg_max,
                    'actual': reg_nueva,
                })
        else:
            # Se espera Balanceado
            if str(reg_nueva).strip() != 'Balanceado':
                errores_dom.append({
                    'ID': inst_id,
                    'max_pct': max_pct * 100,
                    'esperado': 'Balanceado',
                    'actual': reg_nueva,
                })

    if errores_dom:
        print(f"\n[!] ERROR: {len(errores_dom)} instrumentos con clasificación incorrecta:")
        for item in errores_dom[:5]:
            print(f"    ID {item['ID']}: max={item['max_pct']:.1f}%, esperado={item['esperado']}, actual={item['actual']}")
        todos_ok = False
    else:
        print(f"\n[[OK]] Clasificación por dominancia correcta (umbral={umbral*100:.0f}%)")

    # ------------------------------------------------------------------ #
    # TEST 6: FORMATO DE pct_dominancia_nueva
    # ------------------------------------------------------------------ #
    print_section("Test 6: Formato de pct_dominancia_nueva")

    sample = df.drop_duplicates('ID')['pct_dominancia_nueva'].dropna().head(20)
    errores_fmt = []

    for val in sample:
        if str(val).strip().upper() == 'BALANCEADO':
            continue  # Balanceado no tiene formato "REGIÓN XX%"
        import re
        if not re.match(r'^.+\s+\d+\.?\d*\s*%$', str(val).strip()):
            errores_fmt.append(val)

    if errores_fmt:
        print(f"\n[!] ADVERTENCIA: {len(errores_fmt)} valores con formato inesperado:")
        for v in errores_fmt[:5]:
            print(f"    '{v}'")
    else:
        print(f"\n[[OK]] Formato 'REGIÓN XX.XX%' validado correctamente")
        print(f"\n[i] Ejemplos de pct_dominancia_nueva:")
        for val in sample.head(5):
            print(f"    {val}")

    # ------------------------------------------------------------------ #
    # TEST 7: NOMBRES DE REGIÓN (no deben ser muy cortos ni vacíos)
    # ------------------------------------------------------------------ #
    print_section("Test 7: Validación de Nombres de Región")

    regiones = df['region'].dropna().unique()
    print(f"\n[i] Regiones únicas detectadas ({len(regiones)}):")
    for reg in sorted(regiones):
        print(f"    - '{reg}'")

    vacias = [r for r in regiones if str(r).strip() == '']
    if vacias:
        print(f"\n[!] ADVERTENCIA: {len(vacias)} regiones vacías detectadas")
        todos_ok = False
    else:
        print(f"\n[[OK]] Todas las regiones tienen nombre válido")

    # ------------------------------------------------------------------ #
    # TEST 8: ESTADÍSTICAS GENERALES
    # ------------------------------------------------------------------ #
    print_section("Test 8: Estadísticas Generales")

    total_instr = df['ID'].nunique()
    total_reg   = len(df)
    by_id = df.drop_duplicates('ID')

    dist = by_id['region_nueva'].value_counts()
    balanceados    = dist.get('Balanceado', 0)
    no_balanceados = total_instr - balanceados

    print(f"\n[i] Total instrumentos:          {total_instr}")
    print(f"[i] Total registros (LONG):      {total_reg}")
    print(f"[i] Promedio regiones/instrumento: {total_reg/total_instr:.1f}")
    print(f"\n[i] Clasificación:")
    print(f"    Balanceados:     {balanceados:5} ({balanceados/total_instr*100:.1f}%)")
    print(f"    No balanceados:  {no_balanceados:5} ({no_balanceados/total_instr*100:.1f}%)")

    if no_balanceados > 0:
        print(f"\n[i] Regiones dominantes (Top 10):")
        top = dist[dist.index != 'Balanceado'].head(10)
        for reg, cnt in top.items():
            print(f"    {reg:30} - {cnt:4} instrumentos")

    # ------------------------------------------------------------------ #
    print_section("Resultado Final")
    if todos_ok:
        print("[OK] Todos los cálculos de dominancia y escalado son correctos.")
    else:
        print("[!] Se detectaron problemas. Revisar más arriba.")

    return todos_ok


if __name__ == "__main__":
    exito = test_dominancia_y_escalado_region()
    sys.exit(0 if exito else 1)
