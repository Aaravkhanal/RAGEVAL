# RAGeval companion matrix

**Label:** `companion` (not a confirmatory ranking).
**Experiment:** `live_matrix_v1`.
**Dataset:** `benchmark_v1` 1.3.0, n=40.
**Recall@5:** answerable items only. **Evidence Recall@5:** gold spans in retrieved chunks. **No-answer empty retrieval:** separate rate.

Tables are generated from `metrics.json`. There is no overall score.
Do not read small-n differences as retrieval or faithfulness improvements.

| Configuration           |   claim_support_rate |   unsupported_claim_rate |   contradiction_rate |   recall_at_5 |   evidence_recall_at_5 |   no_answer_empty_retrieval_rate |    mrr |   prompt_tokens |   completion_tokens | estimated_cost_usd   |   answer_em |   answer_f1 |   abstention_accuracy |   mixed_support_n |   mixed_support_f1 |   mixed_support_claim_support |   n |
|:------------------------|---------------------:|-------------------------:|---------------------:|--------------:|-----------------------:|---------------------------------:|-------:|----------------:|--------------------:|:---------------------|------------:|------------:|----------------------:|------------------:|-------------------:|------------------------------:|----:|
| Dense_Chunk128          |               0.6375 |                   0.3417 |               0.0208 |             1 |                      1 |                           0.1667 | 0.9265 |           19647 |                1372 |                      |        0.15 |      0.7582 |                     1 |                 4 |             0.7983 |                         0.75  |  40 |
| Dense_Chunk256_Baseline |               0.6375 |                   0.3417 |               0.0208 |             1 |                      1 |                           0.1667 | 0.9265 |           19647 |                1372 |                      |        0.15 |      0.7589 |                     1 |                 4 |             0.7983 |                         0.75  |  40 |
| Dense_Chunk512          |               0.6375 |                   0.3417 |               0.0208 |             1 |                      1 |                           0.1667 | 0.9265 |           19647 |                1371 |                      |        0.15 |      0.7582 |                     1 |                 4 |             0.7983 |                         0.75  |  40 |
| Sparse_BM25_Chunk256    |               0.65   |                   0.3292 |               0.0208 |             1 |                      1 |                           0.1667 | 0.9618 |           19820 |                1358 |                      |        0.15 |      0.7564 |                     1 |                 4 |             0.7448 |                         0.75  |  40 |
| Hybrid_RRF_Chunk256     |               0.5917 |                   0.3625 |               0.0458 |             1 |                      1 |                           0.1667 | 0.9216 |           19903 |                1468 |                      |        0.15 |      0.751  |                     1 |                 4 |             0.7983 |                         0.625 |  40 |
| Hybrid_RRF_Reranked     |               0.6375 |                   0.3292 |               0.0333 |             1 |                      1 |                           0.1667 | 0.9216 |           13555 |                1457 |                      |        0.15 |      0.7872 |                     1 |                 4 |             0.7983 |                         0.625 |  40 |

Matched real NVIDIA NIM generator across six configs. USD pricing unavailable; token usage is reported; diagnostic due shared documents.
