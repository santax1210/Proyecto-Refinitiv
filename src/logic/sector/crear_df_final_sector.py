import re

import numpy as np
import pandas as pd


VALORES_VACIOS = {'', 'NAN', 'NONE'}
# Valores que fuerzan Estado_3 en balanceados (columna 'Sectores:')
# Incluye variantes con y sin tilde, encoding artifacts y plural con S
ESTADOS_FALTA_ALLOCATION = {
    'FALTA ALLOCATION',   # singular (moneda usa este)
    'FALTA ALLOCATIONS',  # plural (especificado para sector)
    'VACÍO',              # con tilde (latin-1 0xCD)
    'VACÃO',              # con Ã (latin-1 0xC3) — variante real en datos
    'VACIO',              # sin tilde
}


def _normalizar_texto(valor):
    if pd.isna(valor):
        return ''
    texto = str(valor).strip()
    for _ in range(2):
        try:
            texto = texto.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
    return texto.strip()


def normalizar_nombre_sector(nombre):
    texto = _normalizar_texto(nombre)
    return texto.upper()


def normalizar_estado_sector(valor):
    """Normaliza un valor de la columna Sectores: para comparación contra ESTADOS_FALTA_ALLOCATION."""
    return normalizar_nombre_sector(valor)


def extraer_nombre_sector(pct_str):
    if pd.isna(pct_str) or normalizar_nombre_sector(pct_str) in VALORES_VACIOS | {'SIN DATOS'}:
        return 'Sin datos'
    valor = _normalizar_texto(pct_str)
    match = re.match(r'^(.+)\s+(\d+\.?\d*)\s*%$', valor)
    if match:
        return match.group(1).strip()
    return valor


def obtener_top_sectores_por_instrumento(row_antigua, top_n=5):
    cols_metadata = {
        'ID', 'Nombre', 'sectores', 'Pct_dominancia', 'Sectores:',
        'Creado', 'Tipo Instrumento', 'Tipo instrumento', 'RIC', 'Isin', 'Cusip',
        'Pais', 'País', 'Nemo', 'Ticker_BB', 'Currency', 'Moneda',
    }
    categorias_excluir = {'BALANCEADO', 'OTROS', 'N/A', 'GLOBAL', 'GLOBALES'}

    sectores_valores = {}
    for col in row_antigua.index:
        nombre_norm = normalizar_nombre_sector(col)
        if col in cols_metadata or nombre_norm in categorias_excluir:
            continue
        valor = pd.to_numeric(row_antigua[col], errors='coerce')
        if pd.notna(valor) and valor > 0:
            sectores_valores[str(col).strip()] = valor

    if not sectores_valores:
        return []

    top = sorted(sectores_valores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [sector for sector, _ in top]


def extraer_distribucion_antigua_sector(row, top_sectores):
    distribucion = {}
    for sector in top_sectores:
        if sector in row.index:
            valor = pd.to_numeric(row[sector], errors='coerce')
            distribucion[sector] = valor if pd.notna(valor) else 0.0
        else:
            distribucion[sector] = 0.0
    return distribucion


def extraer_distribucion_nueva_sector(df_nuevas, instrument_id, top_sectores):
    df_inst = df_nuevas[df_nuevas['ID'] == instrument_id]
    if df_inst.empty:
        return {sector: 0.0 for sector in top_sectores}

    distribucion = {sector: 0.0 for sector in top_sectores}
    for _, row in df_inst.iterrows():
        sector = _normalizar_texto(row.get('class'))
        for sector_top in top_sectores:
            if normalizar_nombre_sector(sector) == normalizar_nombre_sector(sector_top):
                porcentaje = pd.to_numeric(row.get('percentage'), errors='coerce')
                if pd.notna(porcentaje):
                    distribucion[sector_top] = porcentaje
    return distribucion


def calcular_distancia_hellinger_sector(dist1, dist2):
    if not dist1 or not dist2:
        return None

    sectores = set(dist1.keys()) | set(dist2.keys())
    suma1 = sum(dist1.values())
    suma2 = sum(dist2.values())

    if suma1 == 0 and suma2 == 0:
        return 0.0
    if suma1 == 0 or suma2 == 0:
        return 1.0

    suma_raices = 0.0
    for sector in sectores:
        p1 = max(0, dist1.get(sector, 0) / suma1)
        p2 = max(0, dist2.get(sector, 0) / suma2)
        suma_raices += (np.sqrt(p1) - np.sqrt(p2)) ** 2

    hellinger = (1 / np.sqrt(2)) * np.sqrt(suma_raices)
    return round(min(1.0, max(0.0, hellinger)), 4)


def calcular_hellinger_por_instrumento_sector(row, df_dominancia_antiguas, df_dominancia_nuevas):
    if 'ID' not in row:
        return None

    fila_antigua = df_dominancia_antiguas[df_dominancia_antiguas['ID'] == row['ID']]
    if fila_antigua.empty:
        return None

    top_sectores = obtener_top_sectores_por_instrumento(fila_antigua.iloc[0], top_n=5)
    if not top_sectores:
        return None

    dist_antigua = extraer_distribucion_antigua_sector(fila_antigua.iloc[0], top_sectores)
    dist_nueva = extraer_distribucion_nueva_sector(df_dominancia_nuevas, row['ID'], top_sectores)
    return calcular_distancia_hellinger_sector(dist_antigua, dist_nueva)


def extraer_porcentaje_dominante_sector(row, columna):
    if columna not in row or pd.isna(row[columna]):
        return None
    valor = _normalizar_texto(row[columna])
    if normalizar_nombre_sector(valor) in VALORES_VACIOS | {'SIN DATOS'}:
        return None
    match = re.search(r'(\d+\.?\d*)\s*%', valor)
    if match:
        return float(match.group(1))
    try:
        return float(valor)
    except Exception:
        return None


def obtener_pct_sector_en_nuevas(df_nuevas, instrument_id, sector):
    df_inst = df_nuevas[df_nuevas['ID'] == instrument_id]
    if df_inst.empty:
        return None

    pct_series = pd.to_numeric(df_inst['percentage'], errors='coerce')
    total = pct_series[pct_series > 0].sum()

    for _, fila in df_inst.iterrows():
        clase = fila.get('class')
        if normalizar_nombre_sector(clase) == normalizar_nombre_sector(sector):
            porcentaje = pd.to_numeric(fila.get('percentage'), errors='coerce')
            if pd.notna(porcentaje) and total > 0:
                return round(porcentaje / total * 100, 4)

    return 0.0


def calcular_variacion_balanceados_sector(row, df_dominancia_antiguas, df_dominancia_nuevas):
    if normalizar_nombre_sector(row.get('sector_nueva')) != 'BALANCEADO':
        return None
    if pd.isna(row.get('Estado')) or row.get('Estado') == '':
        return None

    estado = str(row.get('Estado')).strip()
    if estado == 'Estado_1':
        return calcular_hellinger_por_instrumento_sector(row, df_dominancia_antiguas, df_dominancia_nuevas)

    if estado == 'Estado_2':
        pct_antiguo = extraer_porcentaje_dominante_sector(row, 'pct_dominancia_antigua')
        sector_antiguo = extraer_nombre_sector(row.get('pct_dominancia_antigua', ''))
        if pct_antiguo is None or sector_antiguo in ('', 'Sin datos'):
            return None
        pct_mismo_sector = obtener_pct_sector_en_nuevas(df_dominancia_nuevas, row['ID'], sector_antiguo)
        if pct_mismo_sector is None:
            return None
        return round(abs(pct_antiguo - pct_mismo_sector) / 100.0, 4)

    return None


def calcular_variacion_no_balanceados_sector(row, df_dominancia_nuevas):
    if normalizar_nombre_sector(row.get('sector_nueva')) == 'BALANCEADO':
        return None
    if pd.isna(row.get('Estado')) or row.get('Estado') == '' or 'ID' not in row:
        return None

    pct_antiguo = extraer_porcentaje_dominante_sector(row, 'pct_dominancia_antigua')
    sector_antiguo = extraer_nombre_sector(row.get('pct_dominancia_antigua', ''))
    if pct_antiguo is None or sector_antiguo in ('', 'Sin datos'):
        return None

    pct_mismo_sector = obtener_pct_sector_en_nuevas(df_dominancia_nuevas, row['ID'], sector_antiguo)
    if pct_mismo_sector is None:
        return None

    return round(abs(pct_antiguo - pct_mismo_sector) / 100.0, 4)


def detectar_cambio_sector(row):
    # Sin datos SOLO si el instrumento no está en df_nuevas (sector_nueva vacío)
    if 'sector_nueva' not in row:
        return 'Sin datos'

    nueva = normalizar_nombre_sector(row['sector_nueva'])
    if nueva in VALORES_VACIOS:
        return 'Sin datos'

    # sector_antigua vacío (columna 'sectores' en instruments.csv no poblada)
    # → no es 'Sin datos', el instrumento sí existe en df_nuevas
    antigua = normalizar_nombre_sector(row.get('sector_antigua', ''))
    if antigua in VALORES_VACIOS | {'SIN DATOS'}:
        return 'Sí'  # sin clasificación anterior → se considera cambio

    if nueva == antigua:
        return 'No'
    return 'Sí'


def calcular_estado_sector(row):
    if str(row.get('Cambio', '')).strip() == 'Sin datos':
        return ''

    nueva = normalizar_nombre_sector(row.get('sector_nueva', ''))
    if nueva in VALORES_VACIOS:
        return ''

    antigua = normalizar_nombre_sector(row.get('sector_antigua', ''))

    if nueva == 'BALANCEADO':
        base_sector = normalizar_estado_sector(row.get('Sectores:', ''))
        if base_sector in ESTADOS_FALTA_ALLOCATION:
            return 'Estado_3'
        if antigua == 'BALANCEADO':
            return 'Estado_1'
        return 'Estado_2'  # antigua vacía o sin clasificación → Sector/Vacío → Balanceado

    if antigua == 'BALANCEADO':
        return 'Estado_2'
    if antigua in VALORES_VACIOS | {'SIN DATOS'}:
        return 'Estado_3'  # sin clasificación anterior → No Balanceado → Estado_3
    if antigua == nueva:
        return 'Estado_1'
    return 'Estado_3'


def calcular_nivel_variacion_sector(row):
    val_bal = row.get('variacion_balanceados')
    val_nobal = row.get('variacion_no_balanceados')
    estado = str(row.get('Estado', '')).strip()

    if pd.notna(val_bal) and val_bal is not None:
        valor = float(val_bal)
        if estado == 'Estado_1':
            return 'Baja' if valor <= 0.30 else 'Alta'
        return 'Baja' if valor <= 0.40 else 'Alta'

    if pd.notna(val_nobal) and val_nobal is not None:
        return 'Baja' if float(val_nobal) <= 0.40 else 'Alta'

    return None


def filtrar_balanceados_sector(df_final):
    return df_final[df_final['sector_nueva'] == 'Balanceado'].copy()


def filtrar_no_balanceados_sector(df_final):
    return df_final[df_final['sector_nueva'] != 'Balanceado'].copy()


def filtrar_cambios_sector(df_final):
    return df_final[df_final['Cambio'] == 'Sí'].copy()


def crear_df_final_sector(df_instruments, df_dominancia_nuevas_sector, df_dominancia_antiguas_sector):
    cols_base = [c for c in ['ID', 'Nombre', 'Tipo instrumento', 'sectores'] if c in df_instruments.columns]
    df_base = df_instruments[cols_base].copy()

    cols_nuevas = [
        c for c in ['ID', 'sector_nueva', 'pct_dominancia_nueva', 'pct_escalado', 'pct_original']
        if c in df_dominancia_nuevas_sector.columns
    ]
    df_nuevas_ded = df_dominancia_nuevas_sector[cols_nuevas].drop_duplicates(subset=['ID'], keep='first')
    df_final = pd.merge(df_base, df_nuevas_ded, on='ID', how='left')

    if 'sectores' in df_final.columns:
        df_final = df_final.rename(columns={'sectores': 'sector_antigua'})

    cols_antiguas = [c for c in ['ID', 'Pct_dominancia', 'Sectores:'] if c in df_dominancia_antiguas_sector.columns]
    df_final = pd.merge(df_final, df_dominancia_antiguas_sector[cols_antiguas], on='ID', how='left')
    if 'Pct_dominancia' in df_final.columns:
        df_final = df_final.rename(columns={'Pct_dominancia': 'pct_dominancia_antigua'})

    df_final['Cambio'] = df_final.apply(detectar_cambio_sector, axis=1)
    df_final['Estado'] = df_final.apply(calcular_estado_sector, axis=1)

    print('  [INFO] Calculando distancia de Hellinger por instrumento (sector)...')
    df_final['distancia_hellinger'] = df_final.apply(
        lambda row: calcular_hellinger_por_instrumento_sector(
            row, df_dominancia_antiguas_sector, df_dominancia_nuevas_sector
        ),
        axis=1
    )

    print('  [INFO] Calculando variación para balanceados (sector)...')
    df_final['variacion_balanceados'] = df_final.apply(
        lambda row: calcular_variacion_balanceados_sector(
            row, df_dominancia_antiguas_sector, df_dominancia_nuevas_sector
        ),
        axis=1
    )

    print('  [INFO] Calculando variación para no balanceados (sector)...')
    df_final['variacion_no_balanceados'] = df_final.apply(
        lambda row: calcular_variacion_no_balanceados_sector(row, df_dominancia_nuevas_sector),
        axis=1
    )

    df_final['nivel_variacion'] = df_final.apply(calcular_nivel_variacion_sector, axis=1)

    # Alertas de dominancia
    from src.logic.utils.alertas_dominancia import calcular_alerta_dominancia, COLS_META_SECTOR
    print('  [INFO] Calculando alertas de dominancia (sector)...')
    df_final['alerta_dominancia'] = df_final.apply(
        lambda row: calcular_alerta_dominancia(
            row,
            df_dominancia_nuevas_sector,
            df_dominancia_antiguas_sector,
            col_pct_antigua='pct_dominancia_antigua',
            col_pct_nueva='pct_dominancia_nueva',
            col_clase_nuevas='class',
            col_pct_nuevas='percentage',
            cols_meta_antiguas=COLS_META_SECTOR,
        ),
        axis=1
    )
    n_alertas = df_final['alerta_dominancia'].notna().sum()
    print(f'  [OK] Alertas detectadas: {n_alertas} instrumentos')

    cols_orden = [
        'Nombre', 'ID', 'Tipo instrumento',
        'sector_antigua', 'sector_nueva',
        'pct_dominancia_nueva', 'pct_escalado', 'pct_original',
        'pct_dominancia_antigua', 'Cambio', 'Estado', 'nivel_variacion',
        'distancia_hellinger', 'variacion_balanceados', 'variacion_no_balanceados',
        'alerta_dominancia',
    ]
    cols_finales = [c for c in cols_orden if c in df_final.columns]
    return df_final[cols_finales]
