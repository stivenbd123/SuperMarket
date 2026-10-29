"""Paso 2: importar la hoja "Precios por modelo" a market_refs.

Esqueleto: completa los TODO. Listo cuando:
  SELECT COUNT(*) FROM market_refs                -> 131
  my_sale_cop de 'MacBook Pro M1 Pro 16"'         -> 3900000
"""
from openpyxl import load_workbook

from db import connect, now_iso

EXCEL_PATH = "Macs_Marketplace_Colombia_oct2026.xlsx"
SHEET = "Precios por modelo"


def to_int(value):
    """Celda -> entero en pesos, o None si está vacía."""
    # TODO: si value es None o "", devuelve None.
    # TODO: si no, devuelve int(round(float(value))).
    raise NotImplementedError


def main():
    wb = load_workbook(EXCEL_PATH, data_only=True)  # data_only: el valor, no la fórmula
    ws = wb[SHEET]
    conn = connect()
    imported_at = now_iso()
    count = 0

    # min_row=2 salta la fila de encabezados. Mira el Excel: ¿los datos empiezan en la 2?
    for row in ws.iter_rows(min_row=2, values_only=True):
        group, n_listings, min_cop, p25, median, max_cop, my_sale = row[:7]
        if not group:
            continue  # filas vacías al final de la hoja

        # TODO: INSERT INTO market_refs (...) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        #       ON CONFLICT (group_key) DO UPDATE SET ... = excluded.... (todas las columnas)
        #       Usa to_int() en cada número y group.strip() en el nombre.
        count += 1

    conn.commit()
    print(f"{count} filas importadas")


if __name__ == "__main__":
    main()
