import pandas as pd
import os


# ============================================================================
# MAPEO DE NOMBRES DE MONEDAS: REFINITIV → CÓDIGOS ISO
# ============================================================================

# Mapeo único y autoritativo de nombres Refinitiv -> Códigos ISO 4217
CURRENCY_MAP_REFINITIV_TO_ISO = {
    # Monedas principales (mayúsculas - formato Refinitiv típico)
    'CHILEAN PESO': 'CLP',
    'US DOLLAR': 'USD',
    'EURO': 'EUR',
    'HONG KONG DOLLAR': 'HKD',
    'JAPANESE YEN': 'JPY',
    'UK POUND STERLING': 'GBP',
    'BRITISH POUND': 'GBP',
    'SWISS FRANC': 'CHF',
    'CANADIAN DOLLAR': 'CAD',
    'AUSTRALIAN DOLLAR': 'AUD',
    'NEW ZEALAND DOLLAR': 'NZD',
    'CHINESE YUAN': 'CNY',
    'CHINESE R YUAN HK': 'CNY',
    'CHINESE YUAN (OFFSHORE)': 'CNY',
    'SOUTH KOREAN WON': 'KRW',
    'KOREAN WON': 'KRW',
    'SINGAPORE DOLLAR': 'SGD',
    'MEXICAN PESO': 'MXN',
    'BRAZILIAN REAL': 'BRL',
    'ARGENTINIAN PESO': 'ARS',
    'COLOMBIAN PESO': 'COP',
    'PERU NEW SOL': 'PEN',
    'PERUVIAN SOL': 'PEN',
    'SOUTH AFRICAN RAND': 'ZAR',
    'DANISH KRONE': 'DKK',
    'NORWEGIAN KRONE': 'NOK',
    'SWEDISH KRONA': 'SEK',
    'CZECH KORUNA': 'CZK',
    'CZECH CROWN': 'CZK',
    'SAUDI ARABIAN RIYAL': 'SAR',
    'SAUDI RIYAL': 'SAR',
    
    # Categoría especial para monedas agrupadas y monedas menos relevantes
    'OTROS': 'OTROS',
    'OTHERS': 'OTROS',
    'OTHER': 'OTROS',
    'OTHER CURRENCIES': 'OTROS',
    'OTRAS MONEDAS': 'OTROS',
    
    # Monedas específicas clasificadas como "OTROS"
    'VIETNAMESE DONG': 'OTROS',
    'SRI LANKA RUPEE': 'OTROS',
    'SRI LANKAN RUPEE': 'OTROS',
    'VIETNAM DONG': 'OTROS',
    'NETHERLANDS GUILDER': 'OTROS',
    'DUTCH GUILDER': 'OTROS',
    
    # Categorías regionales que Refinitiv agrupa como "OTROS"
    'ROMANIA': 'OTROS',
    'ROMANIAN LEU': 'OTROS',
    'REST OF THE WORLD': 'OTROS',
    'REST OF WORLD': 'OTROS',
    'OTHER EUROPEAN CURRENCIES': 'OTROS',
    'OTHER ASIAN CURRENCIES': 'OTROS',
    'LATIN AMERICA': 'OTROS',
    'OTHER LATIN AMERICAN CURRENCIES': 'OTROS',
    
    # Otras monedas globales
    'TAIWAN DOLLAR': 'TWD',
    'UAE DIRHAM': 'AED',
    'EGYPTIAN POUND': 'EGP',
    'INDIAN RUPEE': 'INR',
    'INDONESIA RUPIAH': 'IDR',
    'ISRAELI SHEKEL': 'ILS',
    'KUWAIT DINAR': 'KWD',
    'KAZAKHSTAN TENGE': 'KZT',
    'MALAYSIAN RINGGIT': 'MYR',
    'PHILIPPINE PESO': 'PHP',
    'POLISH ZLOTY': 'PLN',
    'RUSSIAN RUBLE': 'RUB',
    'THAI BAHT': 'THB',
    'TURKISH LIRA': 'TRY',
    'URUGUAY PESO URUGUAYO': 'UYU',
    'UKRAINIAN HRYVNIA': 'UAH',
    'BENIN CFA FRANC': 'XOF',
    
    # Variantes con capitalización mixta (Title Case)
    'Australian Dollar': 'AUD',
    'Brazilian Real': 'BRL',
    'Canadian Dollar': 'CAD',
    'Chilean Peso': 'CLP',
    'Chinese Yuan': 'CNY',
    'Chinese Yuan (Offshore)': 'CNY',
    'Colombian Peso': 'COP',
    'Danish Krone': 'DKK',
    'Dominican Republic Peso': 'DOP',
    'Egyptian Pound': 'EGP',
    'Euro': 'EUR',
    'Hong Kong Dollar': 'HKD',
    'Indian Rupee': 'INR',
    'Indonesia Rupiah': 'IDR',
    'Israeli Shekel': 'ILS',
    'Japanese Yen': 'JPY',
    'Malaysian Ringgit': 'MYR',
    'Mexican Peso': 'MXN',
    'New Zealand Dollar': 'NZD',
    'Nigerian Naira': 'NGN',
    'Norwegian Krone': 'NOK',
    'Philippine Peso': 'PHP',
    'Polish Zloty': 'PLN',
    'Singapore Dollar': 'SGD',
    'South African Rand': 'ZAR',
    'South Korean Won': 'KRW',
    'Swedish Krona': 'SEK',
    'Swiss Franc': 'CHF',
    'Czech Koruna': 'CZK',
    'Czech Crown': 'CZK',
    'Saudi Arabian Riyal': 'SAR',
    'Saudi Riyal': 'SAR',
    'Taiwan Dollar': 'TWD',
    'Thai Baht': 'THB',
    'Turkish Lira': 'TRY',
    'UAE Dirham': 'AED',
    'UK Pound Sterling': 'GBP',
    'US Dollar': 'USD',
    'Paraguayan Guarani': 'PYG',
    
    # Categoría especial (variantes Title Case)
    'Otros': 'OTROS',
    'Others': 'OTROS',
    'Other': 'OTROS',
    'Other Currencies': 'OTROS',
    
    # Monedas específicas clasificadas como "OTROS" (Title Case)
    'Vietnamese Dong': 'OTROS',
    'Sri Lanka Rupee': 'OTROS',
    'Sri Lankan Rupee': 'OTROS',
    'Vietnam Dong': 'OTROS',
    'Netherlands Guilder': 'OTROS',
    'Dutch Guilder': 'OTROS',
    
    # Categorías regionales (Title Case)
    'Romania': 'OTROS',
    'Romanian Leu': 'OTROS',
    'Rest of the World': 'OTROS',
    'Rest of World': 'OTROS',
    'Other European Currencies': 'OTROS',
    'Other Asian Currencies': 'OTROS',
    'Latin America': 'OTROS',
    'Other Latin American Currencies': 'OTROS',
    
    # Variantes adicionales encontradas en datos reales
    'POUND STERLING': 'GBP',
    'YEN': 'JPY',
    'YUAN': 'CNY',
    'WON': 'KRW',
    'RENMINBI': 'CNY',
    
    # Nuevas monedas exóticas mapeadas a OTROS
    'ALBANIA LEK': 'OTROS', 'ALL': 'OTROS',
    'ARMENIA DRAM': 'OTROS', 'AMD': 'OTROS',
    'AZERBAIJANI MANAT': 'OTROS', 'AZN': 'OTROS',
    'DOMINICAN REPUBLIC PESO': 'OTROS', 'DOP': 'OTROS',
    'HUNGARY FORINT': 'OTROS', 'HUF': 'OTROS',
    'KAZAKHSTAN': 'OTROS', 'KAZAKHSTAN TENGE': 'OTROS', 'KZT': 'OTROS',
    'KUWAIT': 'OTROS', 'KUWAITI DINAR': 'OTROS', 'KWD': 'OTROS',
    'NIGERIAN NAIRA': 'OTROS', 'NGN': 'OTROS',
    'PARAGUAYAN GUARANI': 'OTROS', 'PYG': 'OTROS',
    'UZBEKISTAN SOM': 'OTROS', 'UZBEKISTAN': 'OTROS', 'UZS': 'OTROS',
    
    # Valores especiales a ignorar/filtrar
    'ROUNDING ADJUSTMENT': 'OTROS',  # Ajuste de redondeo, agrupar en OTROS
    'Rounding Adjustment': 'OTROS',
}


# ============================================================================
# FUNCIONES AUXILIARES PARA ALLOCATIONS NUEVAS
# ============================================================================

def _escalar_porcentajes(grupo_monedas):
    """
    Escala los porcentajes de un grupo de monedas para que sumen exactamente 100%.
    
    Parámetros:
        grupo_monedas: DataFrame con columnas [class, percentage]
    
    Retorna:
        tuple: (DataFrame con columna 'pct_escalado', total_original)
    """
    grupo = grupo_monedas.copy()

    # Ignorar filas con porcentaje negativo o cero para el escalado.
    # Valores negativos representan posiciones cortas/hedging que distorsionan
    # la suma total y pueden generar porcentajes escalados absurdos.
    mask_positivos = grupo['percentage'] > 0
    total_original = grupo.loc[mask_positivos, 'percentage'].sum()

    if total_original == 0:
        grupo['pct_escalado'] = 0.0
    else:
        # Solo los positivos se escalan; los negativos/cero quedan en 0
        grupo['pct_escalado'] = 0.0
        grupo.loc[mask_positivos, 'pct_escalado'] = (
            grupo.loc[mask_positivos, 'percentage'] / total_original
        )

    return grupo, total_original


def _mapear_nombres_monedas(df_allocations):
    """
    Mapea nombres de monedas de Refinitiv a códigos ISO estándar.
    
    Aplica el mapeo a:
    - 'class': Nombre de la moneda en cada fila
    - 'moneda_nueva': Moneda dominante (excepto 'Balanceado')
    - 'pct_dominancia_nuevo': Actualiza el texto con el código ISO
    
    El mapeo es case-insensitive para mayor robustez.
    
    Parámetros:
        df_allocations: DataFrame con columnas [class, moneda_nueva, pct_dominancia_nuevo, ...]
    
    Retorna:
        DataFrame con nombres de monedas mapeados a códigos ISO
    """
    df = df_allocations.copy()
    
    # Crear diccionario case-insensitive (todas las claves en mayúsculas)
    currency_map_upper = {k.upper(): v for k, v in CURRENCY_MAP_REFINITIV_TO_ISO.items()}
    
    # 1. MAPEAR COLUMNA 'class' (moneda en cada fila)
    if 'class' in df.columns:
        df['class'] = df['class'].map(lambda x: currency_map_upper.get(str(x).upper(), x) if pd.notna(x) else x)
    
    # 2. MAPEAR COLUMNA 'moneda_nueva' (excepto 'Balanceado')
    if 'moneda_nueva' in df.columns:
        df['moneda_nueva'] = df['moneda_nueva'].apply(
            lambda x: currency_map_upper.get(str(x).upper(), x) if pd.notna(x) and x != 'Balanceado' else x
        )
    
    # 3. ACTUALIZAR 'pct_dominancia_nuevo' con códigos ISO
    if 'pct_dominancia_nuevo' in df.columns:
        def actualizar_pct_dominancia(texto):
            """Extrae moneda y porcentaje, mapea moneda y reconstruye texto."""
            if pd.isna(texto) or not isinstance(texto, str):
                return texto
            
            # Formato esperado: "NOMBRE MONEDA XX.XX%"
            parts = texto.rsplit(' ', 1)  # Dividir por último espacio
            if len(parts) == 2:
                moneda_original = parts[0].strip()
                porcentaje = parts[1].strip()
                moneda_iso = currency_map_upper.get(moneda_original.upper(), moneda_original)
                return f"{moneda_iso} {porcentaje}"
            return texto
        
        df['pct_dominancia_nuevo'] = df['pct_dominancia_nuevo'].apply(actualizar_pct_dominancia)
    
    return df


def _cargar_archivo_nuevas(nuevas_path):
    """
    Carga el archivo de allocations nuevas con manejo especial de caracteres.
    
    El archivo tiene comillas problemáticas que pandas no puede parsear directamente,
    por lo que se usa el módulo csv con configuración específica.
    
    Parámetros:
        nuevas_path: Ruta al archivo allocations_nuevas.csv
    
    Retorna:
        DataFrame con columnas limpias y solo allocations de tipo 'currency'
    """
    import csv
    
    # Lectura manual para evitar ParserError
    rows = []
    with open(nuevas_path, 'r', encoding='latin-1', newline='') as f:
        reader = csv.reader(f, delimiter=';', quoting=csv.QUOTE_NONE, escapechar='\\')
        headers = next(reader)
        headers = [h.strip() for h in headers]
        for row in reader:
            if len(row) == len(headers):
                rows.append(row)
    
    df = pd.DataFrame(rows, columns=headers)
    df.columns = df.columns.str.strip()
    
    # Filtrar solo allocations de moneda (currency)
    if 'classif' in df.columns:
        df = df[df['classif'] == 'currency'].copy()
    else:
        print("  [WARN] ADVERTENCIA: columna 'classif' no encontrada, se incluyen todos los registros.")
    
    # Normalizar percentage (pueden venir con coma como decimal)
    if 'percentage' in df.columns:
        df['percentage'] = (df['percentage']
                           .astype(str)
                           .str.replace(',', '.', regex=False))
        df['percentage'] = pd.to_numeric(df['percentage'], errors='coerce')
    
    return df


def _cruzar_con_instruments(df_instruments, df_nuevas):
    """
    Cruza df_instruments con allocations nuevas usando RIC, Isin o Cusip.
    
    El cruce es secuencial (primero RIC, luego Isin, luego Cusip) para evitar
    duplicados cuando un instrumento matchea por múltiples claves.
    
    FILTRADO AUTOMÁTICO: Excluye instrumentos que tengan TODAS sus filas con
    percentage inválido (NaN, 0 o nulo). Solo retorna instrumentos con al menos
    una fila con percentage válido.
    
    Parámetros:
        df_instruments: DataFrame con instrumentos base
        df_nuevas: DataFrame con allocations nuevas cargadas
    
    Retorna:
        DataFrame con el cruce exitoso, incluyendo columnas:
        [ID, Nombre, instrument, class, percentage, date (opcional), tipo_id]
    """
    resultados = []
    matched_ids = set()

    for key_instr, key_nuevas in [('RIC', 'instrument'), ('Isin', 'instrument'), ('Cusip', 'instrument')]:
        pendientes = df_instruments[~df_instruments['ID'].isin(matched_ids)]
        if pendientes.empty:
            break
        
        df_merge = pd.merge(
            pendientes[['ID', 'Nombre', key_instr]],
            df_nuevas,
            left_on=key_instr,
            right_on=key_nuevas,
            how='inner'
        )
        
        if not df_merge.empty:
            # Agregar columna tipo_id para registrar el tipo de identificador usado
            df_merge['tipo_id'] = key_instr
            resultados.append(df_merge)
            matched_ids.update(df_merge['ID'].tolist())

    if not resultados:
        return pd.DataFrame(columns=['ID', 'Nombre', 'instrument', 'class', 'percentage', 'tipo_id'])

    df_merged = pd.concat(resultados, ignore_index=True)
    
    # Seleccionar columnas relevantes
    cols_to_keep = [c for c in ['ID', 'Nombre', 'instrument', 'class', 'percentage', 'date', 'tipo_id'] 
                    if c in df_merged.columns]
    df_merged = df_merged[cols_to_keep].drop_duplicates(subset=['ID', 'class'])
    
    # FILTRADO: Excluir instrumentos con TODAS las filas percentage inválido
    # Identificar IDs que tienen AL MENOS UNA fila con percentage válido
    ids_con_datos_validos = set()
    ids_sin_datos_validos = set()
    
    for id_instrumento, grupo in df_merged.groupby('ID'):
        # Verificar si tiene AL MENOS UNA fila con percentage válido
        percentages_validos = grupo['percentage'].dropna()
        percentages_validos = percentages_validos[percentages_validos > 0]
        
        if len(percentages_validos) > 0:
            ids_con_datos_validos.add(id_instrumento)
        else:
            ids_sin_datos_validos.add(id_instrumento)
    
    # Log informativo
    if ids_sin_datos_validos:
        print(f"  [INFO] Excluidos {len(ids_sin_datos_validos)} instrumentos con TODAS las filas percentage=NA")
    
    # Filtrar: mantener solo IDs con datos válidos
    df_merged = df_merged[df_merged['ID'].isin(ids_con_datos_validos)].copy()
    
    return df_merged


def _calcular_dominancia_por_instrumento(df_nuevas_merged, umbral=0.9):
    """
    Calcula dominancia y métricas para cada instrumento.
    
    Agrupa las allocations por instrumento y calcula:
    - moneda_nueva: "Balanceado" o moneda específica (USD, CLP, etc.)
    - pct_dominancia_nuevo: Texto "MONEDA XX.XX%"
    - pct_escalado: Suma de porcentajes escalados (debe ser 100%)
    - pct_original: Suma de porcentajes originales (pre-escalado)
    
    Parámetros:
        df_nuevas_merged: DataFrame con allocations cruzadas (formato long)
        umbral: Umbral de dominancia (default 0.9 = 90%)
    
    Retorna:
        DataFrame agrupado con 1 fila por instrumento y columnas calculadas
    """
    resultados = []
    
    for instrumento_id, grupo in df_nuevas_merged.groupby('ID'):
        # INFO BÁSICA DEL INSTRUMENTO
        nombre = grupo['Nombre'].iloc[0] if 'Nombre' in grupo.columns else None
        instrument = grupo['instrument'].iloc[0] if 'instrument' in grupo.columns else None
        date = grupo['date'].iloc[0] if 'date' in grupo.columns else None
        
        # 1. CALCULAR SUMA ORIGINAL
        pct_original = grupo['percentage'].sum()
        
        # 2. ESCALAR PORCENTAJES AL 100%
        grupo_escalado, total_orig = _escalar_porcentajes(grupo[['class', 'percentage']])
        
        # 3. CALCULAR SUMA ESCALADA (validación)
        pct_escalado = grupo_escalado['pct_escalado'].sum()
        
        # 4. IDENTIFICAR MONEDA DOMINANTE
        idx_max = grupo_escalado['pct_escalado'].idxmax()
        moneda_max = grupo_escalado.loc[idx_max, 'class']
        pct_max = grupo_escalado.loc[idx_max, 'pct_escalado']
        
        # 5. CLASIFICAR SEGÚN UMBRAL DE DOMINANCIA
        if pct_max >= umbral:
            moneda_nueva = moneda_max
        else:
            moneda_nueva = "Balanceado"
        
        # 6. FORMATO DE TEXTO PARA PCT_DOMINANCIA_NUEVO
        pct_dominancia_nuevo = f"{moneda_max} {pct_max * 100:.2f}%"
        
        resultados.append({
            'ID': instrumento_id,
            'Nombre': nombre,
            'instrument': instrument,
            'date': date,
            'moneda_nueva': moneda_nueva,
            'pct_dominancia_nuevo': pct_dominancia_nuevo,
            'pct_escalado': round(pct_escalado * 100, 2),  # Convertir a porcentaje
            'pct_original': round(pct_original, 2)
        })
    
    return pd.DataFrame(resultados)


def _enriquecer_allocations_con_dominancia(df_nuevas_merged, umbral=0.9):
    """
    Enriquece el dataframe en formato long agregando columnas de dominancia.
    
    Mantiene todas las filas originales (1 fila por instrumento-moneda) y agrega:
    - moneda_nueva
    - pct_dominancia_nuevo
    - pct_escalado
    - pct_original
    
    Parámetros:
        df_nuevas_merged: DataFrame en formato long con [ID, Nombre, instrument, class, percentage, date]
        umbral: Umbral de dominancia (default 0.9 = 90%)
    
    Retorna:
        DataFrame con todas las filas originales + columnas de dominancia
    """
    # Calcular dominancia por instrumento
    df_dominancia = _calcular_dominancia_por_instrumento(df_nuevas_merged, umbral)
    
    # Hacer merge con el dataframe original para mantener detalle por moneda
    df_enriquecido = pd.merge(
        df_nuevas_merged,
        df_dominancia[['ID', 'moneda_nueva', 'pct_dominancia_nuevo', 'pct_escalado', 'pct_original']],
        on='ID',
        how='left'
    )
    
    return df_enriquecido


# ============================================================================
# FUNCIÓN PRINCIPAL: LOAD ALLOCATIONS NUEVAS
# ============================================================================

def load_allocations_nuevas(df_instruments, nuevas_path, umbral=0.9):
    """
    Carga y procesa allocations nuevas con cálculo completo de dominancia.
    
    PROCESO COMPLETO:
    1. Carga archivo allocations_nuevas.csv (con parsing especial)
    2. Cruza con df_instruments por RIC/Isin/Cusip
    3. Enriquece con columnas de dominancia (manteniendo formato long)
    
    RETORNA DataFrame en formato LONG (múltiples filas por instrumento) con columnas:
    - ID: Identificador del instrumento (df_instruments)
    - Nombre: Nombre del instrumento (df_instruments)
    - instrument: Código usado en el match - RIC, Isin o Cusip (allocations nuevas)
    - class: Moneda (allocations nuevas)
    - percentage: Porcentaje de cada moneda (allocations nuevas)
    - date: Fecha de la allocation (allocations nuevas)
    - moneda_nueva: "Balanceado" o código de moneda (USD, CLP, EUR...)
    - pct_dominancia_nuevo: Texto "MONEDA XX.XX%" con la moneda dominante
    - pct_escalado: Suma de porcentajes escalados (debe ser 100.0)
    - pct_original: Suma de porcentajes originales (pre-escalado)
    
    Parámetros:
        df_instruments: DataFrame base con instrumentos filtrados
        nuevas_path: Ruta al archivo allocations_nuevas.csv
        umbral: Umbral de dominancia (default 0.9 = 90%)
    
    Retorna:
        DataFrame en formato long con columnas de dominancia agregadas
    """
    # PASO 1: CARGAR ARCHIVO
    df_nuevas = _cargar_archivo_nuevas(nuevas_path)
    
    if df_nuevas.empty:
        print("  [WARN] ADVERTENCIA: No se pudieron cargar allocations nuevas.")
        return pd.DataFrame(columns=['ID', 'Nombre', 'instrument', 'class', 'percentage', 'date',
                                    'moneda_nueva', 'pct_dominancia_nuevo', 'pct_escalado', 'pct_original'])
    
    # PASO 2: CRUZAR CON INSTRUMENTS
    df_merged = _cruzar_con_instruments(df_instruments, df_nuevas)
    
    if df_merged.empty:
        print("  [WARN] ADVERTENCIA: No se encontraron matches en allocations nuevas.")
        return pd.DataFrame(columns=['ID', 'Nombre', 'instrument', 'class', 'percentage', 'date',
                                    'moneda_nueva', 'pct_dominancia_nuevo', 'pct_escalado', 'pct_original'])
    
    # PASO 3: ENRIQUECER CON COLUMNAS DE DOMINANCIA (mantener formato long)
    df_resultado = _enriquecer_allocations_con_dominancia(df_merged, umbral)
    
    # PASO 4: MAPEAR NOMBRES DE MONEDAS A CÓDIGOS ISO (consistencia con allocations antiguas)
    df_resultado = _mapear_nombres_monedas(df_resultado)
    
    return df_resultado

# ============================================================================
# FUNCIONES AUXILIARES PARA ALLOCATIONS ANTIGUAS
# ============================================================================

def _identificar_columnas_moneda(df_antiguas, base_cols):
    """
    Identifica qué columnas del dataframe representan monedas (CLP, USD, EUR...).
    Excluye columnas de metadata conocidas.
    
    Parámetros:
        df_antiguas: DataFrame en formato wide (columnas por moneda)
        base_cols: Lista de columnas base (ID, Nombre, SubMoneda)
    
    Retorna:
        List[str]: Lista de nombres de columnas que representan monedas
    """
    # Columnas que NO son monedas (metadata)
    cols_metadata = [
        'ID', 'Nombre', 'Creado', 'Tipo Instrumento', 'Tipo instrumento',
        'RIC', 'Isin', 'Cusip', 'SubMoneda', 'Moneda:', 'Pais', 'País',
        'Nemo', 'Ticker_BB', 'Currency', 'Moneda'
    ]
    
    # Identificar columnas de MONEDAS (lo que NO es metadata y tiene nombres cortos)
    cols_moneda = []
    for col in df_antiguas.columns:
        if col not in cols_metadata and col not in base_cols:
            # Columnas de moneda típicamente tienen nombres cortos (3-15 caracteres)
            if len(str(col).strip()) <= 15:
                cols_moneda.append(col)
    
    return cols_moneda


def _calcular_pct_dominancia_antiguas(row, cols_moneda):
    """
    Calcula el porcentaje de dominancia para una fila de allocations antiguas.
    
    Busca la moneda con mayor porcentaje y retorna el formato "MONEDA XX.XX%".
    
    Parámetros:
        row: Serie de pandas con valores por moneda
        cols_moneda: Lista de columnas que representan monedas
    
    Retorna:
        str: Texto con formato "MONEDA XX.XX%" o "Sin datos"
    """
    moneda_max = None
    pct_max = 0.0
    
    # Buscar la moneda con mayor porcentaje
    for col in cols_moneda:
        try:
            val_str = str(row[col]).strip().replace(',', '.')
            val_num = float(val_str)
            
            if val_num > pct_max:
                pct_max = val_num
                moneda_max = col.strip()
        except (ValueError, TypeError):
            continue
    
    # Formatear resultado
    if moneda_max and pct_max > 0:
        return f"{moneda_max} {pct_max:.2f}%"
    else:
        return "Sin datos"


# ============================================================================
# FUNCIÓN PRINCIPAL: LOAD ALLOCATIONS ANTIGUAS
# ============================================================================

def load_allocations_antiguas(df_instruments, antiguas_path):
    """
    Carga y procesa allocations antiguas con cálculo de dominancia.
    
    PROCESO COMPLETO:
    1. Carga archivo allocations_currency.csv
    2. Cruza con df_instruments por ID
    3. Identifica columnas de monedas (excluye metadata)
    4. Calcula Pct_dominancia (moneda con mayor porcentaje)
    5. Filtra y retorna solo columnas necesarias
    
    RETORNA DataFrame (1 fila por instrumento) con columnas:
    - ID, Nombre, SubMoneda: Identificadores del instrumento
    - CLP, USD, EUR... : Columnas con porcentaje por moneda
    - Pct_dominancia: Texto "MONEDA XX.XX%" con la moneda dominante
    
    Parámetros:
        df_instruments: DataFrame base con instrumentos filtrados
        antiguas_path: Ruta al archivo allocations_currency.csv
    
    Retorna:
        DataFrame procesado con 1 fila por instrumento
    """
    # PASO 1: CARGAR ARCHIVO
    df_antiguas = pd.read_csv(antiguas_path, sep=';', encoding='latin-1', on_bad_lines='skip')
    df_antiguas.columns = df_antiguas.columns.str.strip()
    
    # CONVERTIR ID A ENTERO (importante para el merge con df_instruments)
    if 'ID' in df_antiguas.columns:
        df_antiguas['ID'] = pd.to_numeric(df_antiguas['ID'], errors='coerce').astype('Int64')
        # Eliminar filas con ID inválido
        df_antiguas = df_antiguas.dropna(subset=['ID'])
    
    # PASO 2: PREPARAR COLUMNAS BASE
    base_cols = ['ID', 'Nombre']
    if 'SubMoneda' in df_instruments.columns:
        base_cols.append('SubMoneda')
    
    # PASO 3: CRUZAR POR ID
    df_result = pd.merge(
        df_instruments[base_cols], 
        df_antiguas, 
        on='ID', 
        how='inner', 
        suffixes=('', '_drop')
    )
    
    # Eliminar columnas duplicadas del merge
    cols_to_drop = [col for col in df_result.columns if col.endswith('_drop')]
    if cols_to_drop:
        df_result = df_result.drop(columns=cols_to_drop)
    
    # PASO 4: IDENTIFICAR COLUMNAS DE MONEDAS
    cols_moneda = _identificar_columnas_moneda(df_result, base_cols)
    
    if not cols_moneda:
        print("  [WARN] ADVERTENCIA: No se encontraron columnas de moneda en allocations antiguas.")
        df_result['Pct_dominancia'] = "Sin datos"
        return df_result[base_cols + ['Pct_dominancia']]
    
    # PASO 5: CALCULAR PCT_DOMINANCIA PARA CADA FILA
    df_result['Pct_dominancia'] = df_result.apply(
        lambda row: _calcular_pct_dominancia_antiguas(row, cols_moneda), 
        axis=1
    )
    
    # PASO 6: SELECCIONAR SOLO COLUMNAS NECESARIAS (incluyendo "Moneda:" para Estado_3)
    cols_finales = base_cols + cols_moneda + ['Pct_dominancia']
    
    # Agregar columna "Moneda:" si existe (necesaria para calcular Estado_3 en exports)
    if 'Moneda:' in df_result.columns:
        cols_finales.append('Moneda:')
    
    cols_finales = [col for col in cols_finales if col in df_result.columns]
    
    return df_result[cols_finales]


# ============================================================================
# BLOQUE DE TEST Y EJECUCIÓN MANUAL
# ============================================================================


# ============================================================================
# BLOQUE DE TEST Y EJECUCIÓN MANUAL
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from src.extractors.moneda.load_instruments import load_df_instruments
    
    print("\n" + "="*70)
    print(" TEST: CARGA DE ALLOCATIONS (NUEVAS Y ANTIGUAS) ".center(70, "="))
    print("="*70)
    
    # FASE 1: CARGAR DF_INSTRUMENTS
    print("\n[Fase 1/3] Cargando df_instruments...")
    df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
    print(f"  [OK] {len(df_instr)} instrumentos cargados")
    print(f"  Columnas: {df_instr.columns.tolist()}")
    
    # FASE 2: CARGAR ALLOCATIONS NUEVAS
    print("\n" + "-"*70)
    print("[Fase 2/3] Cargando allocations NUEVAS...")
    print("-"*70)
    df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
    print(f"  [OK] {len(df_nuevas)} registros (formato long con dominancia)")
    print(f"  [OK] Columnas generadas: {df_nuevas.columns.tolist()}")
    
    # Estadísticas de clasificación
    if 'ID' in df_nuevas.columns:
        instrumentos_unicos = df_nuevas['ID'].nunique()
        total_registros = len(df_nuevas)
        print(f"\n  Estadísticas:")
        print(f"    - Total registros:     {total_registros}")
        print(f"    - Instrumentos únicos: {instrumentos_unicos}")
    
    if 'moneda_nueva' in df_nuevas.columns:
        balanceados = (df_nuevas['moneda_nueva'] == 'Balanceado').sum()
        no_balanceados = len(df_nuevas) - balanceados
        print(f"    - Filas Balanceado:     {balanceados}")
        print(f"    - Filas No balanceado:  {no_balanceados}")
        
        if no_balanceados > 0:
            print(f"\n  Monedas más frecuentes (top 5):")
            dist = df_nuevas[df_nuevas['moneda_nueva'] != 'Balanceado']['class'].value_counts().head(5)
            for moneda, count in dist.items():
                print(f"    - {moneda}: {count} registros")
    
    # Ejemplos
    print(f"\n  Primeras 5 filas:")
    cols_mostrar = ['ID', 'Nombre', 'class', 'percentage', 'moneda_nueva', 'pct_dominancia_nuevo']
    if all(c in df_nuevas.columns for c in cols_mostrar):
        print(df_nuevas[cols_mostrar].head().to_string(index=False))
    
    # Guardar
    output_nuevas = 'data/processed/allocations_nuevas.csv'
    df_nuevas.to_csv(output_nuevas, index=False, sep=';', encoding='latin-1')
    print(f"\n  💾 Guardado en {output_nuevas}")
    print(f"     Formato: LONG (múltiples filas por instrumento con dominancia)")
    
    # FASE 3: CARGAR ALLOCATIONS ANTIGUAS
    print("\n" + "-"*70)
    print("[Fase 3/3] Cargando allocations ANTIGUAS...")
    print("-"*70)
    df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
    print(f"  [OK] {len(df_antiguas)} instrumentos procesados")
    print(f"  [OK] Columnas generadas: {df_antiguas.columns.tolist()}")
    
    # Estadísticas
    if 'Pct_dominancia' in df_antiguas.columns:
        sin_datos = (df_antiguas['Pct_dominancia'] == 'Sin datos').sum()
        con_datos = len(df_antiguas) - sin_datos
        print(f"\n  Estadísticas:")
        print(f"    - Con datos:    {con_datos}")
        print(f"    - Sin datos:    {sin_datos}")
    
    # Ejemplos
    print(f"\n  Primeras 5 filas:")
    cols_mostrar = ['ID', 'Nombre', 'SubMoneda', 'Pct_dominancia']
    if all(c in df_antiguas.columns for c in cols_mostrar):
        print(df_antiguas[cols_mostrar].head().to_string(index=False))
    
    # Guardar
    output_antiguas = 'data/processed/allocations_antiguas.csv'
    df_antiguas.to_csv(output_antiguas, index=False, sep=';', encoding='latin-1')
    print(f"\n  💾 Guardado en {output_antiguas}")
    
    # RESUMEN FINAL
    print("\n" + "="*70)
    print(" RESUMEN FINAL ".center(70, "="))
    print("="*70)
    print(f"Allocations nuevas:    {len(df_nuevas)} instrumentos procesados")
    print(f"Allocations antiguas:  {len(df_antiguas)} instrumentos procesados")
    print("="*70)
    print("\n✅ Test completado exitosamente\n")

