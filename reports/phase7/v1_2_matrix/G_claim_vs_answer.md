# RAGeval v1 claim-level vs answer-level (mixed-support)

Slice: `scenario_type=mixed_support`. Gold answers are fully supported; token F1 can stay high while claim support is mixed (RQ3).

| Configuration | mixed n | answer F1 | claim support rate |
| --- | ---: | ---: | ---: |
| Dense_Chunk128 | 4 | 0.5689 | 0.4583 |
| Dense_Chunk256_Baseline | 4 | 0.5689 | 0.4583 |
| Dense_Chunk512 | 4 | 0.5689 | 0.4583 |
| Sparse_BM25_Chunk256 | 4 | 0.6292 | 0.375 |
| Hybrid_RRF_Chunk256 | 4 | 0.5689 | 0.5833 |
| Hybrid_RRF_Reranked | 4 | 0.5689 | 0.4583 |

No overall score. n on this slice is 4 Dataset version 1.2.0.
