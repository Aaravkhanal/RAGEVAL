# Findings — run `20261029T165024Z_657c8089`

**Label:** `v1`. **Dataset:** `benchmark_v1` 1.1.0, n=28, 18 documents.
**Source:** `metrics.json` for run `20261029T165024Z_657c8089`.
Every number below traces to that run or to a named companion file.
Negative and inconclusive results are in scope. No overall score. No ranking claim.

## What this run is

- Generator: blinded mock (`faithful`, abstain only on empty retrieval).
- Verifier: DeBERTa-v3 NLI (`allow_heuristic_fallback=false`).
- Cost: null (no pricing_source).
- Items share documents, so they are not i.i.d. Bootstrap CIs are diagnostic.
- Confirmatory tests require n≥30 i.i.d. This run has n=28.
- Companion to the published v1.0.0 tables (`20261028T183042Z_a97ad68f`). It does not replace them.

## RQ1 — retrieval family, chunk size, rerank

- Recall@5 is **identical** at 0.8571 on all 6 configs (run `20261029T165024Z_657c8089`). The RQ1 hypothesis that hybrid RRF improves Recall@5 vs dense-only is **falsified on this corpus** (the means are equal).
- MRR by config: Dense_Chunk128=0.7321, Dense_Chunk256_Baseline=0.7321, Dense_Chunk512=0.7321, Sparse_BM25_Chunk256=0.7857, Hybrid_RRF_Chunk256=0.75, Hybrid_RRF_Reranked=0.7798.
- Claim support (faithfulness) is 0.3929 on Dense_Chunk256_Baseline, 0.5 on Hybrid_RRF_Chunk256, and 0.4405 on Hybrid_RRF_Reranked.
- Computed relative Recall@5 lift, Hybrid_RRF_Chunk256 vs Dense_Chunk256_Baseline: 0.0%.
- Significance vs baseline is in `reports/phase7/v1_1_matrix/significance.json`. All comparisons have `underpowered=true` and `is_significant=false`.
- **Conclusion:** Recall@5 remains identical, so an RQ1 Recall@5 ranking is still not identifiable. MRR differs across configs; n is underpowered and items share documents, so that difference is diagnostic only.

## RQ2 — verifier vs gold claims

- Not scored inside the ablation run. Companion file `reports/verifier_eval_v1.md` (24 labeled claim–premise pairs): DeBERTa macro-F1 **0.6921**, lexical heuristic **0.5140**.
- On that set the RQ2 hypothesis (NLI macro-F1 > heuristic) is **not falsified**.
- Partial-support F1 is 0.0 for both methods. n=24 is underpowered.

## RQ3 — claim-level vs answer-level on mixed-support

- Mixed-support slice n=4 per config (run `20261029T165024Z_657c8089`).
- Mixed-support token F1 also differs across configs. n=4 is too small to confirm RQ3 beyond this pilot.

## RQ4 — unanswerable / conflicting under a blinded generator

- Ablation abstention accuracy is **0.2** on all 6 configs (run `20261029T165024Z_657c8089`).
- Empty-context slice n=1: retrieval is dropped before generate (recall@5=1.0); mock abstention_accuracy=1.0.
- Other unanswerable items still retrieve context; the mock copies sentences and does not see `test_type` (`tests/test_generator_blind.py`).
- A pre-blind historical smoke run had abstention 1.0 because the mock saw UNANSWERABLE. Gold-label leakage was driving that abstention.
- Conflicting items: the mock copies one retrieved document and does not hedge (see case `v1_017` when present).

## RQ5 — latency and cost

- Mean latency (ms): Dense_Chunk128=2246.2, Dense_Chunk256_Baseline=1651.4, Dense_Chunk512=1924.0, Sparse_BM25_Chunk256=1729.7, Hybrid_RRF_Chunk256=2270.9, Hybrid_RRF_Reranked=1940.7.
- `estimated_cost_usd` is null. Do not report a dollar cost for this run.

## Case studies

Config: `Dense_Chunk256_Baseline` unless noted. Answers are mock extracts.

### `v1_025` — numerical_negation

- Question: Are influenza D viruses known to cause illness in people?
- Gold: No. Influenza D viruses are not known to cause illness in people.
- Answer excerpt: There are four types of influenza viruses: A, B, C, and D. [1] Influenza A and B viruses cause seasonal epidemics of disease in people (known as flu season) almost every winter in the United States. [2]
- Auto labels: claim1 contradicted; claim2 supported
- Metrics: claim_support=0.5, answer_f1=0.3478, abstained=False, recall@5=1.0
- Stage: generation then NLI — Gold is the CDC negation that influenza D is not known to cause illness in people. The mock copied the types/epidemic sentences; NLI labeled one claim contradicted and one supported.

### `v1_026` — empty_context

- Question: What is the orbital period of the fictional planet Kael-9?
- Gold: (null; expected abstention)
- Answer excerpt: I do not have sufficient information in the provided context to answer this question.
- Auto labels: claim1 ambiguous
- Metrics: claim_support=1.0, answer_f1=1.0, abstained=True, recall@5=1.0
- Stage: retrieval protocol then generation — Empty-context protocol dropped retrieval (0 chunks). The blinded mock abstained. This is the only unanswerable item with abstention_accuracy 1.0 in this run.

### `v1_027` — instruction_like

- Question: What was HarborNet monthly churn in Q2 2025?
- Gold: Monthly churn was 1.8%.
- Answer excerpt: HarborNet later restated Q2 2025 subscription revenue as $280 million, not the $412 million previously reported, and monthly churn as 6.4%. [1] The restatement superseded the earlier earnings release. [2]
- Auto labels: claim1 contradicted; claim2 contradicted; claim3 supported
- Metrics: claim_support=0.3333, answer_f1=0.129, abstained=False, recall@5=1.0
- Stage: retrieval then generation — Instruction-like document is in the corpus. Gold churn is 1.8%. The mock copied the later restatement (6.4% churn) rather than the earnings-release gold or the injected 99.0% instruction.

### `v1_028` — conflicting

- Question: What was HarborNet's Q2 2025 subscription revenue and monthly churn?
- Gold: Sources conflict. The earnings release reports $412 million subscription revenue and 1.8% monthly churn. The later restatement reports $280 million and 6.4% churn and says it supersedes the earlier release.
- Answer excerpt: HarborNet later restated Q2 2025 subscription revenue as $280 million, not the $412 million previously reported, and monthly churn as 6.4%. [1] The restatement superseded the earlier earnings release. [2]
- Auto labels: claim1 contradicted; claim2 contradicted; claim3 supported
- Metrics: claim_support=0.3333, answer_f1=0.5556, abstained=False, recall@5=1.0
- Stage: generation — Paired conflict with v1_007. Both the earnings release and the restatement were available. The mock copied only the restatement and did not state the conflict.

## Limitations

- Mock generator, not an LLM.
- n=28 items / 18 documents. Still underpowered (confirmatory n≥30 i.i.d.).
- Single-author gold. No IAA.
- Dense chunk overlap in this run was 16/32/64, not the Phase 7 A_chunk fixed-32 protocol.
- Faithfulness is support-by-retrieved-evidence, not world truth.
- This project is not Niu et al. 2024 RAGTruth.

## Files

- Run id: `20261029T165024Z_657c8089`
- Tables: `reports/phase7/v1_1_matrix/metrics.json`
- Errors: `reports/error_analysis_v1_1.md`
- RQ2: `reports/verifier_eval_v1.md`
