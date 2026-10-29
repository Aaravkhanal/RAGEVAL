# Findings — run `20261029T173408Z_de870a29`

**Label:** `v1`. **Dataset:** `benchmark_v1` 1.2.0, n=32, 21 documents.
**Source:** `metrics.json` for run `20261029T173408Z_de870a29`.
Every number below traces to that run or to a named companion file.
Negative and inconclusive results are in scope. No overall score. No ranking claim.

## What this run is

- Generator: blinded mock (`faithful`, abstain only on empty retrieval).
- Verifier: DeBERTa-v3 NLI (`allow_heuristic_fallback=false`).
- Cost: null (no pricing_source).
- Items share documents, so they are not i.i.d. Bootstrap CIs are diagnostic.
- Confirmatory tests require n≥30 i.i.d. This run has n=32.
- Companion to the published v1.0.0 tables (`20261028T183042Z_a97ad68f`). It does not replace them.

## RQ1 — retrieval family, chunk size, rerank

- Recall@5 is **identical** at 0.8438 on all 6 configs (run `20261029T173408Z_de870a29`). The RQ1 hypothesis that hybrid RRF improves Recall@5 vs dense-only is **falsified on this corpus** (the means are equal).
- MRR by config: Dense_Chunk128=0.7344, Dense_Chunk256_Baseline=0.7344, Dense_Chunk512=0.7344, Sparse_BM25_Chunk256=0.7812, Hybrid_RRF_Chunk256=0.75, Hybrid_RRF_Reranked=0.776.
- Claim support (faithfulness) is 0.401 on Dense_Chunk256_Baseline, 0.4635 on Hybrid_RRF_Chunk256, 0.4583 on Hybrid_RRF_Reranked.
- Computed relative Recall@5 lift, Hybrid_RRF_Chunk256 vs Dense_Chunk256_Baseline: 0.0%.
- Significance vs baseline is in `reports/phase7/v1_2_matrix/significance.json`. Comparisons stay diagnostic unless n≥30 i.i.d.; recorded items share documents, so `underpowered=true` and `is_significant=false`.
- **Conclusion:** Recall@5 remains identical, so an RQ1 Recall@5 ranking is still not identifiable. MRR differs across configs; n is underpowered and items share documents, so that difference is diagnostic only.

## RQ2 — verifier vs gold claims

- Not scored inside the ablation run. Companion file `reports/verifier_eval_v1.md` (24 labeled claim–premise pairs): DeBERTa macro-F1 **0.6921**, lexical heuristic **0.5140**.
- On that set the RQ2 hypothesis (NLI macro-F1 > heuristic) is **not falsified**.
- Partial-support F1 is 0.0 for both methods. n=24 is underpowered.

## RQ3 — claim-level vs answer-level on mixed-support

- Mixed-support slice n=4 per config (run `20261029T173408Z_de870a29`).
- Mixed-support token F1 also differs across configs. n=4 is too small to confirm RQ3 beyond this pilot.

## RQ4 — unanswerable / conflicting under a blinded generator

- Ablation abstention accuracy is **0.1667** on all 6 configs (run `20261029T173408Z_de870a29`).
- Empty-context slice n=1: retrieval is dropped before generate (recall@5=1.0); mock abstention_accuracy=1.0.
- Other unanswerable items still retrieve context; the mock copies sentences and does not see `test_type` (`tests/test_generator_blind.py`).
- A pre-blind historical smoke run had abstention 1.0 because the mock saw UNANSWERABLE. Gold-label leakage was driving that abstention.
- Conflicting items: the mock copies one retrieved document and does not hedge (see case `v1_017` when present).

## RQ5 — latency and cost

- Mean latency (ms): Dense_Chunk128=1902.5, Dense_Chunk256_Baseline=1754.6, Dense_Chunk512=1848.9, Sparse_BM25_Chunk256=1671.7, Hybrid_RRF_Chunk256=1918.0, Hybrid_RRF_Reranked=1759.5.
- `estimated_cost_usd` is null. Do not report a dollar cost for this run.

## Case studies

Config: `Dense_Chunk256_Baseline` unless noted. Answers are mock extracts.

_No case_studies.json supplied._

## Limitations

- Mock generator, not an LLM.
- n=32 items / 21 documents. Still underpowered (confirmatory n≥30 i.i.d.).
- Single-author gold. No IAA.
- Dense chunk overlap in this run was 16/32/64, not the Phase 7 A_chunk fixed-32 protocol.
- Faithfulness is support-by-retrieved-evidence, not world truth.
- This project is not Niu et al. 2024 RAGTruth.

## Files

- Run id: `20261029T173408Z_de870a29`
- Tables: `reports/phase7/v1_2_matrix/metrics.json`
- Errors: `reports/error_analysis_v1_2.md`
- RQ2: `reports/verifier_eval_v1.md`
