# RAGeval

Research-oriented benchmark and software for measuring whether RAG answers are **supported by retrieved evidence** at the **claim** level.

This project was previously prototyped under the name RAGTruth. It is **not** the RAGTruth corpus of Niu et al. (2024). See `docs/RELATED_WORK.md`.

## What is implemented

- Configurable retrieval baselines (dense MiniLM, BM25, hybrid RRF, optional cross-encoder rerank).
- Atomic claim decomposition and NLI verification (`supported` / `unsupported` / `contradicted`, plus `partially_supported` and `ambiguous` in the schema).
- Citation existence and support-conditioned citation metrics.
- A **synthetic smoke dataset** (8 documents, 8 questions). It is author-written fiction, not SEC/NEJM/OSDI source text.
- A **licensed benchmark_v1** (21 documents, 32 questions in v1.2.0): short U.S. government public-domain excerpts plus original CC-BY-4.0 fiction. See `data/cards/benchmark_v1.md`. The committed ablation tables used v1.0.0 (16/24). Companion mock+NLI scored v1.1.0 (18/28) and v1.2.0 (21/32).
- Answer-level EM / token F1 alongside claim-level support (RQ3).
- Official metric registry (`rageval.metrics.registry`) with no composite overall score.
- Adversarial scenarios with a failure taxonomy (`docs/FAILURE_TAXONOMY.md`) and robustness means by `scenario_type`.
- CLI, FastAPI live claim audit, and pytest suite.

Official generation for smoke tests is a **blinded mock** that cannot read gold `test_type` labels. Opt-in HTTP (`openai` / `ollama`) and `local_hf` backends live under `configs/opt_in/`; keys come from `OPENAI_API_KEY` / `RAGEVAL_API_KEY`, never YAML. Live LLM configs need `rageval experiment --allow-opt-in`; HTTP jobs refuse them.

## Status of results

Committed tables under `reports/` are from run `20261028T183042Z_a97ad68f` on `benchmark_v1` 1.0.0 (16 documents, 24 items; US government public-domain excerpts plus CC-BY-4.0 fiction). Honest write-up: `reports/20261028T183042Z_a97ad68f/FINDINGS.md`. Companion mock+NLI: v1.1.0 `657c8089`, v1.2.0 `de870a29`, A_chunk overlap-32 `7e2b94a3`. `reports/paper.tex` is a **draft** whose table matches the published run; $n=24$ is underpowered. New runs write unique folders under `experiments/runs/`.

## Install

Python 3.10+. Prefer a dedicated environment. Software version **0.2.1**. Official ablation tables remain mock run `20261028T183042Z_a97ad68f`.

```bash
# Fast tests and smoke (hashed [dev,api] lock, no torch)
pip install --require-hashes -r requirements-lock-fast.txt
pip install --no-deps -e .
pytest -m "not hf"

# Research install (MiniLM, DeBERTa, FAISS). On linux/amd64 you can pin:
# pip install --require-hashes -r requirements-lock-all.txt && pip install --no-deps -e .
pip install -e ".[all]"
```

Hashed locks: `requirements-lock-fast.txt` (universal) and `requirements-lock-all.txt` (manylinux x86_64, CPU torch). Regenerate with `bash scripts/compile_locks.sh`. Docker: `docker build --platform linux/amd64 -t rageval:0.2.1 .` (see `docs/REPRODUCIBILITY.md`). Packaging history: `CHANGELOG.md`.

First NLI/embedding calls download Hugging Face weights unless they are already cached. There are no paid APIs in the default path. See `docs/QUICKSTART.md`.

## Commands

```bash
# Claim-level evaluation of one answer against supplied context
rageval evaluate --method heuristic --question "What is the test question?" --answer "The test is valid [1]." --context "The test is valid."

# Fast tests (skip Hugging Face)
pytest -m "not hf"

# Optional: licensed v1 ablation (loads MiniLM + DeBERTa; writes experiments/runs/<id>/)
rageval benchmark --dataset benchmark_v1 --data-dir data --output-dir experiments/runs

# CI smoke fixture (BM25 + heuristic; no MiniLM/DeBERTa)
rageval experiment --config configs/experiments/smoke.yaml --output-dir experiments/runs

# Validate a dataset
rageval validate --dataset benchmark_v1

# RQ2: score NLI (or heuristic) against the labeled claim set
rageval verifier-eval --gold data/gold/verifier_eval_v1.json --method nli --output reports/verifier_eval_v1.md

# IAA (kappa is null until an independent rater B fills data/gold/iaa/annotator_b_verifier_eval_v1.json)
rageval iaa --rater-a data/gold/iaa/annotator_a_verifier_eval_v1.json --rater-b data/gold/iaa/annotator_b_template.json --output reports/iaa/iaa.md

# Score an external RAG system's answers (no retrieval). Default verifier is heuristic.
rageval score --input answers.jsonl --output scores.jsonl --method heuristic

# Single YAML config (repeat --config for a custom matrix)
rageval benchmark --dataset smoke_v1 --config configs/ablation/sparse_bm25_256.yaml

# Named Phase 7 experiment (writes experiments/runs/<id>/metrics.json)
rageval experiment --config configs/experiments/C_retrieve.yaml

# Tables from metrics.json (does not re-run the suite)
rageval report --metrics reports/phase7/v1_matrix/metrics.json --output-dir /tmp/rageval-report

# Honest findings + figures from a completed metrics.json (Phase 8)
rageval findings --metrics reports/phase7/v1_matrix/metrics.json --output-dir reports/20261028T183042Z_a97ad68f --run-id 20261028T183042Z_a97ad68f --case-studies reports/20261028T183042Z_a97ad68f/case_studies.json

# Dashboard (Start queues POST /experiments; live /evaluate/answer stays sync)
rageval serve --port 8000 --runs-dir experiments/runs --data-dir data
```

HTTP after `rageval serve`:

- `GET /datasets`, `GET /datasets/{id}`
- `GET /experiment-configs` (allowlisted YAML names under `configs/experiments/`)
- `GET /experiments`, `GET /experiments/{id}`, `GET /experiments/{id}/results`
- `POST /experiments` → 202 `{id, status, poll}` then poll `GET /experiments/{id}`. Default config is `smoke`. NLI / full v1 names need `"allow_heavy": true`. One job at a time (409 if busy).
- `POST /evaluate/answer` (caller-supplied context, sync)
- `POST /benchmark/run` is removed (HTTP 410). OpenAPI: `/docs`

## Documentation

- `CHANGELOG.md`
- `docs/QUICKSTART.md`
- `docs/REPRODUCIBILITY.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/PROJECT_AUDIT.md` — Phase 0 audit
- `docs/ARCHITECTURE_PROPOSAL.md`
- `docs/RESEARCH_GAPS.md`
- `docs/IMPLEMENTATION_ROADMAP.md`
- `docs/RESEARCH_SPEC.md` — research questions
- `docs/TERMINOLOGY.md`
- `docs/METRIC_DEFINITIONS.md`
- `docs/FAILURE_TAXONOMY.md`
- `configs/experiments/` — Phase 7 named matrix slices
- `reports/phase7/` — v1-labeled tables from `metrics.json`
- `reports/20261028T183042Z_a97ad68f/FINDINGS.md` — Phase 8 findings for the recorded run
- `reports/error_analysis_phase6.md`
- `reports/error_analysis_v1_2.md` — v1.2.0 companion notes (`v1_029`–`v1_032`)
- `docs/RELATED_WORK.md`
- `data/cards/smoke_v1.md` — smoke corpus card
- `data/cards/benchmark_v1.md` — licensed pilot card
- `docs/ANNOTATION_GUIDELINES.md`
- `data/cards/verifier_eval_v1.md` — labeled claim set for RQ2
