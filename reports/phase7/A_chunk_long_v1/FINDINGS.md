# Long-document chunk-size diagnostic

Run `20261102T041417Z_2b164af2` used `chunk_benchmark_v1` 1.0.0: seven pinned NASA/CDC documents and 30 single-author questions. The compared pipelines used the same MiniLM dense retriever, top five, 32-word overlap, blinded mock generator, and DeBERTa verifier. Only chunk size changed.

| Chunk size | Indexed chunks | Document Recall@5 | Evidence Recall@5 | MRR |
| ---: | ---: | ---: | ---: | ---: |
| 128 words | 86 | 1.0000 | 0.9000 | 0.9028 |
| 256 words | 39 | 1.0000 | 0.9333 | 0.9011 |
| 512 words | 20 | 1.0000 | 0.9333 | 0.8817 |

The different indexed-chunk counts confirm an actual chunk-size treatment. Document Recall@5 remains saturated because it credits any chunk from a gold document. Evidence Recall@5 checks whether a retrieved chunk contains the full verbatim gold span, and exposes three misses at 128 words and two each at 256 and 512 words. The 0.0333 difference is one question; the paired evidence-recall comparison against 256 words is diagnostic (`significance.json`, `is_significant=false`).

The 30 questions share seven source documents, the labels have one author, and the generator is a mock. The NLI claim-support numbers in `table.md` also change sharply with chunk length and should not be interpreted as a retrieval benefit without a separate verifier-length study. This report does not establish an optimal chunk size or an end-to-end LLM improvement.

`metrics.json` uses `rageval.metrics.v2`: document Recall@5 and MRR exclude no-gold items. This slice has no unanswerable items, so its no-answer empty-retrieval rate is undefined. Earlier recorded `benchmark_v1` reports use the mixed v1 recall definition and are not directly comparable.
