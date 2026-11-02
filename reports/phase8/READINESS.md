# Benchmark and deployment verification (2026-11-02)

## Benchmark

`benchmark_v2` freezes seven NASA/CDC development pages and four different NASA test pages. The test split has 16 ordinary answerable questions, four unanswerable questions, and two conflicting-document questions. The two altered documents are explicitly marked synthetic. Every answerable gold span is checked against its source snapshot when the dataset is rebuilt. The test has single-author labels and is not independently validated.

Rebuild: `uv run python -m rageval.dataset.benchmark_v2`

Run the matched retrieval experiment: `uv run python scripts/run_retrieval_v2.py`

The saved `retrieval_v2.json` measures document Recall@5, exact evidence-span Recall@5, cold index time, and warm retrieval latency across chunk sizes, sparse/dense/hybrid search, a second embedding model, and reranking. It excludes generation and verification latency. It is a local diagnostic with 18 answerable test cases, not a statistical ranking claim. The test documents stay in the retrieval corpus; their source URLs are absent from development labels.

### Baseline observations

The 128/256/512-word settings produced 128/59/31 chunks. This confirms that chunk size changes the indexed material. At 256 words, BM25, MiniLM dense, and hybrid obtained document Recall@5 of 0.8889, 1.0, and 1.0; exact evidence-span Recall@5 was 0.8333, 0.9444, and 1.0. At 512 words, BM25's evidence recall reached 1.0, while dense MiniLM's fell to 0.8333. Replacing MiniLM with MPNet raised 256-word dense evidence recall from 0.9444 to 1.0, with a much higher local warm retrieval p50 (about 51 ms versus about 7 ms). Reranking did not improve hybrid evidence recall on these cases (both 1.0) and raised p50 from about 9 ms to about 151 ms. These values depend on this small NASA-heavy slice and one sequential CPU run. The two conflict questions count as answerable retrieval cases; the four unanswerable questions are excluded from Recall@5.

## Cost and latency

The earlier NVIDIA NIM live matrix records 112,219 prompt tokens and 8,398 completion tokens across six 40-question configurations. Its dollar cost is **unknown**: no billed rate or invoice is available, and the HTTP generator falls back to word counts when a provider omits usage. Do not treat those counts as verified billed tokens. Aggregate metrics now report p50/p95/p99 for retrieval, generation, verification, and total time, plus an explicit cost status and pricing source. Re-run the live matrix with a provider usage record and verified billed rate before reporting USD per question.

The `service_probe.json` timings are for a local HTTP process using the heuristic evaluator. They do not measure cold model load, TLS, external network, or production concurrency.

## Deployment evidence and remaining external gates

The local authenticated probe passed health/readiness, denied an unauthenticated dataset read, accepted an authenticated read, and returned 20/20 successes at five concurrent live evaluations. Unit tests cover per-token rate limits and expired worker lease recovery. The runs-volume backup/restore round trip checks both run files and SQLite integrity. To reproduce: start a single API instance with `RAGEVAL_REQUIRE_AUTH=1`, non-empty public/admin tokens, and then run `RAGEVAL_PUBLIC_TOKEN=... uv run python scripts/probe_service.py`.

Local TLS **passed** on 2026-11-02: Caddy `caddy:2.8-alpine` with `deploy/Caddyfile.host` (internal certs for `localhost`) reverse-proxied the launch-agent API on `127.0.0.1:8000` via Colima `host.docker.internal`. Probe `https://localhost --insecure` is in `service_probe_tls.json` (health/ready 200, unauthenticated datasets 401, authenticated 200, 20/20 evaluate). A purchased public DNS name was **not** set. Remote-host ACME certificates were **not** checked.

Public-host decision: **do not** publish this process on the open internet. Rate limits are process-local, Compose is one API replica, the worker is SQLite, and there is no Redis/Celery or multi-tenant isolation. See `docs/PRODUCTION.md`.

Live v1 retrieval is saturated (document Recall@5 = 1.0 on all six live-matrix configs). Retriever ranking uses the `benchmark_v2` diagnostic in `retrieval_v2.json` (n_test=22, 18 answerable, single-author, NASA-heavy). That file is not a confirmatory ranking.

Cost remains **unknown USD**. Token counts exist; no billed rate or invoice was available.

Human rater B remains unfilled. LLM kappa 0.9423 is diagnostic. Independent slice n=30 on v1.4.0 meets the count threshold with disjoint gold documents; labels are still single-author.

For backup: stop API and worker, then run `uv run python scripts/backup_runs.py backup <runs-dir> <archive.tar.gz>`. Restore only into an empty directory with `uv run python scripts/backup_runs.py restore <empty-runs-dir> <archive.tar.gz>`, then restart services and check `/ready` and a saved run.
