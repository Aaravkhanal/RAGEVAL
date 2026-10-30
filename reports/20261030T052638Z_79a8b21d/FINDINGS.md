# Findings — run `20261030T052638Z_79a8b21d`

**Label:** `pilot`. **Dataset:** `benchmark_v1` 1.2.0, n=32, 21 documents.
**Source:** `metrics.json` for run `20261030T052638Z_79a8b21d`.
Every number below traces to that run. No overall score. No ranking claim.

## What this run is

- Generator: live NVIDIA NIM `nvidia/nemotron-3.5-bolt-e4b` via OpenAI-compatible HTTP (`https://integrate.api.nvidia.com/v1`).
- Retriever: sparse BM25, top_k=5, chunk 256/32. One config, not the six-config ablation.
- Verifier: DeBERTa-v3 NLI (`allow_heuristic_fallback=false`).
- Cost: null (no `pricing_source`).
- Config is `opt_in: true`. CLI required `--allow-opt-in`. HTTP jobs refuse this YAML.
- There is no mock fallback.
- Companion to the published v1.0.0 tables (`20261028T183042Z_a97ad68f`). It does **not** replace them.
- Items share documents, so they are not i.i.d. Bootstrap CIs are diagnostic. n=32 with `independent=False`.

## Recorded metrics (`OptIn_NVIDIA_NIM_NLI`)

| Metric | Mean |
| --- | --- |
| claim_support_rate | 0.7188 |
| unsupported_claim_rate | 0.2812 |
| contradiction_rate | 0.0 |
| Recall@5 | 0.8438 |
| MRR | 0.7812 |
| citation existence precision | 1.0 |
| citation support precision | 0.7188 |
| answer EM | 0.1875 |
| answer F1 | 0.7705 |
| abstention accuracy | 1.0 |
| mean latency | 1885.1472 ms |
| estimated_cost_usd | null |

Recall@5 0.8438 matches the six-config mock+NLI companion on the same 1.2.0 corpus (`20261029T173408Z_de870a29`). Sparse mock MRR on that run was also 0.7812. Claim support on that mock sparse row was 0.4219; this live generator scored 0.7188. That difference is diagnostic (different generator, one config, items share documents).

## Abstention

All six unanswerable / empty-context items abstained (`v1_013`, `v1_014`, `v1_015`, `v1_016`, `v1_026`, `v1_032`). Ablation mock abstention accuracy on the same corpus was 0.1667 (only empty-context `v1_026` abstained).

## New 1.2.0 items vs this generator

| id | claim_support_rate | abstained |
| --- | --- | --- |
| v1_029 | 0.5 | false |
| v1_030 | 0.3333 | false |
| v1_031 | 0.5 | false |
| v1_032 | 1.0 | true |

## What this does not show

- It is not a six-config RAG ranking.
- It does not replace `a97ad68f` / `v1_matrix` / `v1_1_matrix` / `v1_2_matrix`.
- RQ1 is still not identifiable from recorded mock runs (Recall@5 tied). This run has a single sparse config.
- Cost stays null until documented USD/million prices and `pricing_source` are set.

Tables: `reports/phase7/nvidia_nim_v1/`.
