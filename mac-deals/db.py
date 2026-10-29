"""Acceso a la base de datos del buscador de Macs.

Ejecuta `python db.py` para crear mac_deals.db y ver la demo de save_listing.
"""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = HERE / "mac_deals.db"
SCHEMA_PATH = HERE / "schema.sql"


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path=DB_PATH):
    """Abre la base y crea las tablas si no existen."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row  # filas como dict: row["price_usd_cents"]
    # SQLite NO revisa los FOREIGN KEY a menos que se lo pidas en cada conexión.
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
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
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT DO NOTHING""",
        (*key, p.get("release_year")),
    )
    row = conn.execute(
        """SELECT id FROM products
           WHERE model = ? AND chip = ? AND screen_in = ? AND ram_gb = ?
             AND storage_gb = ? AND cpu_cores = ? AND gpu_cores = ?""",
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
    ts = now_iso()

    old = conn.execute(
        "SELECT price_usd_cents FROM listings WHERE source = ? AND external_id = ?",
        (source, external_id),
    ).fetchone()

    # Upsert: si (source, external_id) ya existe, actualiza en vez de fallar.
    # first_seen_at y notified_price_usd_cents NO se tocan al actualizar.
    conn.execute(
        """INSERT INTO listings
             (source, external_id, product_id, seller, condition, url,
              price_usd_cents, first_seen_at, last_seen_at, is_active)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
           ON CONFLICT (source, external_id) DO UPDATE SET
             product_id      = excluded.product_id,
             seller          = excluded.seller,
             condition       = excluded.condition,
             url             = excluded.url,
             price_usd_cents = excluded.price_usd_cents,
             last_seen_at    = excluded.last_seen_at,
             is_active       = 1""",
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
            "SELECT id FROM listings WHERE source = ? AND external_id = ?",
            (source, external_id),
        ).fetchone()["id"]
        conn.execute(
            "INSERT INTO price_history (listing_id, price_usd_cents, seen_at) VALUES (?, ?, ?)",
            (listing_id, price_usd_cents, ts),
        )

    conn.commit()
    return status


def start_run(conn, source):
    cur = conn.execute(
        "INSERT INTO runs (source, started_at) VALUES (?, ?)", (source, now_iso())
    )
    conn.commit()
    return cur.lastrowid


def finish_run(conn, run_id, status, listings_found=None, error=None):
    conn.execute(
        "UPDATE runs SET status = ?, listings_found = ?, error = ? WHERE id = ?",
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

    tables = [r["name"] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")]
    print("tablas:", ", ".join(tables))
