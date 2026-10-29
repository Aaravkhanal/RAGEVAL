# Phase 7 tables

**Label:** `v1`  
**Source run:** `20261028T183042Z_a97ad68f` (`benchmark_v1` 1.0.0, 16 documents, 24 items)  
**Generator:** blinded mock  
**Verifier:** DeBERTa NLI  

`v1_matrix/metrics.json` was **exported** from that recorded run. No new NLI or embedding scores were computed for Phase 7.

Named YAML in `configs/experiments/` (A–G) is the protocol for future runs. `A_chunk.yaml` fixes overlap at 32; the recorded dense configs used overlap 16/32/64. Do not treat the YAML as if it produced these numbers.

`significance.json` compares each config to `Dense_Chunk256_Baseline`. n=24, so `underpowered=true` and `is_significant=false` even when a raw paired t-test p-value is below 0.05.

G (claim vs answer) is `v1_matrix/G_claim_vs_answer.md` from the mixed-support slice (n=4).
