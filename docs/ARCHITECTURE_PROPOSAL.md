# Architecture Proposal — RAGeval on top of RAGeval

**Status:** Proposal only. No module moves or renames without approval.  
**Principle:** map the intended architecture onto the existing `rageval` package. Do not add a parallel `src/rageval` tree.

---

## 1. Goal

Produce a research-grade evaluation framework whose **core engine is independent of the API/UI**, with:

- versioned datasets and manifests
- configurable RAG baselines
- claim-level evidence verification with traceable spans
- a metric registry with explicit formulas
- reproducible experiment runs
- optional inspection API

Research priority: measurement validity and reproducibility. UI remains secondary.

---

## 2. Keep the current package layout

The master prompt’s `src/rageval/{ingestion,chunking,...}` tree is a **conceptual** map. The repository already has equivalent modules:

| Intended module | Existing module | Action |
| --- | --- | --- |
| `datasets/` | `data/` + `rageval.dataset` | Extend `data/` with manifests, licenses, cards. Keep JSONL/JSON. |
| `ingestion/` | `dataset/loader.py`, `importers/` | Keep. Add provenance + download-optional importers later. |
| `chunking/` | `pipeline/chunkers.py`, `semantic_chunker.py` | Keep. Document token vs word. Implement recursive only if an experiment needs it. |
| `embeddings/` | `pipeline/embedders.py` | Keep. Record model id + revision. |
| `retrieval/` | `pipeline/indices.py`, `sparse.py` | Keep. |
| `reranking/` | `pipeline/rerankers.py` | Keep. Default off for smoke tests. |
| `generation/` | `pipeline/generator.py` | Keep mock for tests. Add a **blind** mock that cannot see `test_type`. Real LLM backends remain optional adapters. |
| `claim_extraction/` | `evaluator/decomposer.py` | Keep. Add offsets. Optional later: LLM decomposer behind an interface. |
| `evidence_verification/` | `evaluator/nli_verifier.py`, `span_localizer.py`, `multi_hop.py` | Keep. Wire multi-hop only after a specified fusion policy. Never silently fall back. |
| `citation_analysis/` | `evaluator/citation_parser.py` | Keep parser; rewrite metric definitions. |
| `metrics/` | `evaluator/retrieval_metrics.py` + inline rates in `evaluator.py` | Extract a registry. Do not invent a second scoring path. |
| `experiments/` | `benchmark/` | Add run IDs, config snapshots, non-overwrite storage under `experiments/runs/`. |
| `reporting/` | `benchmark/reporter.py`, `analysis/` | Generate narrative **from numbers**. Quarantine `paper.tex` until results exist. |
| `api/` | `server/` | Keep FastAPI. Do not block on full-suite jobs. |
| `configs/` | missing | Add YAML that deserializes to existing `PipelineConfig`. |
| `tests/` | `tests/` | Extend. |
| `docs/` | missing → created in Phase 0 | Living research + engineering docs. |

**Rename (done):** package, CLI, and product name are **RAGeval** / `rageval`. The published Niu et al. 2024 corpus remains named RAGTruth and is not this repository.

---

## 3. Target runtime architecture

```text
                    YAML PipelineConfig
                            │
Source documents ──► Chunk ──► Embed/Index ──► Retrieve ──► (Rerank) ──► Generate
                                                                      │
Benchmark items (questions, gold spans, gold claims, answerability)   │
                            │                                         ▼
                            │                              Atomic claims + citations
                            │                                         │
                            └──────────────►  Evidence verifier  ◄────┘
                                              (context-bounded)
                                                      │
                                              Metric registry
                                                      │
                              Per-example JSONL  +  run manifest  +  aggregates
```

Contracts already exist as Pydantic models. Extend them; do not replace them.

### 3.1 Stage contracts (existing, to be tightened)

1. **Document → Chunk:** preserve `doc_id`, `chunk_id`, character offsets in the **source document**.
2. **Chunk list → RetrievedChunk:** preserve rank, score, method.
3. **Question + retrieved → answer:** generator must not receive gold labels or `test_type`.
4. **Answer + retrieved → AtomicClaim[]:** each claim has text, source offsets, cited chunk ids.
5. **Claim + evidence pool → ClaimVerification:** label, supporting/contradicting ids, span, method id, optional confidence (null if uncalibrated).
6. **Item + retrieval + verifications → metrics:** named formulas, explicit denominators.

### 3.2 Evaluator isolation (critical)

Primary faithfulness metrics use **only the RAG system’s retrieved context** (plus the answer).  
Evaluator-side extra retrieval, if added later, is a **diagnostic** channel and must be stored under a different metric namespace.

The current NLI verifier already uses retrieved chunks only. Keep that invariant.

### 3.3 Metric registry

Move aggregation out of `RAGEvalEvaluator.evaluate_query` into functions with unit tests:

| Family | Metrics | Source today |
| --- | --- | --- |
| Retrieval | Recall@k, MRR, nDCG@k, noise ratio, latency | `RetrievalMetricsCalculator` |
| Answer-level | correctness vs gold (not implemented), abstention, unsupported-answer rate | partial in evaluator |
| Claim-level | support / unsupported / contradiction rates, coverage | evaluator rates |
| Citation | precision (support-conditioned), completeness | parser (needs redefinition) |
| System | stage latencies, tokens, cost-with-source | evaluator (cost hardcoded) |
| Verifier quality | per-class P/R/F1 vs gold claims | **missing** |

Do not collapse these into one “RAGeval score”.

---

## 4. Dataset architecture

Keep `data/` layout, add explicit layers:

```text
data/
  raw/                      # source documents (current corpus.json remains a smoke fixture)
  gold/                     # questions + gold evidence + gold claims
  adversarial/              # controlled paired perturbations
  manifests/                # dataset_id, version, license, split policy
  cards/                    # human-readable data cards
```

Two corpora, never mixed in reporting:

| Corpus | Role |
| --- | --- |
| **Smoke fixture** (current 8/8 synthetic) | CI, unit tests, demo UI |
| **Benchmark v1** (Phase 2) | Frozen evaluation set with licenses and annotation notes |

Development examples used to tune prompts/thresholds must be disjoint from the frozen test split.

Schema evolution (additive, backward compatible):

- stable `example_id`, `document_id`, `passage_id`
- `answerability`, `scenario_type`
- `source_metadata.{url,license,version}`
- gold claims with allowed labels matching the verifier taxonomy
- optional `split`: `dev` | `test`

Existing `BenchmarkItem` can absorb these via `metadata` first, then first-class fields.

---

## 5. Experiment architecture

Replace “run suite → overwrite `reports/`” with:

```text
experiments/runs/<run_id>/
  config.json          # full PipelineConfig + seeds
  dataset_manifest.json
  environment.json     # python, torch, model ids/revisions, git hash
  predictions.jsonl    # per-example
  metrics.json         # aggregates + CIs when n allows
  errors.jsonl
```

`reports/` becomes derived artifacts of a named run, not the source of truth.

`BenchmarkSuite` already iterates configs. Add: run id, refuse overwrite, optional resume, disable reranker/NLI by flag for CPU smoke.

---

## 6. Verification engine architecture

Keep a single `EvidenceVerifier` protocol implemented by:

1. **NLIVerifier** (current DeBERTa) — primary automated method.
2. **HeuristicVerifier** (current fallback) — tests and ablation only; must be selected explicitly.
3. Later: LLM judge with structured output, behind the same protocol.

Label taxonomy proposal (Phase 1 freeze):

| Label | Meaning |
| --- | --- |
| `supported` | Full support in supplied evidence |
| `partially_supported` | Some constraints match; others missing |
| `unsupported` | No adequate support; not contradicted |
| `contradicted` | Evidence directly refutes the claim |
| `ambiguous` | Evidence insufficient to decide among the above |

Mapping from current enum: `ENTAILEMENT→supported`, `NEUTRAL→unsupported`, `CONTRADICTION→contradicted`. Keep the old enum as a deprecated alias until tests migrate.

Abstention is **not** a claim-support label. Store it on `QueryEvaluationResult.abstained`.

Multi-hop: concatenate complementary premises only when a documented trigger fires; record `verifier_method = "nli_multihop_pair"`.

---

## 7. API architecture (Phase 9, after metrics are valid)

Keep FastAPI. Split:

- **Sync, cheap:** `/health`, `/evaluate/answer` on user-provided context (already exists).
- **Async/job:** `/experiments` for full suites. Do not run `BenchmarkSuite` inside a request thread.
- **Read:** datasets, run manifests, per-example claims.

The static dashboard is useful for claim inspection. Extend it to read run JSONL rather than rebuilding a SPA.

---

## 8. Dependency architecture

Current stack is appropriate: Python, Pydantic v2, PyTorch, sentence-transformers, FAISS CPU, rank-bm25, FastAPI, pytest.

Proposed hygiene (implementation phases, not now):

- Single source of dependencies in `pyproject.toml`.
- Declare `scipy` (used) and `tabulate` (pandas markdown).
- Drop unused `requests`, `pydantic-settings` unless adopted.
- Optional extras: `rageval[bench]` (torch/HF), `rageval[api]`, `rageval[eval-nli]`, so unit tests of metrics can run without MiniLM.
- Never download models inside metric unit tests.

---

## 9. Trade-offs

| Choice | Why | Cost |
| --- | --- | --- |
| Stay on `rageval.*` | Avoids a rewrite of imports, tests, CLI, egg | Product name ≠ import name until a dedicated rename |
| Keep mock generator | Deterministic CI | Must be blinded; cannot support generation-quality claims |
| Keep DeBERTa NLI | Local, deterministic-ish, already cached | Three-way labels only; not human ground truth |
| File JSONL run store | No DB required | Weaker query UX; acceptable through Phase 8 |
| Tiny synthetic fixture retained | Fast tests | Must be labeled “smoke”, never “the benchmark” |
| Delay API job queue | Core validity first | `/benchmark/run` remains unsafe for production until Phase 9 |

---

## 10. Explicit non-goals until later approval

- Rewriting the package as `src/rageval`.
- Training a custom NLI model.
- Large public-dataset downloads (HotpotQA full, FinanceBench corpus) without a Phase 2 plan.
- LLM-as-judge as the primary official metric.
- Decorative dashboard work.
- Claiming SOTA or novelty vs RAGAS / RAGTruth (Niu et al. 2024) / FActScore before a literature review (Phase 1).
