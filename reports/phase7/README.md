# Phase 7 tables

**Matched real-generator companion:** `live_matrix_v1/` combines completed five-config and reranker runs on `benchmark_v1` 1.3.0. All use the same NVIDIA NIM generator and DeBERTa verifier. Metric schema v2 excludes no-gold items from Recall@5. Token counts are recorded; USD cost is null because provider pricing was not available. This is diagnostic, not a confirmatory result.

**Embedding comparison:** `B_embed_v1/` records a matched MiniLM versus MPNet run on `benchmark_v1` 1.3.0 (29 documents, 40 questions). The generator is still a blinded mock, so this is a diagnostic retrieval comparison.

**Published (v1.0.0):** `v1_matrix/` from run `20261028T183042Z_a97ad68f` (`benchmark_v1` 1.0.0, 16 documents, 24 items), blinded mock + DeBERTa NLI.

**Companion (v1.1.0):** `v1_1_matrix/` from run `20261029T165024Z_657c8089` (`benchmark_v1` 1.1.0, 18 documents, 28 items), same six-config matrix (overlap 16/32/64). This does not replace `v1_matrix/`. `v1_029`–`v1_032` are unscored here.

**Companion (v1.2.0):** `v1_2_matrix/` from run `20261029T173408Z_de870a29` (`benchmark_v1` 1.2.0, 21 documents, 32 items), same six-config matrix (overlap 16/32/64). This does not replace `v1_matrix/`.

**A_chunk overlap-32:** `A_chunk_overlap32/` from the named `A_chunk.yaml` protocol on 1.2.0 (dense MiniLM, overlap fixed at 32, sizes 128/256/512). This does not replace `v1_matrix/` or `v1_2_matrix/`.

The current `A_chunk.yaml` uses the separate `chunk_benchmark_v1` long-document slice. The earlier `A_chunk_overlap32/` table is a historical run on short documents where the chunk-size treatment did not change the chunks. New reports use answerable-only document Recall@5 and evidence-span Recall@5; their retrieval scores are not directly comparable with earlier reports.

**A_chunk long-document diagnostic:** `A_chunk_long_v1/` from run `20261102T041417Z_2b164af2` (`chunk_benchmark_v1` 1.0.0, seven documents, 30 items). Its `FINDINGS.md` reports the actual chunk counts and evidence-span results.

**Live NVIDIA NIM companion:** `nvidia_nim_v1/` from run `20261030T052638Z_79a8b21d` (`benchmark_v1` 1.2.0, 21/32). One sparse BM25 config, generator `nvidia/nemotron-3.5-bolt-e4b`, DeBERTa NLI. Faith 0.7188, R@5 0.8438, MRR 0.7812, abstention 1.0. This does not replace `v1_matrix/`.

**Live NVIDIA NIM retrieve:** `nvidia_nim_retrieve/` from run `20261030T055224Z_388c5503`. Dense MiniLM faith 0.7396 / MRR 0.7344; hybrid RRF faith 0.6458 / MRR 0.75. Recall@5 0.8438 and abstention 1.0 on both. This does not replace `v1_matrix/` or `nvidia_nim_v1/`.

Named YAML in `configs/experiments/` (A–G) is the protocol. The six-config v1.0.0 / v1.1.0 / v1.2.0 snapshots used overlap 16/32/64 on dense chunk configs. Do not treat those YAML files as if they produced the six-config numbers.

`significance.json` compares each config to `Dense_Chunk256_Baseline`. n<30, so `underpowered=true` and `is_significant=false` even when a raw paired t-test p-value is below 0.05.

G (claim vs answer) is `G_claim_vs_answer.md` in each snapshot from the mixed-support slice (n=4).
