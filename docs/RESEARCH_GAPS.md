# Research Gaps and Threats to Validity

## Status after R5–R7 (2026-10-29)

The Phase 0 list below is **historical**. Closed for the licensed pilot: synthetic-as-SEC disclosure, generator blinding, metric registry, citation support vs existence, answer-level EM/F1, verifier gold set, unique run dirs, `metrics.json` tables, no overall score. `v1_025`–`v1_028` are scored in companion `657c8089`. `v1_029`–`v1_032` are scored in companion `de870a29`. IAA **tooling** (Cohen's kappa) exists; rater B is a disclosed LLM (`rater_b_llm_grok`), not a second human. External answers score via `rageval score`. Live NVIDIA NIM smoke: `20261030T052448Z_6df3afb9` on `smoke_v1`.

**Still blocking confirmatory RAG claims**

- Official published tables remain $n=24$ / 16 documents (`20261028T183042Z_a97ad68f`). Companions: v1.1.0 $n=28$ / 18 documents; v1.2.0 $n=32$ / 21 documents. Still underpowered (confirmatory $n\ge 30$ i.i.d.); items share documents.
- Official generator is a blinded mock, not an LLM. Live NVIDIA NIM smoke `20261030T052448Z_6df3afb9` and companion `20261030T052638Z_79a8b21d` (n=32, faith 0.7188) do not replace `a97ad68f`. External systems can be scored with `rageval score`.
- Single-author gold; disclosed LLM rater B is diagnostic IAA (kappa 0.9423, n=24). Confirmatory IAA still needs an independent human (`data/gold/iaa/STATUS.md`).
- RQ1 Recall@5 is identical across six configs on recorded runs (0.8333 on v1.0.0, 0.8571 on v1.1.0, 0.8438 on v1.2.0). MRR differs on companions; that difference is diagnostic only.
- `paper.tex` is a draft whose table matches the v1.0.0 published run; it is still not a confirmatory paper.

Honest write-ups: `reports/20261028T183042Z_a97ad68f/FINDINGS.md` (published v1.0.0), `reports/20261029T165024Z_657c8089/FINDINGS.md` (companion v1.1.0), `reports/20261029T173408Z_de870a29/FINDINGS.md` (companion v1.2.0).

---

This document originally asked whether the **audit-time** implementation could support credible conclusions. Engineering completeness is covered in `PROJECT_AUDIT.md`.

The intended central question (Phase 1 will refine it):

> Can claim-level evidence verification provide a more informative and reliable assessment of RAG answer quality than answer-level evaluation alone, particularly when answers mix supported, unsupported, and contradicted claims?

Treat that as a **hypothesis**, not a result. Nothing in the repository currently tests it.

---

## 1. Capability matrix vs intended research design

| Capability | Current support | Blocks credible conclusions? |
| --- | --- | --- |
| Fixed evaluation dataset + versioning | 8 synthetic items, no version/license/split | **Yes** |
| Multiple retrieval configurations | Dense / BM25 / hybrid / rerank configs exist | Partial: tiny corpus saturates Recall@k |
| Multiple generation configurations | Mock + unused HTTP adapter | **Yes** for generation claims |
| Claim-level support classification | 3 NLI labels, no partial/ambiguous | Partial |
| Citation-to-claim attribution | Marker→chunk existence only | **Yes** for citation quality claims |
| Contradiction detection | NLI contradiction head + heuristic mock mode | Partial; unvalidated vs gold |
| Unanswerable questions | 2 items; mock sees `test_type` | **Yes** until generator is blinded |
| Conflicting evidence | 1 item; detection = `len(claims) >= 2` | **Yes** |
| Retrieval metrics | Implemented at doc-id level | Partial; no unit tests; no passage-level gold chunk ids |
| Generation / answer correctness | Gold answers stored, unused | **Yes** |
| Latency | `perf_counter` around stages | Partial (includes model load if cold) |
| Monetary cost | Hardcoded OpenAI-like rates on mock tokens | **Yes** if reported as cost |
| Repeated experiments + statistics | Significance helpers exist; n=8, unused on real runs | **Yes** |
| Verifier accuracy vs human/gold claims | Gold claims unused | **Yes** |
| Answer-level vs claim-level comparison | Answer-level metrics missing | **Yes** (this is RQ3) |

---

## 2. Dataset and annotation gaps

### 2.1 Provenance and licensing

Documents are author-written fiction styled as 10-Q / trial / systems papers. That is legitimate as a **synthetic stress set** if disclosed. It is not legitimate to describe them as SEC, NEJM, or OSDI sources.

No license, URL, or reuse terms exist. A public research release requires this even for synthetic text (original authorship + any later imported corpora).

### 2.2 Scale and coverage

Committed evaluation set:

- 8 documents, ~66 tokens mean
- 5 standard, 2 unanswerable, 1 conflicting
- 16 gold claims, all `ENTAILEMENT`
- 0 distractor, 0 outdated-vs-new pairs, 0 multi-document multi-hop items that require two docs (bench_007 cites a single doc), 0 mixed-support gold answers

Missing categories from the master spec: insufficient evidence, outdated vs newer, numerical/date traps, lexical distractors, required abstention with retrieved noise, partial-support gold, instruction-like injected text.

n=8 cannot support ablation ranking, bootstrap CIs, or significance tests that survive multiple comparisons.

### 2.3 Ground truth unused

`gold_atomic_claims` and `gold_answer` never enter scoring. The system measures **NLI self-consistency with retrieved text**, not agreement with annotated support. There is no human-reviewed verifier test set, no IAA, and no documented annotation guide.

Without gold claim labels on **generated** claims (or a fixed candidate set of claims), verifier F1 is undefined.

### 2.4 Leakage and split policy

- No dev/test split.
- Mock generator is conditioned on `item.test_type` and `item.expected_abstention` indirectly via UNANSWERABLE.
- Paper-report prompts and UI presets reuse the same 8 items that appear in the “benchmark”.
- `DatasetLoader.ensure_data_exists()` can regenerate canonical files from Python, so the JSON on disk is not an independent frozen artifact.

---

## 3. Evaluation-validity gaps

### 3.1 Construct: faithfulness vs truth vs usefulness

The NLI verifier estimates **whether a claim is entailed by retrieved passages**. That is context-faithfulness, not world-factuality. README and paper language use “hallucination”, “factual conflict”, and “unreliable AI answers” interchangeably.

This must be frozen in Phase 1 terminology. A supported claim can still be false in the world; an unsupported claim can still be true.

### 3.2 Claim decomposition validity

Regex sentence/conjunction splitting:

- Drops discourse but also can drop hedging (“suggests”, “up to”, “not”).
- Does not record character offsets, so claim↔answer mapping is weak.
- Has not been measured for completeness/over-splitting against human propositions.
- Citation stripping leaves artifacts (`"The test is valid ."`).

If decomposition is unstable, claim-level rates are unstable.

### 3.3 NLI as unvalidated judge

Threats:

- Three-way MNLI labels ≠ the five-way research taxonomy.
- Thresholds 0.50 / 0.60 are uncalibrated (`ConfidenceCalibrator` exists but is unused).
- Committed runs show NLI marking **extractive copies** of source sentences as NEUTRAL or CONTRADICTION (17 claims labeled NEUTRAL/CONTRADICTION vs 5 ENTAILEMENT on Dense configs). If copying the top chunk is not “supported”, the metric does not match the construct.
- Silent heuristic fallback if HF load fails.
- No confusion matrix vs gold.
- Evaluating a claim against the union of chunks by taking max entailment/contradiction independently can both support and contradict; the code then picks a winner, hiding dual-evidence cases.

### 3.4 Citation metrics do not measure attribution quality

Current precision: “bracket points at a retrieved index”.  
Current recall: “sentence contains a bracket”.

A system can cite `[1]` on every sentence, including unsupported ones, and score precision 1.0 and high recall. That cannot answer RQ-style questions about citation correctness.

`misattributed_citations` is a dead field.

### 3.5 Retrieval metrics are saturated and coarse

Gold evidence is a document id + a span string; `chunk_id` is always null. Recall is document-level. On 8 short docs with distinctive named entities, Recall@5 = 0.75 for every config in the committed run. Ablations cannot show retrieval differences, so they cannot test “does better retrieval improve claim support?”

Unanswerable items with empty gold spans treat **any** retrieval as total failure. That confounds “retrieved irrelevant context” with “retrieved the lexically similar but non-answering doc”, which is the interesting case.

### 3.6 Answer-level baseline missing

RQ3 requires an answer-level metric (EM/F1, NLI-on-whole-answer, LLM judge, etc.) on the **same** examples. It is not implemented. Claim-level superiority cannot be shown.

### 3.7 Adversarial measurement is circular

| Scenario | Implementation issue |
| --- | --- |
| Unanswerable | Generator knows the label |
| Conflicting | Detection heuristic is unrelated to contradiction handling |
| Mixed support | Mock `mixed` mode exists but is not in the ablation matrix |
| Hallucination / contradiction modes | Exist on MockGenerator, not used as official baselines |

### 3.8 Reporting validity (fabricated or mismatched results)

This is the most serious integrity gap.

- `reports/paper.tex` table does not match `reports/benchmark_summary.csv`.
- `paper_analysis.md` embeds the CSV and then states findings the CSV falsifies (16.4% Recall@5 lift; >60% hallucination on unanswerables while abstention accuracy = 1.0).
- README describes real filings and a combinatorial scientific study.

Until these artifacts are quarantined or regenerated from code **without canned claims**, the repository cannot be cited as a research result.

### 3.9 Cost, latency, and systems metrics

- Cost uses a single hardcoded price pair with no source timestamp; mock token counts are word splits.
- Latency includes whatever the machine did (NLI load, GC); no warmup/exclusion policy.
- Reranked config shows **lower** mean latency in the CSV than dense configs, which is implausible as a structural finding and likely run-to-run noise or caching. It is nonetheless reported.

---

## 4. Reproducibility gaps

Missing from each run:

- experiment id
- git commit
- dataset version
- model revision hashes
- random seeds (perturbations use `random` globally)
- software freeze / lockfile
- hardware summary
- non-overwrite policy

`NLIVerifier` prints a warning and continues with a different algorithm if weights are missing. Experiments can silently change method.

Python 3.13 local vs CI 3.10–3.12; transformers 5.x locally vs `>=4.40.0` declared.

---

## 5. Literature and novelty gaps

The codebase cites Lewis 2020, RAGAS, DeBERTa, RRF. It does not review:

- **RAGTruth** (Niu et al., 2024) — published claim-level RAG hallucination corpus; this project is now named RAGeval to avoid that collision
- FActScore / SAFE / Factcheck-GPT / RAGAS faithfulness
- Attributed QA, ALCE, citation evaluation (Gao et al.)
- MiniCheck, AlignScore, TRUE, SummaC
- FreshQA, RGB, RAG-Bench, CRAG

Phase 1 must include a short related-work pass so RAGeval’s contribution is stated as **benchmark design + measurement comparison**, not as inventing claim-level RAG evaluation.

---

## 6. Statistical gaps

Even after fixing leakage, n=8 paired observations cannot support:

- ranking six configs
- “significant” Wilcoxon/t-tests at α=0.05 after six comparisons
- subgroup analysis (domain × scenario)

Need: larger frozen set, pre-registered metric list, paired tests with effect sizes and CIs, and honest “inconclusive” language when power is low.

---

## 7. What *can* be studied with current code (narrow)

If we restrict claims to engineering:

- The pipeline can retrieve from a toy corpus and emit claim JSON.
- Regex decomposition + DeBERTa NLI can be **prototype-evaluated** on hand-crafted triples (the existing NLI unit test).
- Citation *format* errors (`[99]` out of range) can be detected.

These are software tests, not RAG reliability findings.

---

## 8. Minimum fixes before any result is reportable

1. Disclose synthetic data; stop describing it as SEC/NEJM/OSDI.
2. Blind generators to gold fields.
3. Stop overwriting and stop emitting canned paper findings.
4. Align `paper.tex` / README with actual numbers or mark them as non-results.
5. Define labels, denominators, and citation metrics in Phase 1.
6. Score predictions against gold claims for verifier quality.
7. Add an answer-level baseline on the same items.
8. Build a versioned dataset large enough for the RQs, with licenses.
9. Record run metadata; forbid silent model fallback.
10. Resolve the RAGeval name collision.
