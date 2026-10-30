# Production software notes

This is the **software** production surface for RAGeval 0.2.1. Official ablation tables remain blinded-mock run `20261028T183042Z_a97ad68f`. Shipping the API does not make the recorded n=24 table confirmatory.

## What this process does

- Serve the dashboard and OpenAPI (`rageval serve` / Docker `CMD`).
- Live claim audit: `POST /evaluate/answer` (default `method=heuristic`).
- External scorer: `POST /score` (same contract as `rageval score`).
- Process-local jobs: `POST /experiments` → 202, one job at a time.
- Catalog of datasets and committed snapshots.

## What this process does not do

- Redis/Celery multi-worker queues (one in-process job thread).
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
| `RAGEVAL_RATE_LIMIT_PER_MINUTE` | `60` | POST `/evaluate/*` and `/score` per client host. `0` disables |

Copy `.env.example` to a gitignored `.env` for CLI keys. `rageval serve` does not load `.env`. Docker Compose does not ship keys.

## Health

- `GET /health` — liveness (`status`, `service`, `version`, `busy`). Docker HEALTHCHECK uses this.
- `GET /ready` — 200 when `RAGEVAL_DATA_DIR` exists; 503 otherwise.

## Docker

```bash
docker build --platform linux/amd64 -t rageval:0.2.1 .
docker compose up --build
# Apple Silicon:
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker compose up --build
```

The image is CPU torch + hashed `requirements-lock-all.txt`. Hugging Face weights are not in the image. First `method=nli` call downloads DeBERTa unless the cache is mounted.

## Hardening already in the process

- Non-root uid 1000 in the image.
- CORS default is localhost, not `*`+credentials.
- Security headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`.
- `X-Request-ID` echoed (generated if missing).
- Live evaluate/score default heuristic so a public dashboard click does not pull DeBERTa.
- `.dockerignore` excludes `.env`, tests, and run artifacts.

Put a reverse proxy in front for TLS. This app does not terminate HTTPS.
