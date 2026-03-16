"""
Test de Clasificación de Sector
=================================
Valida la lógica de clasificación de estados del pipeline de sector:

  - calcular_estado_sector: Estado_1 / Estado_2 / Estado_3 según combinaciones
  - detectar_cambio_sector: Sí / No / Sin datos
  - normalizar_estado_sector: limpieza y normalización de la columna Sectores:
  - ESTADOS_FALTA_ALLOCATION: set de valores que fuerzan Estado_3
  - calcular_nivel_variacion_sector: Baja / Alta según umbrales
  - Hellinger y variaciones: cobertura de casos borde

Este módulo es el equivalente para sector de test_mapeo_monedas.py en moneda.
"""

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.logic.sector.crear_df_final_sector import (
    ESTADOS_FALTA_ALLOCATION,
    VALORES_VACIOS,
    calcular_estado_sector,
    calcular_nivel_variacion_sector,
    calcular_distancia_hellinger_sector,
    detectar_cambio_sector,
    extraer_nombre_sector,
    normalizar_estado_sector,
    normalizar_nombre_sector,
)


def print_section(title):
    print('\n' + '=' * 70)
    print(f' {title.upper()} '.center(70, '='))
    print('=' * 70)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_calcular_estado_sector_todos_los_casos():
    """
    Verifica la tabla completa de transiciones de estado:
      nueva=Balanceado + antigua=Balanceado         → Estado_1
      nueva=Balanceado + antigua=Industry (dato)    → Estado_2
      nueva=Balanceado + Sectores: en FALTA set     → Estado_3
      nueva=Industry   + antigua=Balanceado          → Estado_2
      nueva=Industry   + antigua=misma Industry      → Estado_1
      nueva=Industry   + antigua=otra Industry       → Estado_3
    """
    print_section('TEST 1: Tabla de transiciones de estado')

    casos = [
        # (sector_nueva, sector_antigua, Sectores:, Cambio, estado_esperado)
        ('Balanceado', 'Balanceado',  'ASIGNADO',       'No',       'Estado_1'),
        ('Balanceado', 'Technology',  'ASIGNADO',       'Sí',       'Estado_2'),
        ('Balanceado', 'Technology',  'VACÍO',          'Sí',       'Estado_3'),
        ('Balanceado', 'Healthcare',  'FALTA ALLOCATION','Sí',      'Estado_3'),
        ('Balanceado', 'Utilities',   'VACIO',          'Sí',       'Estado_3'),
        ('Technology', 'Balanceado',  '',               'Sí',       'Estado_2'),
        ('Technology', 'Technology',  '',               'No',       'Estado_1'),
        ('Technology', 'Healthcare',  '',               'Sí',       'Estado_3'),
        ('Energy',     'Financials',  '',               'Sí',       'Estado_3'),
    ]

    errores = []
    for nueva, antigua, sectores_col, cambio, esperado in casos:
        row = pd.Series({
            'sector_nueva': nueva,
            'sector_antigua': antigua,
            'Sectores:': sectores_col,
            'Cambio': cambio,
        })
        resultado = calcular_estado_sector(row)
        icono = '[OK]' if resultado == esperado else '[X] '
        print(f'    {icono} nueva={nueva:12} antigua={antigua:12} Sectores:={sectores_col!r:20} → {resultado} (esperado: {esperado})')
        if resultado != esperado:
            errores.append((nueva, antigua, sectores_col, resultado, esperado))

    assert not errores, f'{len(errores)} casos de estado incorrecto: {errores}'
    print('\n[OK] test_calcular_estado_sector_todos_los_casos PASADO')
    return True


def test_detectar_cambio_sector():
    """Verifica la detección de cambio Sí / No / Sin datos."""
    print_section('TEST 2: Detección de cambios')

    casos = [
        # (sector_nueva, sector_antigua, cambio_esperado)
        ('Technology', 'Technology',  'No'),
        ('Technology', 'Healthcare',  'Sí'),
        ('Balanceado', 'Balanceado',  'No'),
        ('Balanceado', 'Technology',  'Sí'),
        ('',           'Technology',  'Sin datos'),
        ('Technology', '',            'Sin datos'),
        (np.nan,       'Technology',  'Sin datos'),
        ('Technology', np.nan,        'Sin datos'),
    ]

    errores = []
    for nueva, antigua, esperado in casos:
        row = pd.Series({'sector_nueva': nueva, 'sector_antigua': antigua})
        resultado = detectar_cambio_sector(row)
        icono = '[OK]' if resultado == esperado else '[X] '
        print(f'    {icono} nueva={str(nueva):12} antigua={str(antigua):12} → {resultado!r} (esperado: {esperado!r})')
        if resultado != esperado:
            errores.append((nueva, antigua, resultado, esperado))

    assert not errores, f'{len(errores)} casos de cambio incorrecto'
    print('\n[OK] test_detectar_cambio_sector PASADO')
    return True


def test_estados_falta_allocation():
    """Verifica que ESTADOS_FALTA_ALLOCATION contenga los valores requeridos."""
    print_section('TEST 3: Set ESTADOS_FALTA_ALLOCATION')

    requeridos = {'FALTA ALLOCATION', 'FALTA ALLOCATIONS', 'VACÍO', 'VACÃO', 'VACIO'}
    faltantes = requeridos - ESTADOS_FALTA_ALLOCATION
    assert not faltantes, f'Valores requeridos ausentes en ESTADOS_FALTA_ALLOCATION: {faltantes}'

    print(f'    [OK] ESTADOS_FALTA_ALLOCATION: {sorted(ESTADOS_FALTA_ALLOCATION)}')

    # Verificar normalización: variantes deben coincidir tras normalizar
    variantes_estado3 = ['FALTA ALLOCATION', 'FALTA ALLOCATIONS', 'VACÍO', 'VACÃO', 'VACIO',
                         'vacío', 'vacão', 'vacio', 'falta allocation']
    for v in variantes_estado3:
        norm = normalizar_estado_sector(v)
        assert norm in ESTADOS_FALTA_ALLOCATION, \
            f'{v!r} normalizado a {norm!r} no está en ESTADOS_FALTA_ALLOCATION'
        print(f'    [OK] {v!r:25} → {norm!r} ∈ ESTADOS_FALTA_ALLOCATION')

    print('\n[OK] test_estados_falta_allocation PASADO')
    return True


def test_normalizar_nombre_sector():
    """Verifica que normalizar_nombre_sector haga uppercase correctamente."""
    print_section('TEST 4: normalizar_nombre_sector')

    casos = [
        ('technology',   'TECHNOLOGY'),
        ('Healthcare',   'HEALTHCARE'),
        ('BALANCEADO',   'BALANCEADO'),
        ('  Energy  ',   'ENERGY'),
        (np.nan,         ''),
        ('',             ''),
        (None,           ''),
    ]

    for entrada, esperado in casos:
        resultado = normalizar_nombre_sector(entrada)
        icono = '[OK]' if resultado == esperado else '[X] '
        print(f'    {icono} {str(entrada)!r:15} → {resultado!r} (esperado: {esperado!r})')
        assert resultado == esperado, f'normalizar_nombre_sector({entrada!r}) = {resultado!r}, esperado {esperado!r}'

    print('\n[OK] test_normalizar_nombre_sector PASADO')
    return True


def test_extraer_nombre_sector():
    """Verifica extracción del nombre de sector desde strings de pct_dominancia."""
    print_section('TEST 5: extraer_nombre_sector')

    casos = [
        ('Technology 92.50%',   'Technology'),
        ('Healthcare 45.00%',   'Healthcare'),
        ('Balanceado 40.00%',   'Balanceado'),
        ('Sin datos',           'Sin datos'),
        ('',                    'Sin datos'),
        (np.nan,                'Sin datos'),
        ('Energy 100.00%',      'Energy'),
    ]

    for entrada, esperado in casos:
        resultado = extraer_nombre_sector(entrada)
        icono = '[OK]' if resultado == esperado else '[X] '
        print(f'    {icono} {str(entrada)!r:30} → {resultado!r} (esperado: {esperado!r})')
        assert resultado == esperado, f'extraer_nombre_sector({entrada!r}) = {resultado!r}'

    print('\n[OK] test_extraer_nombre_sector PASADO')
    return True


def test_calcular_nivel_variacion():
    """Verifica los umbrales de nivel de variación (Baja / Alta)."""
    print_section('TEST 6: calcular_nivel_variacion_sector')

    # Estado_1 (balanceados): umbral 0.30
    casos_bal_estado1 = [
        (0.00,  None, 'Estado_1',  'Baja'),
        (0.30,  None, 'Estado_1',  'Baja'),
        (0.301, None, 'Estado_1',  'Alta'),
        (1.00,  None, 'Estado_1',  'Alta'),
    ]
    # Estado_2/3 (balanceados y no balanceados): umbral 0.40
    casos_otros = [
        (0.40,  None, 'Estado_2',  'Baja'),
        (0.401, None, 'Estado_2',  'Alta'),
        (None,  0.40, 'Estado_2',  'Baja'),
        (None,  0.41, 'Estado_2',  'Alta'),
        (None,  None, 'Estado_1',  None),
    ]

    errores = []
    for vbal, vnob, estado, esperado in casos_bal_estado1 + casos_otros:
        row = pd.Series({
            'variacion_balanceados': vbal,
            'variacion_no_balanceados': vnob,
            'Estado': estado,
        })
        resultado = calcular_nivel_variacion_sector(row)
        icono = '[OK]' if resultado == esperado else '[X] '
        print(f'    {icono} vbal={str(vbal):5} vnob={str(vnob):5} estado={estado:8} → {str(resultado):6} (esperado: {str(esperado)})')
        if resultado != esperado:
            errores.append((vbal, vnob, estado, resultado, esperado))

    assert not errores, f'{len(errores)} niveles de variación incorrectos'
    print('\n[OK] test_calcular_nivel_variacion PASADO')
    return True


def test_hellinger_casos_borde():
    """Verifica la distancia de Hellinger para casos borde del sector."""
    print_section('TEST 7: Distancia de Hellinger (casos borde)')

    # Distribuciones idénticas → distancia = 0
    d1 = {'Technology': 60, 'Healthcare': 40}
    d2 = {'Technology': 60, 'Healthcare': 40}
    resultado = calcular_distancia_hellinger_sector(d1, d2)
    assert resultado == 0.0, f'Distribuciones idénticas deben dar 0, obtenido {resultado}'
    print(f'    [OK] Distribuciones idénticas → {resultado}')

    # Distribuciones completamente distintas (ortogonales) → distancia = 1
    d3 = {'Technology': 100, 'Healthcare': 0}
    d4 = {'Technology': 0, 'Healthcare': 100}
    resultado2 = calcular_distancia_hellinger_sector(d3, d4)
    assert resultado2 == 1.0, f'Distribuciones ortogonales deben dar 1.0, obtenido {resultado2}'
    print(f'    [OK] Distribuciones ortogonales → {resultado2}')

    # D1 vacía → distancia = 1
    resultado3 = calcular_distancia_hellinger_sector({}, {'X': 100})
    assert resultado3 is None, f'D1 vacía debe devolver None, obtenido {resultado3}'
    print(f'    [OK] D1 vacía → {resultado3}')

    # Suma cero en d1 → distancia = 1
    d5 = {'Technology': 0, 'Healthcare': 0}
    d6 = {'Technology': 60, 'Healthcare': 40}
    res4 = calcular_distancia_hellinger_sector(d5, d6)
    assert res4 == 1.0, f'Suma cero debe dar 1.0, obtenido {res4}'
    print(f'    [OK] Suma cero en d1 → {res4}')

    print('\n[OK] test_hellinger_casos_borde PASADO')
    return True


def main():
    ok1 = test_calcular_estado_sector_todos_los_casos()
    ok2 = test_detectar_cambio_sector()
    ok3 = test_estados_falta_allocation()
    ok4 = test_normalizar_nombre_sector()
    ok5 = test_extraer_nombre_sector()
    ok6 = test_calcular_nivel_variacion()
    ok7 = test_hellinger_casos_borde()
    return all([ok1, ok2, ok3, ok4, ok5, ok6, ok7])


if __name__ == '__main__':
    sys.exit(0 if main() else 1)
