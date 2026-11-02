# RAGeval companion claim-level vs answer-level (mixed-support)

Slice: `scenario_type=mixed_support`. Gold answers are fully supported; token F1 can stay high while claim support is mixed (RQ3).

| Configuration | mixed n | answer F1 | claim support rate |
| --- | ---: | ---: | ---: |
| Dense_Chunk128 | 4 | 0.7983 | 0.75 |
| Dense_Chunk256_Baseline | 4 | 0.7983 | 0.75 |
| Dense_Chunk512 | 4 | 0.7983 | 0.75 |
| Sparse_BM25_Chunk256 | 4 | 0.7448 | 0.75 |
| Hybrid_RRF_Chunk256 | 4 | 0.7983 | 0.625 |
| Hybrid_RRF_Reranked | 4 | 0.7983 | 0.625 |

No overall score. n on this slice is 4 Dataset version 1.3.0.
