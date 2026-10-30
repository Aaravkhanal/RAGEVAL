# Findings — run `20261030T052448Z_6df3afb9`

**Label:** `pilot`. **Dataset:** `smoke_v1` 1.0.0, n=8, 8 documents.
**Source:** `metrics.json` for run `20261030T052448Z_6df3afb9`.
Every number below traces to that run. This is a synthetic CI fixture, not a publication result. No overall score. No ranking claim.

## What this run is

- Generator: live NVIDIA NIM `nvidia/nemotron-3.5-bolt-e4b` via OpenAI-compatible HTTP (`https://integrate.api.nvidia.com/v1`).
- Retriever: sparse BM25, top_k=5, chunk 256/32.
- Verifier: lexical heuristic (`allow_heuristic_fallback=false`).
- Cost: null (no `pricing_source`).
- Config is `opt_in: true`. CLI required `--allow-opt-in`. HTTP jobs refuse this YAML.
- There is no mock fallback. Official published tables remain blinded-mock run `20261028T183042Z_a97ad68f`.

## Recorded metrics (`OptIn_NVIDIA_NIM`)

| Metric | Mean |
| --- | --- |
| claim_support_rate | 1.0 |
| unsupported_claim_rate | 0.0 |
| contradiction_rate | 0.0 |
| Recall@5 | 0.75 |
| MRR | 0.75 |
| answer EM | 0.25 |
| answer F1 | 0.781 |
| abstention accuracy | 1.0 |
| mean latency | 1296.7575 ms |
| estimated_cost_usd | null |

Unanswerable items `bench_004_unanswerable` and `bench_005_unanswerable` abstained. Faithfulness 1.0 on eight synthetic items is expected when the model copies retrieved text; it does not license a RAG ranking.

See `STATUS.md` in this folder. Companion mock+NLI tables are unchanged.
