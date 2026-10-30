# Run comparison: `Sparse_BM25_Chunk256` vs `OptIn_NVIDIA_NIM_NLI`

Left: blinded mock + DeBERTa, `Sparse_BM25_Chunk256`, run `20261029T173408Z_de870a29`.
Right: live NVIDIA NIM `nvidia/nemotron-3.5-bolt-e4b` + DeBERTa, `OptIn_NVIDIA_NIM_NLI`, run `20261030T052638Z_79a8b21d`.
Official published tables remain `20261028T183042Z_a97ad68f`.

Diagnostic per-item comparison. Items that share documents are not i.i.d. This is not a confirmatory ranking.

**Shared items:** 32.
**Mean Δ claim_support_rate (right − left):** 0.2969.
**Faith improved:** 19. **Worsened:** 7.

**Abstained on the right only:** `v1_013`, `v1_014`, `v1_015`, `v1_016`, `v1_032`.

**Lower claim support on the right:** `v1_003`, `v1_005`, `v1_006`, `v1_019`, `v1_024`, `v1_025`, `v1_029`.

| id | scenario | left faith | right faith | Δ faith | left F1 | right F1 | left abstain | right abstain |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| `v1_001` | standard | 0.5 | 0.6667 | 0.1667 | 0.2041 | 0.7347 | False | False |
| `v1_002` | standard | 0.5 | 1.0 | 0.5 | 0.6667 | 0.9804 | False | False |
| `v1_003` | standard | 0.5 | 0.0 | -0.5 | 0.6667 | 0.9714 | False | False |
| `v1_004` | standard | 0.5 | 0.5 | 0.0 | 0.3571 | 0.913 | False | False |
| `v1_005` | standard | 0.5 | 0.0 | -0.5 | 0.6545 | 0.6875 | False | False |
| `v1_006` | standard | 0.5 | 0.0 | -0.5 | 0.0 | 0.3333 | False | False |
| `v1_007` | standard | 0.3333 | 1.0 | 0.6667 | 0.5238 | 0.2 | False | False |
| `v1_008` | standard | 1.0 | 1.0 | 0.0 | 0.5882 | 0.8333 | False | False |
| `v1_009` | standard | 0.5 | 1.0 | 0.5 | 0.6341 | 0.7429 | False | False |
| `v1_010` | standard | 1.0 | 1.0 | 0.0 | 0.7083 | 0.85 | False | False |
| `v1_011` | standard | 0.0 | 0.5 | 0.5 | 0.4444 | 0.7179 | False | False |
| `v1_012` | standard | 0.5 | 1.0 | 0.5 | 0.5778 | 0.963 | False | False |
| `v1_013` | unanswerable | 0.5 | 1.0 | 0.5 | 0.0 | 1.0 | False | True |
| `v1_014` | unanswerable | 0.0 | 1.0 | 1.0 | 0.0 | 1.0 | False | True |
| `v1_015` | unanswerable | 0.5 | 1.0 | 0.5 | 0.0 | 1.0 | False | True |
| `v1_016` | unanswerable | 0.0 | 1.0 | 1.0 | 0.0 | 1.0 | False | True |
| `v1_017` | conflicting | 0.0 | 1.0 | 1.0 | 0.3704 | 0.5067 | False | False |
| `v1_018` | conflicting | 1.0 | 1.0 | 0.0 | 0.4667 | 0.6486 | False | False |
| `v1_019` | mixed_support | 0.5 | 0.0 | -0.5 | 0.6667 | 0.9714 | False | False |
| `v1_020` | mixed_support | 0.5 | 1.0 | 0.5 | 0.6667 | 0.9804 | False | False |
| `v1_021` | mixed_support | 0.0 | 1.0 | 1.0 | 0.6 | 0.4348 | False | False |
| `v1_022` | mixed_support | 0.5 | 1.0 | 0.5 | 0.5833 | 0.5926 | False | False |
| `v1_023` | distractor | 0.0 | 1.0 | 1.0 | 0.0625 | 0.5 | False | False |
| `v1_024` | distractor | 0.5 | 0.0 | -0.5 | 0.3478 | 0.9167 | False | False |
| `v1_025` | numerical_negation | 0.5 | 0.0 | -0.5 | 0.3478 | 0.9167 | False | False |
| `v1_026` | empty_context | 1.0 | 1.0 | 0.0 | 1.0 | 1.0 | True | True |
| `v1_027` | instruction_like | 0.0 | 1.0 | 1.0 | 0.0625 | 0.6667 | False | False |
| `v1_028` | conflicting | 0.3333 | 1.0 | 0.6667 | 0.5556 | 0.125 | False | False |
| `v1_029` | standard | 1.0 | 0.5 | -0.5 | 0.8214 | 0.8214 | False | False |
| `v1_030` | numerical_negation | 0.3333 | 0.3333 | 0.0 | 0.8267 | 0.8611 | False | False |
| `v1_031` | standard | 0.0 | 0.5 | 0.5 | 0.5106 | 0.7857 | False | False |
| `v1_032` | unanswerable | 0.0 | 1.0 | 1.0 | 0.0 | 1.0 | False | True |
