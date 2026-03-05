"""
Módulo para generar los exports finales con formatos específicos.

Este módulo se encarga de transformar los dataframes procesados
a los formatos requeridos para los archivos de exportación.
"""
import pandas as pd


def _calcular_estado_balanceados(row):
    """
    Calcula el estado para el export de balanceados.
    
    Lógica:
    - Estado_1: Balanceado → Balanceado
    - Estado_2: Moneda → Balanceado
    - Estado_3: FALTA ALLOCATION (columna "Moneda:" = "FALTA ALLOCATION")
    
    Parámetros:
        row: Fila del DataFrame con 'moneda_antigua', 'moneda_nueva' y 'Moneda:'
    
    Retorna:
        str: Estado_1, Estado_2 o Estado_3
    """
    antigua = str(row.get('moneda_antigua', '')).strip().upper()
    nueva = str(row.get('moneda_nueva', '')).strip().upper()
    moneda_col = str(row.get('Moneda:', '')).strip()  # de allocations_antiguas

    # Estado_3: Solo si "Moneda:" es "FALTA ALLOCATION"
    if moneda_col == 'FALTA ALLOCATION':
        return 'Estado_3'

    # Estado_1: Balanceado → Balanceado
    if antigua == 'BALANCEADO' and nueva == 'BALANCEADO':
        return 'Estado_1'

    # Estado_2: Moneda → Balanceado
    if antigua not in ['BALANCEADO', '', 'NAN', 'NONE'] and nueva == 'BALANCEADO':
        return 'Estado_2'

    # Por defecto (no debería llegar aquí en balanceados, pero por seguridad)
    return 'Estado_2'


def _calcular_estado_no_balanceados(row):
    """
    Calcula el estado para el export de no balanceados.
    
    Lógica:
    - Estado_1: Moneda → Misma Moneda (ej: USD → USD)
    - Estado_2: Balanceado → Moneda
    - Estado_3: Moneda → Otra Moneda (ej: USD → EUR)
    
    Parámetros:
        row: Fila del DataFrame con 'moneda_antigua' y 'SubMoneda'
    
    Retorna:
        str: Estado_1, Estado_2 o Estado_3
    """
    antigua = str(row.get('Moneda Anterior', '')).strip().upper()
    nueva = str(row.get('SubMoneda', '')).strip().upper()
    
    # Estado_2: Balanceado → Moneda
    if antigua == 'BALANCEADO' and nueva not in ['BALANCEADO', '', 'NAN', 'NONE']:
        return 'Estado_2'
    
    # Estado_1: Moneda → Misma Moneda
    if antigua == nueva and antigua not in ['BALANCEADO', '', 'NAN', 'NONE']:
        return 'Estado_1'
    
    # Estado_3: Moneda → Otra Moneda
    if antigua not in ['BALANCEADO', '', 'NAN', 'NONE'] and nueva not in ['BALANCEADO', '', 'NAN', 'NONE'] and antigua != nueva:
        return 'Estado_3'
    
    # Por defecto
    return 'Estado_3'


def generar_export_balanceados(df_final, df_allocations_nuevas, df_instruments, df_allocations_antiguas):
    """
    Genera el export de instrumentos balanceados con formato específico.
    
    Formato del export:
    - ID (df_final)
    - Instrumento (Nombre de df_final)
    - Id_ti_valor (instrument de allocations_nuevas)
    - Id_ti (tipo_id de allocations_nuevas - tipo de identificador usado: RIC, Isin, Cusip)
    - Fecha (vacía por ahora)
    - Clasificacion (vacía por ahora)
    - Moneda Anterior (moneda_antigua de df_final)
    - Estado (campo calculado, por ahora vacío)
    - pct_original (de df_final)
    - [Monedas dinámicas] (USD, CLP, EUR, etc. en formato WIDE)
    
    Parámetros:
        df_final: DataFrame final consolidado
        df_allocations_nuevas: DataFrame con allocations nuevas en formato LONG
        df_instruments: DataFrame con información de instrumentos (para obtener SubMoneda)
        df_allocations_antiguas: DataFrame con allocations antiguas (para obtener columna "Moneda:")
    
    Retorna:
        DataFrame con formato de export para balanceados
    """
    # 1. Filtrar solo instrumentos balanceados
    df_balanceados_final = df_final[df_final['moneda_nueva'] == 'Balanceado'].copy()
    
    if len(df_balanceados_final) == 0:
        print("ADVERTENCIA: No hay instrumentos balanceados para exportar.")
        return pd.DataFrame()
    
    # 2. Filtrar allocations_nuevas solo para IDs balanceados
    ids_balanceados = df_balanceados_final['ID'].unique()
    df_alloc_balanceados = df_allocations_nuevas[
        df_allocations_nuevas['ID'].isin(ids_balanceados)
    ].copy()
    
    # 3. Transformar de formato LONG a WIDE (pivot sobre monedas)
    # Crear pivot con las monedas como columnas y sus porcentajes
    df_pivot = df_alloc_balanceados.pivot_table(
        index='ID',
        columns='class',  # class es la moneda (USD, CLP, EUR, etc.)
        values='percentage',
        aggfunc='first'
    ).reset_index()
    
    # 4. Obtener información adicional de allocations_nuevas (instrument, tipo_id)
    # Tomar la primera fila de cada ID para obtener estos valores
    cols_info = ['instrument', 'tipo_id']
    # Eliminamos 'date' de los exports, solo usamos 'Fecha' calculada abajo
    df_info = df_alloc_balanceados.groupby('ID').agg({
        col: 'first' for col in cols_info if col in df_alloc_balanceados.columns
    }).reset_index()
    
    # 5. Merge de df_final con información adicional
    df_export = df_balanceados_final[['ID', 'Nombre', 'moneda_antigua', 'pct_original']].copy()
    
    # Merge con información de allocations (instrument, tipo_id)
    df_export = pd.merge(df_export, df_info, on='ID', how='left')
    
    # Merge con el pivot de monedas
    df_export = pd.merge(df_export, df_pivot, on='ID', how='left')
    
    # 6. ANTES DE RENOMBRAR: Obtener SubMoneda desde df_instruments para cálculo de Fecha
    df_export = pd.merge(
        df_export,
        df_instruments[['ID', 'SubMoneda']],
        on='ID',
        how='left'
    )
    
    # 7. Obtener columna "Moneda:" desde df_allocations_antiguas para calcular Estado
    df_export = pd.merge(
        df_export,
        df_allocations_antiguas[['ID', 'Moneda:']],
        on='ID',
        how='left'
    )
    
    # 8. Obtener también moneda_nueva de df_final para calcular Estado
    # (moneda_antigua ya está en df_export)
    df_export = pd.merge(
        df_export,
        df_final[['ID', 'moneda_nueva']],
        on='ID',
        how='left',
        suffixes=('', '_final')
    )
    
    # 9. Calcular campos ANTES de renombrar columnas
    from datetime import datetime
    hoy = datetime.now()
    primer_dia_mes = hoy.replace(day=1).strftime('%d-%m-%Y')
    
    # Calcular Fecha (basado en columna "Moneda:")
    df_export['Fecha'] = df_export['Moneda:'].apply(
        lambda x: '31-12-2019' if str(x).strip() == 'FALTA ALLOCATION' else primer_dia_mes
    )
    
    # Calcular Clasificacion
    df_export['Clasificacion'] = 'SubMoneda'
    
    # Calcular Estado (necesita "Moneda:", moneda_antigua, moneda_nueva)
    df_export['Estado'] = df_export.apply(_calcular_estado_balanceados, axis=1)
    
    # 10. AHORA SÍ renombrar columnas según especificación
    df_export.rename(columns={
        'Nombre': 'Instrumento',
        'instrument': 'Id_ti_valor',
        'tipo_id': 'Id_ti',
        'moneda_antigua': 'Moneda Anterior'
    }, inplace=True)
    
    # 11. Limpiar columnas temporales
    cols_to_drop = [c for c in df_export.columns if c in ['SubMoneda', 'moneda_nueva', 'Moneda:', 'date']]
    df_export = df_export.drop(columns=cols_to_drop, errors='ignore')
    
    # 8. Reordenar columnas: primero las fijas, luego las monedas dinámicas
    columnas_fijas = ['ID', 'Instrumento', 'Id_ti_valor', 'Id_ti', 'Fecha', 
                     'Clasificacion', 'Moneda Anterior', 'Estado', 'pct_original']
    
    # Identificar columnas de monedas (todas las que no están en fijas)
    columnas_monedas = [col for col in df_export.columns if col not in columnas_fijas]
    
    # Ordenar columnas finales
    columnas_finales = [col for col in columnas_fijas if col in df_export.columns] + columnas_monedas
    df_export = df_export[columnas_finales]
    
    return df_export


def generar_export_no_balanceados(df_final):
    """
    Genera el export de instrumentos NO balanceados con formato específico.
    
    Formato del export:
    - ID (df_final)
    - Instrumento (Nombre de df_final)
    - SubMoneda (moneda_nueva de df_final - la nueva clasificación)
    - Moneda Anterior (moneda_antigua de df_final)
    - Estado (calculado según lógica: Estado_1, Estado_2, Estado_3)
    - Sobreescribir (calculado: "Sí" si hay cambio, "No" si no hay cambio)
    
    Parámetros:
        df_final: DataFrame final consolidado
    
    Retorna:
        DataFrame con formato de export para no balanceados
    """
    # 1. Filtrar solo instrumentos NO balanceados
    df_no_balanceados = df_final[df_final['moneda_nueva'] != 'Balanceado'].copy()
    
    if len(df_no_balanceados) == 0:
        print("ADVERTENCIA: No hay instrumentos no balanceados para exportar.")
        return pd.DataFrame()
    
    # 2. Seleccionar y renombrar columnas
    df_export = df_no_balanceados[['ID', 'Nombre', 'moneda_nueva', 'moneda_antigua', 'Cambio']].copy()
    
    df_export.rename(columns={
        'Nombre': 'Instrumento',
        'moneda_nueva': 'SubMoneda',
        'moneda_antigua': 'Moneda Anterior'
    }, inplace=True)
    
    # 3. Calcular columna Estado
    df_export['Estado'] = df_export.apply(_calcular_estado_no_balanceados, axis=1)
    
    # 4. Calcular columna Sobreescribir
    # "Sí" si Cambio == "Sí", "No" en caso contrario
    df_export['Sobreescribir'] = df_export['Cambio'].apply(
        lambda x: 'Sí' if x == 'Sí' else 'No'
    )
    
    # 5. Eliminar columna auxiliar Cambio (ya no se necesita en el export)
    df_export = df_export[['ID', 'Instrumento', 'SubMoneda', 'Moneda Anterior', 'Estado', 'Sobreescribir']]
    
    return df_export


def generar_export_sin_datos(df_instruments, df_allocations_nuevas):
    """
    Genera el export de instrumentos sin datos.
    
    Este export contiene los instrumentos que:
    1. NO se encuentran en allocations nuevas, O
    2. Se encuentran PERO todas sus filas tienen percentage = NA/inválido
    
    Formato del export:
    - ID (df_instruments)
    - Instrumento (Nombre de df_instruments)
    
    Parámetros:
        df_instruments: DataFrame con instrumentos filtrados
        df_allocations_nuevas: DataFrame con allocations nuevas en formato LONG
    
    Retorna:
        DataFrame con formato de export para instrumentos sin datos
    """
    # 1. Identificar IDs en df_instruments
    ids_instruments = set(df_instruments['ID'].unique())
    
    # 2. Identificar IDs en allocations_nuevas
    ids_allocations = set(df_allocations_nuevas['ID'].unique())
    
    # 3. Calcular diferencia: instrumentos SIN allocations nuevas
    ids_sin_datos = ids_instruments - ids_allocations
    
    # 4. NUEVO: Identificar instrumentos que ESTÁN en allocations pero tienen TODAS las filas con percentage inválido
    ids_con_datos_invalidos = set()
    for id_instrumento in ids_allocations:
        grupo = df_allocations_nuevas[df_allocations_nuevas['ID'] == id_instrumento]
        # Verificar si TODAS las filas tienen percentage inválido
        percentages_validos = grupo['percentage'].dropna()
        percentages_validos = percentages_validos[percentages_validos > 0]
        
        if len(percentages_validos) == 0:
            ids_con_datos_invalidos.add(id_instrumento)
    
    # 5. Combinar ambos sets: instrumentos sin datos = no encontrados + con datos inválidos
    ids_sin_datos = ids_sin_datos | ids_con_datos_invalidos
    
    # LOG: Informar sobre ambos tipos de instrumentos sin datos
    print(f"  [INFO] Instrumentos sin datos:")
    print(f"    - No encontrados en allocations nuevas: {len(ids_sin_datos - ids_con_datos_invalidos)}")
    print(f"    - Con TODAS las filas percentage=NA: {len(ids_con_datos_invalidos)}")
    print(f"    - TOTAL sin datos: {len(ids_sin_datos)}")
    
    if len(ids_sin_datos) == 0:
        print("ADVERTENCIA: No hay instrumentos sin datos.")
        return pd.DataFrame(columns=['ID', 'Instrumento'])
    
    # 6. Filtrar df_instruments para obtener solo los sin datos
    df_sin_datos = df_instruments[df_instruments['ID'].isin(ids_sin_datos)].copy()
    
    # 7. Seleccionar y renombrar columnas
    df_export = df_sin_datos[['ID', 'Nombre']].copy()
    df_export.rename(columns={'Nombre': 'Instrumento'}, inplace=True)
    
    return df_export



# ============================================================================
# BLOQUE DE TEST Y EJECUCIÓN MANUAL
# ============================================================================

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, '.')
    from src.extractors.moneda.load_instruments import load_df_instruments
    from src.extractors.moneda.load_allocations import load_allocations_nuevas, load_allocations_antiguas
    from src.logic.moneda.crear_df_final import crear_df_final
    
    print("\n" + "="*70)
    print(" TEST: GENERACIÓN DE EXPORTS ".center(70, "="))
    print("="*70)
    
    # FASE 1: CARGAR DATOS BASE
    print("\n[Fase 1/4] Cargando datos base...")
    df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
    print(f"  [OK] df_instruments: {len(df_instr)} registros")
    
    # FASE 2: CARGAR ALLOCATIONS NUEVAS
    print("\n[Fase 2/4] Cargando allocations nuevas...")
    df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
    print(f"  [OK] {len(df_nuevas)} registros (formato long)")
    
    # FASE 3: CARGAR ALLOCATIONS ANTIGUAS
    print("\n[Fase 3/4] Cargando allocations antiguas...")
    df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
    print(f"  [OK] {len(df_antiguas)} instrumentos procesados")
    
    # FASE 4: CREAR DF_FINAL
    print("\n[Fase 4/4] Creando df_final...")
    df_final = crear_df_final(df_instr, df_nuevas, df_antiguas)
    print(f"  [OK] df_final creado con {len(df_final)} registros")
    
    # GENERACIÓN DE EXPORTS
    print("\n" + "="*70)
    print(" GENERANDO EXPORTS ".center(70, "="))
    print("="*70)
    
    print("\n[Export 1/2] Generando export de balanceados...")
    export_balanceados = generar_export_balanceados(df_final, df_nuevas, df_instr, df_antiguas)
    print(f"  [OK] {len(export_balanceados)} registros")
    print(f"  Columnas: {list(export_balanceados.columns)}")
    
    print("\n[Export 2/2] Generando export de no balanceados...")
    export_no_balanceados = generar_export_no_balanceados(df_final)
    print(f"  [OK] {len(export_no_balanceados)} registros")
    print(f"  Columnas: {list(export_no_balanceados.columns)}")
    
    # GUARDAR EXPORTS
    print("\n" + "="*70)
    print(" GUARDANDO EXPORTS ".center(70, "="))
    print("="*70)
    
    os.makedirs('data/exports', exist_ok=True)
    
    export_balanceados.to_csv(
        'data/exports/export_balanceados.csv',
        index=False,
        sep=';',
        encoding='latin-1'
    )
    print("  💾 data/exports/export_balanceados.csv")
    
    export_no_balanceados.to_csv(
        'data/exports/export_no_balanceados.csv',
        index=False,
        sep=';',
        encoding='latin-1'
    )
    print("  💾 data/exports/export_no_balanceados.csv")
    
    # PREVIEW DE LOS EXPORTS
    print("\n" + "="*70)
    print(" PREVIEW EXPORT BALANCEADOS ".center(70, "="))
    print("="*70)
    if len(export_balanceados) > 0:
        print("\nPrimeras 5 filas:")
        print(export_balanceados.head(5).to_string(index=False))
    
    print("\n" + "="*70)
    print(" PREVIEW EXPORT NO BALANCEADOS ".center(70, "="))
    print("="*70)
    if len(export_no_balanceados) > 0:
        print("\nPrimeras 10 filas:")
        print(export_no_balanceados.head(10).to_string(index=False))
    
    # RESUMEN FINAL
    print("\n" + "="*70)
    print(" TEST COMPLETADO EXITOSAMENTE ".center(70, "="))
    print("="*70)
    print(f"\nExports generados:")
    print(f"  - Balanceados:     {len(export_balanceados)} registros")
    print(f"  - No balanceados:  {len(export_no_balanceados)} registros")
    print(f"  - Total:           {len(export_balanceados) + len(export_no_balanceados)} registros")
    print("\n")
