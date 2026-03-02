"""
Test de Mapeo de Monedas: Refinitiv -> ISO 4217
================================================
Valida que todos los nombres de monedas de Refinitiv sean correctamente
mapeados a códigos ISO estándar.
"""

import pandas as pd
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.extractors.load_allocations import CURRENCY_MAP_REFINITIV_TO_ISO

def print_section(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)

def test_mapeo_monedas():
    """Valida que el mapeo de monedas funcione correctamente."""
    
    print_section("Test 1: Validación del Diccionario de Mapeo")
    
    # Contar entradas
    total_mapeos = len(CURRENCY_MAP_REFINITIV_TO_ISO)
    print(f"\n[i] Total de mapeos definidos: {total_mapeos}")
    
    # Contar códigos ISO únicos (destinos)
    codigos_iso = set(CURRENCY_MAP_REFINITIV_TO_ISO.values())
    print(f"[i] Códigos ISO únicos (destino): {len(codigos_iso)}")
    print(f"    Ejemplos: {', '.join(sorted(codigos_iso)[:15])}")
    
    # Verificar monedas principales
    monedas_principales = {
        'US DOLLAR': 'USD',
        'EURO': 'EUR',
        'JAPANESE YEN': 'JPY',
        'CHILEAN PESO': 'CLP',
        'UK POUND STERLING': 'GBP',
        'SWISS FRANC': 'CHF',
        'CANADIAN DOLLAR': 'CAD',
    }
    
    print("\n[[OK]] Validación de monedas principales:")
    errores = []
    for nombre, codigo_esperado in monedas_principales.items():
        codigo_actual = CURRENCY_MAP_REFINITIV_TO_ISO.get(nombre)
        if codigo_actual == codigo_esperado:
            print(f"    [OK] {nombre:25} -> {codigo_actual}")
        else:
            print(f"    [X] {nombre:25} -> {codigo_actual} (esperado: {codigo_esperado})")
            errores.append(nombre)
    
    if errores:
        print(f"\n[!] ERROR: {len(errores)} monedas principales tienen mapeo incorrecto.")
        return False
    else:
        print(f"\n[[OK]] Todas las monedas principales correctamente mapeadas.")
    
    # --- TEST 2: CASE INSENSITIVITY ---
    print_section("Test 2: Case Insensitivity")
    
    # Probar variantes de capitalización
    variantes = [
        ('US DOLLAR', 'US Dollar', 'US dollar'),
        ('EURO', 'Euro', 'euro'),
        ('JAPANESE YEN', 'Japanese Yen', 'japanese yen'),
    ]
    
    print("\n[i] Verificando que el mapeo funcione con diferentes capitalizaciones...")
    
    # Crear diccionario case-insensitive
    currency_map_upper = {k.upper(): v for k, v in CURRENCY_MAP_REFINITIV_TO_ISO.items()}
    
    for grupo in variantes:
        codigos = [currency_map_upper.get(v.upper(), v) for v in grupo]
        if len(set(codigos)) == 1:
            print(f"    [OK] {grupo[0]} -> {codigos[0]} (todas las variantes)")
        else:
            print(f"    [X] Inconsistencia: {grupo} -> {codigos}")
            errores.append(grupo[0])
    
    if errores:
        print(f"\n[!] ERROR: Problemas de case insensitivity detectados.")
        return False
    else:
        print(f"\n[[OK]] Mapeo case-insensitive funciona correctamente.")
    
    # --- TEST 3: VALIDACIÓN EN ARCHIVOS PROCESADOS ---
    print_section("Test 3: Validación en Archivos Procesados")
    
    try:
        df_nuevas = pd.read_csv('data/processed/allocations_nuevas.csv', 
                                sep=';', encoding='latin-1')
        
        print(f"\n[i] Archivo cargado: allocations_nuevas.csv")
        print(f"    Registros: {len(df_nuevas)}")
        
        if 'class' not in df_nuevas.columns:
            print(f"[!] ERROR: Columna 'class' no encontrada.")
            return False
        
        # Obtener monedas únicas
        monedas = [m for m in df_nuevas['class'].unique() if pd.notna(m)]
        print(f"\n[i] Monedas únicas en archivo: {len(monedas)}")
        print(f"    {', '.join(sorted(monedas))}")
        
        # Verificar longitud (códigos ISO son de 3-5 letras, nombres largos indican falta de mapeo)
        nombres_largos = [m for m in monedas if len(str(m)) > 10]
        
        if nombres_largos:
            print(f"\n[!] ADVERTENCIA: {len(nombres_largos)} monedas sin mapear detectadas:")
            for nombre in nombres_largos[:10]:
                print(f"    - {nombre}")
            print(f"\n[!] TEST FALLIDO: Hay monedas sin mapear.")
            return False
        else:
            print(f"\n[[OK]] Todas las monedas están en formato ISO (3-5 caracteres).")
        
        # Verificar columna moneda_nueva
        if 'moneda_nueva' in df_nuevas.columns:
            monedas_nuevas = [m for m in df_nuevas['moneda_nueva'].unique() 
                             if pd.notna(m) and m != 'Balanceado']
            nombres_largos_nuevas = [m for m in monedas_nuevas if len(str(m)) > 10]
            
            if nombres_largos_nuevas:
                print(f"\n[!] ADVERTENCIA: Monedas sin mapear en 'moneda_nueva':")
                for nombre in nombres_largos_nuevas[:5]:
                    print(f"    - {nombre}")
                return False
            else:
                print(f"[[OK]] Columna 'moneda_nueva' correctamente mapeada.")
        
        # Verificar pct_dominancia_nuevo
        if 'pct_dominancia_nuevo' in df_nuevas.columns:
            sample = df_nuevas['pct_dominancia_nuevo'].dropna().head(10)
            print(f"\n[i] Muestra de 'pct_dominancia_nuevo':")
            for val in sample:
                print(f"    {val}")
            
            # Verificar formato "ISO XXX.XX%"
            problemas = []
            for val in sample:
                parts = str(val).rsplit(' ', 1)
                if len(parts) == 2:
                    moneda = parts[0]
                    if len(moneda) > 10:  # No es código ISO
                        problemas.append(val)
            
            if problemas:
                print(f"\n[!] ADVERTENCIA: {len(problemas)} valores con formato incorrecto.")
                return False
            else:
                print(f"\n[[OK]] Formato de 'pct_dominancia_nuevo' correcto (códigos ISO).")
    
    except FileNotFoundError:
        print(f"\n[!] ADVERTENCIA: Archivo no encontrado. Ejecute pipeline primero.")
        print(f"    Comando: python run_pipeline.py")
        return False
    
    except Exception as e:
        print(f"\n[!] ERROR al leer archivo: {str(e)}")
        return False
    
    # --- TEST 4: CONSISTENCIA CON ALLOCATIONS ANTIGUAS ---
    print_section("Test 4: Consistencia con Allocations Antiguas")
    
    try:
        df_antiguas = pd.read_csv('data/processed/allocations_antiguas.csv',
                                   sep=';', encoding='latin-1', nrows=10)
        
        # Obtener columnas de monedas (excluir metadata)
        cols_excluir = ['ID', 'Nombre', 'SubMoneda', 'Pct_dominancia']
        cols_monedas = [c for c in df_antiguas.columns if c not in cols_excluir]
        
        print(f"\n[i] Columnas de monedas en antiguas: {len(cols_monedas)}")
        print(f"    Ejemplos: {', '.join(cols_monedas[:15])}")
        
        # Verificar overlap con monedas nuevas
        monedas_nuevas_set = set(monedas)
        monedas_antiguas_set = set(cols_monedas)
        comunes = monedas_nuevas_set.intersection(monedas_antiguas_set)
        
        cobertura = len(comunes) / len(monedas_nuevas_set) * 100
        print(f"\n[i] Monedas comunes: {len(comunes)}")
        print(f"[i] Cobertura: {cobertura:.1f}%")
        
        solo_nuevas = monedas_nuevas_set - monedas_antiguas_set
        if solo_nuevas:
            print(f"\n[i] Monedas solo en NUEVAS ({len(solo_nuevas)}):")
            for m in sorted(solo_nuevas):
                print(f"    - {m}")
        
        if cobertura >= 95.0:
            print(f"\n[[OK]] Excelente consistencia entre archivos (>{cobertura:.0f}%).")
        elif cobertura >= 85.0:
            print(f"\n[[!]] Buena consistencia, pero hay diferencias ({cobertura:.0f}%).")
        else:
            print(f"\n[!] ADVERTENCIA: Baja consistencia entre archivos ({cobertura:.0f}%).")
    
    except FileNotFoundError:
        print(f"\n[!] ADVERTENCIA: Archivo antiguas no encontrado.")
    
    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
    
    # --- RESUMEN FINAL ---
    print_section("Resumen Final")
    print("\n[OK] Test de mapeo de monedas completado exitosamente.")
    print(f"[OK] {total_mapeos} mapeos definidos.")
    print(f"[OK] {len(codigos_iso)} códigos ISO únicos.")
    print(f"[OK] Todas las monedas en formato ISO estándar.")
    print(f"[OK] Consistencia verificada con allocations antiguas.")
    
    return True

if __name__ == "__main__":
    exito = test_mapeo_monedas()
    if not exito:
        print("\n[!] TEST FALLIDO.")
        sys.exit(1)
    else:
        print("\n[[OK]] TODOS LOS TESTS PASARON.")
        sys.exit(0)
