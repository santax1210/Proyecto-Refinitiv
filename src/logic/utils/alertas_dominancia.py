"""
Módulo de alertas de dominancia para los pipelines de Moneda, Región y Sector.

Detecta dos escenarios anómalos comparando la distribución completa
de allocations antiguas y nuevas para un instrumento:

    DESAPARECE: La clase que era dominante en antiguas ya NO aparece con
                porcentaje > 0 en la distribución nueva completa.

    NUEVA:      La clase que es dominante en las nuevas NUNCA tuvo porcentaje
                > 0 en la distribución antigua completa.
"""
import re
import pandas as pd


# Categorías especiales que NO son clases reales de distribución.
# Se excluyen al escanear las distribuciones antiguas y nuevas completas.
CLASES_ESPECIALES = {
    'BALANCEADO', 'BALANCEADA',
    'OTROS', 'OTHER', 'OTHERS',
    'N/A', 'NA',
    'GLOBAL', 'GLOBALES',
    'TEMÁTICOS', 'TEMATICOS',
}

# ---------------------------------------------------------------------------
# Helpers de extracción
# ---------------------------------------------------------------------------

def _extraer_clase_de_pct(pct_str):
    """
    Extrae el nombre de la clase (moneda/región/sector) desde un string
    tipo 'CLP 100.00%' o 'Chile 85.50%'.

    Retorna None si el valor es vacío, 'Sin datos', 'Balanceado' o no parseable.
    """
    if pct_str is None:
        return None
    valor = str(pct_str).strip()
    if not valor or valor.upper() in ('NAN', 'NONE', 'SIN DATOS', ''):
        return None
    match = re.match(r'^(.+?)\s+[\d\.]+\s*%', valor)
    if not match:
        return None
    clase = match.group(1).strip()
    if clase.upper() in ('BALANCEADO', 'BALANCEADA', ''):
        return None
    return clase


def _obtener_clases_nuevas_con_pct(df_nuevas, instrument_id, col_clase='class', col_pct='percentage'):
    """
    Devuelve el Set de clases reales (case-insensitive, strip) que tienen
    porcentaje > 0 en la distribución nueva para el instrumento dado.

    Excluye categorías especiales: Balanceado, Otros, N/A, Global, etc.
    Funciona con df_nuevas en formato LONG (una fila por clase).
    """
    df_inst = df_nuevas[df_nuevas['ID'] == instrument_id]
    if df_inst.empty:
        return None  # instrumento sin datos nuevos → no generar alerta

    clases = set()
    for _, fila in df_inst.iterrows():
        clase = fila.get(col_clase)
        if clase is None or str(clase).strip().upper() in ('NAN', 'NONE', ''):
            continue
        clase_norm = str(clase).strip().upper()
        if clase_norm in CLASES_ESPECIALES:
            continue
        pct = pd.to_numeric(fila.get(col_pct), errors='coerce')
        if pd.notna(pct) and pct > 0:
            clases.add(clase_norm)
    return clases


def _obtener_clases_antiguas_con_pct(df_antiguas, instrument_id, cols_metadata):
    """
    Devuelve el Set de clases reales (case-insensitive, strip) que tienen
    porcentaje > 0 en la distribución antigua para el instrumento dado.

    Excluye columnas de metadata y categorías especiales: Balanceado, Otros, etc.
    Funciona con df_antiguas en formato WIDE (una columna por clase).
    """
    fila = df_antiguas[df_antiguas['ID'] == instrument_id]
    if fila.empty:
        return None  # instrumento sin datos antiguos → no generar alerta

    fila = fila.iloc[0]
    clases = set()
    for col in fila.index:
        if col in cols_metadata:
            continue
        col_norm = str(col).strip().upper()
        if col_norm in CLASES_ESPECIALES:
            continue
        pct = pd.to_numeric(fila[col], errors='coerce')
        if pd.notna(pct) and pct > 0:
            clases.add(col_norm)
    return clases


# ---------------------------------------------------------------------------
# Columnas de metadata a excluir según pipeline
# ---------------------------------------------------------------------------

COLS_META_MONEDA = {
    'ID', 'Nombre', 'SubMoneda', 'Pct_dominancia', 'Moneda:',
    'Creado', 'Tipo Instrumento', 'Tipo instrumento',
    'RIC', 'Isin', 'Cusip', 'Pais', 'País', 'Nemo', 'Ticker_BB', 'Currency', 'Moneda',
}

COLS_META_REGION = {
    'ID', 'Nombre', 'Pct_dominancia', 'Base Region:',
    'Creado', 'Tipo Instrumento', 'Tipo instrumento',
    'RIC', 'Isin', 'Cusip', 'Pais', 'País', 'Nemo', 'Ticker_BB',
}

COLS_META_SECTOR = {
    'ID', 'Nombre', 'sectores', 'Pct_dominancia', 'Sectores:',
    'Creado', 'Tipo Instrumento', 'Tipo instrumento',
    'RIC', 'Isin', 'Cusip', 'Pais', 'País', 'Nemo', 'Ticker_BB', 'Currency', 'Moneda',
}


# ---------------------------------------------------------------------------
# Función principal
# ---------------------------------------------------------------------------

def calcular_alerta_dominancia(
    row,
    df_nuevas,
    df_antiguas,
    col_pct_antigua='pct_dominancia_antigua',
    col_pct_nueva=None,           # si None, prueba pct_dominancia_nuevo y pct_dominancia_nueva
    col_clase_nuevas='class',     # columna de clase en df_nuevas (long format)
    col_pct_nuevas='percentage',  # columna de pct en df_nuevas (long format)
    cols_meta_antiguas=None,      # columnas a ignorar en df_antiguas (wide format)
):
    """
    Calcula la alerta de dominancia para un instrumento.

    Parámetros:
        row: fila del df_final
        df_nuevas: DataFrame en formato LONG con columnas [ID, col_clase_nuevas, col_pct_nuevas]
        df_antiguas: DataFrame en formato WIDE con columnas [ID, <clase1>, <clase2>, ...]
        col_pct_antigua: nombre de la col de dominancia antigua en df_final
        col_pct_nueva: nombre de la col de dominancia nueva en df_final (autodetecta si None)
        col_clase_nuevas: nombre de la col de clase en df_nuevas
        col_pct_nuevas: nombre de la col de porcentaje en df_nuevas
        cols_meta_antiguas: set de columnas de metadata en df_antiguas (excluidas del análisis)

    Retorna:
        'DESAPARECE' | 'NUEVA' | None
    """
    if cols_meta_antiguas is None:
        cols_meta_antiguas = COLS_META_MONEDA

    instrument_id = row.get('ID')
    if instrument_id is None:
        return None

    # --- Extraer clases dominantes ---
    clase_antigua = _extraer_clase_de_pct(row.get(col_pct_antigua))

    # Autodetectar columna nueva
    if col_pct_nueva is None:
        pct_nueva_val = row.get('pct_dominancia_nuevo') or row.get('pct_dominancia_nueva')
    else:
        pct_nueva_val = row.get(col_pct_nueva)
    clase_nueva = _extraer_clase_de_pct(pct_nueva_val)

    # Sin datos en alguno → sin alerta
    if clase_antigua is None and clase_nueva is None:
        return None

    # --- Obtener distribuciones completas ---
    clases_nuevas = _obtener_clases_nuevas_con_pct(df_nuevas, instrument_id, col_clase_nuevas, col_pct_nuevas)
    clases_antiguas = _obtener_clases_antiguas_con_pct(df_antiguas, instrument_id, cols_meta_antiguas)

    if clases_nuevas is None or clases_antiguas is None:
        return None  # datos insuficientes en uno de los lados

    # --- ALERTA DESAPARECE ---
    # La clase dominante antigua ya no aparece en absoluto en la nueva distribución
    if clase_antigua is not None and clase_antigua.upper() not in clases_nuevas:
        return 'DESAPARECE'

    # --- ALERTA NUEVA ---
    # La clase dominante nueva no existía en absoluto en la distribución antigua
    if clase_nueva is not None and clase_nueva.upper() not in clases_antiguas:
        return 'NUEVA'

    return None
