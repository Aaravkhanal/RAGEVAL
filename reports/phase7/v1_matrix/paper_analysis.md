# RAGeval run report

**Status:** tables generated from `metrics.json`. Narrative scientific findings are **pending** until Phase 8.

**Label:** `v1`. **Experiment:** `recorded_v1_0_0_matrix`.

This report must not claim retrieval or faithfulness improvements unless those differences appear in the table below and n is large enough for confirmatory tests (n≥30 i.i.d.).

---

# RAGeval v1 matrix

**Label:** `v1` (not a confirmatory ranking).
**Experiment:** `recorded_v1_0_0_matrix`.
**Dataset:** `benchmark_v1` 1.0.0, n=24.

Tables are generated from `metrics.json`. There is no overall score.
Do not read small-n differences as retrieval or faithfulness improvements.

| Configuration           |   claim_support_rate |   unsupported_claim_rate |   contradiction_rate |   recall_at_5 |    mrr |   answer_em |   answer_f1 |   abstention_accuracy |   mixed_support_n |   mixed_support_f1 |   mixed_support_claim_support |   n |
|:------------------------|---------------------:|-------------------------:|---------------------:|--------------:|-------:|------------:|------------:|----------------------:|------------------:|-------------------:|------------------------------:|----:|
| Dense_Chunk128          |               0.4375 |                   0.1806 |               0.3819 |        0.8333 | 0.8125 |           0 |      0.4174 |                     0 |                 4 |             0.6292 |                         0.375 |  24 |
| Dense_Chunk256_Baseline |               0.4375 |                   0.1806 |               0.3819 |        0.8333 | 0.8125 |           0 |      0.4174 |                     0 |                 4 |             0.6292 |                         0.375 |  24 |
| Dense_Chunk512          |               0.4375 |                   0.1806 |               0.3819 |        0.8333 | 0.8125 |           0 |      0.4174 |                     0 |                 4 |             0.6292 |                         0.375 |  24 |
| Sparse_BM25_Chunk256    |               0.5    |                   0.2361 |               0.2639 |        0.8333 | 0.8125 |           0 |      0.4074 |                     0 |                 4 |             0.6292 |                         0.625 |  24 |
| Hybrid_RRF_Chunk256     |               0.5625 |                   0.1806 |               0.2569 |        0.8333 | 0.8125 |           0 |      0.4174 |                     0 |                 4 |             0.6292 |                         0.625 |  24 |
| Hybrid_RRF_Reranked     |               0.5833 |                   0.375  |               0.0417 |        0.8333 | 0.8125 |           0 |      0.4038 |                     0 |                 4 |             0.6292 |                         0.5   |  24 |

Exported from the recorded v1.0.0 ablation (16 documents, 24 items). Dense chunk configs in that run used overlap 16/32/64, not the Phase 7 A_chunk fixed-overlap-32 protocol. n=24 is underpowered. Generator: blinded mock. No new NLI scores were computed for this export.


---

# RAGeval v1 claim-level vs answer-level (mixed-support)

Slice: `scenario_type=mixed_support`. Gold answers are fully supported; token F1 can stay high while claim support is mixed (RQ3).

| Configuration | mixed n | answer F1 | claim support rate |
| --- | ---: | ---: | ---: |
| Dense_Chunk128 | 4 | 0.6292 | 0.375 |
| Dense_Chunk256_Baseline | 4 | 0.6292 | 0.375 |
| Dense_Chunk512 | 4 | 0.6292 | 0.375 |
| Sparse_BM25_Chunk256 | 4 | 0.6292 | 0.625 |
| Hybrid_RRF_Chunk256 | 4 | 0.6292 | 0.625 |
| Hybrid_RRF_Reranked | 4 | 0.6292 | 0.5 |

No overall score. n on this slice is 4 in the recorded v1.0.0 run.


---

## Notes

- Default generation is a blinded mock that copies retrieved sentences.
- Cost is omitted unless explicit pricing is configured.
- Compare named metrics only. There is no overall score.
- Significance tests with n<30 are diagnostic (`underpowered=true`).
