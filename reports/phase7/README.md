# Phase 7 tables

**Published (v1.0.0):** `v1_matrix/` from run `20261028T183042Z_a97ad68f` (`benchmark_v1` 1.0.0, 16 documents, 24 items), blinded mock + DeBERTa NLI.

**Companion (v1.1.0):** `v1_1_matrix/` from run `20261029T165024Z_657c8089` (`benchmark_v1` 1.1.0, 18 documents, 28 items), same six-config matrix (overlap 16/32/64). This does not replace `v1_matrix/`. Current on-disk corpus is v1.2.0; `v1_029`–`v1_032` are unscored here.

Named YAML in `configs/experiments/` (A–G) is the protocol for future runs. `A_chunk.yaml` fixes overlap at 32; both recorded dense configs used overlap 16/32/64. Do not treat the YAML as if it produced these numbers.

`significance.json` compares each config to `Dense_Chunk256_Baseline`. n<30, so `underpowered=true` and `is_significant=false` even when a raw paired t-test p-value is below 0.05.

G (claim vs answer) is `G_claim_vs_answer.md` in each snapshot from the mixed-support slice (n=4).
