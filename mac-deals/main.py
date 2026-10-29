# Corre todo cada 30 minutos: TRM -> refurb.me -> filtro + Claude.
import time
from datetime import datetime

import db
import deals
import refurbme
import trm

EVERY_MINUTES = 30

while True:
    print("=== Corrida", datetime.now().strftime("%Y-%m-%d %H:%M"), "===")
    try:
        conn = db.connect()
        today_trm = trm.get_trm(conn)
        refurbme.scrape(conn)
        deals.check_deals(conn, today_trm)
        conn.close()
    except Exception as e:
        print("ERROR:", e)

    print("Esperando", EVERY_MINUTES, "minutos...\n")
    time.sleep(EVERY_MINUTES * 60)
