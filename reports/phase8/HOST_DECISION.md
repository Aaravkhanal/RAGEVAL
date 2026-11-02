# Public-host decision (2026-11-02)

**Decision:** do not put RAGeval on the public internet.

Reasons that remain true in 0.3.0:

- Rate limits are process-local (per API process, not a shared gateway).
- Compose starts one API replica.
- The worker is a SQLite lease loop in `RAGEVAL_RUNS_DIR`. There is no Redis or Celery.
- There is no multi-tenant isolation.

Supported mode: local or private host, `RAGEVAL_REQUIRE_AUTH=1`, distinct `RAGEVAL_PUBLIC_TOKEN` and `RAGEVAL_ADMIN_TOKEN`, TLS in a reverse proxy (Caddy). The app does not terminate HTTPS.

What was checked here:

- Distinct tokens in gitignored `.env` (and the launch-agent secrets file). Values are not printed or committed.
- Local TLS: Caddy internal certs for `localhost` (`deploy/Caddyfile.host`) in front of `127.0.0.1:8000`. Probe: `service_probe_tls.json`.
- NVIDIA key locally blanked in `.env`. If that key was ever pasted in chat, revoke it at NVIDIA; this repo cannot rotate the remote credential.

What was not checked:

- A purchased public domain and ACME certificate.
- A remote host outside this laptop.
- A linux/amd64 image build (Colima is aarch64; hashed all-lock is x86_64).
