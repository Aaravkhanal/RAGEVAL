# RAGeval

Research-oriented benchmark and software for measuring whether RAG answers are **supported by retrieved evidence** at the **claim** level.

This project was previously prototyped under the name RAGTruth. It is **not** the RAGTruth corpus of Niu et al. (2024). See `docs/RELATED_WORK.md`.

## What is implemented

- Configurable retrieval baselines (dense MiniLM, BM25, hybrid RRF, optional cross-encoder rerank).
- Atomic claim decomposition and NLI verification (`supported` / `unsupported` / `contradicted`, plus `partially_supported` and `ambiguous` in the schema).
- Citation existence and support-conditioned citation metrics.
- A **synthetic smoke dataset** (8 documents, 8 questions). It is author-written fiction, not SEC/NEJM/OSDI source text.
- A **licensed benchmark_v1** (36 documents, 47 questions in v1.4.0): short U.S. government public-domain excerpts plus original CC-BY-4.0 fiction. See `data/cards/benchmark_v1.md`. The committed ablation tables used v1.0.0 (16/24). Companion mock+NLI scored v1.1.0 (18/28) and v1.2.0 (21/32). v1.3.0/1.4.0 are on-disk only until a new companion run is recorded. Independent slice n=30 is a count threshold with disjoint gold documents; labels remain single-author.
- A separate **chunk_benchmark_v1** diagnostic slice (7 long public NASA/CDC documents, 30 questions). The named `A_chunk` experiment now uses it so 128/256/512-word settings produce different chunks. See `data/cards/chunk_benchmark_v1.md`.
- Answer-level EM / token F1 alongside claim-level support (RQ3).
- Official metric registry (`rageval.metrics.registry`) with no composite overall score.
- Adversarial scenarios with a failure taxonomy (`docs/FAILURE_TAXONOMY.md`) and robustness means by `scenario_type`.
- CLI, FastAPI live claim audit, and pytest suite.
- Optional fail-closed API-token protection for dataset, run, metrics, and evaluation routes; Docker Compose enables it by default. See `docs/PRODUCTION.md`.

Official generation for smoke tests is a **blinded mock** that cannot read gold `test_type` labels. Opt-in HTTP (`openai` / `ollama`) and `local_hf` backends live under `configs/opt_in/`; keys come from `OPENAI_API_KEY` / `RAGEVAL_API_KEY`, never YAML. Live LLM configs need `rageval experiment --allow-opt-in`; HTTP jobs refuse them.

## Status of results

Committed tables under `reports/` are from run `20261028T183042Z_a97ad68f` on `benchmark_v1` 1.0.0 (16 documents, 24 items; US government public-domain excerpts plus CC-BY-4.0 fiction). Honest write-up: `reports/20261028T183042Z_a97ad68f/FINDINGS.md`. Companion mock+NLI: v1.1.0 `657c8089`, v1.2.0 `de870a29`, A_chunk overlap-32 `7e2b94a3`. `reports/paper.tex` is a **draft** whose table matches the published run; $n=24$ is underpowered. New runs write unique folders under `experiments/runs/`.

The current long-document chunk diagnostic is `reports/phase7/A_chunk_long_v1/`. It uses metric schema v2: document Recall@5 is calculated only on answerable items, with separate evidence-span recall and no-answer retrieval reporting. Historical v1 recall values mixed answerable and unanswerable questions and are not directly comparable.

`reports/phase7/B_embed_v1/` records a matched MiniLM versus MPNet embedding comparison on `benchmark_v1` 1.3.0. It remains diagnostic and uses the blinded mock generator.

`reports/phase7/live_matrix_v1/` records six matched retrieval settings with a real NVIDIA NIM generator on the 40-item v1.3.0 corpus. The paper includes this companion table. Live v1 document Recall@5 is 1.0 on all six configs, so that matrix cannot rank retrievers. Use `reports/phase8/retrieval_v2.json` for a non-saturated retrieval diagnostic. Token counts are recorded; USD cost is unknown because a provider rate was not available. Live NVIDIA stays companion; the official SUT is the blinded mock on `a97ad68f`.

`data/gold/review/claim_review_v1.jsonl` is an unlabeled review queue for independent claim-boundary, evidence-support, and citation judgments (`human_*` fields null). See `docs/CLAIM_REVIEW.md`; no human agreement result is claimed yet.

## Install

### Live free preview

[Open RAGeval on Render](https://rageval-free.onrender.com/). Enter
`RAGEVAL_PUBLIC_TOKEN` from the Render service's **Environment** page in the
RAGeval access token field. This token controls access to the hosted service;
it is not a key for the AI system being evaluated or an AI model provider.
You can check any answer by pasting its question, retrieved source text, and
answer. On **Claim audit**,
choose Faithful, Hallucinated, or Contradictory to compare an answer with its
source text. The claim cards show which individual statements have support;
click a card to inspect its matching evidence. The default verifier is a fast
lexical heuristic, so its labels are diagnostic rather than human judgments.
The **Dataset Explorer** shows questions and gold answers. On **Ablation
Benchmark**, enter the separate admin token and start the `smoke` job to see
BM25 retrieval and scoring on two synthetic questions. The free service does
not run dense embedding, reranking, or NLI experiments, and its new run results
disappear when Render sleeps or restarts. See [Render free preview](docs/RENDER_FREE.md).

## Local install

Python 3.10+. Prefer a dedicated environment. Software version **0.3.0**. Official ablation tables remain mock run `20261028T183042Z_a97ad68f`.

```bash
# Fast tests and smoke (hashed [dev,api] lock, no torch)
pip install --require-hashes -r requirements-lock-fast.txt
pip install --no-deps -e .
pytest -m "not hf"

# Research install (MiniLM, DeBERTa, FAISS). On linux/amd64 you can pin:
# pip install --require-hashes -r requirements-lock-all.txt && pip install --no-deps -e .
pip install -e ".[all]"
```

Hashed locks: `requirements-lock-fast.txt` (universal) and `requirements-lock-all.txt` (manylinux x86_64, CPU torch). Regenerate with `bash scripts/compile_locks.sh`. Docker: `docker build --platform linux/amd64 -t rageval:0.3.0 .` or `docker compose up --build` (see `docs/REPRODUCIBILITY.md`, `docs/PRODUCTION.md`). Packaging history: `CHANGELOG.md`.

First NLI/embedding calls download Hugging Face weights unless they are already cached. There are no paid APIs in the default path. See `docs/QUICKSTART.md`.

## Commands

```bash
# Claim-level evaluation of one answer against supplied context
rageval evaluate --method heuristic --question "What is the test question?" --answer "The test is valid [1]." --context "The test is valid."

# Fast tests (skip Hugging Face)
pytest -m "not hf"

# Optional: licensed v1 ablation (loads MiniLM + DeBERTa; writes experiments/runs/<id>/)
rageval benchmark --dataset benchmark_v1 --data-dir data --output-dir experiments/runs

# Diagnostic long-document chunk comparison with evidence-span Recall@5
rageval experiment --config configs/experiments/A_chunk.yaml --output-dir experiments/runs

# CI smoke fixture (BM25 + heuristic; no MiniLM/DeBERTa)
rageval experiment --config configs/experiments/smoke.yaml --output-dir experiments/runs

# Validate a dataset
rageval validate --dataset benchmark_v1

# RQ2: score NLI (or heuristic) against the labeled claim set
rageval verifier-eval --gold data/gold/verifier_eval_v1.json --method nli --output reports/verifier_eval_v1.md

# IAA (disclosed LLM rater B is diagnostic; confirmatory IAA still needs an independent human)
rageval iaa --rater-a data/gold/iaa/annotator_a_verifier_eval_v1.json --rater-b data/gold/iaa/annotator_b_verifier_eval_v1.json --output reports/iaa/iaa.md
# Apply human labels onto the blank template (does not invent labels)
rageval iaa-label --template data/gold/iaa/annotator_b_template.json --output data/gold/iaa/annotator_b_human.json --set ve_001=supported

# Opt-in live NVIDIA NIM (requires NVIDIA_API_KEY in .env; HTTP jobs refuse this)
rageval experiment --config configs/opt_in/smoke_llm_nvidia.yaml --allow-opt-in --output-dir experiments/runs

# Score an external RAG system's answers (no retrieval). Default verifier is heuristic.
# Also accepts a run predictions.jsonl (generated_answer + retrieved_chunks).
rageval score --input answers.jsonl --output scores.jsonl --method heuristic

# Diagnostic per-item comparison of two per_example.jsonl files
rageval compare --left reports/phase7/v1_2_matrix/metrics/per_example.jsonl --right reports/phase7/nvidia_nim_v1/metrics/per_example.jsonl --left-config Sparse_BM25_Chunk256 --right-config OptIn_NVIDIA_NIM_NLI --output reports/error_analysis_nvidia_v1.md

# Single YAML config (repeat --config for a custom matrix)
rageval benchmark --dataset smoke_v1 --config configs/ablation/sparse_bm25_256.yaml

# Named Phase 7 experiment (writes experiments/runs/<id>/metrics.json)
rageval experiment --config configs/experiments/C_retrieve.yaml

# Tables from metrics.json (does not re-run the suite)
rageval report --metrics reports/phase7/v1_matrix/metrics.json --output-dir /tmp/rageval-report

# Honest findings + figures from a completed metrics.json (Phase 8)
rageval findings --metrics reports/phase7/v1_matrix/metrics.json --output-dir reports/20261028T183042Z_a97ad68f --run-id 20261028T183042Z_a97ad68f --case-studies reports/20261028T183042Z_a97ad68f/case_studies.json

# Dashboard (Start queues POST /experiments; live /evaluate/answer stays sync)
export RAGEVAL_ADMIN_TOKEN="choose-a-long-random-token"
rageval serve --port 8000 --runs-dir experiments/runs --data-dir data
# In a second terminal, with the same run and data directories:
rageval worker --runs-dir experiments/runs --data-dir data
# Docker with TLS reverse proxy: see docs/PRODUCTION.md
# docker compose -f docker-compose.yml -f docker-compose.tls.yml up --build
```

HTTP after `rageval serve`:

- `GET /datasets`, `GET /datasets/{id}`
- `GET /experiment-configs` (allowlisted YAML names under `configs/experiments/`)
- `GET /experiments`, `GET /experiments/{id}`, `GET /experiments/{id}/results`
- `POST /experiments` requires `X-RAGEVAL-ADMIN-TOKEN` matching `RAGEVAL_ADMIN_TOKEN` and returns 202 `{id, status, poll}`. The separate worker executes the job; poll `GET /experiments/{id}`. Default config is `smoke`. NLI / full v1 names need `"allow_heavy": true`. One job at a time (409 if busy).
- `GET /health` (liveness: version, busy), `GET /ready`
- `POST /evaluate/answer` (caller-supplied context, sync; default `method=heuristic`)
- `POST /score` (external RAG scorer, same contract as `rageval score`)
- `POST /benchmark/run` is removed (HTTP 410). OpenAPI: `/docs`

## Documentation

- `CHANGELOG.md`
- `docs/QUICKSTART.md`
- `docs/REPRODUCIBILITY.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/KNOWN_LIMITATIONS.md`
- `docs/PRODUCTION.md`
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

### Audit your own saved responses

Open **Batch audit**, download the example JSON, and replace it with your agent's
responses. Each row has `question`, `answer`, and `context_chunks` (an array of
retrieved source passages). Connect with your service token, select the file,
and run the audit. The preview supports 1–20 rows per file, 10 source passages
per row, and a 2 MB file limit. Expand rows for claim details and export JSON
results before closing the tab. This evaluates saved outputs with the heuristic
verifier; it does not register a dataset or run your agent automatically.

### Private workspaces and durable deployment

See [workspace operations](docs/WORKSPACE.md) for accounts, custom benchmark
execution, durable queue migrations, full artifact export/restore, and deployed
workflow tests. The [release diagnostic](reports/release_20261103/ANALYSIS.md)
records a fresh smoke run and the heuristic verifier's limitations; independent
human review remains an explicit evidence requirement.
