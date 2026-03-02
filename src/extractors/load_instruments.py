import pandas as pd
import os

def load_df_instruments(pos_path, instr_path):
    """
    Carga el dataframe df_instruments cruzando posiciones y maestro de instrumentos.
    Aplica filtros de fecha y tipo de instrumento.
    """
    # 1. Leer archivos
    df_pos = pd.read_csv(pos_path, sep=';', encoding='latin-1', on_bad_lines='skip')
    df_instr = pd.read_csv(instr_path, sep=';', encoding='latin-1', on_bad_lines='skip')
    
    # Normalizar columnas (eliminar espacios en blanco en los extremos)
    df_pos.columns = df_pos.columns.str.strip()
    df_instr.columns = df_instr.columns.str.strip()
    
    with open('debug_cols_runtime.txt', 'w') as f:
        f.write("\n".join(df_instr.columns.tolist()))
    
    # 2. Filtrar posiciones por fecha > 1/6/2025
    col_fecha = 'F. Proceso'
    df_pos[col_fecha] = pd.to_datetime(df_pos[col_fecha], dayfirst=True, errors='coerce')
    df_pos = df_pos[df_pos[col_fecha] > pd.Timestamp(2025, 6, 1)]
    
    # 3. Cruzar con maestro usando ID
    # El maestro contiene los códigos C02, C03, etc. que necesitamos para filtrar
    df_merged = pd.merge(df_pos[['ID', col_fecha]], df_instr, on='ID', how='inner')
    
    # 4. Filtrar por Tipo Instrumento (códigos en el maestro)
    # Nota: El nombre exacto es 'Tipo instrumento' con i minúscula
    col_tipo = 'Tipo instrumento'
    tipos_interes = ['C02', 'C14', 'C04', 'C03', 'C09', 'C10']
    df_merged = df_merged[df_merged[col_tipo].isin(tipos_interes)]
    
    # 5. Seleccionar columnas requeridas por el usuario
    # ID, Nombre, Pais, Tipo instrumento, RIC,Isin,Cusip, SubMoneda
    cols_map = {
        'ID': 'ID',
        'Nombre': 'Nombre',
        'País': 'Pais',
        'Tipo instrumento': 'Tipo instrumento',
        'RIC': 'RIC',
        'Isin': 'Isin',
        'Cusip': 'Cusip',
        'SubMoneda': 'SubMoneda'  # Columna directa del maestro
    }
    
    # Identificamos columnas existentes
    existing_cols = [c for c in cols_map.keys() if c in df_merged.columns]
    df_result = df_merged[existing_cols].copy()
    
    # Renombrar
    df_result = df_result.rename(columns={k:v for k,v in cols_map.items() if k in existing_cols})
    
    # Eliminar duplicados de ID (un registro por instrumento)
    df_result = df_result.drop_duplicates(subset=['ID'])
    
    return df_result

if __name__ == "__main__":
    # Test rápido
    pos = 'data/raw/posiciones.csv'
    instr = 'data/raw/instruments.csv'
    df = load_df_instruments(pos, instr)
    print(f"df_instruments cargado con {len(df)} registros.")
    print("Columnas actuales:", df.columns.tolist())
    print(df.head())
    
    # Guardar para inspección
    os.makedirs('data/processed', exist_ok=True)
    df.to_csv('data/processed/df_instruments.csv', index=False, sep=';')
