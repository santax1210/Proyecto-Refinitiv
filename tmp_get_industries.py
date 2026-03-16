import pandas as pd

df = pd.read_csv(r'c:\Users\Santiago\Documents\allocations_validation\data\raw\sector\allocations_nuevas.csv', sep=';', encoding='latin-1', dtype=str)

if 'classif' in df.columns:
    df_industry = df[df['classif'].str.strip().str.lower() == 'industry']
    print(df_industry['class'].unique())
else:
    print('No classif column found')
