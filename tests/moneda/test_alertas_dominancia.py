"""
Test unitario para la función calcular_alerta_dominancia.
Verifica los dos escenarios:
  DESAPARECE: la clase dominante antigua ya no está en la distribución nueva
  NUEVA:      la clase dominante nueva nunca estuvo en la distribución antigua
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pandas as pd
from src.logic.utils.alertas_dominancia import calcular_alerta_dominancia, COLS_META_MONEDA


def make_df_nuevas(instrument_id, clases_pcts):
    """Construye un df_nuevas en formato LONG para tests."""
    rows = [{'ID': instrument_id, 'class': clase, 'percentage': pct}
            for clase, pct in clases_pcts.items()]
    # Ensure columns always exist even when there are no rows
    return pd.DataFrame(rows, columns=['ID', 'class', 'percentage']) if not rows \
        else pd.DataFrame(rows)


def make_df_antiguas(instrument_id, clases_pcts):
    """Construye un df_antiguas en formato WIDE para tests."""
    row = {'ID': instrument_id}
    row.update(clases_pcts)
    return pd.DataFrame([row])


def run_test(nombre, row_data, df_nuevas, df_antiguas, esperado):
    row = pd.Series(row_data)
    resultado = calcular_alerta_dominancia(
        row, df_nuevas, df_antiguas,
        col_pct_antigua='pct_dominancia_antigua',
        col_pct_nueva='pct_dominancia_nuevo',
        col_clase_nuevas='class',
        col_pct_nuevas='percentage',
        cols_meta_antiguas=COLS_META_MONEDA,
    )
    ok = resultado == esperado
    estado = "[OK]" if ok else f"[FAIL] got={resultado}"
    print(f"  {estado} {nombre} -> esperado={esperado}")
    return resultado == esperado


def main():
    print("\n" + "=" * 70)
    print(" TEST: calcular_alerta_dominancia ".center(70, "="))
    print("=" * 70)

    okcount = 0
    total = 0

    # ── CASO 1: Sin alerta – misma moneda dominante, aparece en ambas ──────
    total += 1
    df_n = make_df_nuevas(1, {'CLP': 70.0, 'USD': 30.0})
    df_a = make_df_antiguas(1, {'CLP': 50.0, 'USD': 40.0, 'EUR': 10.0})
    row = {'ID': 1, 'pct_dominancia_antigua': 'CLP 50.00%', 'pct_dominancia_nuevo': 'CLP 70.00%'}
    okcount += run_test("Sin alerta – misma clase en ambas distribuciones", row, df_n, df_a, None)

    # ── CASO 2: DESAPARECE – USD era 50% en antiguas, no aparece en nuevas ─
    total += 1
    df_n = make_df_nuevas(2, {'CLP': 70.0, 'EUR': 30.0})
    df_a = make_df_antiguas(2, {'USD': 50.0, 'CLP': 40.0, 'EUR': 10.0})
    row = {'ID': 2, 'pct_dominancia_antigua': 'USD 50.00%', 'pct_dominancia_nuevo': 'CLP 70.00%'}
    okcount += run_test("DESAPARECE – USD 50% antiguo, no existe en nuevas", row, df_n, df_a, 'DESAPARECE')

    # -- CASO 3: ambos se combinan -- USD desaparece Y CLP es nueva
    # DESAPARECE tiene prioridad (se evalua primero en la funcion)
    total += 1
    df_n = make_df_nuevas(3, {'CLP': 95.0})
    df_a = make_df_antiguas(3, {'USD': 80.0, 'EUR': 20.0})
    row = {'ID': 3, 'pct_dominancia_antigua': 'USD 80.00%', 'pct_dominancia_nuevo': 'CLP 95.00%'}
    okcount += run_test("DESAPARECE (prioridad) -- USD se fue Y CLP es nueva", row, df_n, df_a, 'DESAPARECE')

    # -- CASO 3b: NUEVA puro -- clase antigua sigue en nuevas, nueva dominante nunca estuvo
    total += 1
    df_n = make_df_nuevas(31, {'CLP': 75.0, 'USD': 20.0, 'EUR': 5.0})
    df_a = make_df_antiguas(31, {'USD': 60.0, 'EUR': 40.0})
    row = {'ID': 31, 'pct_dominancia_antigua': 'USD 60.00%', 'pct_dominancia_nuevo': 'CLP 75.00%'}
    okcount += run_test("NUEVA puro -- USD sigue en nuevas pero CLP nunca estuvo en antiguas", row, df_n, df_a, 'NUEVA')

    # ── CASO 4: DESAPARECE aunque la nueva clase existía en antiguas ────────
    total += 1
    df_n = make_df_nuevas(4, {'EUR': 90.0, 'CLP': 10.0})
    df_a = make_df_antiguas(4, {'USD': 80.0, 'CLP': 15.0, 'EUR': 5.0})
    row = {'ID': 4, 'pct_dominancia_antigua': 'USD 80.00%', 'pct_dominancia_nuevo': 'EUR 90.00%'}
    okcount += run_test("DESAPARECE – USD antiguo desapareció (EUR sí estaba)", row, df_n, df_a, 'DESAPARECE')

    # ── CASO 5: Sin alerta – Sin datos en ambos campos ──────────────────────
    total += 1
    df_n = pd.DataFrame(columns=['ID', 'class', 'percentage'])  # sin filas
    df_a = pd.DataFrame(columns=['ID'])                          # sin filas
    row = {'ID': 5, 'pct_dominancia_antigua': 'Sin datos', 'pct_dominancia_nuevo': 'Sin datos'}
    okcount += run_test("Sin alerta - Sin datos en ambos campos", row, df_n, df_a, None)

    # ── CASO 6: Sin alerta – Balanceado en dominante antigua ────────────────
    total += 1
    df_n = make_df_nuevas(6, {'USD': 90.0})
    df_a = make_df_antiguas(6, {'USD': 50.0, 'CLP': 50.0})
    row = {'ID': 6, 'pct_dominancia_antigua': 'Balanceado 100.00%', 'pct_dominancia_nuevo': 'USD 90.00%'}
    okcount += run_test("Sin alerta – antigua es Balanceado (ignorado)", row, df_n, df_a, None)

    # ── CASO 7: Sin alerta – clase antigua existe en nuevas con 0% exacto ──
    # La función solo marca DESAPARECE si la clase antigua NO EXISTE en las nuevas
    # Si existe (porcentaje > 0) no hay alerta
    total += 1
    df_n = make_df_nuevas(7, {'USD': 10.0, 'CLP': 90.0})
    df_a = make_df_antiguas(7, {'USD': 80.0, 'CLP': 20.0})
    row = {'ID': 7, 'pct_dominancia_antigua': 'USD 80.00%', 'pct_dominancia_nuevo': 'CLP 90.00%'}
    okcount += run_test("Sin alerta – USD bajó pero sigue en distribución nueva", row, df_n, df_a, None)

    # ── RESUMEN ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"  Resultado: {okcount}/{total} tests pasados")
    if okcount == total:
        print("  ALL TESTS PASSED")
    else:
        print("  SOME TESTS FAILED -- check logic")
    print("=" * 70)
    return okcount == total


if __name__ == '__main__':
    ok = main()
    sys.exit(0 if ok else 1)
