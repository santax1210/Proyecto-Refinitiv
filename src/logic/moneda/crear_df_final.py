"""
Módulo para crear el dataframe final consolidado para análisis.
"""
import pandas as pd
import numpy as np


# ============================================================================
# FUNCIONES PARA CÁLCULO DE DISTANCIA DE HELLINGER
# ============================================================================

def obtener_top_monedas_por_instrumento(row_antigua, top_n=5):
    """
    Obtiene las N monedas con mayor peso para UN INSTRUMENTO específico en allocations antiguas.
    
    EXCLUYE categorías especiales como "Balanceado", "Otros", etc.
    
    Parámetros:
        row_antigua: Fila del DataFrame de allocations antiguas para un instrumento
        top_n: Número de monedas principales a retornar (default: 5)
    
    Retorna:
        list: Lista de nombres de las top N monedas para ese instrumento (ej: ['USD', 'EUR', 'JPY'])
    """
    # Identificar columnas de metadata a excluir
    cols_metadata = [
        'ID', 'Nombre', 'SubMoneda', 'Pct_dominancia', 'Moneda:',
        'Creado', 'Tipo Instrumento', 'Tipo instrumento',
        'RIC', 'Isin', 'Cusip', 'Pais', 'País',
        'Nemo', 'Ticker_BB', 'Currency', 'Moneda'
    ]
    
    # EXCLUIR categorías especiales que NO son monedas reales
    categorias_excluir = [
        'Balanceado',  # No es moneda, indica distribución balanceada
        'Otros',       # Agrupación de monedas pequeñas
        'OTROS',
        'N/A',
        'Global'       # Otra categoría especial
    ]
    
    # Extraer valores de monedas para este instrumento
    monedas_valores = {}
    for col in row_antigua.index:
        if col not in cols_metadata and col not in categorias_excluir and len(col) <= 10:
            valor = pd.to_numeric(row_antigua[col], errors='coerce')
            if pd.notna(valor) and valor > 0:
                monedas_valores[col] = valor
    
    if not monedas_valores:
        return []
    
    # Ordenar por valor y tomar las top N
    top_monedas = sorted(monedas_valores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [moneda for moneda, _ in top_monedas]


def extraer_distribucion_antigua(row, top_monedas):
    """
    Extrae la distribución de monedas de un instrumento en allocations antiguas.
    
    Parámetros:
        row: Fila del DataFrame de allocations antiguas
        top_monedas: Lista de nombres de monedas a extraer
    
    Retorna:
        dict: {moneda: porcentaje} para las monedas especificadas
    """
    distribucion = {}
    for moneda in top_monedas:
        if moneda in row.index:
            valor = pd.to_numeric(row[moneda], errors='coerce')
            distribucion[moneda] = valor if pd.notna(valor) else 0.0
        else:
            distribucion[moneda] = 0.0
    return distribucion


def extraer_distribucion_nueva(df_nuevas, instrument_id, top_monedas):
    """
    Extrae la distribución de monedas de un instrumento en allocations nuevas.
    
    Parámetros:
        df_nuevas: DataFrame con allocations nuevas (formato long)
        instrument_id: ID del instrumento
        top_monedas: Lista de nombres de monedas a extraer
    
    Retorna:
        dict: {moneda: porcentaje} para las monedas especificadas
    """
    # Filtrar filas del instrumento
    df_inst = df_nuevas[df_nuevas['ID'] == instrument_id]
    
    if df_inst.empty:
        # Si no hay datos, retornar distribución vacía (ceros)
        return {moneda: 0.0 for moneda in top_monedas}
    
    # Extraer distribución
    distribucion = {moneda: 0.0 for moneda in top_monedas}
    
    for _, row in df_inst.iterrows():
        if 'class' in row and 'percentage' in row:
            moneda = str(row['class']).strip().upper()
            if moneda in top_monedas:
                porcentaje = pd.to_numeric(row['percentage'], errors='coerce')
                if pd.notna(porcentaje):
                    distribucion[moneda] = porcentaje
    
    return distribucion


def calcular_distancia_hellinger(dist1, dist2):
    """
    Calcula la distancia de Hellinger entre dos distribuciones de probabilidad.
    
    La distancia de Hellinger mide la similitud entre dos distribuciones de
    probabilidad y toma valores entre 0 (idénticas) y 1 (completamente diferentes).
    
    Fórmula: H = (1/√2) * √(Σ(√p_i - √q_i)²)
    
    Parámetros:
        dist1: dict {moneda: porcentaje} - Distribución 1 (antigua)
        dist2: dict {moneda: porcentaje} - Distribución 2 (nueva)
    
    Retorna:
        float: Distancia de Hellinger (0 a 1), o None si no se puede calcular
    """
    if not dist1 or not dist2:
        return None
    
    # Asegurar que ambas distribuciones tengan las mismas monedas
    monedas = set(dist1.keys()) | set(dist2.keys())
    
    # Normalizar a proporciones (dividir por 100 para trabajar con 0-1)
    suma1 = sum(dist1.values())
    suma2 = sum(dist2.values())
    
    # Si ambas sumas son 0, no hay distribución
    if suma1 == 0 and suma2 == 0:
        return 0.0
    
    # Si solo una es 0, distancia máxima
    if suma1 == 0 or suma2 == 0:
        return 1.0
    
    # Normalizar y calcular Hellinger
    suma_raices = 0.0
    for moneda in monedas:
        p1 = max(0, dist1.get(moneda, 0) / suma1)  # Asegurar no negativos
        p2 = max(0, dist2.get(moneda, 0) / suma2)  # Asegurar no negativos
        
        # Calcular diferencia de raíces cuadradas
        diff = np.sqrt(p1) - np.sqrt(p2)
        suma_raices += diff ** 2
    
    # Distancia de Hellinger
    hellinger = (1 / np.sqrt(2)) * np.sqrt(suma_raices)
    
    # Asegurar que esté en el rango [0, 1] (por errores de redondeo puede exceder ligeramente)
    hellinger = min(1.0, max(0.0, hellinger))
    
    return round(hellinger, 4)


def calcular_hellinger_por_instrumento(row, df_dominancia_antiguas, df_dominancia_nuevas):
    """
    Calcula la distancia de Hellinger para un instrumento específico.
    
    Las top 5 monedas se calculan específicamente para este instrumento basándose
    en su distribución en allocations antiguas, excluyendo "Balanceado" y "Otros".
    
    Parámetros:
        row: Fila del df_final con la información del instrumento
        df_dominancia_antiguas: DataFrame con allocations antiguas
        df_dominancia_nuevas: DataFrame con allocations nuevas
    
    Retorna:
        float: Distancia de Hellinger, o None si no se puede calcular
    """
    if 'ID' not in row:
        return None
    
    instrument_id = row['ID']
    
    # Extraer fila de allocations antiguas para este instrumento
    fila_antigua = df_dominancia_antiguas[df_dominancia_antiguas['ID'] == instrument_id]
    if fila_antigua.empty:
        return None
    
    # PASO 1: Obtener top 5 monedas ESPECÍFICAS de este instrumento
    top_monedas = obtener_top_monedas_por_instrumento(fila_antigua.iloc[0], top_n=5)
    
    if not top_monedas:
        # Si no hay monedas válidas, retornar None
        return None
    
    # PASO 2: Extraer distribución antigua usando esas top 5 monedas
    dist_antigua = extraer_distribucion_antigua(fila_antigua.iloc[0], top_monedas)
    
    # PASO 3: Extraer distribución nueva usando las MISMAS top 5 monedas
    dist_nueva = extraer_distribucion_nueva(df_dominancia_nuevas, instrument_id, top_monedas)
    
    # PASO 4: Calcular distancia de Hellinger
    return calcular_distancia_hellinger(dist_antigua, dist_nueva)


def calcular_variacion_balanceados(row, df_dominancia_antiguas, df_dominancia_nuevas):
    """
    Calcula la métrica de variación para instrumentos BALANCEADOS según el Estado.
    
    Lógica:
    - Estado_1 (Balanceado → Balanceado): Usa distancia de Hellinger (compara dos distribuciones)
    - Estado_2 (Moneda → Balanceado): Usa diferencia entre el pct de la moneda
      dominante antigua y el pct de esa MISMA moneda en la nueva distribución
    - Otros casos: Retorna None
    
    Parámetros:
        row: Fila del df_final con la información del instrumento
        df_dominancia_antiguas: DataFrame con allocations antiguas
        df_dominancia_nuevas: DataFrame con allocations nuevas
    
    Retorna:
        float: Métrica de variación según el Estado, o None si no aplica
    """
    # Solo aplica para instrumentos balanceados (moneda_nueva == "Balanceado")
    if 'moneda_nueva' not in row or str(row['moneda_nueva']).strip().upper() != 'BALANCEADO':
        return None
    
    # Verificar que tenga Estado
    if 'Estado' not in row or pd.isna(row['Estado']) or row['Estado'] == '':
        return None
    
    estado = str(row['Estado']).strip()
    
    # CASO 1: Estado_1 (Balanceado → Balanceado)
    # Usar distancia de Hellinger para comparar las dos distribuciones
    if estado == 'Estado_1':
        return calcular_hellinger_por_instrumento(row, df_dominancia_antiguas, df_dominancia_nuevas)
    
    # CASO 2: Estado_2 (Moneda → Balanceado)
    # Comparar el pct de la moneda dominante antigua con el pct de ESA MISMA
    # moneda en la nueva distribución (puede ser 0 si ya no aparece)
    elif estado == 'Estado_2':
        pct_antiguo = extraer_porcentaje_dominante(row, 'pct_dominancia_antigua')
        moneda_antigua = extraer_moneda_dominante(row, 'pct_dominancia_antigua')
        
        if pct_antiguo is not None and moneda_antigua is not None and 'ID' in row:
            # Buscar el % de esa misma moneda en la nueva distribución
            pct_misma_moneda = obtener_pct_moneda_en_nuevas(
                df_dominancia_nuevas, row['ID'], moneda_antigua
            )
            # Si el instrumento no tiene datos nuevos, no calcular
            if pct_misma_moneda is None:
                return None
            # Diferencia absoluta normalizada a escala 0-1
            # Ej: CLP 100% antigua → CLP 20% nueva → variacion = 0.80
            diferencia = abs(pct_antiguo - pct_misma_moneda) / 100.0
            return round(diferencia, 4)
        else:
            return None
    
    # Otros estados: no aplica
    return None


def extraer_porcentaje_dominante(row, columna):
    """
    Extrae el porcentaje numérico de una columna de dominancia.
    
    Formato esperado: "MONEDA XX.XX%" o "XX.XX"
    
    Parámetros:
        row: Fila del DataFrame
        columna: Nombre de la columna (ej: 'pct_dominancia_antigua')
    
    Retorna:
        float: Porcentaje numérico (0-100), o None si no se puede extraer
    """
    if columna not in row or pd.isna(row[columna]):
        return None
    
    valor = str(row[columna]).strip()
    
    if valor == '' or valor.upper() == 'SIN DATOS':
        return None
    
    # Intentar extraer número del formato "MONEDA XX.XX%"
    import re
    match = re.search(r'(\d+\.?\d*)\s*%', valor)
    if match:
        return float(match.group(1))
    
    # Intentar convertir directamente si es solo número
    try:
        return float(valor)
    except:
        return None


def extraer_moneda_dominante(row, columna):
    """
    Extrae el nombre de la moneda de una columna de dominancia.
    
    Formato esperado: "MONEDA XX.XX%" (ej: "CLP 100.00%" → "CLP")
    
    Parámetros:
        row: Fila del DataFrame
        columna: Nombre de la columna (ej: 'pct_dominancia_antigua')
    
    Retorna:
        str: Nombre de la moneda en mayúsculas, o None si no se puede extraer
    """
    if columna not in row or pd.isna(row[columna]):
        return None
    
    valor = str(row[columna]).strip()
    
    if valor == '' or valor.upper() == 'SIN DATOS':
        return None
    
    import re
    match = re.match(r'^([A-Za-z]+)', valor)
    if match:
        return match.group(1).upper()
    
    return None


def obtener_pct_moneda_en_nuevas(df_nuevas, instrument_id, moneda):
    """
    Obtiene el porcentaje ESCALADO de una moneda específica en las allocations nuevas.

    Escala los porcentajes crudos dividiéndolos por la suma total del instrumento,
    para que sean comparables con pct_dominancia_antigua (que ya está en escala 0-100%).

    Parámetros:
        df_nuevas: DataFrame con allocations nuevas (formato long)
        instrument_id: ID del instrumento
        moneda: Nombre de la moneda a buscar (ej: 'CLP')

    Retorna:
        float: Porcentaje escalado (0-100). Retorna 0.0 si el instrumento existe pero
               la moneda no está en la nueva distribución. None si el instrumento
               no existe.
    """
    df_inst = df_nuevas[df_nuevas['ID'] == instrument_id]

    if df_inst.empty:
        return None

    # Calcular suma total usando solo porcentajes positivos (igual que _escalar_porcentajes)
    # Ignorar negativos/cero para evitar totales distorsionados por posiciones cortas
    pct_series = pd.to_numeric(df_inst['percentage'], errors='coerce')
    total = pct_series[pct_series > 0].sum()

    for _, fila in df_inst.iterrows():
        if 'class' in fila:
            clase = str(fila['class']).strip().upper()
            if clase == moneda.upper():
                porcentaje = pd.to_numeric(fila['percentage'], errors='coerce')
                if pd.notna(porcentaje) and total > 0:
                    # Escalar al 100% para comparar con pct_dominancia_antigua
                    return round(porcentaje / total * 100, 4)

    # El instrumento existe en nuevas pero la moneda ya no aparece → 0%
    return 0.0


def calcular_variacion_no_balanceados(row, df_dominancia_nuevas):
    """
    Calcula la métrica de variación para instrumentos NO BALANCEADOS.

    Métrica (igual que balanceados Estado_2): diferencia entre el pct de la
    moneda dominante antigua y el pct de esa MISMA moneda en la nueva
    distribución.

    Aplica a todos los Estados de no balanceados:
    - Estado_1 (Moneda → Misma Moneda): cuánto cambió el % aunque la moneda sea la misma
    - Estado_2 (Balanceado → Moneda): % de la moneda dominante antigua (del bal.) en la nueva
    - Estado_3 (Moneda → Otra Moneda): % de la moneda original en la nueva distribución

    Parámetros:
        row: Fila del df_final con la información del instrumento
        df_dominancia_nuevas: DataFrame con allocations nuevas (formato long)

    Retorna:
        float: Métrica de variación (0-1), o None si no aplica/calcula
    """
    # Solo aplica para instrumentos NO balanceados
    if 'moneda_nueva' not in row or str(row['moneda_nueva']).strip().upper() == 'BALANCEADO':
        return None

    # Verificar que tenga Estado válido
    if 'Estado' not in row or pd.isna(row['Estado']) or row['Estado'] == '':
        return None

    if 'ID' not in row:
        return None

    pct_antiguo = extraer_porcentaje_dominante(row, 'pct_dominancia_antigua')
    moneda_antigua = extraer_moneda_dominante(row, 'pct_dominancia_antigua')

    if pct_antiguo is None or moneda_antigua is None:
        return None

    # Buscar el % de esa misma moneda en la nueva distribución
    pct_misma_moneda = obtener_pct_moneda_en_nuevas(
        df_dominancia_nuevas, row['ID'], moneda_antigua
    )

    # Si el instrumento no tiene datos nuevos, no calcular
    if pct_misma_moneda is None:
        return None

    # Diferencia absoluta normalizada a escala 0-1
    # Ej: USD 80% antigua → USD 10% nueva → variacion = 0.70
    diferencia = abs(pct_antiguo - pct_misma_moneda) / 100.0
    return round(diferencia, 4)


# ============================================================================
# FUNCIÓN PRINCIPAL: CREAR DF_FINAL
# ============================================================================

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
    - Estado (calculado - Estado_1, Estado_2, Estado_3)
    - distancia_hellinger (calculado - métrica de variación entre distribuciones usando top 5 monedas)
    - variacion_balanceados (calculado - métrica específica para balanceados según Estado:
        * Estado_1: Hellinger
        * Estado_2: Diferencia de porcentajes dominantes)
    - variacion_no_balanceados (calculado - para no balanceados, todos los Estados:
        * |pct_moneda_dominante_antigua - pct_misma_moneda_en_nueva| / 100)
    
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
    
    # 3. Merge con dominancia antiguas (Pct_dominancia y Moneda: para Estado_3)
    cols_antiguas = ['ID', 'Pct_dominancia', 'Moneda:']
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
    
    # 6. CALCULAR DISTANCIA DE HELLINGER (métrica de variación de distribución)
    # Por cada instrumento se calculan sus top 5 monedas específicas (excluyendo Balanceado y Otros)
    print("  [INFO] Calculando distancia de Hellinger por instrumento...")
    print("  [INFO] (Top 5 monedas se calculan individualmente para cada instrumento)")
    
    df_final['distancia_hellinger'] = df_final.apply(
        lambda row: calcular_hellinger_por_instrumento(
            row, df_dominancia_antiguas, df_dominancia_nuevas
        ),
        axis=1
    )
    
    # 7. CALCULAR VARIACIÓN PARA BALANCEADOS (lógica específica según Estado)
    # Esta métrica aplica SOLO para instrumentos balanceados (moneda_nueva == "Balanceado")
    print("  [INFO] Calculando variación para instrumentos balanceados...")
    print("  [INFO] (Estado_1: Hellinger, Estado_2: Diferencia de porcentajes)")
    
    df_final['variacion_balanceados'] = df_final.apply(
        lambda row: calcular_variacion_balanceados(
            row, df_dominancia_antiguas, df_dominancia_nuevas
        ),
        axis=1
    )
    
    # 8. CALCULAR VARIACIÓN PARA NO BALANCEADOS
    # Métrica: |pct_moneda_dominante_antigua - pct_misma_moneda_en_nueva| / 100
    # Aplica para todos los Estados de no balanceados (Estado_1, Estado_2, Estado_3)
    print("  [INFO] Calculando variación para instrumentos no balanceados...")
    print("  [INFO] (Diferencia de pct moneda dominante antigua en distribución nueva)")
    
    df_final['variacion_no_balanceados'] = df_final.apply(
        lambda row: calcular_variacion_no_balanceados(
            row, df_dominancia_nuevas
        ),
        axis=1
    )
    
    # 9. CALCULAR NIVEL DE VARIACIÓN (para filtros en frontend)
    # Igual que 'Estado', se calcula en el backend y el frontend solo filtra sobre el valor.
    # Hellinger (balanceados): Baja ≤ 0.30, Alta > 0.30
    # Porcentual (no balanceados): Baja ≤ 0.40, Alta > 0.40
    # Sin datos: None
    df_final['nivel_variacion'] = df_final.apply(calcular_nivel_variacion, axis=1)

    # 10. CALCULAR ALERTA DE DOMINANCIA
    # Detecta dos escenarios anómalos comparando la distribución COMPLETA:
    # - 'DESAPARECE': la clase dominante antigua ya no aparece en la nueva distribución
    # - 'NUEVA': la clase dominante nueva nunca existió en la distribución antigua
    from src.logic.utils.alertas_dominancia import calcular_alerta_dominancia, COLS_META_MONEDA
    print("  [INFO] Calculando alertas de dominancia...")
    df_final['alerta_dominancia'] = df_final.apply(
        lambda row: calcular_alerta_dominancia(
            row,
            df_dominancia_nuevas,
            df_dominancia_antiguas,
            col_pct_antigua='pct_dominancia_antigua',
            col_pct_nueva='pct_dominancia_nuevo',
            col_clase_nuevas='class',
            col_pct_nuevas='percentage',
            cols_meta_antiguas=COLS_META_MONEDA,
        ),
        axis=1
    )
    n_alertas = df_final['alerta_dominancia'].notna().sum()
    print(f"  [OK] Alertas detectadas: {n_alertas} instrumentos")

    # 11. Reordenar columnas para presentación
    cols_orden = [
        'Nombre', 'ID', 'Tipo instrumento', 'moneda_antigua',
        'moneda_nueva', 'pct_dominancia_nuevo', 'pct_escalado', 'pct_original',
        'pct_dominancia_antigua', 'Cambio', 'Estado', 'nivel_variacion',
        'distancia_hellinger', 'variacion_balanceados', 'variacion_no_balanceados',
        'alerta_dominancia',
    ]
    
    # Seleccionar solo las que existen
    cols_finales = [col for col in cols_orden if col in df_final.columns]
    df_final = df_final[cols_finales]
    
    return df_final


def calcular_nivel_variacion(row):
    """
    Clasifica el nivel de variación de un instrumento como 'Alta', 'Baja' o None.

    Umbrales según el tipo de métrica usada:
    - Hellinger (balanceados Estado_1: Bal→Bal):
        Baja: <= 0.30  |  Alta: > 0.30
    - Porcentual (balanceados Estado_2: Mon→Bal  +  todos los no balanceados):
        Baja: <= 0.40  |  Alta: > 0.40
    - Sin datos (ninguna variación calculada): None
    """
    val_bal = row.get('variacion_balanceados')
    val_nobal = row.get('variacion_no_balanceados')
    estado = str(row.get('Estado', '')).strip()

    if pd.notna(val_bal) and val_bal is not None:
        val = float(val_bal)
        if estado == 'Estado_1':
            # Hellinger (Balanceado → Balanceado)
            return 'Baja' if val <= 0.30 else 'Alta'
        else:
            # Estado_2 (Moneda → Balanceado): variación porcentual
            return 'Baja' if val <= 0.40 else 'Alta'
    elif pd.notna(val_nobal) and val_nobal is not None:
        # No balanceados: siempre variación porcentual
        return 'Baja' if float(val_nobal) <= 0.40 else 'Alta'
    return None


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
        # Estado_3: Balanceado sin allocations antiguas
        if 'Moneda:' in row and str(row['Moneda:']).strip() == 'FALTA ALLOCATION':
            return 'Estado_3'
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
    from src.extractors.moneda.load_instruments import load_df_instruments
    from src.extractors.moneda.load_allocations import load_allocations_nuevas, load_allocations_antiguas
    
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
    
    if 'distancia_hellinger' in df_final.columns:
        hellinger_validos = df_final['distancia_hellinger'].dropna()
        if len(hellinger_validos) > 0:
            print(f"\n  Distancia de Hellinger (variación de distribución):")
            print(f"    - Con datos:        {len(hellinger_validos)}")
            print(f"    - Promedio:         {hellinger_validos.mean():.4f}")
            print(f"    - Mediana:          {hellinger_validos.median():.4f}")
            print(f"    - Mínimo:           {hellinger_validos.min():.4f}")
            print(f"    - Máximo:           {hellinger_validos.max():.4f}")
            print(f"    Interpretación: 0 = sin cambio, 1 = cambio máximo")
    
    if 'variacion_balanceados' in df_final.columns:
        variacion_validos = df_final['variacion_balanceados'].dropna()
        if len(variacion_validos) > 0:
            print(f"\n  Variación para Balanceados (métrica específica por Estado):")
            print(f"    - Con datos:        {len(variacion_validos)}")
            print(f"    - Promedio:         {variacion_validos.mean():.4f}")
            print(f"    - Mediana:          {variacion_validos.median():.4f}")
            print(f"    - Mínimo:           {variacion_validos.min():.4f}")
            print(f"    - Máximo:           {variacion_validos.max():.4f}")
            
            # Analizar por Estado
            if 'Estado' in df_final.columns:
                bal_estado1 = df_final[(df_final['variacion_balanceados'].notna()) & (df_final['Estado'] == 'Estado_1')]
                bal_estado2 = df_final[(df_final['variacion_balanceados'].notna()) & (df_final['Estado'] == 'Estado_2')]
                print(f"    - Estado_1 (Bal→Bal, Hellinger):    {len(bal_estado1)}")
                print(f"    - Estado_2 (Mon→Bal, Dif. %):       {len(bal_estado2)}")
    
    if 'variacion_no_balanceados' in df_final.columns:
        var_no_bal = df_final['variacion_no_balanceados'].dropna()
        if len(var_no_bal) > 0:
            print(f"\n  Variación para No Balanceados (pct moneda dominante antigua en nueva dist.):")
            print(f"    - Con datos:        {len(var_no_bal)}")
            print(f"    - Promedio:         {var_no_bal.mean():.4f}")
            print(f"    - Mediana:          {var_no_bal.median():.4f}")
            print(f"    - Mínimo:           {var_no_bal.min():.4f}")
            print(f"    - Máximo:           {var_no_bal.max():.4f}")
            
            if 'Estado' in df_final.columns:
                for estado in ['Estado_1', 'Estado_2', 'Estado_3']:
                    n = df_final[(df_final['variacion_no_balanceados'].notna()) & (df_final['Estado'] == estado)]
                    if len(n) > 0:
                        print(f"    - {estado}: {len(n)} instrumentos, promedio {n['variacion_no_balanceados'].mean():.4f}")
    
    # EJEMPLOS
    print("\n" + "=" * 70)
    print(" EJEMPLOS DE DF_FINAL ".center(70, "="))
    print("=" * 70)
    cols_mostrar = ['Nombre', 'ID', 'moneda_nueva', 'moneda_antigua', 'Estado', 'Cambio', 'variacion_balanceados']
    cols_disponibles = [c for c in cols_mostrar if c in df_final.columns]
    if cols_disponibles:
        print("\nPrimeros 10 registros:")
        print(df_final[cols_disponibles].head(10).to_string(index=False))
    
    # Mostrar ejemplos específicos de BALANCEADOS con variación
    if 'variacion_balanceados' in df_final.columns and 'moneda_nueva' in df_final.columns:
        balanceados_con_var = df_final[
            (df_final['moneda_nueva'] == 'Balanceado') & 
            (df_final['variacion_balanceados'].notna())
        ]
        if len(balanceados_con_var) > 0:
            print("\n" + "=" * 70)
            print(" EJEMPLOS DE BALANCEADOS CON VARIACIÓN ".center(70, "="))
            print("=" * 70)
            cols_bal = ['Nombre', 'Estado', 'pct_dominancia_antigua', 'pct_dominancia_nuevo', 'variacion_balanceados']
            cols_bal_disponibles = [c for c in cols_bal if c in balanceados_con_var.columns]
            print(f"\nPrimeros 5 balanceados con variación calculada:")
            print(balanceados_con_var[cols_bal_disponibles].head(5).to_string(index=False))
    
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

