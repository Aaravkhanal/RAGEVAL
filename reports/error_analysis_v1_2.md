# Error notes — v1.2.0 companion run `20261029T173408Z_de870a29`

Filled from **recorded** predictions on config `Dense_Chunk256_Baseline` unless a cell names another config. Official published tables remain `20261028T183042Z_a97ad68f`. n=32 is underpowered (items share documents). This file does not replace `reports/error_analysis_v1_1.md` or `reports/error_analysis_phase6.md`.

## New items (`v1_029`–`v1_032`)

| Id | Scenario | Abstained | claim support | answer F1 | Recall@5 | Stage |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `v1_029` | standard (last volcanism) | no | 0.5 | 0.8214 | 1.0 | generation then NLI |
| `v1_030` | numerical_negation | no | 0.3333 | 0.8267 | 1.0 | generation then NLI |
| `v1_031` | standard (ISS 25-year) | no | 0.0 | 0.5106 | 1.0 | generation then NLI |
| `v1_032` | unanswerable | no | 0.0 | 0.0 | 0.0 | generation (no abstain) |

- `v1_029`: gold is USGS last-eruption FAQ (rhyolite flows ~70,000 years ago; Pitchstone Plateau). Recall@5 is 1.0 on all six configs. Dense/hybrid claim support is 0.5 with contradiction 0.5. Sparse_BM25_Chunk256 and Hybrid_RRF_Reranked reach claim support 1.0 on this item. Answer EM is 0; token F1 is 0.8214.
- `v1_030`: gold is the USGS post-caldera counts (~80 eruptions: 27 / 13 / 40). Recall@5 is 1.0 on all six configs. Claim support is 0.3333 and unsupported rate 0.6667 on every config. The mock copies retrieved sentences; NLI does not treat the copied mix as fully supported.
- `v1_031`: gold is NASA ISS 25-year presence (2 November 2025) and the five principal agencies. Recall@5 is 1.0 on all six configs. Claim support is 0.0 on every config (dense/hybrid contradiction 0.5; sparse and reranked unsupported 1.0). Token F1 is 0.5106. Retrieval found the document; the mock extract is not NLI-supported against the retrieved chunks.
- `v1_032`: gold is null (Expedition 75 Thanksgiving dinner is absent from the stored NASA excerpt). Expected abstention. Recall@5 is 0.0 (no gold evidence docs). The blinded mock did **not** abstain; claim support 0.0, answer F1 0.0. Same on all six configs.

## Unanswerable remainder

Six unanswerable items on this corpus. Only empty-context `v1_026` abstains (protocol drops retrieval before generate). `v1_013`–`v1_016` and `v1_032` still retrieve or copy non-empty context. Overall abstention accuracy is 0.1667 (1 of 6). `by_scenario.unanswerable.abstention_accuracy` is 0.0 on Dense_Chunk256_Baseline; empty-context is a separate scenario slice.

## A_chunk overlap-32 (`20261029T173515Z_7e2b94a3`)

Three dense MiniLM configs with overlap fixed at 32 (`reports/phase7/A_chunk_overlap32/`). Rounded claim support, Recall@5, MRR, answer EM/F1, and abstention match the six-config dense rows on this corpus (faith 0.401, R@5 0.8438, MRR 0.7344). New-item scores on all three overlap-32 configs match the dense rows above. Chunk size did not move those means.

## What this file is not

It is not a ranking of retrievers. Recall@5 is 0.8438 on all six configs of `de870a29` and all three A_chunk configs. Mixed-support n=4. The six-config dense overlap was 16/32/64; A_chunk is overlap 32.
