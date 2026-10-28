# RAGeval run report

**Status:** tables from named run `20261028T183042Z_a97ad68f` on `benchmark_v1` (n=24, split=all). Narrative scientific findings are **not** claimed. `paper.tex` is a draft.

Generator: blinded mock. Evaluator: DeBERTa NLI. Cost: null.

This report must not claim retrieval or faithfulness improvements unless those differences appear in the table below **and** are interpreted at this sample size.

---

## Ablation table

| Configuration | Faithfulness | Hallucination Rate | Contradiction Rate | Citation Precision | Recall@5 | MRR | Answer EM | Answer F1 | Mixed-support n | Mixed-support F1 | Mixed-support Faithfulness | Abstention Acc | Latency (ms) | P95 Latency (ms) | Est. Cost ($) | Dataset |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Dense_Chunk128 | 0.4375 | 0.1806 | 0.3819 | 1.0 | 0.8333 | 0.8125 | 0.0 | 0.4174 | 4 | 0.6292 | 0.375 | 0.0 | 2571.59 | 4407.86 |  | benchmark_v1 |
| Dense_Chunk256_Baseline | 0.4375 | 0.1806 | 0.3819 | 1.0 | 0.8333 | 0.8125 | 0.0 | 0.4174 | 4 | 0.6292 | 0.375 | 0.0 | 2349.09 | 4365.24 |  | benchmark_v1 |
| Dense_Chunk512 | 0.4375 | 0.1806 | 0.3819 | 1.0 | 0.8333 | 0.8125 | 0.0 | 0.4174 | 4 | 0.6292 | 0.375 | 0.0 | 2857.61 | 4884.96 |  | benchmark_v1 |
| Sparse_BM25_Chunk256 | 0.5000 | 0.2361 | 0.2639 | 1.0 | 0.8333 | 0.8125 | 0.0 | 0.4074 | 4 | 0.6292 | 0.625 | 0.0 | 2471.74 | 3443.06 |  | benchmark_v1 |
| Hybrid_RRF_Chunk256 | 0.5625 | 0.1806 | 0.2569 | 1.0 | 0.8333 | 0.8125 | 0.0 | 0.4174 | 4 | 0.6292 | 0.625 | 0.0 | 2192.38 | 3200.03 |  | benchmark_v1 |
| Hybrid_RRF_Reranked | 0.5833 | 0.3750 | 0.0417 | 1.0 | 0.8333 | 0.8125 | 0.0 | 0.4038 | 4 | 0.6292 | 0.500 | 0.0 | 1590.42 | 2415.55 |  | benchmark_v1 |

---

## Notes

- Default generation is a **blinded mock** that copies retrieved sentences. It is not a production LLM.
- Dataset: `benchmark_v1` (16 documents, 24 items). Public-domain US government excerpts plus original CC-BY-4.0 fiction.
- The 16/8 dev/test split exists; this run scored **all 24** because n_test=8 is underpowered.
- Retrieval Recall@5/MRR did not change across configs on this corpus.
- Cost is omitted unless explicit pricing is configured.
- Compare configurations using the table, not canned commentary.

## Figures

- Figure 1: `figures/fig1_pareto_latency_faithfulness.png`
- Figure 2: `figures/fig2_claim_attribution_breakdown.png`
- Figure 3: `figures/fig3_retrieval_recall_mrr.png`
- Figure 4: `figures/fig4_adversarial_abstention.png`
