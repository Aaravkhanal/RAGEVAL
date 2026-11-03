# Render free preview

`render.yaml` runs the API and the SQLite worker in one free web service. Render
creates separate random public and admin tokens. The image installs the fast
dependency lock, so the public service supports the dashboard, dataset/results
reads, heuristic claim evaluation, scoring, and `smoke` BM25 jobs. Dense
embeddings, rerankers, and NLI are intentionally unavailable on this 512 MB
instance. Run the full research experiments locally.

## Deploy

1. In Render, choose **New > Blueprint** and connect this GitHub repository.
2. Select `render.yaml` and confirm that `rageval-free` uses the **Free** plan.
3. After deployment, open its `onrender.com` URL and check `/ready`.
4. In Render's environment settings, reveal the generated public token for the
   dashboard's API token field. Keep the admin token private; it is required
   only for creating smoke jobs.

The service requires both tokens at startup. Never put them in the repository.
If Render assigns a different hostname, same-origin dashboard requests still
work; the default CORS setting does not grant other origins access.

## Free-tier limits

Render spins the service down after 15 minutes without incoming traffic. Its
local filesystem is ephemeral, so `jobs.sqlite3` and new run outputs disappear
on sleep, restart, and redeploy. A job interrupted by sleep is lost. Committed
datasets and report snapshots remain because they are built into the image.
Do not use this setup for durable experiment results or a production service.
The free tier also has limited CPU/memory, build minutes, and bandwidth.

For durable jobs, move to a host with persistent storage or replace the SQLite
queue and run-file store with persistent services. A free Render Postgres
database alone is insufficient: this app does not use Postgres, and Render's
free Postgres databases expire after 30 days.
