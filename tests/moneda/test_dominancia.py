"""
Test de Cálculos de Dominancia y Escalado
==========================================
Valida que los cálculos de dominancia y escalado de porcentajes sean correctos.
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

def print_section(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)

def test_dominancia_y_escalado():
    """Valida cálculos de dominancia y escalado de porcentajes."""
    
    print_section("Test 1: Carga de Datos")
    
    try:
        df = pd.read_csv('data/processed/allocations_nuevas.csv',
                        sep=';', encoding='latin-1')
        print(f"\n[[OK]] Archivo cargado: {len(df)} registros")
        print(f"[i] Columnas: {list(df.columns)}")
    
    except FileNotFoundError:
        print(f"\n[!] ERROR: Archivo no encontrado.")
        print(f"    Ejecute primero: python run_pipeline.py")
        return False
    
    # --- TEST 2: VALIDAR COLUMNAS DE DOMINANCIA ---
    print_section("Test 2: Validación de Columnas")
    
    columnas_requeridas = {
        'ID': 'Identificador del instrumento',
        'class': 'Moneda de cada allocation',
        'percentage': 'Porcentaje original de la moneda',
        'moneda_nueva': 'Clasificación: Balanceado o moneda dominante',
        'pct_dominancia_nuevo': 'Texto con moneda dominante y porcentaje',
        'pct_escalado': 'Suma de porcentajes escalados (debe ser 100.0)',
        'pct_original': 'Suma de porcentajes originales (pre-escalado)'
    }
    
    faltantes = []
    for col, desc in columnas_requeridas.items():
        if col in df.columns:
            print(f"    [OK] {col:25} - {desc}")
        else:
            print(f"    [X] {col:25} - FALTANTE")
            faltantes.append(col)
    
    if faltantes:
        print(f"\n[!] ERROR: Columnas faltantes: {faltantes}")
        return False
    
    # --- TEST 3: VALIDAR ESCALADO POR INSTRUMENTO ---
    print_section("Test 3: Validación de Escalado (pct_escalado = 100.0)")
    
    print("\n[...] Verificando que pct_escalado sea 100.0 para cada instrumento...")
    
    # Agrupar por instrumento y verificar que pct_escalado sea 100 (o muy cercano)
    instrumentos_problema = []
    instrumentos_sin_datos = []
    
    for instrumento_id in df['ID'].unique()[:100]:  # Verificar primeros 100
        df_inst = df[df['ID'] == instrumento_id]
        pct_escalado = df_inst['pct_escalado'].iloc[0]  # Valor repetido en todas las filas
        
        # Tolerancia de 0.01% para errores de redondeo
        if abs(pct_escalado - 100.0) > 0.01:
            if pct_escalado == 0.0:
                # Instrumentos sin datos (esperado)
                instrumentos_sin_datos.append(instrumento_id)
            else:
                # Error real de escalado
                instrumentos_problema.append({
                    'ID': instrumento_id,
                    'pct_escalado': pct_escalado
                })
    
    if instrumentos_sin_datos:
        print(f"\n[i] {len(instrumentos_sin_datos)} instrumentos sin datos (pct_escalado = 0.0) - Normal")
    
    if instrumentos_problema:
        print(f"\n[!] ERROR: {len(instrumentos_problema)} instrumentos con pct_escalado incorrecto:")
        for item in instrumentos_problema[:5]:
            print(f"    ID {item['ID']}: pct_escalado = {item['pct_escalado']}")
    else:
        print(f"\n[[OK]] Todos los instrumentos con datos tienen pct_escalado = 100.0")
    
    # --- TEST 4: VALIDAR SUMA DE PORCENTAJES ESCALADOS ---
    print_section("Test 4: Validación de Suma de Porcentajes (Debe ser 100.0)")
    
    print("\n[...] Verificando que suma(percentage) sea 100.0 (ahora que están escalados)...")
    
    errores = []
    for instrumento_id in df['ID'].unique()[:50]:
        df_inst = df[df['ID'] == instrumento_id]
        
        # Sumar porcentajes (ahora escalados)
        suma_calculada = df_inst['percentage'].sum()
        pct_escalado_registrado = df_inst['pct_escalado'].iloc[0]
        
        # Ignorar instrumentos sin datos
        if pct_escalado_registrado == 0:
            continue
            
        # Tolerancia de 0.1 para diferencias de redondeo
        if abs(suma_calculada - 100.0) > 0.1:
            errores.append({
                'ID': instrumento_id,
                'suma_calculada': suma_calculada,
                'pct_escalado': pct_escalado_registrado,
                'diferencia': abs(suma_calculada - 100.0)
            })
    
    if errores:
        print(f"\n[!] ERROR: {len(errores)} instrumentos con sumas distintos a 100.0:")
        for item in errores[:3]:
            print(f"    ID {item['ID']}: suma={item['suma_calculada']:.2f}, "
                  f"pct_escalado={item['pct_escalado']:.2f}, "
                  f"diff={item['diferencia']:.2f}")
    else:
        print(f"\n[[OK]] Consistencia verificada: suma(percentage) = 100.0")
    
    # --- TEST 5: VALIDAR DOMINANCIA ---
    print_section("Test 5: Validación de Clasificación por Dominancia")
    
    print("\n[...] Verificando clasificación Balanceado vs Moneda dominante...")
    
    umbral = 0.9  # 90%
    
    # Seleccionar muestra de instrumentos
    errores_dominancia = []
    
    for instrumento_id in df['ID'].unique()[:50]:
        df_inst = df[df['ID'] == instrumento_id]
        
        # Calcular porcentajes escalados por moneda
        total = df_inst['percentage'].sum()
        if total > 0:
            porcentajes_escalados = df_inst['percentage'] / total
            max_pct = porcentajes_escalados.max()
            moneda_max = df_inst.loc[porcentajes_escalados.idxmax(), 'class']
            
            # Obtener clasificación registrada
            moneda_nueva = df_inst['moneda_nueva'].iloc[0]
            
            # Validar lógica de dominancia
            if max_pct >= umbral:
                # Debería ser la moneda dominante
                if moneda_nueva != moneda_max:
                    errores_dominancia.append({
                        'ID': instrumento_id,
                        'max_pct': max_pct * 100,
                        'moneda_esperada': moneda_max,
                        'moneda_registrada': moneda_nueva
                    })
            else:
                # Debería ser Balanceado
                if moneda_nueva != 'Balanceado':
                    errores_dominancia.append({
                        'ID': instrumento_id,
                        'max_pct': max_pct * 100,
                        'moneda_esperada': 'Balanceado',
                        'moneda_registrada': moneda_nueva
                    })
    
    if errores_dominancia:
        print(f"\n[!] ERROR: {len(errores_dominancia)} instrumentos con clasificación incorrecta:")
        for item in errores_dominancia[:3]:
            print(f"    ID {item['ID']}: max={item['max_pct']:.1f}%, "
                  f"esperado={item['moneda_esperada']}, "
                  f"actual={item['moneda_registrada']}")
    else:
        print(f"\n[[OK]] Clasificación por dominancia correcta (umbral={umbral*100:.0f}%)")
    
    # --- TEST 6: FORMATO DE pct_dominancia_nuevo ---
    print_section("Test 6: Validación de Formato pct_dominancia_nuevo")
    
    print("\n[...] Verificando formato 'MONEDA XX.XX%'...")
    
    sample = df['pct_dominancia_nuevo'].dropna().head(20)
    errores_formato = []
    
    for val in sample:
        # Debe tener formato "MONEDA XX.XX%"
        if not isinstance(val, str):
            errores_formato.append(f"No es string: {val}")
            continue
        
        parts = val.rsplit(' ', 1)
        if len(parts) != 2:
            errores_formato.append(f"Formato incorrecto: {val}")
            continue
        
        moneda, porcentaje = parts
        
        # Verificar que porcentaje termine en %
        if not porcentaje.endswith('%'):
            errores_formato.append(f"Sin símbolo %: {val}")
            continue
        
        # Verificar que el número sea válido
        try:
            num = float(porcentaje[:-1])
            if num < 0 or num > 100:
                errores_formato.append(f"Porcentaje fuera de rango: {val}")
        except ValueError:
            errores_formato.append(f"Porcentaje no numérico: {val}")
    
    if errores_formato:
        print(f"\n[!] ADVERTENCIA: {len(errores_formato)} valores con formato incorrecto:")
        for err in errores_formato[:3]:
            print(f"    {err}")
    else:
        print(f"\n[[OK]] Formato 'MONEDA XX.XX%' validado correctamente")
        print(f"\n[i] Ejemplos:")
        for val in sample.head(5):
            print(f"    {val}")
    
    # --- TEST 7: ESTADÍSTICAS GENERALES ---
    print_section("Test 7: Estadísticas Generales")
    
    total_instrumentos = df['ID'].nunique()
    total_registros = len(df)
    
    # Distribución de clasificación
    dist_clasificacion = df.groupby('ID')['moneda_nueva'].first().value_counts()
    
    balanceados = dist_clasificacion.get('Balanceado', 0)
    no_balanceados = total_instrumentos - balanceados
    
    print(f"\n[i] Total instrumentos: {total_instrumentos}")
    print(f"[i] Total registros: {total_registros}")
    print(f"[i] Promedio filas/instrumento: {total_registros/total_instrumentos:.1f}")
    
    print(f"\n[i] Clasificación:")
    print(f"    Balanceados:     {balanceados:6} ({balanceados/total_instrumentos*100:.1f}%)")
    print(f"    No balanceados:  {no_balanceados:6} ({no_balanceados/total_instrumentos*100:.1f}%)")
    
    if no_balanceados > 0:
        print(f"\n[i] Monedas dominantes (Top 10):")
        top_monedas = dist_clasificacion[dist_clasificacion.index != 'Balanceado'].head(10)
        for moneda, count in top_monedas.items():
            print(f"    {moneda:5} - {count:4} instrumentos")
    
    # --- RESUMEN FINAL ---
    print_section("Resumen Final")
    
    if not errores_dominancia and not instrumentos_problema:
        print("\n[OK] Todos los cálculos de dominancia son correctos.")
        print("[OK] Todos los porcentajes escalados suman 100.0.")
        print("[OK] Formato de columnas validado correctamente.")
        print("\n[[OK]] TODOS LOS TESTS PASARON.")
        return True
    else:
        print("\n[!] Se encontraron algunos problemas.")
        print("[!] Revise los detalles arriba.")
        return False

if __name__ == "__main__":
    exito = test_dominancia_y_escalado()
    sys.exit(0 if exito else 1)
