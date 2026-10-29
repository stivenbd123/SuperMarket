-- Base de datos del buscador de Macs (PostgreSQL).
-- No la ejecutes a mano: `python db.py` crea las tablas si no existen.

-- 1) QUÉ Mac es: una fila por configuración.
--    NOT NULL DEFAULT 0 en vez de NULL porque en Postgres (igual que en SQLite)
--    dos NULL no cuentan como iguales y el UNIQUE dejaría pasar duplicados.
CREATE TABLE IF NOT EXISTS products (
  id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
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
  id                       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source                   TEXT    NOT NULL,  -- 'refurbme' | 'backmarket'
  external_id              TEXT    NOT NULL,  -- id de la tienda: 'US.R.MK183-046.US.C.ebay'
  product_id               BIGINT  NOT NULL REFERENCES products(id),
  seller                   TEXT,              -- 'eBay', 'Back Market'...
  condition                TEXT,              -- A / B / C
  url                      TEXT,
  price_usd_cents          INTEGER NOT NULL,  -- precio actual, en centavos
  first_seen_at            TIMESTAMPTZ NOT NULL,  -- tu "fecha de publicación"
  last_seen_at             TIMESTAMPTZ NOT NULL,
  is_active                BOOLEAN NOT NULL DEFAULT TRUE,
  notified_price_usd_cents INTEGER,           -- precio con el que ya te avisamos (NULL = nunca)
  UNIQUE (source, external_id)
);

-- 3) Historial: una fila solo cuando el precio CAMBIA.
CREATE TABLE IF NOT EXISTS price_history (
  id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  listing_id      BIGINT  NOT NULL REFERENCES listings(id),
  price_usd_cents INTEGER NOT NULL,
  seen_at         TIMESTAMPTZ NOT NULL
);

-- 4) Mercado en Colombia: tu Excel, hoja "Precios por modelo".
CREATE TABLE IF NOT EXISTS market_refs (
  group_key      TEXT PRIMARY KEY,  -- 'MacBook Pro M1 Max 16"' o 'MacBook Pro M1 Max 16" 64GB'
  listings_count INTEGER,           -- nº de anuncios: pocos = configuración rara
  min_cop        BIGINT,
  p25_cop        BIGINT,
  median_cop     BIGINT,
  max_cop        BIGINT,
  my_sale_cop    BIGINT,            -- "Tu precio de venta": manda sobre el P25
  imported_at    TIMESTAMPTZ NOT NULL
);

-- 5) TRM por día, para no consultarla 48 veces al día.
--    NUMERIC y no REAL: es exacto, sin errores de redondeo de punto flotante.
CREATE TABLE IF NOT EXISTS trm (
  date        DATE PRIMARY KEY,     -- '2026-10-11'
  cop_per_usd NUMERIC(10, 2) NOT NULL
);

-- 6) Cada corrida del script. Si una sale con 0 ofertas, algo se rompió.
CREATE TABLE IF NOT EXISTS runs (
  id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  source         TEXT NOT NULL,
  started_at     TIMESTAMPTZ NOT NULL,
  status         TEXT,              -- 'ok' | 'blocked' | 'error'
  listings_found INTEGER,
  error          TEXT
);
