# RAGeval run report

**Status:** tables generated from `metrics.json`. Narrative is `FINDINGS.md` for a named run, not this table file.

**Label:** `v1`. **Experiment:** `A_chunk`.

This report must not claim retrieval or faithfulness improvements unless those differences appear in the table below and n is large enough for confirmatory tests (n≥30 i.i.d.).

---

# RAGeval v1 matrix

**Label:** `v1` (not a confirmatory ranking).
**Experiment:** `A_chunk`.
**Dataset:** `benchmark_v1` 1.2.0, n=32.

Tables are generated from `metrics.json`. There is no overall score.
Do not read small-n differences as retrieval or faithfulness improvements.

| Configuration            |   claim_support_rate |   unsupported_claim_rate |   contradiction_rate |   recall_at_5 |    mrr |   answer_em |   answer_f1 |   abstention_accuracy |   mixed_support_n |   mixed_support_f1 |   mixed_support_claim_support |   n |
|:-------------------------|---------------------:|-------------------------:|---------------------:|--------------:|-------:|------------:|------------:|----------------------:|------------------:|-------------------:|------------------------------:|----:|
| Dense_Chunk128_overlap32 |                0.401 |                   0.1979 |                0.401 |        0.8438 | 0.7344 |      0.0312 |      0.4374 |              0.166667 |                 4 |             0.5689 |                        0.4583 |  32 |
| Dense_Chunk256_Baseline  |                0.401 |                   0.1979 |                0.401 |        0.8438 | 0.7344 |      0.0312 |      0.4374 |              0.166667 |                 4 |             0.5689 |                        0.4583 |  32 |
| Dense_Chunk512_overlap32 |                0.401 |                   0.1979 |                0.401 |        0.8438 | 0.7344 |      0.0312 |      0.4374 |              0.166667 |                 4 |             0.5689 |                        0.4583 |  32 |

Exported from A_chunk overlap-32 protocol on benchmark_v1 1.2.0 (21 documents, 32 items, blinded mock + DeBERTa NLI). Overlap fixed at 32. n=32 is still underpowered (confirmatory n>=30 i.i.d.; items share documents). Official published tables remain run 20261028T183042Z_a97ad68f (v1.0.0, n=24). Companion six-config v1.2.0 remains 20261029T173408Z_de870a29. Do not copy those scores onto these rows.

---

# RAGeval v1 claim-level vs answer-level (mixed-support)

Slice: `scenario_type=mixed_support`. Gold answers are fully supported; token F1 can stay high while claim support is mixed (RQ3).

| Configuration | mixed n | answer F1 | claim support rate |
| --- | ---: | ---: | ---: |
| Dense_Chunk128_overlap32 | 4 | 0.5689 | 0.4583 |
| Dense_Chunk256_Baseline | 4 | 0.5689 | 0.4583 |
| Dense_Chunk512_overlap32 | 4 | 0.5689 | 0.4583 |

No overall score. n on this slice is 4 Dataset version 1.2.0.
