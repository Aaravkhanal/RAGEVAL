# Implementation Roadmap — RAGeval

Each phase is **approval-gated**. Completing or approving Phase *n* does not authorize Phase *n+1*.

Existing `rageval` modules are the implementation surface. New files are added only when the current module cannot absorb the responsibility.

**Legend**

- Complexity: S (<1 day), M (1–3 days), L (>3 days) of focused engineering, excluding large experiments.
- Compute: None / Local-CPU-light / Local-CPU-models / Optional-API.

---

## Phase 0 — Repository audit

**Status:** Complete in this session (documents only).

**Deliverables:** `docs/PROJECT_AUDIT.md`, `docs/ARCHITECTURE_PROPOSAL.md`, `docs/RESEARCH_GAPS.md`, this file.

**Acceptance:** Maintainer reviews findings and records decisions listed in §Approvals below.

---

## Phase 1 — Research question and benchmark specification

**Objective:** Freeze RQs, hypotheses, terminology, metric formulas, and exclusions **before** expanding data or models.

**Prerequisites:** Phase 0 approved; naming decision (see Approvals).

**Expected deliverables**

- `docs/RESEARCH_SPEC.md` — RQs, hypotheses, IVs/DVs, controls
- `docs/TERMINOLOGY.md` — claim, evidence, faithfulness vs truth, citation precision/completeness, abstention, unreliable answer
- `docs/METRIC_DEFINITIONS.md` — formulas, denominators, edge cases
- `docs/EXPERIMENTAL_DESIGN.md` — baseline matrix, analysis plan
- `docs/RELATED_WORK.md` — short literature note (RAGTruth/Niu 2024, FActScore, ALCE, RAGAS, MiniCheck, CRAG/RGB). No novelty claims without this.

**Files likely to change:** `docs/*` only. Optionally comment-level clarifications in `rageval/core/schemas.py` if we document current enum aliases. **No metric code changes** until formulas are approved.

**Acceptance criteria**

- Each RQ has a falsifiable hypothesis and a stated analysis that could fail.
- Faithfulness is defined as support-by-supplied-evidence, distinct from world truth.
- Citation precision is defined as support-conditioned, not mere ID validity.
- Abstention is excluded from claim-support denominators (or a documented exception exists).
- Official vs diagnostic evaluator retrieval is specified.
- Benchmark exclusions listed (languages, modalities, training a new NLI model, etc.).

**Tests:** none required (spec review).

**Risks:** Over-scoping RQs relative to compute. Mitigate by declaring a **core** RQ set (claim-level vs answer-level; retrieval ablation on a small frozen set; adversarial abstention) and a **stretch** set.

**Compute:** None.

**Proposed core RQs (draft, to refine in Phase 1)**

- RQ1: How do chunking, retriever family, and reranking affect retrieval metrics **and** claim-support rates on a frozen set?
- RQ2: How accurate is the automated claim verifier vs gold labels (per class, including contradiction)?
- RQ3: Do claim-level rates catch mixed-support answers that answer-level scores mark as correct?
- RQ4: How do systems behave on unanswerable and conflicting items when the generator cannot see gold labels?
- RQ5: What are latency (and optional cost) trade-offs among the baseline configs?

---

## Phase 2 — Dataset construction and ground-truth design

**Status:** Complete for the licensed pilot (`benchmark_v1` v1.1.0, 28 items). Expansion toward 50–150 items remains a later increment.

**Objective:** A versioned, licensed, small-but-valid benchmark plus retention of the current 8-item set as `smoke`.

**Prerequisites:** Phase 1 terminology and schema fields approved.

**Expected deliverables**

- Additive schema fields on `BenchmarkItem` / `Document` (ids, license, scenario_type, split).
- `data/manifests/smoke_v1.json` describing the existing synthetic corpus honestly.
- `data/cards/smoke_v1.md`
- Annotation guidelines `docs/ANNOTATION_GUIDELINES.md`
- Validation CLI or `pytest` over schema + referential integrity
- **Benchmark v1** plan: either (a) expand synthetic with documented authorship, or (b) import a **permitted** public slice (e.g. a few HotpotQA/PubMedQA items) with license notes. Start at ~50–150 items, not thousands.

**Files likely to change:** `rageval/core/schemas.py`, `dataset/generator.py`, `dataset/validator.py`, `dataset/loader.py`, `dataset/importers/*`, `data/**`, `tests/test_importers.py`, new `tests/test_dataset_schema.py`

**Acceptance criteria**

- Smoke fixture still loads; README/docs call it synthetic.
- Every document has license + provenance fields.
- Gold spans resolve into source text (validator already approximates this; tighten to verbatim or recorded exception).
- Gold claims exist for standard items; mixed-support and contradiction gold exist for adversarial items.
- Dev vs test split documented; test annotations not used for prompt/threshold tuning.
- No silent dropping of hard items.

**Tests:** schema/integrity tests; importer stub tests remain; forbid network in unit tests.

**Risks:** Scraping without license; over-annotating with a single author (disclose). Importing full HotpotQA is too large and may overlap train corpora of embedders (leakage). Prefer a hand-validated slice.

**Compute:** Local-CPU-light. No full-dataset download without a written size/license note in the Phase 2 proposal.

---

## Phase 3 — RAG baseline pipeline (harden, do not rebuild)

**Status:** Complete for the mock/CPU baseline: YAML ablation configs, sparse-only pipelines skip MiniLM, unique run dirs snapshot YAML, blinded mock, `rageval validate`, `tests/test_pipeline_smoke.py`.

**Objective:** A reproducible, blinded, configurable baseline that can run a **smoke** experiment without API keys.

**Prerequisites:** Phase 2 smoke manifest (can proceed in parallel with benchmark-v1 collection if smoke-only).

**Expected deliverables**

- YAML configs under `configs/` mapping to `PipelineConfig`
- Blind `MockGenerator` (no `test_type` / gold fields)
- Explicit failure if `local_hf`/NLI model missing (no silent heuristic)
- CLI runner that writes `experiments/runs/<id>/` and does not overwrite
- Documented smoke command using the 8-item fixture
- Optional OpenAI-like backend remains opt-in

**Files likely to change:** `pipeline/generator.py`, `pipeline/rag.py`, `core/config.py`, `cli.py`, `benchmark/suite.py`, `benchmark/runner.py`, `benchmark/reporter.py`, new `configs/*.yaml`, `tests/test_pipeline_smoke.py`

**Acceptance criteria**

- `pytest` still green.
- Smoke run produces a run directory with config snapshot + per-example JSON.
- Unanswerable items are **not** auto-abstained via gold labels.
- Dense, BM25, hybrid configs run on smoke set on CPU.
- Reranker config is optional and documented as heavier.
- Chunk size/overlap, top_k, method, temperature are independently settable.

**Tests:** blinded mock (unanswerable item still generates unless the **retrieved text** is empty / prompt policy abstains); config validation; no-overwrite; retrieval on fixture.

**Risks:** Enabling reranker + DeBERTa on every test makes CI slow. Mark tests that load HF as `slow`. Keep metric tests CPU-only.

**Compute:** Local-CPU-models for optional integration test; unit tests Local-CPU-light.

---

## Phase 4 — Claim-level evidence verification engine

**Status:** Complete for the labeled 24-pair pilot. Offset-preserving decomposition, documented 5-way collapse, citation support vs existence, `verifier_eval_v1`, `rageval verifier-eval`. NLI macro-F1 0.692 vs heuristic 0.514 on that set (honest, underpowered).

**Objective:** Make verification traceable, labeled as specified, and measurable against gold.

**Prerequisites:** Phase 1 label set; Phase 2 gold claims (even if only smoke+a small gold set).

**Expected deliverables**

- Offset-preserving decomposition (fill `char_start`/`char_end`)
- Versioned classification schema (new labels or documented mapping)
- Citation verification: valid id, cited chunk actually supports, missing citations, citation of contradicting chunk
- Wire multi-hop fusion **behind a config flag** with method id recorded
- Small human-reviewed claim set (`data/gold/verifier_eval_v1.json`)
- Verifier evaluation report: per-class P/R/F1, confusion matrix
- Failure-case list

**Files likely to change:** `evaluator/decomposer.py`, `nli_verifier.py`, `citation_parser.py`, `evaluator.py`, `multi_hop.py`, `core/schemas.py`, new tests `test_metrics_claims.py`, `test_citation_support.py`

**Acceptance criteria**

- Silent heuristic fallback removed or only active when `verifier.method = "heuristic"`.
- Abstention is not scored as `ENTAILEMENT`.
- Dual support+contradiction evidence is represented, not collapsed without a rule.
- Verifier F1 is computed on the labeled set (results may be poor; report honestly).
- Primary metrics remain context-bounded.

**Tests:** decomposition offsets; label mapping; citation support vs existence; no-fallback default; gold comparison harness on fixtures.

**Risks:** DeBERTa quality on partial support/negation. Do not “fix” this by leaking world knowledge. LLM judge, if added, is a second system under test.

**Compute:** Local-CPU-models for NLI eval (model already cached here).

---

## Phase 5 — Metrics and evaluation framework

**Status:** Complete: `rageval/metrics/registry.py`, hand-computed tests, per-example/aggregate JSON, bootstrap CIs gated on n≥30 and independence, cost null without a pricing source, no overall score.

**Objective:** Central registry with tested formulas.

**Prerequisites:** Phase 1 metric definitions; Phase 4 label outputs.

**Expected deliverables**

- `rageval/metrics/` (or `evaluator/registry.py`) with pure functions
- Unit tests for Recall@k, MRR, nDCG, claim rates, citation precision/completeness, abstention
- Evaluation runner writing per-example + aggregate JSON
- Docs already in `METRIC_DEFINITIONS.md` updated if implementation forced a clarification
- Bootstrap CI only when n and independence assumptions are documented

**Files likely to change:** `evaluator/retrieval_metrics.py`, `evaluator/evaluator.py`, `benchmark/runner.py`, new `tests/test_retrieval_metrics.py`, `tests/test_claim_metrics.py`

**Acceptance criteria**

- Every official metric has a test with a hand-computed example.
- Denominators documented for empty answers, abstentions, unassessable claims.
- No single unexplained scalar “overall score” as the official ranking (composite optional, labeled as such).
- Cost field is `null` unless a pricing source+timestamp is supplied; local runs report latency/tokens.

**Tests:** as above; edge cases (k > retrieved, no gold, all abstain).

**Risks:** Changing citation metric definitions will break current dashboard copy (“citation recall = sentences with brackets”). Update UI strings when metrics change.

**Compute:** None for unit tests.

---

## Phase 6 — Adversarial evaluation and robustness

**Status:** Complete for the reviewed v1.1 adversarial increment (paired HarborNet conflict, empty-context protocol, instruction-like document, numerical/negation, robustness-by-scenario, failure taxonomy). Phase 7 is not authorized by this increment.

**Objective:** Controlled paired scenarios with a failure taxonomy.

**Prerequisites:** Blinded generator; metric registry; at least smoke+adversarial gold.

**Expected deliverables**

- Extended adversarial split using `PerturbationEngine` **plus** hand-checked items
- Paired items (same question, added conflict doc)
- Robustness metrics by `scenario_type`
- `docs/FAILURE_TAXONOMY.md` (dataset / retrieval / generation / decomposition / verifier / citation / eval bug)
- Error analysis template filled for the smoke+v1 adversarial set

**Files likely to change:** `dataset/perturbations.py`, `dataset/generator.py`, `data/adversarial/`, `benchmark/runner.py`, `tests/test_adversarial.py`

**Acceptance criteria**

- Unanswerable, conflicting, lexical distractor, mixed-support, numerical/negation, empty context, instruction-like document text each have ≥1 **reviewed** item.
- Failures attributed to a stage, not only a score drop.
- Mock leakage tests assert that `test_type` is unavailable to the generator.

**Tests:** perturbation determinism with a seed; taxonomy tagging; paired-item loader.

**Compute:** Local-CPU-light; optional NLI.

---

## Phase 7 — Experimental matrix and ablations

**Status:** Complete for the named A–G YAML matrix, `metrics.json` tables, the v1.0.0 recorded-run export, and a companion v1.1.0 six-config mock+NLI export (`20261029T165024Z_657c8089`). `A_chunk` overlap-fixed protocol has not been re-run. Published numbers remain the historical 6-config v1.0.0 snapshot.

**Objective:** A **small** matrix on the frozen set, not a full factorial.

**Prerequisites:** Phases 3–5; dataset v1 or an approved “pilot on smoke” with that limitation in the report title.

**Expected deliverables**

- `configs/experiments/{A_chunk,B_embed,C_retrieve,D_rerank,E_verifier,F_ablate,G_claim_vs_answer}.yaml`
- Runner + manifests
- Result tables labeled **pilot** or **v1** correctly
- No canned narrative

**Suggested first matrix (CPU-practical)**

- Chunk: 128 / 256 / 512, overlap fixed, dense MiniLM, mock or one local gen, rerank off
- Retrieve: dense vs BM25 vs hybrid, chunk 256
- Rerank: on/off for hybrid only
- Verifier: NLI vs heuristic (diagnostic)
- Claim vs answer: on mixed-support items

Embeddings beyond MiniLM and any paid LLM are **opt-in** after a resource note.

**Files likely to change:** `benchmark/suite.py`, `configs/`, `analysis/significance.py` (wire to runs), `analysis/generate_paper_report.py` (delete hardcoded findings)

**Acceptance criteria**

- Each run has id, config, dataset version, git hash, timestamps.
- Interrupted runs cannot clobber completed runs.
- Tables are generated from `metrics.json`.
- If n is small, significance tests are omitted or clearly underpowered.

**Tests:** runner dry-run on 1 item × 2 configs; overwrite protection.

**Compute:** Local-CPU-models. Full 6-config × 8-item historically took seconds-to-minutes of embedding plus NLI per claim. Scaling to 100 items × 6 configs × DeBERTa is still CPU-feasible; reranker + large embedders need approval.

---

## Phase 8 — Statistical analysis and findings

**Status:** Complete for run `20261028T183042Z_a97ad68f`. Phase 9 is not authorized by this increment.

**Objective:** Honest findings from **completed** runs only.

**Prerequisites:** Phase 7 artifacts on disk.

**Expected deliverables**

- `reports/<run_id>/FINDINGS.md`
- Case studies (question, evidence, answer, claims, gold, auto labels)
- Limitations / threats (can reuse `RESEARCH_GAPS.md` updated)
- Figures regenerated from run data
- `paper.tex` updated **or** marked draft-not-results until numbers match

**Files likely to change:** `analysis/*`, `reports/*`, `README.md` claims

**Acceptance criteria**

- Every numerical claim traces to a run id.
- Negative/inconclusive results allowed.
- No “SOTA” language.
- README domain descriptions match actual corpus.

**Tests:** optional snapshot test that the report generator refuses to emit the 16.4% sentence unless computed.

**Compute:** None beyond plotting.

---

## Phase 9 — API, interface, developer experience

**Status:** Complete for dataset/experiment HTTP plus dashboard job UI (P6). `POST /experiments` queues a process-local job; the Experiments tab polls until complete. Live `/evaluate/answer` stays sync. `POST /benchmark/run` returns 410. Full NLI v1 still needs `allow_heavy` or the CLI.

**Objective:** Inspect experiments; do not block HTTP on training-sized jobs.

**Prerequisites:** Core metrics trusted (Phase 5+). Existing FastAPI kept.

**Expected deliverables**

- Job-style experiment start or CLI-only with API read of `experiments/runs/`
- `GET /datasets`, `GET /experiments`, `GET /experiments/{id}/results`
- Dashboard reads run files; dataset tab from API not HTML literals
- OpenAPI + API tests

**Files likely to change:** `server/app.py`, `server/static/index.html`, `tests/test_api.py`

**Acceptance criteria:** `/benchmark/run` is non-blocking or removed; evaluate-on-provided-context remains sync; no secrets in responses.

**Compute:** Local-CPU-light for API tests.

---

## Phase 10 — QA and release candidate

**Status:** Complete for 0.2.0rc1 (`v0.2.0-rc1`). Software **0.2.0** (`v0.2.0`) is jobs, backends, locks, Docker, HF CI. **0.2.1** (`v0.2.1`) adds the dashboard Start-job UI. Fast CI is `pytest -m "not hf"`. Hugging Face tests are a manual/weekly workflow.

**Objective:** Another researcher can reproduce smoke + documented baseline.

**Prerequisites:** At least one complete pilot run with honest reporting.

**Expected deliverables**

- Quickstart + reproducibility guide
- Release checklist
- Optional extras in `pyproject.toml`
- CI: unit tests without HF; optional nightly slow job
- LICENSE, dataset licenses, known limitations
- Version tag `0.2.0-rc` or similar

**Acceptance criteria:** clean extra-env install of a documented extra; `pytest` of fast tests; smoke experiment command; no credentials; reports match runs.

**Compute:** CI minutes; no paid APIs by default.

---

## Cross-cutting rules for all phases

1. Do not overwrite user work; this tree was clean at audit time.
2. Do not commit unless asked.
3. Do not download large models/datasets or call paid APIs without a resource note in that phase’s proposal.
4. Distinguish implemented / tested / pending in every report.
5. Preserve working APIs (`VerificationLabel` spelling, CLI names) until a dedicated migration is approved.

---

## Approvals required before Phase 1 implementation

Record a decision on each item:

1. **Product vs package name.** Keep import `rageval` for now vs rename to `rageval` immediately vs later.
2. **Relationship to published RAGTruth (Niu et al. 2024).** This repo is now **RAGeval**; README and related work must disambiguate.
3. **Phase 1 scope.** Core RQs 1–5 as drafted vs a narrower subset (recommend: RQ2, RQ3, RQ4 as core; RQ1/RQ5 on smoke then v1).
4. **Dataset strategy.** Synthetic-expanded vs licensed public slice vs both (smoke synthetic + small public).
5. **Generator for official baselines.** Blind mock only until a local/OpenAI backend is approved; if OpenAI, budget cap.
6. **Verifier for official labels.** DeBERTa NLI as primary automated metric; heuristic only as ablation; LLM judge later/never.
7. **Label taxonomy.** Adopt five labels now vs keep three and map partial/ambiguous later.
8. **Quarantine of `reports/paper.tex` and canned `paper_analysis.md` findings.** Recommend: banner “not experimental results” in Phase 1 docs, rewrite in Phase 8.
9. **CI policy.** Fast tests without model download vs current heavy `pip install -r requirements.txt` + HF.
10. **Whether Phase 2 may add files under `data/` that replace the current JSON** (recommend: keep current files as smoke, add new versioned files).

---

## Suggested sequence after approval

```text
Phase 1 (spec) ──► Phase 2 (dataset v0.1 + smoke honesty)
                 └──► Phase 3 (blind pipeline + run store) ──► Phase 4 (verifier)
                                                              └──► Phase 5 (metrics)
                                                                   └──► Phase 6–8
                                                                        └──► 9–10
```

Phases 3 and 2 can overlap if Phase 2 first only **documents** the smoke set and defers public-corpus import.

---

## Resource envelope (do not exceed without approval)

| Action | Approx. cost |
| --- | --- |
| Current pytest (models cached) | ~40s CPU, 27 tests, passed 2026-10-28 |
| Cold HF download MiniLM + DeBERTa + MiniLM cross-encoder | hundreds of MB, once |
| Smoke 8 items × 6 configs × NLI | minutes on CPU |
| 100 items × 6 configs × NLI | tens of minutes–a few hours CPU |
| Paid chat APIs | $0 unless OpenAI-like backend enabled |
| Full public HotpotQA / FinanceBench download | large; not in default plan |
