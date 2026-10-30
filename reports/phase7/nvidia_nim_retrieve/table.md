# NVIDIA NIM retrieve companion (`20261030T055224Z_388c5503`)

`benchmark_v1` 1.2.0, n=32. Generator: `nvidia/nemotron-3.5-bolt-e4b`. Verifier: DeBERTa NLI. Does not replace `v1_matrix/` or sparse `nvidia_nim_v1/`.

| config | n | claim_support_rate | Recall@5 | MRR | answer F1 | abstention |
| --- | --- | --- | --- | --- | --- | --- |
| OptIn_NVIDIA_NIM_Dense_NLI | 32 | 0.7396 | 0.8438 | 0.7344 | 0.7465 | 1.0 |
| OptIn_NVIDIA_NIM_Hybrid_NLI | 32 | 0.6458 | 0.8438 | 0.75 | 0.746 | 1.0 |
