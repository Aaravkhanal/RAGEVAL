# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Software versions do not replace the recorded ablation.** Official tables under `reports/` are from blinded-mock run [`20261028T183042Z_a97ad68f`](reports/20261028T183042Z_a97ad68f/FINDINGS.md) on `benchmark_v1` **1.0.0** (16 documents, 24 items). $n=24$ is underpowered. Companion mock+NLI runs: v1.1.0 [`20261029T165024Z_657c8089`](reports/20261029T165024Z_657c8089/FINDINGS.md) (18/28) and v1.2.0 [`20261029T173408Z_de870a29`](reports/20261029T173408Z_de870a29/FINDINGS.md) (21/32). They do not replace the published table. This changelog is a packaging history, not a confirmatory RAG ranking.

## [Unreleased]

## [0.3.0] - 2026-11-02

Software release. Official ablation tables remain blinded-mock run `20261028T183042Z_a97ad68f`. This tag is not a confirmatory RAG ranking and is not a PyPI publish.

### Added

- Production-readiness follow-up: dashboard text escaping, admin-token protection and job rate limiting, bounded evaluation bodies and fields, SQLite-backed experiment queue with a separate worker and lease recovery, stricter readiness, wheel-bundled benchmark assets, split validation, and CI lint/build/clean-wheel checks. These changes do not change the recorded research results.
- Caddy TLS compose overlay (`docker-compose.tls.yml`, `deploy/Caddyfile`) plus a host-process overlay (`deploy/Caddyfile.host`) for Colima/Docker when Compose service DNS is missing. The app still does not terminate HTTPS.
- Local authenticated TLS probe against `https://localhost` with Caddy internal certs (`reports/phase8/service_probe_tls.json`). A purchased public domain was not set.
- Host token helper `scripts/generate_host_tokens.py` writes gitignored `.env` with distinct public/admin tokens and never prints values.
- `benchmark_v1` **1.4.0**: 36 documents, 47 items (39 dev / 8 frozen test). New public-domain docs/items `v1_041`–`v1_047` (NPS Zion/Acadia/Smoky/Olympic, CDC tetanus/pertussis, NASA Parker Solar Probe). Independent slice n=30 (`items_independent.json`). Count threshold only; labels remain single-author. HTTP `max_items` stays 32. Does not replace `a97ad68f`.
- `rageval iaa-label --set id=label` writes a human rater-B file from the blank template. It does not invent labels. Confirmatory IAA still needs an independent human.
- `benchmark_v1` **1.3.0**: 29 documents, 40 items (32 dev / 8 frozen test). New public-domain docs/items `v1_033`–`v1_040` (CDC measles/handwashing, NPS Grand Canyon/Yosemite/Everglades, NASA Voyager/Hubble/Webb). Companion split `independent` (`items_independent.json`, experiment `H_independent.yaml`). HTTP `max_items` stays 32; CLI can run the full set. Does not replace `a97ad68f`. Superseded on disk by 1.4.0.
- Production HTTP hardening: `GET /ready`, version+busy on `GET /health`, `POST /score`, live `method=heuristic|nli` (default heuristic), CORS from `RAGEVAL_CORS_ORIGINS`, trusted hosts, request-id, security headers, per-IP rate limit on evaluate/score. Docker `HEALTHCHECK`, `docker-compose.yml`, `.dockerignore`, `.env.example`, `docs/PRODUCTION.md`. Dashboard live audit no longer loads Google Fonts.
- NVIDIA NIM opt-in generator (`configs/opt_in/nvidia_nim.yaml`, `smoke_llm_nvidia.yaml`, `benchmark_llm_nvidia.yaml`, `benchmark_llm_nvidia_retrieve.yaml`). Keys from `NVIDIA_API_KEY` in the environment or a gitignored `.env` (`rageval.core.envfile`). Model used: `nvidia/nemotron-3.5-bolt-e4b`. Live smoke `20261030T052448Z_6df3afb9` on `smoke_v1` (n=8, heuristic). Sparse companion `20261030T052638Z_79a8b21d` (faith 0.7188, R@5 0.8438, MRR 0.7812, abstention 1.0). Dense/hybrid companion `20261030T055224Z_388c5503` (dense faith 0.7396 / MRR 0.7344; hybrid faith 0.6458 / MRR 0.75; R@5 0.8438 and abstention 1.0 on both). Does not replace `a97ad68f`.
- Disclosed LLM rater B (`data/gold/iaa/annotator_b_verifier_eval_v1.json`, annotator_id `rater_b_llm_grok`). Diagnostic kappa 0.9423 on n=24. Not confirmatory human IAA.
- OpenAI-like generator reads NVIDIA `reasoning_content` when `content` is empty. `GeneratorConfig.timeout_s` default 60.
- Companion `benchmark_v1` **1.1.0** six-config mock + DeBERTa NLI ablation (`20261029T165024Z_657c8089`, 18 documents, 28 items). Tables: `reports/phase7/v1_1_matrix/`. Official published tables remain `20261028T183042Z_a97ad68f`. n=28 is still underpowered.
- R3: `configs/opt_in/smoke_llm.yaml` plus CLI `--allow-opt-in` on `rageval experiment` and `rageval benchmark`. HTTP jobs still list only `configs/experiments/` and refuse `opt_in: true`. Live NVIDIA NIM smoke is recorded (`reports/opt_in_smoke_llm/STATUS.md`).
- R4: `rageval iaa` (Cohen's kappa, `rageval.iaa.v1`). Disclosed LLM rater B is diagnostic (kappa 0.9423); confirmatory IAA still needs a human. Files: `data/gold/iaa/`.
- R4: `benchmark_v1` **1.2.0** — 21 documents, 32 items (24 dev / 8 test). New USGS Yellowstone FAQs and NASA ISS excerpt; new ids `v1_029`–`v1_032` are **dev**. Test ids remain frozen. HTTP `max_items` cap is 32.
- R5: external RAG scorer — `rageval score --input answers.jsonl --output scores.jsonl` and `score_answer(question, answer, contexts)`. Question + chunks + answer in, `QueryEvaluationResult` out. Default verifier is heuristic. No retrieval, no generator, no gold in a prompt.
- Companion `benchmark_v1` **1.2.0** six-config mock + DeBERTa NLI ablation (`20261029T173408Z_de870a29`, 21 documents, 32 items). Tables: `reports/phase7/v1_2_matrix/`. Recall@5 0.8438 identical; Dense faith 0.401; Sparse 0.4219; Hybrid 0.4635; Reranked 0.4583; abstention 0.1667. n=32 is still underpowered. Official published tables remain `a97ad68f`.
- R7: `A_chunk` overlap-32 protocol on 1.2.0 (`20261029T173515Z_7e2b94a3`). Tables: `reports/phase7/A_chunk_overlap32/`. Three dense configs; faith 0.401 / R@5 0.8438 / MRR 0.7344 identical (matches the six-config dense rows). Does not replace `a97ad68f` or `v1_2_matrix`.
- `rageval compare --left --right` for diagnostic per-item deltas between two `per_example.jsonl` files.

### Changed

- Public-host decision: do not publish this process on the open internet. Rate limits are process-local, Compose runs one API replica, the worker is SQLite, and there is no Redis/Celery or multi-tenant isolation. Supported mode is a local or private host with TLS in front.
- Package version `0.2.1` → `0.3.0`. Git tag `v0.3.0`. PyPI upload is skipped (no token; CI does not publish).
- `rageval findings` describes the generator/verifier from recorded `pipelines` identity instead of always saying "blinded mock". NVIDIA companion findings stay live-LLM text.
- `rageval score` accepts run `predictions.jsonl` rows (`generated_answer` + `retrieved_chunks`).
- OpenAI-like HTTP generator retries 429/502/503/504 (and connect errors) up to `max_retries` (default 2).
- Significance tests are confirmatory only when n≥30 **and** items are treated as i.i.d. (`independent=True`). Default remains `independent=False` because recorded items share documents. The v1.2.0 Hybrid vs Dense faithfulness raw p=0.0435 is diagnostic; `is_significant` stays false.

### Fixed

- `rageval benchmark` no longer raises `UnboundLocalError` on `BenchmarkReporter` after the suite finishes (local import in the findings branch shadowed the module import).
- Findings text for A_chunk no longer prints `None` for missing hybrid configs. Mixed-support narrative does not claim claim-support moved when every config is tied.

## [0.2.1] - 2026-10-29

Software patch after `0.2.0` so the dashboard job UI is in a tagged release. Official tables remain run `20261028T183042Z_a97ad68f`.

### Added

- Dashboard experiment tab: config dropdown from `GET /experiment-configs`, `max_items`, Start → `POST /experiments`, poll `GET /experiments/{id}` every 2 s, results table on complete. Heavy configs stay hidden until “Allow heavy (NLI / full v1)”. No API keys in the form. Live `/evaluate/answer` stays sync.

## [0.2.0] - 2026-10-29

Installable software release after `0.2.0rc1`: HTTP jobs, opt-in LLM backends, hashed locks, a CPU Docker image, and proven Hugging Face CI.

### Added

- Process-local experiment job queue: `POST /experiments` returns 202; poll `GET /experiments/{id}`. Allowlisted YAML names under `configs/experiments/`. Default HTTP config is `smoke`. NLI / full v1 names require `allow_heavy=true`. One job at a time (HTTP 409 if busy).
- Opt-in generators `openai`, `ollama`, and `local_hf` (`configs/opt_in/`). API keys from `OPENAI_API_KEY` / `RAGEVAL_API_KEY` only. HTTP errors raise; there is no mock fallback and no silent NLI→heuristic fallback.
- Hashed lockfiles: `requirements-lock-fast.txt` (`[dev,api]`, universal) and `requirements-lock-all.txt` (manylinux x86_64, CPU `torch` + `faiss-cpu`). Regenerator: `bash scripts/compile_locks.sh`.
- Docker image: Python 3.12, hashed all-lock, `CMD ["rageval", "serve"]`. Build with `--platform linux/amd64`.
- Hugging Face nightly workflow with hub cache, 90-minute timeout, and no `continue-on-error`. First green GitHub run: [40891849818](https://github.com/Aaravkhanal/RAGEVAL/actions/runs/40891849818) (commit `94c9eeb`).
- This changelog. Local sdist/wheel check: `python -m build && twine check dist/*`. PyPI upload is a maintainer step (`twine upload dist/*`) and is not run by CI.

### Changed

- Package version `0.2.0rc1` → `0.2.0`. Git tag `v0.2.0`.
- Fast GitHub CI installs from `requirements-lock-fast.txt`.

### Fixed

- HTTP job status writes are atomic so a truncated `status.json` cannot 400 a poll.
- OpenAI-like generators no longer turn HTTP failures into an answer string.

## [0.2.0rc1] - 2026-10-28

Phase 10 release candidate (tag `v0.2.0-rc1`). Split extras so fast tests run without Hugging Face; MIT `LICENSE` and dataset license notes; smoke experiment YAML; quickstart and reproducibility docs; CI that skips `-m hf`.

[0.3.0]: https://github.com/Aaravkhanal/RAGEVAL/releases/tag/v0.3.0
[0.2.1]: https://github.com/Aaravkhanal/RAGEVAL/releases/tag/v0.2.1
[0.2.0]: https://github.com/Aaravkhanal/RAGEVAL/releases/tag/v0.2.0
[0.2.0rc1]: https://github.com/Aaravkhanal/RAGEVAL/releases/tag/v0.2.0-rc1
