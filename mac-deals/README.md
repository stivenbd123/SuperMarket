# mac-deals

Cada 30 minutos revisa refurb.me, calcula cuánto cuesta cada Mac puesta en Colombia,
la compara con tu Excel y te muestra las que dejan $1.200.000 COP o más.

| Archivo | Qué hace |
|---|---|
| `main.py` | Corre todo cada 30 min: TRM → refurb.me → filtro + Claude |
| `refurbme.py` | Abre las páginas con Selenium y guarda las ofertas |
| `deals.py` | Fórmula de costo y margen, filtro, y pregunta a Claude |
| `trm.py` | TRM del día (datos.gov.co) |
| `import_excel.py` | Pasa tu Excel a la tabla `market_refs` (se corre a mano) |
| `db.py` | Todo lo que habla con Postgres |
| `schema.sql` | Las tablas |

## Arrancar en tu Mac

1. Docker: `brew install --cask docker` y abre Docker Desktop una vez.
2. Pon `Macs_Marketplace_Colombia_oct2026.xlsx` en esta carpeta.
3. Token de Claude: corre `claude setup-token`, copia `.env.example` como `.env` y pega el token.
4. Arrancar todo:
   ```
   docker compose up -d --build
   docker compose run --rm app python import_excel.py
   docker compose logs -f app
   ```

## Ver la base

DBeaver o la extensión "PostgreSQL" de VS Code: `localhost:5432`,
usuario `macdeals`, clave `macdeals`, base `macdeals`.

## En la nube

Igual que en la Mac, en cualquier servidor con Docker (un VPS de ~USD 5/mes):
`git clone`, copiar el Excel y el `.env`, y `docker compose up -d --build`.

Ojo: Cloudflare suele bloquear IPs de servidores y navegadores sin ventana.
Mira los logs de la primera corrida. Si dice `BLOQUEADO`, en ese servidor
no sirve; no intentes saltarte el bloqueo.

## Pendiente

- Las páginas con más de 12 grupos (salen con "OJO" en el log) necesitan el respaldo por SKU.
- La forma exacta del JSON de refurb.me no está verificada: si `save_group` falla,
  revisa la primera corrida y ajusta los nombres de los campos.
- Back Market.
