# TRM del día desde datos.gov.co (gratis, sin llave).
import json
import urllib.request
from datetime import date

URL = "https://www.datos.gov.co/resource/32sa-8pi3.json?$order=vigenciadesde%20DESC&$limit=1"


def get_trm(conn):
    today = date.today()

    # Si ya la pedimos hoy, usar la guardada
    row = conn.execute("SELECT cop_per_usd FROM trm WHERE date = %s", (today,)).fetchone()
    if row:
        return float(row["cop_per_usd"])

    with urllib.request.urlopen(URL, timeout=30) as response:
        data = json.load(response)
    value = float(data[0]["valor"])

    conn.execute("INSERT INTO trm (date, cop_per_usd) VALUES (%s, %s)", (today, value))
    conn.commit()
    print("TRM de hoy:", value)
    return value
