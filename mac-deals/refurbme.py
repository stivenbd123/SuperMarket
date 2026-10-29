# Lee las ofertas de refurb.me con Selenium y las guarda en la base.
import time

from selenium import webdriver

import db

BASE_URL = "https://www.refurb.me/refurbished/"

# (modelo, pulgadas, página). Mac mini = 0 pulgadas.
# Sin "?" en la URL: el robots.txt de refurb.me no lo permite.
PAGES = [
    ("MacBook Pro", 13, "macbook/macbook-pro/13-inch/m1"),
    ("MacBook Pro", 13, "macbook/macbook-pro/13-inch/m2"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m1-pro"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m1-max"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m2-pro"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m2-max"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m3"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m3-pro"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m3-max"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m4"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m4-pro"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m4-max"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m5"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m5-pro"),
    ("MacBook Pro", 14, "macbook/macbook-pro/14-inch/m5-max"),
    ("MacBook Pro", 16, "macbook/macbook-pro/16-inch/m1-pro"),
    ("MacBook Pro", 16, "macbook/macbook-pro/16-inch/m1-max"),
    ("MacBook Pro", 16, "macbook/macbook-pro/16-inch/m2-pro"),
    ("MacBook Pro", 16, "macbook/macbook-pro/16-inch/m2-max"),
    ("MacBook Pro", 16, "macbook/macbook-pro/16-inch/m3-pro"),
    ("MacBook Pro", 16, "macbook/macbook-pro/16-inch/m3-max"),
    ("MacBook Pro", 16, "macbook/macbook-pro/16-inch/m4-pro"),
    ("MacBook Pro", 16, "macbook/macbook-pro/16-inch/m4-max"),
    ("MacBook Pro", 16, "macbook/macbook-pro/16-inch/m5-pro"),
    ("MacBook Pro", 16, "macbook/macbook-pro/16-inch/m5-max"),
    ("MacBook Air", 13, "macbook/macbook-air/13-inch/m1"),
    ("MacBook Air", 13, "macbook/macbook-air/13.6-inch/m2"),
    ("MacBook Air", 13, "macbook/macbook-air/13.6-inch/m3"),
    ("MacBook Air", 13, "macbook/macbook-air/13.6-inch/m4"),
    ("MacBook Air", 13, "macbook/macbook-air/13.6-inch/m5"),
    ("MacBook Air", 15, "macbook/macbook-air/15-inch/m2"),
    ("MacBook Air", 15, "macbook/macbook-air/15-inch/m3"),
    ("MacBook Air", 15, "macbook/macbook-air/15-inch/m4"),
    ("MacBook Air", 15, "macbook/macbook-air/15-inch/m5"),
    ("Mac mini", 0, "mac-mini/2020-release"),
    ("Mac mini", 0, "mac-mini/2023-release"),
    ("Mac mini", 0, "mac-mini/2024-release"),
    ("Mac mini", 0, "mac-mini/2026-release"),
]


def open_browser():
    # Chromium sin ventana, dentro de Docker
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.binary_location = "/usr/bin/chromium"
    service = webdriver.ChromeService("/usr/bin/chromedriver")
    return webdriver.Chrome(options=options, service=service)


def to_gb(value):
    # "16 GB" -> 16, "1 TB" -> 1024, 512 -> 512
    text = str(value).upper()
    number = int("".join(c for c in text if c.isdigit()) or 0)
    if "TB" in text:
        number = number * 1024
    return number


def to_int(value):
    if value is None:
        return 0
    return int(value)


def find_offers(data):
    # Busca dentro del grupo todo lo que parezca una oferta (tiene precio y tienda).
    # Así no importa si vienen como group["A"] o group["offers"]["A"].
    offers = []
    if isinstance(data, dict):
        if "price" in data and "merchantName" in data:
            offers.append(data)
        else:
            for value in data.values():
                offers = offers + find_offers(value)
    elif isinstance(data, list):
        for value in data:
            offers = offers + find_offers(value)
    return offers


def save_group(conn, model, screen_in, group, page_url):
    specs = group["best"]["product"]
    product = {
        "model": model,
        "chip": str(specs["cpuCollection"]).replace("Apple ", "").strip(),
        "screen_in": screen_in,
        "ram_gb": to_gb(specs["memorySize"]),
        "storage_gb": to_gb(specs["storageSize"]),
        "cpu_cores": to_int(specs.get("cpuCoreCount")),
        "gpu_cores": to_int(specs.get("graphicsCoreCount")),
        "release_year": specs.get("releaseYear"),
    }

    # Puede que "best" también salga como oferta: lo evitamos con los ids ya vistos
    seen_ids = []
    statuses = []
    for offer in find_offers(group):
        if offer["id"] in seen_ids:
            continue
        seen_ids.append(offer["id"])

        price_cents = round(float(offer["price"]) * 100)  # 745 dólares -> 74500 centavos
        status = db.save_listing(
            conn, "refurbme", str(offer["id"]), product, price_cents,
            offer.get("merchantName"), offer.get("condition"),
            offer.get("url") or page_url,
        )
        statuses.append(status)
    return statuses


def scrape(conn):
    run_id = db.start_run(conn, "refurbme")
    run_started = db.now()
    browser = open_browser()
    total = 0
    counts = {"new": 0, "same": 0, "price_changed": 0}

    try:
        for model, screen_in, path in PAGES:
            url = BASE_URL + path
            browser.get(url)
            time.sleep(3)  # esperar a que cargue

            # Reto de Cloudflare: parar. Nunca intentar saltarlo.
            if "Just a moment" in browser.title or "Un momento" in browser.title:
                print("BLOQUEADO por Cloudflare en", url)
                db.finish_run(conn, run_id, "blocked", total, "Cloudflare en " + url)
                return

            result = browser.execute_script(
                "return JSON.parse(JSON.stringify(window.__NUXT__.state.result))"
            )
            groups = result["data"]

            if result["pagination"]["haveNext"]:
                print("OJO: más de 12 grupos en", path, "- falta el respaldo por SKU")

            for group in groups:
                for status in save_group(conn, model, screen_in, group, url):
                    counts[status] += 1
                    total += 1

            print(path, "->", len(groups), "grupos")
            time.sleep(1.5)  # no saturar la página

        # Las que no aparecieron en esta corrida ya no están a la venta
        conn.execute(
            "UPDATE listings SET is_active = FALSE WHERE source = 'refurbme' AND last_seen_at < %s",
            (run_started,),
        )
        conn.commit()
        db.finish_run(conn, run_id, "ok", total, None)
        print("refurb.me:", total, "ofertas", counts)

    except Exception as e:
        conn.rollback()
        db.finish_run(conn, run_id, "error", total, str(e))
        print("ERROR en refurb.me:", e)

    finally:
        browser.quit()
