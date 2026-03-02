"""
Script de diagnóstico para verificar por qué no aparecen casos de Estado_3
"""
import sys
import os
import pandas as pd

sys.path.insert(0, '.')

from src.extractors.load_instruments import load_df_instruments
from src.extractors.load_allocations import load_allocations_nuevas, load_allocations_antiguas
from src.logic.crear_df_final import crear_df_final

print("\n" + "="*70)
print(" DIAGNÓSTICO: Estado_3 en Export Balanceados ".center(70, "="))
print("="*70)

# Cargar datos
print("\n[1/4] Cargando datos...")
df_instr = load_df_instruments('data/raw/posiciones.csv', 'data/raw/instruments.csv')
df_nuevas = load_allocations_nuevas(df_instr, 'data/raw/allocations_nuevas.csv', umbral=0.9)
df_antiguas = load_allocations_antiguas(df_instr, 'data/raw/allocations_currency.csv')
df_final = crear_df_final(df_instr, df_nuevas, df_antiguas)

print(f"  ✓ df_instruments: {len(df_instr)} registros")
print(f"  ✓ df_final: {len(df_final)} registros")

# Verificar instrumentos con SubMoneda='unassigned' en df_instruments
print("\n[2/4] Verificando SubMoneda='unassigned' en df_instruments...")
unassigned = df_instr[df_instr['SubMoneda'].str.lower().str.strip() == 'unassigned']
print(f"  Total con SubMoneda='unassigned': {len(unassigned)} instrumentos")

if len(unassigned) > 0:
    print(f"  Primeros 5 IDs con unassigned: {unassigned['ID'].head().tolist()}")

# Verificar instrumentos balanceados
print("\n[3/4] Verificando instrumentos balanceados en df_final...")
balanceados = df_final[df_final['moneda_nueva'] == 'Balanceado']
print(f"  Total balanceados: {len(balanceados)} instrumentos")

# Cruzar: ¿Hay instrumentos balanceados CON SubMoneda='unassigned'?
print("\n[4/4] CRUCE: Balanceados + SubMoneda='unassigned'...")

# Merge df_instruments con df_final para ver SubMoneda de los balanceados
df_balanceados_submoneda = pd.merge(
    balanceados[['ID', 'Nombre', 'moneda_antigua', 'moneda_nueva']],
    df_instr[['ID', 'SubMoneda']],
    on='ID',
    how='left'
)

# Filtrar los que tienen unassigned
balanceados_unassigned = df_balanceados_submoneda[
    df_balanceados_submoneda['SubMoneda'].str.lower().str.strip() == 'unassigned'
]

print(f"  ✓ Instrumentos balanceados con SubMoneda='unassigned': {len(balanceados_unassigned)}")

if len(balanceados_unassigned) > 0:
    print("\n  Estos instrumentos DEBERÍAN tener Estado_3:")
    print(balanceados_unassigned[['ID', 'Nombre', 'SubMoneda', 'moneda_antigua', 'moneda_nueva']].head(10).to_string(index=False))
else:
    print("\n  ⚠️  NO HAY instrumentos balanceados con SubMoneda='unassigned'")
    print("  Por eso no aparecen casos de Estado_3")

# Mostrar distribución de SubMoneda en balanceados
print("\n[Extra] Distribución de SubMoneda en instrumentos balanceados:")
submoneda_counts = df_balanceados_submoneda['SubMoneda'].value_counts().head(10)
for val, count in submoneda_counts.items():
    print(f"  - {val}: {count} instrumentos")

print("\n" + "="*70)
