# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Software versions do not replace the recorded ablation.** Official tables under `reports/` are from blinded-mock run [`20261028T183042Z_a97ad68f`](reports/20261028T183042Z_a97ad68f/FINDINGS.md) on `benchmark_v1` **1.0.0** (16 documents, 24 items). $n=24$ is underpowered. A companion v1.1.0 mock+NLI run is [`20261029T165024Z_657c8089`](reports/20261029T165024Z_657c8089/FINDINGS.md) (18 documents, 28 items); it does not replace the published table. This changelog is a packaging history, not a confirmatory RAG ranking.

## [Unreleased]

### Added

- Companion `benchmark_v1` **1.1.0** six-config mock + DeBERTa NLI ablation (`20261029T165024Z_657c8089`, 18 documents, 28 items). Tables: `reports/phase7/v1_1_matrix/`. Official published tables remain `20261028T183042Z_a97ad68f`. n=28 is still underpowered.

### Fixed

- `rageval benchmark` no longer raises `UnboundLocalError` on `BenchmarkReporter` after the suite finishes (local import in the findings branch shadowed the module import).

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

[0.2.1]: https://github.com/Aaravkhanal/RAGEVAL/releases/tag/v0.2.1
[0.2.0]: https://github.com/Aaravkhanal/RAGEVAL/releases/tag/v0.2.0
[0.2.0rc1]: https://github.com/Aaravkhanal/RAGEVAL/releases/tag/v0.2.0-rc1
