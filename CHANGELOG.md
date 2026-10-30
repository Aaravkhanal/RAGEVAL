# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

**Software versions do not replace the recorded ablation.** Official tables under `reports/` are from blinded-mock run [`20261028T183042Z_a97ad68f`](reports/20261028T183042Z_a97ad68f/FINDINGS.md) on `benchmark_v1` **1.0.0** (16 documents, 24 items). $n=24$ is underpowered. Companion mock+NLI runs: v1.1.0 [`20261029T165024Z_657c8089`](reports/20261029T165024Z_657c8089/FINDINGS.md) (18/28) and v1.2.0 [`20261029T173408Z_de870a29`](reports/20261029T173408Z_de870a29/FINDINGS.md) (21/32). They do not replace the published table. This changelog is a packaging history, not a confirmatory RAG ranking.

## [Unreleased]

### Added

- NVIDIA NIM opt-in generator (`configs/opt_in/nvidia_nim.yaml`, `smoke_llm_nvidia.yaml`, `benchmark_llm_nvidia.yaml`). Keys from `NVIDIA_API_KEY` in the environment or a gitignored `.env` (`rageval.core.envfile`). Model used: `nvidia/nemotron-3.5-bolt-e4b`. Live smoke `20261030T052448Z_6df3afb9` on `smoke_v1` (n=8, heuristic). Live companion `20261030T052638Z_79a8b21d` on `benchmark_v1` 1.2.0 (n=32, DeBERTa NLI): faith 0.7188, R@5 0.8438, MRR 0.7812, abstention 1.0. Does not replace `a97ad68f`.
- Disclosed LLM rater B (`data/gold/iaa/annotator_b_verifier_eval_v1.json`, annotator_id `rater_b_llm_grok`). Diagnostic kappa 0.9423 on n=24. Not confirmatory human IAA.
- OpenAI-like generator reads NVIDIA `reasoning_content` when `content` is empty. `GeneratorConfig.timeout_s` default 60.
- Companion `benchmark_v1` **1.1.0** six-config mock + DeBERTa NLI ablation (`20261029T165024Z_657c8089`, 18 documents, 28 items). Tables: `reports/phase7/v1_1_matrix/`. Official published tables remain `20261028T183042Z_a97ad68f`. n=28 is still underpowered.
- R3: `configs/opt_in/smoke_llm.yaml` plus CLI `--allow-opt-in` on `rageval experiment` and `rageval benchmark`. HTTP jobs still list only `configs/experiments/` and refuse `opt_in: true`. Live LLM smoke was **not** run (no API key, empty Ollama models); see `reports/opt_in_smoke_llm/STATUS.md`.
- R4: `rageval iaa` (Cohen's kappa, `rageval.iaa.v1`). Rater B is still missing; kappa on the template is null. Files: `data/gold/iaa/`.
- R4: `benchmark_v1` **1.2.0** — 21 documents, 32 items (24 dev / 8 test). New USGS Yellowstone FAQs and NASA ISS excerpt; new ids `v1_029`–`v1_032` are **dev**. Test ids remain frozen. HTTP `max_items` cap is 32.
- R5: external RAG scorer — `rageval score --input answers.jsonl --output scores.jsonl` and `score_answer(question, answer, contexts)`. Question + chunks + answer in, `QueryEvaluationResult` out. Default verifier is heuristic. No retrieval, no generator, no gold in a prompt.
- Companion `benchmark_v1` **1.2.0** six-config mock + DeBERTa NLI ablation (`20261029T173408Z_de870a29`, 21 documents, 32 items). Tables: `reports/phase7/v1_2_matrix/`. Recall@5 0.8438 identical; Dense faith 0.401; Sparse 0.4219; Hybrid 0.4635; Reranked 0.4583; abstention 0.1667. n=32 is still underpowered. Official published tables remain `a97ad68f`.
- R7: `A_chunk` overlap-32 protocol on 1.2.0 (`20261029T173515Z_7e2b94a3`). Tables: `reports/phase7/A_chunk_overlap32/`. Three dense configs; faith 0.401 / R@5 0.8438 / MRR 0.7344 identical (matches the six-config dense rows). Does not replace `a97ad68f` or `v1_2_matrix`.

### Changed

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

[0.2.1]: https://github.com/Aaravkhanal/RAGEVAL/releases/tag/v0.2.1
[0.2.0]: https://github.com/Aaravkhanal/RAGEVAL/releases/tag/v0.2.0
[0.2.0rc1]: https://github.com/Aaravkhanal/RAGEVAL/releases/tag/v0.2.0-rc1
