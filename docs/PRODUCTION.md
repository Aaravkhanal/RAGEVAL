# Production software notes

This is the **software** production surface for RAGeval 0.2.1. Official ablation tables remain blinded-mock run `20261028T183042Z_a97ad68f`. Shipping the API does not make the recorded n=24 table confirmatory.

## What this process does

- Serve the dashboard and OpenAPI (`rageval serve` / Docker `CMD`).
- Live claim audit: `POST /evaluate/answer` (default `method=heuristic`).
- External scorer: `POST /score` (same contract as `rageval score`).
- Durable jobs: `POST /experiments` → 202; a separate `rageval worker` claims one job at a time from SQLite in `RAGEVAL_RUNS_DIR`.
- Catalog of datasets and committed snapshots.

## What this process does not do

- Distributed scheduling across different run volumes. API and worker processes must share one persistent `RAGEVAL_RUNS_DIR`.
- Store provider API keys. Generators read env names only; HTTP jobs refuse `opt_in` YAML.
- PyPI publish (`twine upload` is maintainer-only).
- Independent human IAA or i.i.d. n≥30 confirmatory rankings.

## Environment

| Variable | Default | Role |
| --- | --- | --- |
| `RAGEVAL_RUNS_DIR` | `experiments/runs` | Job output root |
| `RAGEVAL_DATA_DIR` | `data` | Dataset root |
| `RAGEVAL_INCLUDE_SNAPSHOTS` | `1` | Include committed `reports/phase7/` tables in `GET /experiments` |
| `RAGEVAL_CORS_ORIGINS` | `http://127.0.0.1:8000,http://localhost:8000` | CORS allow list. `*` disables credentials |
| `RAGEVAL_ALLOWED_HOSTS` | `*` | Starlette trusted hosts |
| `RAGEVAL_RATE_LIMIT_PER_MINUTE` | `60` | POST `/evaluate/*` and `/score` per API token (or client host without a token). Job creation remains capped at 6/minute |
| `RAGEVAL_READ_RATE_LIMIT_PER_MINUTE` | `120` | Protected GET requests per token per minute |
| `RAGEVAL_REQUIRE_AUTH` | `0` (`1` in Docker Compose) | Require an API token for datasets, experiments, metrics, evaluate, and score |
| `RAGEVAL_PUBLIC_TOKEN` | unset | `X-RAGEVAL-API-TOKEN` for protected endpoints. Public mode fails closed with 503 if unset |
| `RAGEVAL_ADMIN_TOKEN` | unset | Required `X-RAGEVAL-ADMIN-TOKEN` for POST `/experiments`; jobs are disabled if unset |
| `RAGEVAL_ENABLE_HTTP_NLI` | `0` | Set to `1` only when the NLI model and CPU/memory capacity are provisioned |

Copy `.env.example` to a gitignored `.env` for CLI keys. `rageval serve` does not load `.env`. Docker Compose does not ship keys.

## Health

- `GET /health` — liveness (`status`, `service`, `version`, `busy`). Docker HEALTHCHECK uses this.
- `GET /ready` — 200 when the data directory exists and the run directory is writable; 503 otherwise.

## Docker

```bash
docker build --platform linux/amd64 -t rageval:0.2.1 .
docker compose up --build
# Apple Silicon:
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose up --build
```

The image is CPU torch + hashed `requirements-lock-all.txt`. Hugging Face weights are not in the image. First `method=nli` call downloads DeBERTa unless the cache is mounted. Compose starts an API and a worker sharing the named run volume. It publishes the API on localhost. Compose enables API authentication; set a long random `RAGEVAL_PUBLIC_TOKEN` and a separate `RAGEVAL_ADMIN_TOKEN`. The dashboard accepts the API token in a password field and keeps it in memory only. Keep TLS in front of remote access. Rate limits are process-local; use a shared gateway quota if multiple API replicas serve the same token.

TLS overlay (Caddy terminates HTTPS; this app does not):

```bash
# Local (Caddy internal/local certs for localhost)
RAGEVAL_DOMAIN=localhost RAGEVAL_PUBLIC_TOKEN="choose-a-long-random-api-token" RAGEVAL_ADMIN_TOKEN="choose-a-long-random-admin-token" \
  docker compose -f docker-compose.yml -f docker-compose.tls.yml up --build

# Public hostname (Caddy obtains a certificate; set CORS and hosts to the same name)
RAGEVAL_DOMAIN=eval.example.com \
RAGEVAL_CORS_ORIGINS=https://eval.example.com \
RAGEVAL_ALLOWED_HOSTS=eval.example.com \
RAGEVAL_PUBLIC_TOKEN="choose-a-long-random-api-token" \
RAGEVAL_ADMIN_TOKEN="choose-a-long-random-admin-token" \
  docker compose -f docker-compose.yml -f docker-compose.tls.yml up -d
```

The API still binds `127.0.0.1:8000` on the host. Caddy publishes 80/443 and reverse-proxies the `rageval` service on the compose network.
Direct `rageval serve --host 0.0.0.0` exits unless public auth is enabled and a public token is configured.

## Hardening already in the process

- Non-root uid 1000 in the image.
- CORS default is localhost, not `*`+credentials.
- Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`.
- `X-Request-ID` echoed (generated if missing).
- Live evaluate/score default heuristic. HTTP NLI is disabled by default so a request cannot trigger a model download.
- Evaluation request bodies are capped at 64 KiB; model inputs and context arrays have explicit limits.
- Job creation requires an admin token and has a separate rate limit. The worker retries a running job after its 30-second lease expires if it crashes.
- Protected data, results, metrics, and evaluation routes require an API token in public mode. Invalid token attempts are limited to 20/minute per client host; authenticated reads have a separate quota.
- `.dockerignore` excludes `.env`, tests, and run artifacts.

Put a reverse proxy in front for TLS. This app does not terminate HTTPS.
