-- Base de datos del buscador de Macs.
-- No la ejecutes a mano: `python db.py` la crea en mac_deals.db.

-- 1) QUÉ Mac es: una fila por configuración.
--    NOT NULL DEFAULT 0 en vez de NULL porque en SQLite dos NULL no
--    cuentan como iguales y el UNIQUE dejaría pasar duplicados.
CREATE TABLE IF NOT EXISTS products (
  id           INTEGER PRIMARY KEY,
  model        TEXT    NOT NULL,            -- 'MacBook Pro', 'MacBook Air', 'Mac mini'
  chip         TEXT    NOT NULL,            -- 'M1 Pro', 'M2 Max'...
  screen_in    INTEGER NOT NULL DEFAULT 0,  -- 14, 16... (0 = sin pantalla)
  ram_gb       INTEGER NOT NULL,
  storage_gb   INTEGER NOT NULL,
  cpu_cores    INTEGER NOT NULL DEFAULT 0,
  gpu_cores    INTEGER NOT NULL DEFAULT 0,
  release_year INTEGER,
  UNIQUE (model, chip, screen_in, ram_gb, storage_gb, cpu_cores, gpu_cores)
);

-- 2) QUIÉN la vende: una oferta en una tienda.
CREATE TABLE IF NOT EXISTS listings (
  id                       INTEGER PRIMARY KEY,
  source                   TEXT    NOT NULL,  -- 'refurbme' | 'backmarket'
  external_id              TEXT    NOT NULL,  -- id de la tienda: 'US.R.MK183-046.US.C.ebay'
  product_id               INTEGER NOT NULL REFERENCES products(id),
  seller                   TEXT,              -- 'eBay', 'Back Market'...
  condition                TEXT,              -- A / B / C
  url                      TEXT,
  price_usd_cents          INTEGER NOT NULL,  -- precio actual, en centavos
  first_seen_at            TEXT    NOT NULL,  -- tu "fecha de publicación"
  last_seen_at             TEXT    NOT NULL,
  is_active                INTEGER NOT NULL DEFAULT 1,
  notified_price_usd_cents INTEGER,           -- precio con el que ya te avisamos (NULL = nunca)
  UNIQUE (source, external_id)
);

-- 3) Historial: una fila solo cuando el precio CAMBIA.
CREATE TABLE IF NOT EXISTS price_history (
  id              INTEGER PRIMARY KEY,
  listing_id      INTEGER NOT NULL REFERENCES listings(id),
  price_usd_cents INTEGER NOT NULL,
  seen_at         TEXT    NOT NULL
);

-- 4) Mercado en Colombia: tu Excel, hoja "Precios por modelo".
CREATE TABLE IF NOT EXISTS market_refs (
  group_key      TEXT PRIMARY KEY,  -- 'MacBook Pro M1 Max 16"' o 'MacBook Pro M1 Max 16" 64GB'
  listings_count INTEGER,           -- nº de anuncios: pocos = configuración rara
  min_cop        INTEGER,
  p25_cop        INTEGER,
  median_cop     INTEGER,
  max_cop        INTEGER,
  my_sale_cop    INTEGER,           -- "Tu precio de venta": manda sobre el P25
  imported_at    TEXT NOT NULL
);

-- 5) TRM por día, para no consultarla 48 veces al día.
CREATE TABLE IF NOT EXISTS trm (
  date        TEXT PRIMARY KEY,     -- '2026-10-11'
  cop_per_usd REAL NOT NULL
);

-- 6) Cada corrida del script. Si una sale con 0 ofertas, algo se rompió.
CREATE TABLE IF NOT EXISTS runs (
  id             INTEGER PRIMARY KEY,
  source         TEXT NOT NULL,
  started_at     TEXT NOT NULL,
  status         TEXT,              -- 'ok' | 'blocked' | 'error'
  listings_found INTEGER,
  error          TEXT
);
