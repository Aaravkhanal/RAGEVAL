# Findings — run `20261030T055224Z_388c5503`

**Label:** `pilot`. **Dataset:** `benchmark_v1` 1.2.0, n=32, 21 documents.
**Source:** `metrics.json` for run `20261030T055224Z_388c5503`.
Every number below traces to that run. No overall score. No ranking claim.

## What this run is

- Generator: live NVIDIA NIM `nvidia/nemotron-3.5-bolt-e4b` via OpenAI-compatible HTTP.
- Retrievers: dense MiniLM and hybrid RRF, top_k=5, chunk 256/32. Two configs.
- Verifier: DeBERTa-v3 NLI (`allow_heuristic_fallback=false`).
- Sparse live NVIDIA companion is `20261030T052638Z_79a8b21d` (faith 0.7188, MRR 0.7812).
- Cost: null. CLI `--allow-opt-in`. HTTP jobs refuse this YAML.
- Companion only. Official published tables remain `20261028T183042Z_a97ad68f`.
- Items share documents. Diagnostic.

## Recorded metrics

| config | claim_support_rate | Recall@5 | MRR | answer F1 | abstention | latency ms |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| OptIn_NVIDIA_NIM_Dense_NLI | 0.7396 | 0.8438 | 0.7344 | 0.7465 | 1.0 | 1331.5056 |
| OptIn_NVIDIA_NIM_Hybrid_NLI | 0.6458 | 0.8438 | 0.75 | 0.746 | 1.0 | 1342.9362 |
| OptIn_NVIDIA_NIM_NLI (sparse, `79a8b21d`) | 0.7188 | 0.8438 | 0.7812 | 0.7705 | 1.0 | 1885.1472 |

Recall@5 is identical at 0.8438 on all three live retrievers, matching the mock six-config companion on this corpus. MRR matches the mock family on this corpus (dense 0.7344, hybrid 0.75, sparse 0.7812). Claim support moved: dense 0.7396, sparse 0.7188, hybrid 0.6458. Hybrid also has contradiction_rate 0.0312. Those faith differences are diagnostic (n=32, items share documents, not a ranking).

Abstention accuracy is 1.0 on both configs in this run.

Tables: `reports/phase7/nvidia_nim_retrieve/`.
