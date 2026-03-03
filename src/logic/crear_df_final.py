"""
Módulo para crear el dataframe final consolidado para análisis.
"""
import pandas as pd


def crear_df_final(df_instruments, df_dominancia_nuevas, df_dominancia_antiguas):
    """
    Crea el dataframe final consolidado para análisis y validación.
    
    Columnas esperadas en df_final:
    - Nombre (df_instruments)
    - ID (df_instruments)
    - Tipo instrumento (df_instruments)
    - moneda_antigua (df_instruments.SubMoneda renombrada - clasificación antigua)
    - moneda_nueva (df_dominancia_nuevas - clasificación nueva calculada)
    - pct_dominancia_nuevo (df_dominancia_nuevas)
    - pct_escalado (df_dominancia_nuevas)
    - pct_original (df_dominancia_nuevas)
    - pct_dominancia_antigua (df_dominancia_antiguas.Pct_dominancia renombrada)
    - Cambio (calculado - comparación entre moneda_antigua y moneda_nueva)
    
    Parámetros:
        df_instruments: DataFrame base con info de instrumentos (SubMoneda = clasificación antigua)
        df_dominancia_nuevas: DataFrame con dominancia calculada de nuevas allocations
        df_dominancia_antiguas: DataFrame con dominancia calculada de antiguas allocations
    
    Retorna:
        DataFrame final consolidado para análisis
    """
    # 1. Seleccionar columnas base de df_instruments
    cols_base = ['ID', 'Nombre', 'Tipo instrumento', 'SubMoneda']
    # Verificar que existan en df_instruments
    cols_disponibles = [col for col in cols_base if col in df_instruments.columns]
    
    df_base = df_instruments[cols_disponibles].copy()
    
    # 2. Merge con dominancia nuevas
    # Consolidar para tener solo UNA fila por ID (eliminar duplicados del formato LONG)
    cols_nuevas = ['ID', 'moneda_nueva', 'pct_dominancia_nuevo', 'pct_escalado', 'pct_original']
    cols_nuevas_disponibles = [col for col in cols_nuevas if col in df_dominancia_nuevas.columns]
    
    df_nuevas_consolidado = df_dominancia_nuevas[cols_nuevas_disponibles].drop_duplicates(subset=['ID'], keep='first')
    
    df_final = pd.merge(
        df_base,
        df_nuevas_consolidado,
        on='ID',
        how='left'
    )
    
    # Renombrar SubMoneda a moneda_antigua (representa la clasificación antigua)
    if 'SubMoneda' in df_final.columns:
        df_final.rename(columns={'SubMoneda': 'moneda_antigua'}, inplace=True)
    
    # 3. Merge con dominancia antiguas (solo Pct_dominancia para referencia)
    cols_antiguas = ['ID', 'Pct_dominancia']
    cols_antiguas_disponibles = [col for col in cols_antiguas if col in df_dominancia_antiguas.columns]
    
    df_final = pd.merge(
        df_final,
        df_dominancia_antiguas[cols_antiguas_disponibles],
        on='ID',
        how='left'
    )
    
    # Renombrar para claridad
    if 'Pct_dominancia' in df_final.columns:
        df_final.rename(columns={'Pct_dominancia': 'pct_dominancia_antigua'}, inplace=True)
    
    # 4. Calcular columna de Cambio
    df_final['Cambio'] = df_final.apply(detectar_cambio, axis=1)
    
    # 5. Calcular columna de Estado (para filtros en frontend)
    df_final['Estado'] = df_final.apply(calcular_estado, axis=1)
    
    # 6. Reordenar columnas para presentación
    cols_orden = [
        'Nombre', 'ID', 'Tipo instrumento', 'moneda_antigua',
        'moneda_nueva', 'pct_dominancia_nuevo', 'pct_escalado', 'pct_original',
        'pct_dominancia_antigua', 'Cambio', 'Estado'
    ]
    
    # Seleccionar solo las que existen
    cols_finales = [col for col in cols_orden if col in df_final.columns]
    df_final = df_final[cols_finales]
    
    return df_final


def detectar_cambio(row):
    """
    Detecta si hubo cambio entre la moneda nueva y la antigua.
    Normaliza los nombres de monedas para comparar correctamente.
    
    Parámetros:
        row: Fila del DataFrame con columnas 'moneda_nueva' y 'moneda_antigua'
    
    Retorna:
        str: "Sí" si hay cambio, "No" si no hay cambio, "Sin datos" si falta información
    """
    if 'moneda_nueva' not in row or 'moneda_antigua' not in row:
        return "Sin datos"
    
    nueva = str(row['moneda_nueva']).strip().upper()
    antigua = str(row['moneda_antigua']).strip().upper()
    
    # Casos especiales
    if nueva in ['', 'NAN', 'NONE'] or antigua in ['', 'NAN', 'NONE', 'SIN DATOS']:
        return "Sin datos"
    
    # Mapeos comunes para normalizar
    mapeo = {
        "US DOLLAR": "USD",
        "UNITED STATES DOLLAR": "USD",
        "CHILEAN PESO": "CLP",
        "CHILE PESO": "CLP",
        "EURO": "EUR",
        "JAPANESE YEN": "JPY",
        "BRITISH POUND": "GBP"
    }
    
    nueva = mapeo.get(nueva, nueva)
    antigua = mapeo.get(antigua, antigua)
    
    if nueva == antigua:
        return "No"
    else:
        return "Sí"


def calcular_estado(row):
    """
    Calcula el estado del instrumento con la MISMA lógica que generar_exports.py.
    
    Lógica:
    - Sin datos: Cambio == "Sin datos" → retorna vacío ""
    - Para balanceados (moneda_nueva == "Balanceado"):
        * Estado_1: Balanceado → Balanceado (moneda_antigua == "BALANCEADO")
        * Estado_2: Moneda → Balanceado (moneda_antigua != "BALANCEADO")
    - Para no balanceados (moneda_nueva != "Balanceado"):
        * Estado_1: Moneda → Misma Moneda (moneda_antigua == moneda_nueva)
        * Estado_2: Balanceado → Moneda (moneda_antigua == "BALANCEADO")
        * Estado_3: Moneda → Otra Moneda (moneda_antigua != moneda_nueva)
    
    Parámetros:
        row: Fila del DataFrame con columnas 'moneda_nueva', 'moneda_antigua', 'Cambio'
    
    Retorna:
        str: "Estado_1", "Estado_2", "Estado_3" o "" (vacío para sin datos)
    """
    # Si no hay datos (Cambio == "Sin datos"), retornar vacío
    if 'Cambio' in row and str(row['Cambio']).strip() == "Sin datos":
        return ""
    
    # Obtener monedas
    if 'moneda_nueva' not in row or 'moneda_antigua' not in row:
        return ""
    
    moneda_nueva = str(row['moneda_nueva']).strip().upper()
    moneda_antigua = str(row['moneda_antigua']).strip().upper()
    
    # Si son vacías o NaN, retornar vacío
    if moneda_nueva in ['', 'NAN', 'NONE'] or moneda_antigua in ['', 'NAN', 'NONE']:
        return ""
    
    # CASO 1: Instrumentos BALANCEADOS (moneda_nueva == "BALANCEADO")
    if moneda_nueva == 'BALANCEADO':
        # Estado_1: Balanceado → Balanceado
        if moneda_antigua == 'BALANCEADO':
            return 'Estado_1'
        # Estado_2: Moneda → Balanceado
        else:
            return 'Estado_2'
    
    # CASO 2: Instrumentos NO BALANCEADOS (moneda_nueva es moneda específica)
    else:
        # Estado_2: Balanceado → Moneda
        if moneda_antigua == 'BALANCEADO':
            return 'Estado_2'
        
        # Estado_1: Moneda → Misma Moneda
        if moneda_antigua == moneda_nueva:
            return 'Estado_1'
        
        # Estado_3: Moneda → Otra Moneda
        return 'Estado_3'


def filtrar_cambios(df_final):
    """
    Filtra el df_final para mostrar solo los instrumentos con cambios.
    
    Retorna:
        DataFrame solo con instrumentos que tienen Cambio = "Sí"
    """
    if 'Cambio' not in df_final.columns:
        print("ADVERTENCIA: Columna 'Cambio' no encontrada.")
        return df_final
    
    return df_final[df_final['Cambio'] == 'Sí'].copy()


def filtrar_balanceados(df_final):
    """
    Filtra el df_final para mostrar solo los instrumentos balanceados.
    
    Retorna:
        DataFrame solo con instrumentos que tienen moneda_nueva = "Balanceado"
    """
    if 'moneda_nueva' not in df_final.columns:
        print("ADVERTENCIA: Columna 'moneda_nueva' no encontrada.")
        return df_final
    
    return df_final[df_final['moneda_nueva'] == 'Balanceado'].copy()


def filtrar_no_balanceados(df_final):
    """
    Filtra el df_final para mostrar solo los instrumentos NO balanceados.
    
    Retorna:
        DataFrame solo con instrumentos que tienen moneda_nueva != "Balanceado"
    """
    if 'moneda_nueva' not in df_final.columns:
        print("ADVERTENCIA: Columna 'moneda_nueva' no encontrada.")
        return df_final
    
    return df_final[df_final['moneda_nueva'] != 'Balanceado'].copy()



# ============================================================================
# BLOQUE DE TEST Y EJECUCIÓN MANUAL
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from src.extractors.load_instruments import load_df_instruments
    from src.extractors.load_allocations import load_allocations_nuevas, load_allocations_antiguas
    
    print("\n" + "="*70)
    print(" TEST: CREACIÓN DE DF_FINAL ".center(70, "="))
    print("="*70)
    
    # FASE 1: CARGAR DATOS BASE
    print("\n[Fase 1/4] Cargando datos base...")
    df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
    print(f"  [OK] df_instruments: {len(df_instr)} registros")
    
    # FASE 2: CARGAR ALLOCATIONS NUEVAS (YA CON DOMINANCIA)
    print("\n[Fase 2/4] Cargando allocations nuevas...")
    df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
    print(f"  [OK] {len(df_nuevas)} registros (formato long)")
    
    # FASE 3: CARGAR ALLOCATIONS ANTIGUAS (YA CON DOMINANCIA)
    print("\n[Fase 3/4] Cargando allocations antiguas...")
    df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
    print(f"  [OK] {len(df_antiguas)} instrumentos procesados")
    
    # FASE 4: CREAR DF_FINAL
    print("\n[Fase 4/4] Creando df_final...")
    df_final = crear_df_final(df_instr, df_nuevas, df_antiguas)
    print(f"  [OK] df_final creado con {len(df_final)} registros")
    print(f"  Columnas: {df_final.columns.tolist()}")
    
    # ESTADÍSTICAS
    print("\n" + "=" * 70)
    print(" ESTADÍSTICAS DEL DF_FINAL ".center(70, "="))
    print("=" * 70)
    print(f"Total instrumentos:     {len(df_final)}")
    
    if 'Cambio' in df_final.columns:
        cambios = (df_final['Cambio'] == 'Sí').sum()
        sin_cambios = (df_final['Cambio'] == 'No').sum()
        sin_datos = (df_final['Cambio'] == 'Sin datos').sum()
        print(f"  - Con cambios:        {cambios}")
        print(f"  - Sin cambios:        {sin_cambios}")
        print(f"  - Sin datos:          {sin_datos}")
    
    if 'moneda_nueva' in df_final.columns:
        balanceados = (df_final['moneda_nueva'] == 'Balanceado').sum()
        no_balanceados = len(df_final) - balanceados
        print(f"  - Balanceados:        {balanceados}")
        print(f"  - No balanceados:     {no_balanceados}")
    
    # EJEMPLOS
    print("\n" + "=" * 70)
    print(" EJEMPLOS DE DF_FINAL ".center(70, "="))
    print("=" * 70)
    cols_mostrar = ['Nombre', 'ID', 'moneda_nueva', 'moneda_antigua', 'Cambio']
    cols_disponibles = [c for c in cols_mostrar if c in df_final.columns]
    if cols_disponibles:
        print("\nPrimeros 10 registros:")
        print(df_final[cols_disponibles].head(10).to_string(index=False))
    
    # GUARDAR DF_FINAL PRINCIPAL
    output_path = 'data/processed/df_final.csv'
    df_final.to_csv(output_path, index=False, sep=';', encoding='latin-1')
    print(f"\n  💾 df_final guardado en {output_path}")
    
    # GENERAR ARCHIVOS FILTRADOS
    print("\n" + "=" * 70)
    print(" GENERANDO ARCHIVOS FILTRADOS ".center(70, "="))
    print("=" * 70)
    
    df_cambios = filtrar_cambios(df_final)
    df_cambios.to_csv('data/processed/df_final_con_cambios.csv', index=False, sep=';', encoding='latin-1')
    print(f"  💾 Con cambios: {len(df_cambios)} registros → df_final_con_cambios.csv")
    
    df_bal = filtrar_balanceados(df_final)
    df_bal.to_csv('data/processed/df_final_balanceados.csv', index=False, sep=';', encoding='latin-1')
    print(f"  💾 Balanceados: {len(df_bal)} registros → df_final_balanceados.csv")
    
    df_no_bal = filtrar_no_balanceados(df_final)
    df_no_bal.to_csv('data/processed/df_final_no_balanceados.csv', index=False, sep=';', encoding='latin-1')
    print(f"  💾 No balanceados: {len(df_no_bal)} registros → df_final_no_balanceados.csv")
    
    # RESUMEN FINAL
    print("\n" + "="*70)
    print(" TEST COMPLETADO EXITOSAMENTE ".center(70, "="))
    print("="*70)

