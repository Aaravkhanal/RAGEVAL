# RAGeval diagnostic matrix

**Label:** `diagnostic` (not a confirmatory ranking).
**Experiment:** `A_chunk`.
**Dataset:** `chunk_benchmark_v1` 1.0.0, n=30.
**Recall@5:** answerable items only. **Evidence Recall@5:** gold spans in retrieved chunks. **No-answer empty retrieval:** separate rate.

Tables are generated from `metrics.json`. There is no overall score.
Do not read small-n differences as retrieval or faithfulness improvements.

| Configuration            |   claim_support_rate |   unsupported_claim_rate |   contradiction_rate |   recall_at_5 |   evidence_recall_at_5 | no_answer_empty_retrieval_rate   |    mrr |   answer_em |   answer_f1 |   abstention_accuracy | mixed_support_n   | mixed_support_f1   | mixed_support_claim_support   |   n |
|:-------------------------|---------------------:|-------------------------:|---------------------:|--------------:|-----------------------:|:---------------------------------|-------:|------------:|------------:|----------------------:|:------------------|:-------------------|:------------------------------|----:|
| Dense_Chunk128_overlap32 |               0.2449 |                   0.6495 |               0.1056 |             1 |                 0.9    |                                  | 0.9028 |           0 |      0.0883 |                     1 |                   |                    |                               |  30 |
| Dense_Chunk256_Baseline  |               0.1233 |                   0.76   |               0.1167 |             1 |                 0.9333 |                                  | 0.9011 |           0 |      0.087  |                     1 |                   |                    |                               |  30 |
| Dense_Chunk512_overlap32 |               0      |                   0.5841 |               0.4159 |             1 |                 0.9333 |                                  | 0.8817 |           0 |      0.0896 |                     1 |                   |                    |                               |  30 |

Pinned NASA/CDC long-document slice; single-author questions share seven sources. Blinded mock generator and DeBERTa NLI. Diagnostic only.
