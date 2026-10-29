"""Acceso a la base de datos del buscador de Macs (PostgreSQL).

Antes: `docker compose up -d` para arrancar Postgres.
Ejecuta `python db.py` para crear las tablas y ver la demo de save_listing.
"""
import os
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

HERE = Path(__file__).resolve().parent
SCHEMA_PATH = HERE / "schema.sql"
# Igual a lo que dice docker-compose.yml. Para otra base: export DATABASE_URL=...
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://macdeals:macdeals@localhost:5432/macdeals"
)


def now_utc():
    return datetime.now(timezone.utc)


def connect(url=DATABASE_URL):
    """Abre la base y crea las tablas si no existen."""
    conn = psycopg.connect(url, row_factory=dict_row)  # filas como dict: row["price_usd_cents"]
    conn.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def get_or_create_product(conn, p):
    """Devuelve el id del producto; lo crea si es la primera vez que lo vemos.

    p es un dict con model, chip, ram_gb, storage_gb y opcionalmente
    screen_in, cpu_cores, gpu_cores, release_year.
    """
    key = (
        p["model"], p["chip"], p.get("screen_in") or 0,
        p["ram_gb"], p["storage_gb"],
        p.get("cpu_cores") or 0, p.get("gpu_cores") or 0,
    )
    # ON CONFLICT DO NOTHING: si ya existe esa configuración (el UNIQUE), no hace nada.
    conn.execute(
        """INSERT INTO products
             (model, chip, screen_in, ram_gb, storage_gb, cpu_cores, gpu_cores, release_year)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT DO NOTHING""",
        (*key, p.get("release_year")),
    )
    row = conn.execute(
        """SELECT id FROM products
           WHERE model = %s AND chip = %s AND screen_in = %s AND ram_gb = %s
             AND storage_gb = %s AND cpu_cores = %s AND gpu_cores = %s""",
        key,
    ).fetchone()
    return row["id"]


def save_listing(conn, source, external_id, product, price_usd_cents,
                 seller=None, condition=None, url=None):
    """Guarda una oferta y dice qué pasó con ella.

    Devuelve:
      'new'           -> nunca la habíamos visto
      'same'          -> ya existía con el mismo precio
      'price_changed' -> ya existía pero el precio cambió
    """
    product_id = get_or_create_product(conn, product)
    ts = now_utc()

    old = conn.execute(
        "SELECT price_usd_cents FROM listings WHERE source = %s AND external_id = %s",
        (source, external_id),
    ).fetchone()

    # Upsert: si (source, external_id) ya existe, actualiza en vez de fallar.
    # first_seen_at y notified_price_usd_cents NO se tocan al actualizar.
    conn.execute(
        """INSERT INTO listings
             (source, external_id, product_id, seller, condition, url,
              price_usd_cents, first_seen_at, last_seen_at, is_active)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
           ON CONFLICT (source, external_id) DO UPDATE SET
             product_id      = excluded.product_id,
             seller          = excluded.seller,
             condition       = excluded.condition,
             url             = excluded.url,
             price_usd_cents = excluded.price_usd_cents,
             last_seen_at    = excluded.last_seen_at,
             is_active       = TRUE""",
        (source, external_id, product_id, seller, condition, url,
         price_usd_cents, ts, ts),
    )

    if old is None:
        status = "new"
    elif old["price_usd_cents"] == price_usd_cents:
        status = "same"
    else:
        status = "price_changed"

    # El historial solo crece cuando hay un precio nuevo.
    if status != "same":
        listing_id = conn.execute(
            "SELECT id FROM listings WHERE source = %s AND external_id = %s",
            (source, external_id),
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO price_history (listing_id, price_usd_cents, seen_at) VALUES (%s, %s, %s)",
            (listing_id, price_usd_cents, ts),
        )

    conn.commit()
    return status


def start_run(conn, source):
    run_id = conn.execute(
        "INSERT INTO runs (source, started_at) VALUES (%s, %s) RETURNING id",
        (source, now_utc()),
    ).fetchone()["id"]
    conn.commit()
    return run_id


def finish_run(conn, run_id, status, listings_found=None, error=None):
    conn.execute(
        "UPDATE runs SET status = %s, listings_found = %s, error = %s WHERE id = %s",
        (status, listings_found, error, run_id),
    )
    conn.commit()


if __name__ == "__main__":
    conn = connect()
    demo_mac = {
        "model": "MacBook Pro", "chip": "M1 Pro", "screen_in": 16,
        "ram_gb": 16, "storage_gb": 512, "cpu_cores": 10, "gpu_cores": 16,
        "release_year": 2021,
    }
    ext = "DEMO.MK183-046"
    print(save_listing(conn, "demo", ext, demo_mac, 74500, "eBay", "A"))  # new
    print(save_listing(conn, "demo", ext, demo_mac, 74500, "eBay", "A"))  # same
    print(save_listing(conn, "demo", ext, demo_mac, 71900, "eBay", "A"))  # price_changed

    # Borrar la demo para no ensuciar la base real (el producto se queda; no estorba).
    conn.execute(
        "DELETE FROM price_history WHERE listing_id IN "
        "(SELECT id FROM listings WHERE source = 'demo')"
    )
    conn.execute("DELETE FROM listings WHERE source = 'demo'")
    conn.commit()

    tables = [r["table_name"] for r in conn.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' ORDER BY table_name")]
    print("tablas:", ", ".join(tables))
