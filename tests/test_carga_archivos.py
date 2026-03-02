import pandas as pd
import os

def print_section(title):
    print("\n" + "="*60)
    print(f" {title.upper()} ".center(60, "="))
    print("="*60)

def test_carga_archivos():
    # Rutas de los archivos
    files = {
        "Maestro Instrumentos": "data/raw/instruments.csv",
        "Posiciones": "data/raw/posiciones.csv",
        "Nuevas Allocations": "data/raw/allocations_nuevas.csv",
        "Antiguas Allocations": "data/raw/allocations_currency.csv"
    }

    print_section("Validación de Carga de Archivos")

    for name, path in files.items():
        print(f"\n[+] Analizando: {name}")
        print(f"    Ruta: {path}")
        
        if not os.path.exists(path):
            print(f"    [!] ERROR: El archivo no existe.")
            continue
            
        try:
            # Determinamos el delimitador (suponemos ; o ,)
            # Para este proyecto la mayoría son ;
            sep = ';' if "nuevas" not in path.lower() else ';'
            
            # Carga rápida para validación
            df = pd.read_csv(path, sep=sep, encoding='latin-1', nrows=5, on_bad_lines='skip')
            
            print(f"    [OK] Archivo cargado correctamente.")
            print(f"    [i] Columnas detectadas ({len(df.columns)}):")
            for col in df.columns.tolist():
                print(f"        - {col}")
            
            print(f"    [i] Muestra de datos (primeras 2 filas):")
            print(df.head(2).to_string(index=False))
            
        except Exception as e:
            print(f"    [!] ERROR al cargar: {str(e)}")

    print_section("Resumen Final de Carga")
    print("Verificación completada. Asegúrese de que los nombres de las columnas")
    print("coincidan con los requerimientos del pipeline.")

if __name__ == "__main__":
    test_carga_archivos()
