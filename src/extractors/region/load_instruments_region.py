# Extractor de instrumentos para región
# Reutiliza load_instruments de moneda ya que la fuente de instrumentos es compartida
# Este módulo puede aplicar filtros específicos para región si se requiere en el futuro

from src.extractors.moneda.load_instruments import load_df_instruments


def load_instruments_region(pos_path='data/raw/posiciones.csv', instr_path='data/raw/instruments.csv'):
    """
    Carga el maestro de instrumentos para el pipeline de región.
    Actualmente reutiliza la misma lógica que moneda (misma fuente de datos).

    Parámetros:
        pos_path: Ruta al archivo de posiciones.
        instr_path: Ruta al archivo de instrumentos (maestro).

    Retorna: df_instruments
    """
    return load_df_instruments(pos_path, instr_path)

