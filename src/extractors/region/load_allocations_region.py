import pandas as pd
import re


# ============================================================================
# NOMBRES CANÓNICOS DE REGIÓN (deben coincidir exactamente con columnas de allocations_region.csv)
# ============================================================================
CANONICAL_REGION_NAMES = {
    'Africa Eme.', 'Africa Front.', 'Asia Des.', 'Asia Eme.', 'Asia Front.',
    'Balanceado', 'Chile', 'Europa Des.', 'Europa Eme.', 'Europa Front.',
    'Global Des.', 'Global Eme.', 'Globales', 'Latam Eme. ex-Chile',
    'Latam Front.', 'M. Oriente Eme.', 'M. Oriente Front.',
    'N/A', 'Norteamerica', 'Oceanía', 'Otros', 'Temáticos',
}

# ============================================================================
# MAPEO DE COLUMNAS: nombres raw del CSV nuevas → nombre canónico
# Claves en minúsculas (lookup siempre normaliza a minúsculas).
# Columnas sin entrada en este mapa son descartadas del export.
# ============================================================================
REGION_COLUMN_MAP = {
    # --- Ya correctos (identidad) ---
    'africa eme.':               'Africa Eme.',
    'africa front.':             'Africa Front.',
    'asia des.':                 'Asia Des.',
    'asia eme.':                 'Asia Eme.',
    'asia front.':               'Asia Front.',
    'balanceado':                'Balanceado',
    'chile':                     'Chile',
    'europa des.':               'Europa Des.',
    'europa eme.':               'Europa Eme.',
    'europa front.':             'Europa Front.',
    'global des.':               'Global Des.',
    'global eme.':               'Global Eme.',
    'globales':                  'Globales',
    'latam eme. ex-chile':       'Latam Eme. ex-Chile',
    'latam eme. ex chile':       'Latam Eme. ex-Chile',
    'latam front.':              'Latam Front.',
    'm. oriente eme.':           'M. Oriente Eme.',
    'm. oriente front.':         'M. Oriente Front.',
    'n/a':                       'N/A',
    'norteamerica':              'Norteamerica',
    'otros':                     'Otros',
    'temáticos':                 'Temáticos',
    'tematicos':                 'Temáticos',
    'oceanía':                   'Oceanía',
    'oceania':                   'Oceanía',
    # --- Variantes de nombre (nuevas usan nombre distinto al de antiguas) ---
    'latam eme.':                'Latam Eme. ex-Chile',
    'technology':                'Temáticos',
    # --- Nombres de sistema externo (snake_case / inglés) ---
    'north_america_fi':          'Norteamerica',
    'north_america':             'Norteamerica',
    'europe_fi':                 'Europa Des.',
    'europe_eq':                 'Europa Des.',
    'europe':                    'Europa Des.',
    'apac_(ex_japan)_fi':        'Asia Des.',
    'apac_ex_japan':             'Asia Des.',
    'apac_(ex japan)_fi':        'Asia Des.',
    'australia_&_new_zealand':   'Oceanía',
    'australia_and_new_zealand': 'Oceanía',
    'emerging_market_fi':        'Global Eme.',
    'emerging_markets':          'Global Eme.',
    'middle_east_&_africa':      'M. Oriente Eme.',
    'middle_east_and_africa':    'M. Oriente Eme.',
    'world':                     'Globales',
    "people's_republic_of_china": 'Asia Eme.',
    # País → región canónica más cercana
    'honduras':                  'Latam Eme. ex-Chile',
    'mexice':                    'Latam Eme. ex-Chile',   # typo de Mexico
    'mexico':                    'Latam Eme. ex-Chile',
    'azerbaijan':                'M. Oriente Eme.',
    'uzbekistan':                'M. Oriente Eme.',
    'faroe_islands':             'Otros',
    # Encoding artifacts conocidos (latin-1 misread de UTF-8)
    # 'OceanÃ­a' → lowercased after decode fix = 'oceanía' (ya cubierto)
    # 'TÃ¼rkiye' o variantes → M. Oriente Eme.
    'türkiye':                   'M. Oriente Eme.',
    'turkiye':                   'M. Oriente Eme.',
    # Garbled directamente (sin fix de encoding posible)
    'tãâ¼rkiye':                 'M. Oriente Eme.',
    'peopleã¢â¬â¢s_republic_of_china': 'Asia Eme.',
    # No hay mapeo válido para estos → serán descartados por ausencia en este dict:
    # 'cash/equiv', 'cash_&_forwards'
}

# Para comparación antigua vs nueva (mantiene compatibilidad con código existente)
REGION_NAMES_NORMALIZE = {
    'LATAM EME.':          'LATAM_EME',
    'LATAM EME. EX-CHILE': 'LATAM_EME',
    'LATAM EME. EX CHILE': 'LATAM_EME',
    'OCÉANIA':             'OCEANIA',
    'OCEANIA':             'OCEANIA',
    'OCEANÍA':             'OCEANIA',
    'TEMÁTICOS':           'TEMATICOS',
    'TEMATICOS':           'TEMATICOS',
    'TECHNOLOGY':          'TEMATICOS',
}


def _normalizar_clave_region(nombre):
    """Normaliza un nombre de columna para lookup en REGION_COLUMN_MAP.
    Intenta corregir problemas de encoding latin-1/UTF-8 en uno o dos pasos."""
    s = str(nombre).strip()
    for _ in range(2):
        try:
            s = s.encode('latin-1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            break
    return s.lower().strip()


def _mapear_columna_region(nombre):
    """Mapea un nombre de columna raw al nombre canónico de región.
    Retorna None si no existe mapeo válido (la columna debe descartarse)."""
    key = _normalizar_clave_region(nombre)
    if key in REGION_COLUMN_MAP:
        return REGION_COLUMN_MAP[key]
    # Fallback por palabras clave para nombres con encoding muy dañado
    if 'china' in key and 'republic' in key:
        return 'Asia Eme.'
    if 'rkiye' in key or 'turkey' in key:
        return 'M. Oriente Eme.'
    return None


def normalizar_nombre_region(nombre):
    """Normaliza un nombre de región para comparación (maneja variantes de nombre y encoding)."""
    if not nombre or str(nombre).upper() in ('', 'NAN', 'NONE', 'SIN DATOS'):
        return nombre
    s = str(nombre).strip()
    for _ in range(2):
        try:
            s = s.encode('latin-1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            break
    upper = s.strip().upper()
    return REGION_NAMES_NORMALIZE.get(upper, upper)


# ============================================================================
# FUNCIONES AUXILIARES PARA ALLOCATIONS NUEVAS (WIDE → LONG)
# ============================================================================

def _escalar_porcentajes_region(grupo_regiones):
    """
    Escala los porcentajes de un grupo de regiones para que sumen exactamente 100%.
    Ignora valores negativos o cero (posiciones cortas / hedging).
    """
    grupo = grupo_regiones.copy()
    mask_positivos = grupo['percentage'] > 0
    total_original = grupo.loc[mask_positivos, 'percentage'].sum()

    if total_original == 0:
        grupo['pct_escalado'] = 0.0
    else:
        grupo['pct_escalado'] = 0.0
        grupo.loc[mask_positivos, 'pct_escalado'] = (
            grupo.loc[mask_positivos, 'percentage'] / total_original
        )
    return grupo, total_original


def _cargar_archivo_nuevas_region(nuevas_path):
    """
    Carga allocations_nuevas_region.csv (formato WIDE) y lo convierte a LONG.

    Diferencias clave vs moneda:
    - Formato WIDE: primera columna (sin nombre) = identificador del instrumento.
    - Resto de columnas = regiones con sus porcentajes (coma como decimal).
    - No hay columna 'classif' (todo el archivo es región).
    """
    import csv

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

    # Primera columna (sin nombre) = identificador → renombrar a 'instrument'
    first_col = df.columns[0]
    df = df.rename(columns={first_col: 'instrument'})

    # Columnas de región = todo excepto 'instrument'
    region_cols = [c for c in df.columns if c != 'instrument']

    # WIDE → LONG
    df_long = df.melt(
        id_vars=['instrument'],
        value_vars=region_cols,
        var_name='region',
        value_name='percentage'
    )

    # Normalizar decimales y convertir a numérico
    df_long['percentage'] = (
        df_long['percentage']
        .astype(str)
        .str.strip()
        .str.replace(',', '.', regex=False)
    )
    df_long['percentage'] = pd.to_numeric(df_long['percentage'], errors='coerce')

    # Eliminar filas con percentage nulo o cero para reducir volumen
    df_long = df_long[df_long['percentage'].notna() & (df_long['percentage'] > 0)].copy()

    # Mapear nombres de columna raw → nombres canónicos de allocations_region.csv
    df_long['region'] = df_long['region'].apply(_mapear_columna_region)
    # Descartar columnas sin mapeo válido (ej. cash/equiv, columnas de países sin región)
    df_long = df_long[df_long['region'].notna()].copy()
    # Agregar filas que quedaron con mismo (instrument, region) tras el mapeo
    # (ej. europe_fi + europe_eq → ambas mapean a Europa Des., se suman)
    df_long = df_long.groupby(['instrument', 'region'], as_index=False)['percentage'].sum()

    return df_long


def _cruzar_con_instruments_region(df_instruments, df_nuevas_long):
    """
    Cruza df_instruments con las allocations nuevas de región (LONG)
    intentando secuencialmente RIC → Isin → Cusip.

    Excluye automáticamente instrumentos cuyas filas tengan TODAS el
    percentage inválido (NaN, 0 o nulo).
    """
    resultados = []
    matched_ids = set()

    for key_instr, key_nuevas in [('RIC', 'instrument'), ('Isin', 'instrument'), ('Cusip', 'instrument')]:
        pendientes = df_instruments[~df_instruments['ID'].isin(matched_ids)]
        if pendientes.empty:
            break

        df_merge = pd.merge(
            pendientes[['ID', 'Nombre', key_instr]],
            df_nuevas_long,
            left_on=key_instr,
            right_on=key_nuevas,
            how='inner'
        )

        if not df_merge.empty:
            df_merge['tipo_id'] = key_instr
            resultados.append(df_merge)
            matched_ids.update(df_merge['ID'].tolist())

    if not resultados:
        return pd.DataFrame(columns=['ID', 'Nombre', 'instrument', 'region', 'percentage', 'tipo_id'])

    df_merged = pd.concat(resultados, ignore_index=True)

    cols_to_keep = [c for c in ['ID', 'Nombre', 'instrument', 'region', 'percentage', 'tipo_id']
                    if c in df_merged.columns]
    df_merged = df_merged[cols_to_keep].drop_duplicates(subset=['ID', 'region'])

    # Excluir instrumentos con TODAS las filas de percentage inválido
    ids_validos = set()
    ids_invalidos = set()
    for id_inst, grupo in df_merged.groupby('ID'):
        pcts_validos = grupo['percentage'].dropna()
        pcts_validos = pcts_validos[pcts_validos > 0]
        if len(pcts_validos) > 0:
            ids_validos.add(id_inst)
        else:
            ids_invalidos.add(id_inst)

    if ids_invalidos:
        print(f"  [INFO] Excluidos {len(ids_invalidos)} instrumentos (región) con todas las filas percentage=NA")

    return df_merged[df_merged['ID'].isin(ids_validos)].copy()


def _calcular_dominancia_region(df_nuevas_merged, umbral=0.9):
    """
    Calcula dominancia de región por instrumento.
    Retorna 1 fila por instrumento con:
      - region_nueva:         "Balanceado" o nombre de región dominante
      - pct_dominancia_nueva: Texto "REGION XX.XX%"
      - pct_escalado:         Suma escalada × 100 (debe ser ~100.0)
      - pct_original:         Suma original
    """
    resultados = []

    for instrumento_id, grupo in df_nuevas_merged.groupby('ID'):
        nombre = grupo['Nombre'].iloc[0] if 'Nombre' in grupo.columns else None
        instrument = grupo['instrument'].iloc[0] if 'instrument' in grupo.columns else None

        pct_original = grupo['percentage'].sum()

        grupo_escalado, _ = _escalar_porcentajes_region(grupo[['region', 'percentage']])
        pct_escalado = grupo_escalado['pct_escalado'].sum()

        idx_max = grupo_escalado['pct_escalado'].idxmax()
        region_max = grupo_escalado.loc[idx_max, 'region']
        pct_max = grupo_escalado.loc[idx_max, 'pct_escalado']

        region_nueva = region_max if pct_max >= umbral else "Balanceado"
        pct_dominancia_nueva = f"{region_max} {pct_max * 100:.2f}%"

        resultados.append({
            'ID': instrumento_id,
            'Nombre': nombre,
            'instrument': instrument,
            'region_nueva': region_nueva,
            'pct_dominancia_nueva': pct_dominancia_nueva,
            'pct_escalado': round(pct_escalado * 100, 2),
            'pct_original': round(pct_original, 2)
        })

    return pd.DataFrame(resultados)


def _enriquecer_allocations_region(df_nuevas_merged, umbral=0.9):
    """
    Enriquece el DataFrame LONG con columnas de dominancia
    y ASEGURA que la columna 'percentage' esté escalada al 100% total.
    """
    # 1. Aplicar escalado individual a cada fila (prorrateo)
    df_list = []
    for _, grupo in df_nuevas_merged.groupby('ID'):
        grupo_escalado, _ = _escalar_porcentajes_region(grupo)
        # Reemplazar percentage con la versión escalada (multiplicada por 100)
        grupo_escalado['percentage'] = (grupo_escalado['pct_escalado'] * 100).round(4)
        df_list.append(grupo_escalado)
    
    df_final_long = pd.concat(df_list, ignore_index=True)

    # 2. Calcular dominancia de región por instrumento (resumen)
    df_dominancia = _calcular_dominancia_region(df_nuevas_merged, umbral)
    
    # 3. Merge con el resumen de dominancia
    df_enriquecido = pd.merge(
        df_final_long,
        df_dominancia[['ID', 'region_nueva', 'pct_dominancia_nueva', 'pct_escalado', 'pct_original']],
        on='ID',
        how='left'
    )

    # Eliminar columna auxiliar de escalado si quedó duplicada por el merge
    if 'pct_escalado_x' in df_enriquecido.columns:
        df_enriquecido = df_enriquecido.drop(columns=['pct_escalado_x'])
    if 'pct_escalado_y' in df_enriquecido.columns:
        df_enriquecido = df_enriquecido.rename(columns={'pct_escalado_y': 'pct_escalado'})

    return df_enriquecido


# ============================================================================
# FUNCIÓN PRINCIPAL: LOAD ALLOCATIONS NUEVAS REGIÓN
# ============================================================================

def load_allocations_nuevas_region(df_instruments, nuevas_path, umbral=0.9):
    """
    Carga y procesa allocations nuevas de REGIÓN.

    PROCESO:
    1. Lee el archivo WIDE (primera col = identificador, resto = regiones con %)
    2. Convierte a LONG (melt)
    3. Cruza con df_instruments por RIC → Isin → Cusip
    4. Calcula dominancia (umbral 90% por defecto)

    RETORNA DataFrame LONG (múltiples filas por instrumento):
      ID, Nombre, instrument, region, percentage, tipo_id,
      region_nueva, pct_dominancia_nueva, pct_escalado, pct_original
    """
    df_nuevas_long = _cargar_archivo_nuevas_region(nuevas_path)

    if df_nuevas_long.empty:
        print("  [WARN] No se pudieron cargar allocations nuevas de región.")
        return pd.DataFrame(columns=['ID', 'Nombre', 'instrument', 'region', 'percentage',
                                     'tipo_id', 'region_nueva', 'pct_dominancia_nueva',
                                     'pct_escalado', 'pct_original'])

    df_merged = _cruzar_con_instruments_region(df_instruments, df_nuevas_long)

    if df_merged.empty:
        print("  [WARN] No se encontraron matches en allocations nuevas de región.")
        return pd.DataFrame(columns=['ID', 'Nombre', 'instrument', 'region', 'percentage',
                                     'tipo_id', 'region_nueva', 'pct_dominancia_nueva',
                                     'pct_escalado', 'pct_original'])

    return _enriquecer_allocations_region(df_merged, umbral)


# ============================================================================
# FUNCIONES AUXILIARES PARA ALLOCATIONS ANTIGUAS REGIÓN
# ============================================================================

def _detectar_columna_base_region(df):
    """
    Detecta la columna 'Base Región:' independientemente de la codificación.
    Busca una columna que contenga 'base' y 'regi' (case-insensitive).
    """
    for col in df.columns:
        col_lower = col.lower().strip()
        if 'base' in col_lower and 'regi' in col_lower:
            return col
    return None


def _identificar_columnas_region(df_antiguas, excluir_cols):
    """
    Identifica columnas de región en el dataframe de antiguas.
    Excluye metadata conocida y la columna Base Región:.
    """
    cols_metadata = [
        'ID', 'Nombre', 'Creado', 'Tipo Instrumento', 'Tipo instrumento',
        'RIC', 'Isin', 'Cusip', 'Moneda', 'Pais', 'País',
        'Nemo', 'Ticker_BB', 'Currency',
    ]

    cols_region = []
    for col in df_antiguas.columns:
        if col in cols_metadata or col in excluir_cols:
            continue
        # Excluir Base Región: (cualquier variante de encoding)
        col_lower = col.lower().strip()
        if 'base' in col_lower and 'regi' in col_lower:
            continue
        cols_region.append(col)

    return cols_region


def _calcular_pct_dominancia_antiguas_region(row, cols_region):
    """
    Busca la región con mayor porcentaje en una fila y retorna  "REGION XX.XX%".
    """
    region_max = None
    pct_max = 0.0

    for col in cols_region:
        try:
            val = float(str(row[col]).strip().replace(',', '.'))
            if val > pct_max:
                pct_max = val
                region_max = col.strip()
        except (ValueError, TypeError):
            continue

    if region_max and pct_max > 0:
        return f"{region_max} {pct_max:.2f}%"
    return "Sin datos"


# ============================================================================
# FUNCIÓN PRINCIPAL: LOAD ALLOCATIONS ANTIGUAS REGIÓN
# ============================================================================

def load_allocations_antiguas_region(df_instruments, antiguas_path):
    """
    Carga y procesa allocations antiguas de REGIÓN.

    PROCESO:
    1. Lee allocations_region.csv
    2. Cruza con df_instruments por ID
    3. Identifica columnas de región (excluye metadata y 'Base Región:')
    4. Calcula Pct_dominancia
    5. Retorna DataFrame con columnas de región + Pct_dominancia + 'Base Region:'

    DIFERENCIAS vs moneda:
    - Columna de estado se llama 'Base Región:' (en lugar de 'Moneda:')
    - Dos valores indican falta de allocation: 'FALTA ALLOCATION' y 'SIN ASIGNAR'
      (en moneda solo era 'FALTA ALLOCATION')
    """
    df_antiguas = pd.read_csv(antiguas_path, sep=';', encoding='latin-1', on_bad_lines='skip')
    df_antiguas.columns = df_antiguas.columns.str.strip()

    if 'ID' in df_antiguas.columns:
        df_antiguas['ID'] = pd.to_numeric(df_antiguas['ID'], errors='coerce').astype('Int64')
        df_antiguas = df_antiguas.dropna(subset=['ID'])

    base_cols = ['ID', 'Nombre']

    # Detectar columna Base Región: (encoding variable)
    col_base_region = _detectar_columna_base_region(df_antiguas)

    # Cruzar por ID con df_instruments
    df_result = pd.merge(
        df_instruments[base_cols],
        df_antiguas,
        on='ID',
        how='inner',
        suffixes=('', '_drop')
    )
    cols_drop = [c for c in df_result.columns if c.endswith('_drop')]
    if cols_drop:
        df_result = df_result.drop(columns=cols_drop)

    # Identificar columnas de región (excluir base_cols + col_base_region)
    excluir = base_cols + ([col_base_region] if col_base_region else [])
    cols_region = _identificar_columnas_region(df_result, excluir)

    if not cols_region:
        print("  [WARN] No se encontraron columnas de región en allocations antiguas.")
        df_result['Pct_dominancia'] = "Sin datos"
        df_result['Base Region:'] = ''
        return df_result[base_cols + ['Pct_dominancia', 'Base Region:']]

    # Normalizar porcentajes mal formateados: algunos archivos vienen con valores
    # como 884.39 en lugar de 88.439. Si un valor supera 120, se mueve el separador decimal
    # un lugar a la izquierda (divide por 10).
    for col in cols_region:
        df_result[col] = pd.to_numeric(
            df_result[col].astype(str).str.strip().str.replace(',', '.', regex=False),
            errors='coerce'
        )
        mask_mal_formateado = df_result[col] > 120
        if mask_mal_formateado.any():
            n = mask_mal_formateado.sum()
            print(f"  [FIX] Columna '{col}': {n} valor(es) >120% corregidos (decimal a la izquierda, /10) en allocations antiguas de región.")
            df_result.loc[mask_mal_formateado, col] = df_result.loc[mask_mal_formateado, col] / 10

    # Calcular Pct_dominancia
    df_result['Pct_dominancia'] = df_result.apply(
        lambda row: _calcular_pct_dominancia_antiguas_region(row, cols_region), axis=1
    )

    # Normalizar nombre de la columna Base Región: → 'Base Region:' (sin tilde, consistente)
    if col_base_region:
        df_result = df_result.rename(columns={col_base_region: 'Base Region:'})

    cols_finales = base_cols + cols_region + ['Pct_dominancia']
    if 'Base Region:' in df_result.columns:
        cols_finales.append('Base Region:')
    cols_finales = [c for c in cols_finales if c in df_result.columns]

    return df_result[cols_finales]


# ============================================================================
# BLOQUE DE TEST Y EJECUCIÓN MANUAL
# ============================================================================

if __name__ == "__main__":
    import sys
    sys.path.insert(0, '.')
    from src.extractors.region.load_instruments_region import load_instruments_region

    print("\n" + "="*70)
    print(" TEST: CARGA DE ALLOCATIONS REGIÓN ".center(70, "="))
    print("="*70)

    df_instr = load_instruments_region()
    print(f"  [OK] {len(df_instr)} instrumentos cargados")

    print("\n[Fase 2/3] Cargando allocations nuevas de región...")
    df_nuevas = load_allocations_nuevas_region(
        df_instr,
        'data/raw/region/allocations_nuevas_region.csv',
        umbral=0.9
    )
    print(f"  [OK] {len(df_nuevas)} filas (formato long)")
    if 'region_nueva' in df_nuevas.columns:
        bal = (df_nuevas['region_nueva'] == 'Balanceado').sum()
        print(f"    Balanceados: {bal}  |  No balanceados: {len(df_nuevas) - bal}")

    print("\n[Fase 3/3] Cargando allocations antiguas de región...")
    df_antiguas = load_allocations_antiguas_region(
        df_instr,
        'data/raw/region/allocations_region.csv'
    )
    print(f"  [OK] {len(df_antiguas)} instrumentos")
    if 'Pct_dominancia' in df_antiguas.columns:
        sin_datos = (df_antiguas['Pct_dominancia'] == 'Sin datos').sum()
        print(f"    Con datos: {len(df_antiguas) - sin_datos}  |  Sin datos: {sin_datos}")

