# RAGeval diagnostic matrix

**Label:** `diagnostic` (not a confirmatory ranking).
**Experiment:** `B_embed`.
**Dataset:** `benchmark_v1` 1.3.0, n=40.
**Recall@5:** answerable items only. **Evidence Recall@5:** gold spans in retrieved chunks. **No-answer empty retrieval:** separate rate.

Tables are generated from `metrics.json`. There is no overall score.
Do not read small-n differences as retrieval or faithfulness improvements.

| Configuration   |   claim_support_rate |   unsupported_claim_rate |   contradiction_rate |   recall_at_5 |   evidence_recall_at_5 |   no_answer_empty_retrieval_rate |    mrr |   answer_em |   answer_f1 |   abstention_accuracy |   mixed_support_n |   mixed_support_f1 |   mixed_support_claim_support |   n |
|:----------------|---------------------:|-------------------------:|---------------------:|--------------:|-----------------------:|---------------------------------:|-------:|------------:|------------:|----------------------:|------------------:|-------------------:|------------------------------:|----:|
| Embed_MiniLM    |               0.4292 |                   0.2417 |               0.3292 |             1 |                      1 |                           0.1667 | 0.9265 |       0.025 |      0.4477 |              0.166667 |                 4 |             0.5689 |                        0.4583 |  40 |
| Embed_MPNet     |               0.3917 |                   0.3042 |               0.3042 |             1 |                      1 |                           0.1667 | 0.9314 |       0.025 |      0.4429 |              0.166667 |                 4 |             0.5689 |                        0.3333 |  40 |

Matched MiniLM/MPNet mock+NLI run; diagnostic because items share documents.
