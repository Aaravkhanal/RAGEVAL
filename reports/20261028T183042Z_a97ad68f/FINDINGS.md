# Findings — run `20261028T183042Z_a97ad68f`

**Label:** `v1`. **Dataset:** `benchmark_v1` 1.0.0, n=24.
**Source:** `metrics.json` for run `20261028T183042Z_a97ad68f`.
Every number below traces to that run or to a named companion file.
Negative and inconclusive results are in scope. No overall score. No ranking claim.

## What this run is

- Generator: blinded mock (`faithful`, abstain only on empty retrieval).
- Verifier: DeBERTa-v3 NLI (`allow_heuristic_fallback=false`).
- Cost: null (no pricing_source).
- Items share documents, so they are not i.i.d. Bootstrap CIs are diagnostic.
- Confirmatory tests require n≥30 i.i.d. This run has n=24.

## RQ1 — retrieval family, chunk size, rerank

- Recall@5 is **identical** at 0.8333 on all 6 configs (run `20261028T183042Z_a97ad68f`). The RQ1 hypothesis that hybrid RRF improves Recall@5 vs dense-only is **falsified on this corpus** (the means are equal).
- MRR is identical at 0.8125.
- Claim support (faithfulness) is 0.4375 on Dense_Chunk256_Baseline, 0.5625 on Hybrid_RRF_Chunk256, and 0.5833 on Hybrid_RRF_Reranked.
- Computed relative Recall@5 lift, Hybrid_RRF_Chunk256 vs Dense_Chunk256_Baseline: 0.0%.
- Significance vs baseline is in `reports/phase7/v1_matrix/significance.json`. All comparisons have `underpowered=true` and `is_significant=false`.
- **Conclusion:** RQ1 retrieval differences are **not identifiable** at this n and corpus size.

## RQ2 — verifier vs gold claims

- Not scored inside the ablation run. Companion file `reports/verifier_eval_v1.md` (24 labeled claim–premise pairs): DeBERTa macro-F1 **0.6921**, lexical heuristic **0.5140**.
- On that set the RQ2 hypothesis (NLI macro-F1 > heuristic) is **not falsified**.
- Partial-support F1 is 0.0 for both methods. n=24 is underpowered.

## RQ3 — claim-level vs answer-level on mixed-support

- Mixed-support slice n=4 per config (run `20261028T183042Z_a97ad68f`).
- Token F1 is identical at 0.6292 across configs, while claim support ranges 0.375–0.625.
- That is the RQ3 pattern on this slice: answer-level F1 does not move; claim support does. n=4 is too small to confirm the hypothesis beyond this pilot.

## RQ4 — unanswerable / conflicting under a blinded generator

- Ablation abstention accuracy is **0.0** on all configs (run `20261028T183042Z_a97ad68f`).
- Unanswerable items still retrieved context; the mock copies sentences and does not see `test_type` (`tests/test_generator_blind.py`).
- A pre-blind historical smoke run had abstention 1.0 because the mock saw UNANSWERABLE. After blinding, abstention on v1 unanswerables is 0.0. That matches RQ4: gold-label leakage was driving abstention.
- Conflicting items: the mock copies one retrieved document and does not hedge (see case `v1_017`).

## RQ5 — latency and cost

- Mean latency (ms): Dense_Chunk128=2571.6, Dense_Chunk256_Baseline=2349.1, Dense_Chunk512=2857.6, Sparse_BM25_Chunk256=2471.7, Hybrid_RRF_Chunk256=2192.4, Hybrid_RRF_Reranked=1590.4.
- Hybrid_RRF_Reranked mean latency (1590.4237) is **lower** than Dense_Chunk256_Baseline (2349.0862) in this snapshot. The RQ5 hypothesis that reranking increases latency is **not supported** here (likely caching / shared evaluator load, not a structural ranking).
- `estimated_cost_usd` is null. Do not report a dollar cost for this run.

## Case studies

Config: `Dense_Chunk256_Baseline` unless noted. Answers are mock extracts.

### `v1_001` — standard

- Question: When did Apollo 11 launch, and who were the three crew members?
- Gold: Apollo 11 launched from Cape Kennedy on July 16, 1969, carrying Neil Armstrong, Michael Collins, and Edwin "Buzz" Aldrin.
- Answer excerpt: The primary objective of Apollo 11 was to complete a national goal set by President John F. [1] Kennedy on May 25, 1961: perform a crewed lunar landing and return to Earth. [2]
- Auto labels: claim1 contradicted; claim2 supported (NLI). Decomposition split "John F. Kennedy" across two claims.
- Metrics: claim_support=0.5, answer_f1=0.2041, abstained=False, recall@5=1.0
- Stage: decomposition — Gold launch/crew facts are in the retrieved NASA excerpt; the mock copied the objective sentence and the decomposer split a name, so NLI contradicted a fragment.

### `v1_013` — unanswerable

- Question: What meals did the Apollo 11 crew eat during translunar coast?
- Gold: (null; expected abstention)
- Answer excerpt: Partially piloted manually by Armstrong, the Eagle landed in the Sea of Tranquility...
- Auto labels: contradicted + supported on landing sentences; abstained=false
- Metrics: claim_support=0.5, answer_f1=0.0, abstained=False, recall@5=0.0
- Stage: retrieval then generation — No gold documents. Retriever returned landing text; blinded mock copied it instead of abstaining.

### `v1_017` — conflicting

- Question: Did CedarRail operate unsupervised light-rail cars in Tacoma without licensed operators?
- Gold: Sources conflict. The press note says CedarRail opened unsupervised service with 40 driverless cars. The Pierce County audit required a licensed operator in every cab and suspended unsupervised service.
- Answer excerpt: CedarRail opened unsupervised light-rail service in Tacoma in March 2025 with 40 driverless cars running 20 hours per day and zero passenger injuries in the first 60 days. [1]
- Auto labels: single claim contradicted (NLI against the joint pool that includes the audit)
- Metrics: claim_support=0.0, answer_f1=0.3704, abstained=False, recall@5=1.0
- Stage: generation — Both conflict docs were retrieved. The mock copied only the press note and did not state the conflict.

### `v1_019` — mixed_support

- Question: Which influenza virus types cause seasonal epidemics in people in the United States?
- Gold: Influenza A and B viruses cause seasonal epidemics of disease in people almost every winter in the United States.
- Answer excerpt: There are four types of influenza viruses: A, B, C, and D. [1] Influenza A and B viruses cause seasonal epidemics... [2]
- Auto labels: lead sentence contradicted; epidemic sentence supported
- Metrics: claim_support=0.5, answer_f1=0.6667, abstained=False, recall@5=1.0
- Stage: generation — RQ3: token F1 stays high (0.6667) while claim support is 0.5.

### `v1_023` — distractor

- Question: What was HarborNet monthly churn in Q2 2025?
- Gold: Monthly churn was 1.8%.
- Answer excerpt: For Q3 2025 HarborNet expects subscription revenue of $420 million to $428 million and monthly churn at or below 1.9%. [1]
- Auto labels: both claims supported by the Q3 guidance chunk
- Metrics: claim_support=1.0, answer_f1=0.1111, abstained=False, recall@5=1.0
- Stage: retrieval then generation — Retriever ranked Q3 guidance above Q2 (MRR 0.5 on this item in Dense_Chunk128; here top doc is guidance). Claim support is 1.0 against retrieved text while answer F1 vs Q2 gold is 0.1111.

## Limitations

- Mock generator, not an LLM.
- n=24 items / 16 documents; v1.1.0 items `v1_025`–`v1_028` are unscored.
- Single-author gold. No IAA.
- Dense chunk overlap in this run was 16/32/64, not the Phase 7 A_chunk fixed-32 protocol.
- Faithfulness is support-by-retrieved-evidence, not world truth.
- This project is not Niu et al. 2024 RAGTruth.

## Files

- Run id: `20261028T183042Z_a97ad68f`
- Tables: `reports/phase7/v1_matrix/metrics.json`
- Errors: `reports/error_analysis_phase6.md`
- RQ2: `reports/verifier_eval_v1.md`
