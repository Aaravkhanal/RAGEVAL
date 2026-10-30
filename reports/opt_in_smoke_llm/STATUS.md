# Opt-in live LLM smoke — NVIDIA NIM

**Date:** 2026-10-30  
**Software:** RAGeval 0.2.1  
**Config:** `configs/opt_in/smoke_llm_nvidia.yaml` (`opt_in: true`, NVIDIA NIM OpenAI-compatible HTTP on `smoke_v1`)  
**Run:** `20261030T052448Z_6df3afb9`  
**Model:** `nvidia/nemotron-3.5-bolt-e4b` at `https://integrate.api.nvidia.com/v1`  
**Key:** `NVIDIA_API_KEY` from a gitignored `.env` (never YAML, never git)

This is a **live LLM** generator on the synthetic `smoke_v1` fixture (8 items). It is **not** an official ablation. Official published tables remain blinded-mock run `20261028T183042Z_a97ad68f`.

| Check | Result |
| --- | --- |
| HTTP jobs | refuse `smoke_llm_nvidia` / `opt_in: true` |
| CLI | `--allow-opt-in` required |
| Mock fallback | none |
| NLI silent fallback | none (`method=heuristic`) |
| Cost USD | null (no `pricing_source`) |

Recorded metrics for `OptIn_NVIDIA_NIM` (n=8, independent=false, diagnostic):

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
| mean latency | 1296.76 ms |
| estimated_cost_usd | null |

Unanswerable smoke items (`bench_004_unanswerable`, `bench_005_unanswerable`) abstained with “I do not have sufficient information to answer.” Faithfulness 1.0 on this 8-item synthetic fixture is **not** a publication result.

Live answers were also scored with `rageval score --method heuristic` from `predictions.jsonl` (`external_score_input.jsonl` → `external_scores.jsonl` in the run dir).

How to re-run (CLI only):

```bash
# copy .env.example to .env and set NVIDIA_API_KEY
rageval experiment --config configs/opt_in/smoke_llm_nvidia.yaml --allow-opt-in --output-dir experiments/runs
```

Official published tables remain blinded-mock run `20261028T183042Z_a97ad68f`. Companion mock+NLI: `20261029T165024Z_657c8089` (v1.1.0), `20261029T173408Z_de870a29` (v1.2.0), `20261029T173515Z_7e2b94a3` (A_chunk overlap-32). Live NVIDIA NIM on `benchmark_v1` 1.2.0: `20261030T052638Z_79a8b21d`.
