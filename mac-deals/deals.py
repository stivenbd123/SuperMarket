# Calcula el margen de cada Mac y le pide opinión a Claude sobre las que sirven.
import subprocess

TAX = 0.08625            # impuesto de venta de San Francisco (algunos códigos postales: 0.09875)
SHIPPING_USD = 100       # envío a Colombia
MIN_MARGIN_COP = 1_200_000


def landed_cost_cop(price_usd, trm):
    # Cuánto te cuesta la Mac puesta en Colombia
    return round((price_usd * (1 + TAX) + SHIPPING_USD) * trm)


def margin_cop(sale_cop, cost_cop):
    return sale_cop - cost_cop


def find_market_ref(conn, mac):
    # Primero con RAM: 'MacBook Pro M1 Max 16" 64GB'. Si no, sin RAM: 'MacBook Pro M1 Max 16"'
    name = mac["model"] + " " + mac["chip"]
    if mac["screen_in"] > 0:
        name = name + " " + str(mac["screen_in"]) + '"'

    for key in [name + " " + str(mac["ram_gb"]) + "GB", name]:
        row = conn.execute("SELECT * FROM market_refs WHERE group_key = %s", (key,)).fetchone()
        if row:
            return row
    return None


def ask_claude(text):
    prompt = (
        "Revendo Macs usadas de USA en Colombia. Estas pasaron mi filtro de margen. "
        "Ordénalas de mejor a peor oportunidad y di qué tan rara es cada configuración "
        "(pocos anuncios en Colombia = rara). Máximo 10 líneas, en español.\n\n" + text
    )
    try:
        result = subprocess.run(["claude", "-p", prompt],
                                capture_output=True, text=True, timeout=300)
        return result.stdout or result.stderr
    except FileNotFoundError:
        return "(no está instalado el comando claude)"


def check_deals(conn, trm):
    # Solo las que todavía no te avisamos con este precio
    # (IS DISTINCT FROM también cuenta NULL = nunca avisada)
    rows = conn.execute(
        """SELECT l.id, l.price_usd_cents, l.seller, l.condition, l.url,
                  p.model, p.chip, p.screen_in, p.ram_gb, p.storage_gb
           FROM listings l
           JOIN products p ON p.id = l.product_id
           WHERE l.is_active
             AND l.notified_price_usd_cents IS DISTINCT FROM l.price_usd_cents"""
    ).fetchall()

    good = []
    for mac in rows:
        ref = find_market_ref(conn, mac)
        if ref is None:
            continue  # no está en el Excel

        sale = ref["my_sale_cop"] or ref["p25_cop"]  # tu precio manda sobre el P25
        if not sale:
            continue

        price_usd = mac["price_usd_cents"] / 100
        cost = landed_cost_cop(price_usd, trm)
        margin = margin_cop(sale, cost)
        if margin >= MIN_MARGIN_COP:
            good.append((mac, ref, price_usd, cost, sale, margin))

    if not good:
        print("Nada nuevo que pase el filtro.")
        return

    lines = []
    for mac, ref, price_usd, cost, sale, margin in good:
        lines.append(
            f'{mac["model"]} {mac["chip"]} {mac["screen_in"]}" {mac["ram_gb"]}GB/{mac["storage_gb"]}GB '
            f'grado {mac["condition"]} ({mac["seller"]}) | USD {price_usd:,.0f} | '
            f'costo ${cost:,} | venta ${sale:,} | margen ${margin:,} | '
            f'{ref["listings_count"]} anuncios en Colombia | {mac["url"]}'
        )
    text = "\n".join(lines)

    print("=== OPORTUNIDADES ===")
    print(text)
    print("=== CLAUDE ===")
    print(ask_claude(text))

    # Marcar como avisadas con este precio para no repetirlas
    for mac, ref, price_usd, cost, sale, margin in good:
        conn.execute(
            "UPDATE listings SET notified_price_usd_cents = price_usd_cents WHERE id = %s",
            (mac["id"],),
        )
    conn.commit()
