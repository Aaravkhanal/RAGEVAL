# NVIDIA NIM companion (`20261030T052638Z_79a8b21d`)

`benchmark_v1` 1.2.0, n=32, 21 documents. Generator: `nvidia/nemotron-3.5-bolt-e4b`. Verifier: DeBERTa NLI. Retriever: sparse BM25. Does not replace `v1_matrix/`.

| config | n | claim_support_rate | Recall@5 | MRR | answer F1 | abstention | cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OptIn_NVIDIA_NIM_NLI | 32 | 0.7188 | 0.8438 | 0.7812 | 0.7705 | 1.0 | null |
