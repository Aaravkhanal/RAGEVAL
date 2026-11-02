# Data card — chunk_benchmark_v1

This diagnostic slice tests whether changing chunk size changes retrieval of the **actual evidence span**. It does not replace `benchmark_v1` or its recorded tables.

| Field | Value |
| --- | --- |
| Version | `1.0.0` |
| Size | 7 public documents, 30 answerable questions |
| Length | Every document exceeds 512 whitespace-delimited words |
| Sources | NASA Apollo 11, 13, 14, 15, and 16 mission articles; CDC influenza types and antigenic-change articles |
| License | U.S. government works, public domain under 17 U.S.C. § 105 |
| Snapshot | Main-content paragraphs fetched 2026-11-02 and pinned under `data/datasets/chunk_benchmark_v1/sources/` |
| Labels | Single-author questions, answers, and verbatim gold evidence spans |
| Split | Dev only; no held-out test or independent-document sample |

Source URLs and SHA-256 hashes of the pinned text files are in `corpus.json`. The Apollo 11 snapshot uses its first 15 substantive article paragraphs; the CDC influenza-types snapshot uses its 10 substantive main-content paragraphs. Other snapshots use substantive paragraphs from each article's main content. Paragraph whitespace is collapsed in the generated corpus. The text files are the reproducible source of truth; rebuilding never fetches live pages.

The named `A_chunk` experiment holds embedder, dense retrieval, top-k, generator, verifier, and 32-word overlap fixed, while testing chunk sizes 128, 256, and 512. Report document Recall@5 and **Evidence Recall@5** separately. The latter counts a gold span only when it appears completely within a retrieved chunk. A span cut across a chunk boundary is a miss by this definition.

This slice is deliberately diagnostic. Its questions share seven source documents, labels have not been independently reviewed, and its mock generator does not establish end-to-end LLM quality.
