# Todo lo que habla con la base de datos (PostgreSQL).
import os
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row

# docker-compose.yml le pasa DATABASE_URL al script.
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://macdeals:macdeals@localhost:5432/macdeals"
)


def now():
    return datetime.now(timezone.utc)


def connect():
    # dict_row: cada fila es un diccionario, por ejemplo row["price_usd_cents"]
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    # Crea las tablas si no existen
    with open("schema.sql", encoding="utf-8") as f:
        conn.execute(f.read())
    conn.commit()
    return conn


def get_product_id(conn, p):
    # Busca la configuración. Si no existe, la crea.
    row = conn.execute(
        """SELECT id FROM products
           WHERE model = %s AND chip = %s AND screen_in = %s AND ram_gb = %s
             AND storage_gb = %s AND cpu_cores = %s AND gpu_cores = %s""",
        (p["model"], p["chip"], p["screen_in"], p["ram_gb"],
         p["storage_gb"], p["cpu_cores"], p["gpu_cores"]),
    ).fetchone()
    if row:
        return row["id"]

    row = conn.execute(
        """INSERT INTO products
             (model, chip, screen_in, ram_gb, storage_gb, cpu_cores, gpu_cores, release_year)
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
           RETURNING id""",
        (p["model"], p["chip"], p["screen_in"], p["ram_gb"],
         p["storage_gb"], p["cpu_cores"], p["gpu_cores"], p["release_year"]),
    ).fetchone()
    return row["id"]


def save_listing(conn, source, external_id, product, price_usd_cents,
                 seller, condition, url):
    # Guarda una oferta. Devuelve 'new', 'same' o 'price_changed'.
    product_id = get_product_id(conn, product)

    old = conn.execute(
        "SELECT id, price_usd_cents FROM listings WHERE source = %s AND external_id = %s",
        (source, external_id),
    ).fetchone()

    if old is None:
        # Nunca la habíamos visto: crearla y guardar su primer precio
        row = conn.execute(
            """INSERT INTO listings
                 (source, external_id, product_id, seller, condition, url,
                  price_usd_cents, first_seen_at, last_seen_at)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (source, external_id, product_id, seller, condition, url,
             price_usd_cents, now(), now()),
        ).fetchone()
        conn.execute(
            "INSERT INTO price_history (listing_id, price_usd_cents, seen_at) VALUES (%s, %s, %s)",
            (row["id"], price_usd_cents, now()),
        )
        status = "new"

    elif old["price_usd_cents"] == price_usd_cents:
        # Mismo precio: solo anotar que la seguimos viendo
        conn.execute(
            "UPDATE listings SET last_seen_at = %s, is_active = TRUE WHERE id = %s",
            (now(), old["id"]),
        )
        status = "same"

    else:
        # Cambió el precio: actualizarlo y guardar el nuevo en el historial
        conn.execute(
            """UPDATE listings
               SET price_usd_cents = %s, last_seen_at = %s, is_active = TRUE
               WHERE id = %s""",
            (price_usd_cents, now(), old["id"]),
        )
        conn.execute(
            "INSERT INTO price_history (listing_id, price_usd_cents, seen_at) VALUES (%s, %s, %s)",
            (old["id"], price_usd_cents, now()),
        )
        status = "price_changed"

    conn.commit()
    return status


def start_run(conn, source):
    row = conn.execute(
        "INSERT INTO runs (source, started_at) VALUES (%s, %s) RETURNING id",
        (source, now()),
    ).fetchone()
    conn.commit()
    return row["id"]


def finish_run(conn, run_id, status, listings_found, error):
    conn.execute(
        "UPDATE runs SET status = %s, listings_found = %s, error = %s WHERE id = %s",
        (status, listings_found, error, run_id),
    )
    conn.commit()
