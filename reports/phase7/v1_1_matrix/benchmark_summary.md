# RAGeval v1 matrix

**Label:** `v1` (not a confirmatory ranking).
**Experiment:** `recorded_v1_1_0_matrix`.
**Dataset:** `benchmark_v1` 1.1.0, n=28.

Tables are generated from `metrics.json`. There is no overall score.
Do not read small-n differences as retrieval or faithfulness improvements.

| Configuration           |   claim_support_rate |   unsupported_claim_rate |   contradiction_rate |   recall_at_5 |    mrr |   answer_em |   answer_f1 |   abstention_accuracy |   mixed_support_n |   mixed_support_f1 |   mixed_support_claim_support |   n |
|:------------------------|---------------------:|-------------------------:|---------------------:|--------------:|-------:|------------:|------------:|----------------------:|------------------:|-------------------:|------------------------------:|----:|
| Dense_Chunk128          |               0.3929 |                   0.131  |               0.4762 |        0.8571 | 0.7321 |      0.0357 |      0.4228 |                   0.2 |                 4 |             0.5689 |                        0.3333 |  28 |
| Dense_Chunk256_Baseline |               0.3929 |                   0.131  |               0.4762 |        0.8571 | 0.7321 |      0.0357 |      0.4228 |                   0.2 |                 4 |             0.5689 |                        0.3333 |  28 |
| Dense_Chunk512          |               0.3929 |                   0.131  |               0.4762 |        0.8571 | 0.7321 |      0.0357 |      0.4228 |                   0.2 |                 4 |             0.5689 |                        0.3333 |  28 |
| Sparse_BM25_Chunk256    |               0.4524 |                   0.2202 |               0.3274 |        0.8571 | 0.7857 |      0.0357 |      0.4198 |                   0.2 |                 4 |             0.6292 |                        0.5    |  28 |
| Hybrid_RRF_Chunk256     |               0.5    |                   0.1191 |               0.381  |        0.8571 | 0.75   |      0.0357 |      0.4228 |                   0.2 |                 4 |             0.5689 |                        0.5833 |  28 |
| Hybrid_RRF_Reranked     |               0.4405 |                   0.3393 |               0.2202 |        0.8571 | 0.7798 |      0.0357 |      0.4112 |                   0.2 |                 4 |             0.5689 |                        0.4583 |  28 |

Exported from the recorded v1.1.0 ablation (18 documents, 28 items, blinded mock + DeBERTa NLI). Dense chunk configs used overlap 16/32/64, not the Phase 7 A_chunk fixed-overlap-32 protocol. n=28 is still underpowered (confirmatory n≥30 i.i.d.). Official published tables remain run 20261028T183042Z_a97ad68f (v1.0.0, n=24). Do not copy those scores onto these rows.
