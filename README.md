# RAGeval

Research-oriented benchmark and software for measuring whether RAG answers are **supported by retrieved evidence** at the **claim** level.

This project was previously prototyped under the name RAGTruth. It is **not** the RAGTruth corpus of Niu et al. (2024). See `docs/RELATED_WORK.md`.

## What is implemented

- Configurable retrieval baselines (dense MiniLM, BM25, hybrid RRF, optional cross-encoder rerank).
- Atomic claim decomposition and NLI verification (`supported` / `unsupported` / `contradicted`, plus `partially_supported` and `ambiguous` in the schema).
- Citation existence and support-conditioned citation metrics.
- A **synthetic smoke dataset** (8 documents, 8 questions). It is author-written fiction, not SEC/NEJM/OSDI source text.
- A **licensed benchmark_v1** (18 documents, 28 questions in v1.1.0): short U.S. government public-domain excerpts plus original CC-BY-4.0 fiction. See `data/cards/benchmark_v1.md`. The committed ablation tables used v1.0.0 (16/24).
- Answer-level EM / token F1 alongside claim-level support (RQ3).
- Official metric registry (`rageval.metrics.registry`) with no composite overall score.
- Adversarial scenarios with a failure taxonomy (`docs/FAILURE_TAXONOMY.md`) and robustness means by `scenario_type`.
- CLI, FastAPI live claim audit, and pytest suite.

Official generation for smoke tests is a **blinded mock** that cannot read gold `test_type` labels.

## Status of results

Committed tables under `reports/` are from run `20261028T183042Z_a97ad68f` on `benchmark_v1` (see `reports/README.md`). `reports/paper.tex` is a **draft** and must not be cited as experimental evidence. New benchmark runs write unique folders under `experiments/runs/` and do not overwrite previous runs.

## Install

Python 3.10+ with PyTorch, sentence-transformers, and FAISS. Prefer a dedicated environment:

```bash
pip install -e .
```

First NLI/embedding calls download Hugging Face weights unless they are already cached.

## Commands

```bash
# Claim-level evaluation of one answer against supplied context
rageval evaluate --question "What is the test question?" --answer "The test is valid [1]." --context "The test is valid."

# Unit tests
pytest -v

# Optional: licensed v1 ablation (loads MiniLM + DeBERTa; writes experiments/runs/<id>/)
rageval benchmark --dataset benchmark_v1 --data-dir data --output-dir experiments/runs

# CI smoke fixture
rageval benchmark --dataset smoke_v1 --data-dir data --output-dir experiments/runs

# Validate a dataset
rageval validate --dataset benchmark_v1

# RQ2: score NLI (or heuristic) against the labeled claim set
rageval verifier-eval --gold data/gold/verifier_eval_v1.json --method nli --output reports/verifier_eval_v1.md

# Single YAML config (repeat --config for a custom matrix)
rageval benchmark --dataset smoke_v1 --config configs/ablation/sparse_bm25_256.yaml

# Dashboard
rageval serve --port 8000
```

## Documentation

- `docs/PROJECT_AUDIT.md` — Phase 0 audit
- `docs/ARCHITECTURE_PROPOSAL.md`
- `docs/RESEARCH_GAPS.md`
- `docs/IMPLEMENTATION_ROADMAP.md`
- `docs/RESEARCH_SPEC.md` — research questions
- `docs/TERMINOLOGY.md`
- `docs/METRIC_DEFINITIONS.md`
- `docs/FAILURE_TAXONOMY.md`
- `reports/error_analysis_phase6.md`
- `docs/RELATED_WORK.md`
- `data/cards/smoke_v1.md` — smoke corpus card
- `data/cards/benchmark_v1.md` — licensed pilot card
- `docs/ANNOTATION_GUIDELINES.md`
- `data/cards/verifier_eval_v1.md` — labeled claim set for RQ2
