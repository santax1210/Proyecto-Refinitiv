"""
Script para verificar casos de FALTA ALLOCATION
"""
import pandas as pd

df = pd.read_csv('data/raw/allocations_currency.csv', sep=';', encoding='latin-1', on_bad_lines='skip')
df.columns = df.columns.str.strip()

print('Total registros:', len(df))

falta = df[df['Moneda:'].str.strip() == 'FALTA ALLOCATION']
print('Con FALTA ALLOCATION:', len(falta))

if len(falta) > 0:
    print('\nPrimeros 10:')
    print(falta[['ID', 'Nombre', 'Moneda:']].head(10))
