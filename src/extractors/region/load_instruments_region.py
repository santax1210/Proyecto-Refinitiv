# Extractor de instrumentos para región
# Reutiliza load_instruments de moneda ya que la fuente de instrumentos es compartida
# Este módulo puede aplicar filtros específicos para región si se requiere en el futuro

from src.extractors.moneda.load_instruments import load_instruments


def load_instruments_region():
    """
    Carga el maestro de instrumentos para el pipeline de región.
    Actualmente reutiliza la misma lógica que moneda (misma fuente de datos).
    Retorna: df_instruments
    """
    return load_instruments()
