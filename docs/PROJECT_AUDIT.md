# Phase 0 Project Audit — RAGeval / RAGeval

**Audit date:** 2026-10-28  
**Repository:** `/Users/aaravkhanal/Desktop/RAGEVAL` (`origin`: `https://github.com/Aaravkhanal/RAGEVAL.git`)  
**Git state:** branch `main` at `3980f38`, working tree clean, no uncommitted user changes.  
**Current package name:** `rageval` v0.1.0  

This audit is inspection-only. No application code was modified. Four Phase 0 documents were added under `docs/`.

---

## 1. Executive summary

The repository is **not empty**. It is a working Python research prototype named **RAGeval** that already implements a large fraction of the RAGeval vision:

- Configurable RAG pipeline (chunking, MiniLM dense retrieval, BM25, hybrid RRF, optional cross-encoder reranker, mock/OpenAI-like generation).
- Claim decomposition, DeBERTa-v3 NLI verification, citation parsing, retrieval metrics, FastAPI dashboard, CLI, tests, and committed ablation reports.

It is **not yet a scientifically credible benchmark**. The core engineering loop works. Measurement validity, dataset provenance, experimental isolation, and reporting honesty do not.

Highest-severity findings:

1. **Synthetic corpus presented as real-domain sources.** README and `reports/paper.tex` describe SEC 10-Q, NEJM, and OSDI documents. The actual corpus is eight short fictional documents (ApexCloud, Veloceptin, HydraKV, NovaDrive) totaling 527 whitespace tokens.
2. **Committed paper claims contradict committed numbers.** `reports/benchmark_summary.csv` shows identical Recall@5 = 0.75 and faithfulness = 0.4167 across all six configs. `reports/paper.tex` and the narrative in `paper_analysis.md` claim a 16.4% Recall@5 gain and per-config differences that do not exist in the CSV.
3. **Mock generator leaks gold test type.** `MockGenerator` receives the `BenchmarkItem` and abstains when `test_type == UNANSWERABLE`. Abstention accuracy of 1.0 is therefore not a model result.
4. **Gold atomic claims are unused.** Sixteen gold claims exist in the dataset schema but the evaluator never scores verifier labels against them.
5. **Name collision (resolved in the follow-up rename).** A published 2024 hallucination corpus is named RAGTruth (Niu et al.). This repository is now **RAGeval**.

**What works end to end (tested this session):** unit/integration tests (27/27 pass), CLI `evaluate`, dataset load + integrity validation, live NLI model load (`cross-encoder/nli-deberta-v3-base`).

**What was not re-run:** full ablation suite, `rageval serve`, remote GitHub Actions.

---

## 2. Git and environment

| Item | State |
| --- | --- |
| Branch | `main`, tracking `origin/main` |
| Commits | `f301052` initial system; `4e8a103` “phase-2”; `3980f38` “phase-3” |
| Uncommitted work | None |
| Local docs dir | Did not exist before this audit |
| License file | Missing |
| Lockfile | Missing (`requirements.txt` + `pyproject.toml` only) |

Prior git “phases” are **not** the RAGeval master-prompt phases. Existing work already covers pipeline, evaluation, adversarial items, CI, streaming, and integrations.

**Runtime observed:**

- Homebrew `/opt/homebrew/bin/python3` (3.13.3) cannot import `torch` or `pytest`. A clean default Python is **not** currently executable.
- Miniforge `/Users/aaravkhanal/miniforge3/bin/python` (3.13.13) has an **editable** install of `rageval` and the scientific stack. Tests and CLI were run there.
- Hugging Face cache already contains `all-MiniLM-L6-v2`, `nli-deberta-v3-base`, and `ms-marco-MiniLM-L-6-v2`. No new model downloads were required for the audit tests.

CI (`.github/workflows/ci.yml`) tests Python 3.10–3.12, installs from `requirements.txt`, runs `pytest -v`, then a CLI evaluate smoke command. Remote CI status was not queried (`gh` is not installed).

---

## 3. Directory map

```text
RAGEVAL/
├── rageval/                 # installable package (not src/rageval)
│   ├── cli.py                # rageval {benchmark,report,evaluate,serve}
│   ├── core/                 # pydantic schemas + PipelineConfig
│   ├── dataset/              # synthetic generator, loader, validator, importers
│   ├── pipeline/             # chunk, embed, FAISS, BM25, RRF, rerank, generate
│   ├── evaluator/            # decompose, NLI, citations, retrieval metrics
│   ├── benchmark/            # ablation matrix, runner, reporter
│   ├── analysis/             # plots, paper markdown, significance, ECE
│   ├── integrations/         # decorator, LangChain-like callback, LlamaIndex handler
│   └── server/               # FastAPI + static dashboard
├── data/{raw,gold,adversarial}/
├── tests/                    # 16 files, 27 tests
├── reports/                  # committed tables, figures, paper.tex
├── .github/workflows/ci.yml
├── pyproject.toml
├── requirements.txt
└── README.md
```

**Missing relative to the target architecture:** `configs/`, `scripts/`, `experiments/` (run store), `docs/` (now created), `src/rageval/`, dataset cards, manifests with versions/licenses.

**Do not create a parallel `src/rageval` tree.** Map new work onto `rageval.*`. A rename, if approved, is a dedicated later task.

---

## 4. Component inventory

### 4.1 Entry points — working

| Entry | Status |
| --- | --- |
| `rageval benchmark` | Implemented. Loads corpus + all items, runs 6 pipeline configs, writes reports. Not re-run this session (downloads/compute). |
| `rageval report` | Re-runs the full suite, then writes markdown/figures. Narrative text is **hardcoded**, not derived from scores. |
| `rageval evaluate` | **Tested.** Produces claim JSON with real DeBERTa NLI. |
| `rageval serve` | FastAPI app exists. Health and `/evaluate/answer` covered by tests. Full UI not browser-verified this session. |

### 4.2 Core schemas and config — working, incomplete contracts

`rageval/core/schemas.py` is the real data contract. Useful types already exist: `Document`, `Chunk`, `RetrievedChunk`, `BenchmarkItem`, `GoldEvidence`, `GoldClaim`, `AtomicClaim`, `ClaimVerification`, `QueryEvaluationResult`, `BenchmarkRunSummary`.

Issues:

- `VerificationLabel.ENTAILEMENT` is misspelled (should be `ENTAILMENT`). Changing it is an API break; tests and JSON dumps use the current spelling.
- Labels are only `{ENTAILEMENT, CONTRADICTION, NEUTRAL}`. No `partially_supported`, `ambiguous`, or `unverifiable`.
- `AtomicClaim.char_start` / `char_end` exist but the decomposer never fills them.
- `CitationMetric.misattributed_citations` exists but is never populated.
- `TestType.DISTRACTOR` exists but no dataset items use it.
- No experiment-run metadata: seed, git hash, model revision, hardware, dataset version.

`PipelineConfig` is a solid Pydantic object. `load_yaml_config()` exists but **no YAML files** exist and the suite hardcodes configs in Python (`get_default_ablation_matrix()`).

Commented-but-unimplemented config values:

- `chunker.strategy = "recursive"` falls through to fixed token chunking.
- `generator.backend = "local_hf"` falls through to `MockGenerator`.

### 4.3 Dataset — implemented synthetic fixture, not a research corpus

| Split file | Contents |
| --- | --- |
| `data/raw/corpus.json` | 8 documents, 4 fictional domains |
| `data/gold/benchmark_standard.json` | 5 standard items |
| `data/adversarial/benchmark_adversarial.json` | 2 unanswerable + 1 conflicting |
| `data/gold/benchmark_all.json` | Union (8 items) |

Integrity validator: **valid, 0 errors, 0 warnings** on the committed files.

Profiler (not wired into CLI): 527 tokens, vocab 370, mean 2.8 gold claims per standard item.

`create_synthetic_benchmark()` is both the dataset definition and the regeneration path. `DatasetLoader.ensure_data_exists()` will silently regenerate if `corpus.json` is missing. There is no dataset version, license, URL provenance, annotator protocol, or train/dev/test split.

Importers (`FinanceBench`, `PubMedQA`, `HotpotQA`) normalize **in-memory dicts**. They do not download or cache the public datasets. Tests only check schema mapping on tiny stubs.

Perturbation engine can invert polarity, mutate numbers, inject hallucination templates, and synthesize unanswerable questions. It is **not** used to expand the committed benchmark.

### 4.4 RAG pipeline — working for smoke use, mock-dominated

| Stage | Implementation | Notes |
| --- | --- | --- |
| Fixed token chunking | Working, tested | Word-split, not tokenizer tokens. `start_char` via `str.find` is approximate. |
| Sentence-window chunking | Working, tested | Window chunk `start_char`/`end_char` are relative to the window, not the document. |
| Semantic chunking | Working, tested | Loads MiniLM. Not in the default ablation matrix. |
| Dense FAISS | Working, tested | FlatIP or HNSW. Default MiniLM on CPU. |
| BM25Plus | Working, tested | |
| Hybrid RRF | Working, tested | |
| Cross-encoder rerank | Implemented | Enabled only in `Hybrid_RRF_Reranked`. Loads `ms-marco-MiniLM-L-6-v2`. |
| Mock generator | Default | Extractive copy of top-chunk sentences + citations; mode-aware abstention. |
| OpenAI-like HTTP generator | Implemented | Optional; not used in committed runs. |

`RAGPipeline.index()` always builds both FAISS and BM25 even for dense-only configs.

### 4.5 Claim-level evaluation — working prototype, incomplete research engine

**Decomposer (`AtomicClaimDecomposer`):** sentence split, discourse-marker strip, conjunction split, citation attach. Tested. Does not preserve claim offsets. Conjunction splits are regex, not a proposition model. Qualifiers/negation can be split incorrectly.

**NLI verifier:** loads `cross-encoder/nli-deberta-v3-base` when available (**confirmed loaded this session**). If load fails, it **silently switches** to a lexical-overlap heuristic. That silent substitution violates reproducibility Rule F.

Decision rules (hardcoded): contradiction if `p_con > 0.60` and greater than entailment; else entailment if `p_ent >= 0.50`; else neutral. No partial support. A claim can collect both supporting and contradicting chunk IDs, but the final label is a single enum.

Abstention text is classified as `ENTAILEMENT` with confidence 1.0 (“correct abstention”), mixing a behavioral label into a support label.

**Span localizer:** lexical overlap + number bonus. Tested. Wired into NLI for entailed/contradicted claims.

**Multi-hop fusion:** complementary entity-overlap pairs + concatenated premise. **Tested in isolation. Not called from `RAGEvalEvaluator`.**

**Citation parser:** `[1]`, `[2, 3]`, `[doc_id]`. Precision = citation token resolves to a retrieved chunk. Recall = fraction of sentences that contain any citation marker. It does **not** check that the cited chunk supports the claim. Hallucinated citations are out-of-pool IDs only.

**Retrieval metrics:** Recall@{1,3,5,k}, MRR, binary nDCG@k, noise ratio, all at **document id** level. Untested as unit tests. For items with empty gold evidence, any retrieval scores recall 0 and noise 1; empty retrieval scores recall 1. That encodes “retrieving anything on unanswerable questions is wrong,” which is a design choice, not documented.

**Evaluator orchestrator:** decompose → citation audit → per-claim NLI → rate aggregation → keyword abstention → retrieval metrics → hardcoded USD cost (`$1.50 / $2.00` per 1M tokens). Gold claims, gold answers, and multi-hop fusion are unused.

### 4.6 Benchmark runner and reports — executable, scientifically weak

Default matrix (6 configs): Dense 128 / 256 / 512, BM25 256, Hybrid RRF 256, Hybrid + rerank.

Committed summary (`reports/benchmark_summary.csv`):

| Configuration | Faithfulness | Hallucination | Contradiction | Recall@5 | MRR | Abstention | Latency ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Dense_Chunk128 | 0.4167 | 0.3229 | 0.2604 | 0.75 | 0.75 | 1.0 | 2844.83 |
| Dense_Chunk256_Baseline | 0.4167 | 0.3229 | 0.2604 | 0.75 | 0.75 | 1.0 | 2409.06 |
| Dense_Chunk512 | 0.4167 | 0.3229 | 0.2604 | 0.75 | 0.75 | 1.0 | 2554.63 |
| Sparse_BM25_Chunk256 | 0.4167 | 0.2917 | 0.2917 | 0.75 | 0.75 | 1.0 | 2701.04 |
| Hybrid_RRF_Chunk256 | 0.4167 | 0.3542 | 0.2292 | 0.75 | 0.75 | 1.0 | 2934.00 |
| Hybrid_RRF_Reranked | 0.4167 | 0.3542 | 0.2292 | 0.75 | 0.75 | 1.0 | 2159.01 |

Interpretation of these numbers (from code + detailed JSON, not from the paper narrative):

- Generator is mock extractive, so answers are mostly the first sentences of the top retrieved chunk. Ablations barely change generation.
- Faithfulness ~0.42 is NLI disagreement with extractive copies plus mixed unanswerable/conflict items — not a ranking of retrievers.
- Recall@5 is saturated at 0.75 on 8 tiny documents.
- Abstention = 1.0 because the mock generator sees `test_type`.
- Conflict detection = 1.0 because the runner treats `"conflict" in answer` **or** `len(claims) >= 2` as detection.
- Cost column is mock token counts times OpenAI-like prices.

`reports/paper.tex` table is **incompatible** with the CSV (example: Hybrid_RRF_Reranked faithfulness 0.938 vs 0.4167; Recall@5 0.965 vs 0.75; latency 67.5 ms vs 2159 ms). Treat `paper.tex` numbers as **not experimental results**.

`generate_paper_report.py` interpolates the real table into markdown, then appends canned findings (“16.4% higher Recall@5”, “hallucinate answers in over 60% of cases”) that the table refutes (abstention accuracy is 1.0; Recall@5 is identical).

Reporter overwrites `reports/benchmark_*.csv|json|md|tex` in place. No experiment ID, no resume, no git snapshot.

Significance tests (paired t-test + Wilcoxon) exist and are unit-tested on synthetic arrays. They are not applied to committed runs. `is_significant` uses raw p < 0.05 with no multiple-comparison correction and n=8 would be underpowered.

Calibration ECE/Brier and temperature scaling exist and are unit-tested. They are **not** applied to NLI outputs in the evaluator.

### 4.7 API and UI — implemented, secondary

Working endpoints (code + tests): `GET /health`, `POST /evaluate/answer`, Prometheus-style `GET /metrics`.

Implemented but lightly tested: `POST /evaluate/stream` (simulated token list, not SSE), `POST /benchmark/run` (blocking full suite), `GET /metrics/summary`.

Dashboard (`server/static/index.html`): live claim audit with evidence-span highlight, benchmark table, hardcoded dataset cards. Dataset explorer does **not** call an API. “Execute Full Ablation Run” blocks the request on six embedding pipelines.

Missing vs master prompt: `GET /datasets`, `GET /experiments/{id}`, `GET /claims/{id}`, job queue.

Integrations: `@monitor_rag`, LangChain-shaped callback, LlamaIndex handler. They do not depend on LangChain/LlamaIndex packages. Tested with mocks. Production value is limited until the evaluator is valid.

### 4.8 Tests — all passing in the miniforge environment

Command:

```text
/Users/aaravkhanal/miniforge3/bin/python -m pytest -v --durations=20
```

Result: **27 passed, 21 warnings, 39.20s** (Python 3.13.13, pytest 8.4.0).

| File | Coverage intent |
| --- | --- |
| `test_decomposer.py` | Claim split + citation attach |
| `test_nli_verifier.py` | Entail / contradict / neutral on one finance sentence |
| `test_citation_parser.py` | Extract + hallucinated `[5]` |
| `test_adversarial.py` | Abstention keyword detection |
| `test_api.py` | Health + evaluate |
| `test_chunkers.py` | Fixed + sentence window |
| `test_semantic_chunker.py` | Loads MiniLM (~5s) |
| `test_sparse_and_indices.py` | FAISS + BM25 + hybrid (~5s) |
| `test_span_localizer.py` | Span offsets |
| `test_importers.py` | Stub record mapping |
| `test_perturbations.py` | Mutation strings |
| `test_multi_hop.py` | Pair discovery; entailed passthrough |
| `test_streaming.py` | Guardrail on contradiction |
| `test_integrations.py` | Decorator / callbacks |
| `test_calibration.py` | ECE, temperature |
| `test_significance.py` | Fake paired scores |

Gaps: no metric-formula tests, no dataset-schema tests beyond importer stubs, no RAGPipeline + evaluator integration test, no CLI tests, no gold-claim vs predicted-label tests, no tests that mock HF so CI can run offline.

CLI smoke (same environment): `python rageval/cli.py evaluate --question "What is the test question?" --answer "The test is valid [1]." --context "The test is valid."` returned `ENTAILEMENT` with confidence ~0.95. NLI model **did** load.

---

## 5. Working / incomplete / placeholder / broken

### Working (implemented and exercised)

- Pydantic schemas and pipeline config objects.
- Synthetic 8-doc / 8-item fixture load and integrity check.
- Fixed/sentence/semantic chunkers (semantic tested; not in default matrix).
- Dense, BM25, hybrid retrieval on tiny docs.
- Claim regex decomposition.
- DeBERTa NLI path when the model is cached.
- Citation *existence* audit.
- FastAPI health + evaluate.
- pytest suite in the miniforge env.
- Plotting code (figures exist in git; not regenerated this session).

### Incomplete (code exists, not research-ready)

- Gold claims, gold answers, and gold spans are stored but not used as verifier ground truth.
- Multi-hop fusion not in the main evaluator.
- Semantic chunking, calibration, profiler, YAML loader, perturbation engine unused by default experiments.
- Citation precision/recall definitions do not match the intended research metrics.
- Generators: mock is default; `local_hf` is a comment; OpenAI-like is untested against a live endpoint.
- Experiment reproducibility metadata and non-overwriting run store.
- Dataset importers are schema adapters, not dataset pipelines.
- Dashboard dataset tab is static HTML.

### Placeholders / misleading surfaces

- README “curated multi-domain benchmark” of 10-Q / NEJM / OSDI.
- Paper abstract “16.4% higher Recall@5”.
- `reports/paper.tex` numerical table.
- Cost USD on mock runs.
- Prometheus exporter is an in-process rolling list, not a Prometheus client.
- Streaming endpoint consumes a pre-tokenized list.

### Broken or invalid for research conclusions

- Paper narrative vs CSV contradiction.
- Mock generator gold-label leakage for unanswerable items.
- Conflict-detection heuristic (`len(claims) >= 2`).
- Silent NLI → heuristic fallback.
- Homebrew Python cannot run the project without installing the stack.
- `scipy` is imported in `significance.py` but not declared in `pyproject.toml` / `requirements.txt` (it arrived transitively via scikit-learn in this env).
- `requests` is in `requirements.txt` but unused; `pydantic-settings` is declared and unused.

### Duplication

- `requirements.txt` duplicates `pyproject.toml` dependencies (plus `requests`).
- Report generation lives in both `BenchmarkReporter` and `generate_paper_report.py`.
- Two `/metrics` concepts: Prometheus text vs JSON summary.

---

## 6. Reusable implementations (keep)

Retain and extend, do not rewrite:

1. `rageval.core.schemas` / `config` — widen labels and add run metadata.
2. `pipeline/{chunkers,embedders,indices,sparse,rerankers,rag}` — real baselines.
3. `evaluator/{decomposer,nli_verifier,citation_parser,retrieval_metrics,span_localizer,evaluator}` — the evaluation spine.
4. `benchmark/{runner,suite,reporter}` — orchestration, after leakage and overwrite fixes.
5. `dataset/{loader,validator,generator}` — keep as a **dev smoke fixture**, not as the published benchmark.
6. CLI + FastAPI evaluate path.
7. pytest layout and CI skeleton.

---

## 7. Clean-environment executability

**Not verified from a truly empty venv.** Evidence:

- Default Homebrew Python 3.13 lacks torch/pytest.
- README `pip install -e .` would pull torch, transformers, sentence-transformers, faiss-cpu. That is a large install and was not executed.
- No pinned lockfile, so CI and local versions will drift (local transformers is 5.10.2).
- First NLI/embedder call needs Hugging Face downloads if cache is cold.
- Default ablation with reranker enabled is CPU-heavy relative to an 8-item set.

Safe smoke path once deps exist: `pytest` plus `rageval evaluate`. Full `rageval benchmark` should remain opt-in.

---

## 8. Files created by this phase

| Path | Action |
| --- | --- |
| `docs/PROJECT_AUDIT.md` | Created |
| `docs/ARCHITECTURE_PROPOSAL.md` | Created |
| `docs/RESEARCH_GAPS.md` | Created |
| `docs/IMPLEMENTATION_ROADMAP.md` | Created |

No other files were modified or deleted.
