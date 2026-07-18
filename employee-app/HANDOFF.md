# Handoff Notes — Employee Directory (2-Tier App)

## Architecture
- **Tier 1 (App):** Python 3.11 / Flask, serves HTTP on `APP_PORT` (default 5000)
- **Tier 2 (Data):** MySQL 8.x

## Run locally (dev machine, no containers)
```
pip install -r requirements.txt
mysql -u root -p < schema.sql
cp .env.example .env   # fill in real values
python app.py
```

## Runtime dependencies
- Python 3.11+
- MySQL 8.x reachable from the app host on `DB_PORT` (3306)
- All dependencies pinned in `requirements.txt`

## Configuration (env vars — no secrets hardcoded)
| Var | Purpose | Default |
|---|---|---|
| APP_PORT | port Flask binds to | 5000 |
| DB_HOST | MySQL host | localhost |
| DB_PORT | MySQL port | 3306 |
| DB_USER | MySQL user | app_user |
| DB_PASSWORD | MySQL password | — (must be injected, not committed) |
| DB_NAME | database name | employee_directory |

`DB_PASSWORD` must never be committed — inject via secrets manager / vault / k8s secret at deploy time.

## Ports
- App listens on `0.0.0.0:${APP_PORT}` — needs to be exposed/load-balanced.
- DB listens on `3306` — should stay internal, not public-facing.

## Health/readiness (for LB or k8s probes)
- Liveness: `GET /health` → 200 `{"status":"ok"}` if app is up and DB is reachable, 503 otherwise
- Readiness: `GET /ready` → 200 once app has started

## Database bootstrap
- `schema.sql` must be run once against the target MySQL instance before first app start (creates DB + table + optional seed rows).

## Process start command (prod)
Don't use `python app.py` in prod — that's the Flask dev server. The container uses:
```
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```
(`gunicorn` is already in requirements.txt, already set as Dockerfile CMD)

## Logging
- App logs to stdout/stderr only (Flask/gunicorn default) — no file logging. This is intentional for `docker logs` / driver-based log collection.

## Docker specifics
- **Image**: `Dockerfile` builds on `python:3.11-slim`, installs deps, copies app + templates, runs gunicorn on port 5000. Build with:
  ```
  docker build -t employee-app:local .
  ```
- **Container healthcheck**: baked into the image (`HEALTHCHECK` hits `/health` every 30s). `docker ps` will show `healthy`/`unhealthy` status directly.
- **Local 2-tier stack**: `docker-compose.yml` wires app + MySQL together for local/dev use — not intended for prod as-is (uses plaintext env passwords, single DB instance, no TLS).
  ```
  docker compose up --build
  ```
- **DB init**: compose mounts `schema.sql` into MySQL's `docker-entrypoint-initdb.d/`, so schema + seed data load automatically on first container start (only runs when the `db_data` volume is empty).
- **Networking**: app and db share a bridge network (`appnet`); DB port 3306 is **not** published to the host — only reachable from the app container. App port 5000 is published to host.
- **Persistence**: MySQL data lives in a named volume (`db_data`) so data survives container restarts/recreates but not `docker compose down -v`.
- **.dockerignore** excludes `.env`, `.git`, `__pycache__`, and markdown files from the build context.

## What's intentionally NOT included (yours to build)
- Production-grade docker-compose (secrets, TLS, resource limits) — current compose file is dev/local only
- Image registry push / tagging strategy
- CI/CD pipeline to build & push images
- Reverse proxy / TLS termination (e.g. nginx/traefik in front of the app container)
- Monitoring, alerting, log aggregation
- Backup strategy for the MySQL volume
- Multi-replica / scaling setup (app is stateless, so running multiple `app` containers behind a proxy is safe — no session state)

## Known constraints to design around
- App is stateless (no local file writes, no in-memory session) — safe for multi-replica deploys.
- App will crash-loop if it can't reach MySQL at startup pool creation — build your readiness/startup probes accordingly, and make sure DB is up before app tier in your deploy order.
- No DB migrations tool wired in yet (just one schema.sql) — if you need Flyway/Alembic-style versioned migrations for your pipeline, flag it and I'll add one.
