# Benchmark evidence and validation status

These are recorded pilot results, not a claim of production accuracy.

## Retrieval comparison

Dataset: benchmark_v2 2.0.0; 13 documents; 22 test questions, including 18 answerable questions. Single-author labels. Recall below is measured on the answerable subset.

| Configuration | Chunks | Document Recall@5 | Evidence Recall@5 | Retrieval p50 ms |
| --- | ---: | ---: | ---: | ---: |
| sparse_128 | 128 | 0.8889 | 0.6667 | 0.134 |
| sparse_256 | 59 | 0.8889 | 0.8333 | 0.074 |
| sparse_512 | 31 | 1.0000 | 1.0000 | 0.055 |
| dense_128 | 128 | 1.0000 | 0.7222 | 7.050 |
| dense_256 | 59 | 1.0000 | 0.9444 | 7.053 |
| dense_512 | 31 | 0.8889 | 0.8333 | 7.555 |
| hybrid_128 | 128 | 1.0000 | 0.7778 | 9.473 |
| hybrid_256 | 59 | 1.0000 | 1.0000 | 9.198 |
| hybrid_512 | 31 | 0.9444 | 0.8889 | 7.950 |
| dense_256_mpnet | 59 | 1.0000 | 1.0000 | 51.096 |
| hybrid_256_reranked | 59 | 1.0000 | 1.0000 | 150.686 |

Chunk size has an effective treatment here: 128, 59 and 31 chunks for sizes 128, 256 and 512. The small sample does not establish a universally best configuration. Evidence recall checks complete evidence spans and can penalize a span split across chunks. Larger chunks also carry more text, so this comparison does not hold retrieved token budget constant.

Timing is the recorded local macOS ARM run, after one warm query. It excludes generation and answer verification. No billed provider rate was supplied; actual USD cost is unknown.

## Evaluator development diagnostic

The revised heuristic makes 4 errors out of 24, with macro-F1 0.8529. These examples were used during tuning, so this is development performance. Independent accuracy, false-positive rate and missed-contradiction rate remain unestablished. See release_20261104/ANALYSIS.md and verifier_diagnostic.md.

## Reproduction

Use the repository dependency locks and the same dataset/configuration revision. Run:

```sh
python scripts/run_retrieval_v2.py --output reports/reproduced/retrieval_v2.json
python -m rageval.cli verifier-eval --method heuristic --output reports/reproduced/verifier.md
```

Model downloads are needed for dense embeddings and reranking. The lightweight hosted service does not run this full model matrix. Preserve new results separately rather than overwriting recorded observations.

## Independent review handoff

The blinded queue is data/gold/review/claim_review_v1.jsonl (40 answers). Follow docs/CLAIM_REVIEW.md and docs/ANNOTATION_GUIDELINES.md. Two people should label independently before adjudication; do not expose verifier predictions. Human fields remain blank until those people supply judgments. Record reviewer identities or pseudonyms, dates, disagreements and adjudicated labels, then freeze and hash the held-out set before further tuning.

## Operational evidence

The deployed workflow passed on 2026-11-05: https://github.com/Aaravkhanal/RAGEVAL/actions/runs/41966864355 . This verifies the scripted service flow, not real email delivery or every account lifecycle action.

The earlier full logical database restore passed: https://github.com/Aaravkhanal/RAGEVAL/actions/runs/41774502581 . Auth tables were empty; populated-account recovery is still pending.

On 2026-11-05 the repository was observed to be public. Both backup schedules were disabled pending confirmation of a private destination or explicit approval for encrypted artifacts in the public repository. Existing backups use encryption; no plaintext exposure was established.

The user subsequently approved encrypted backup artifacts in the public repository on 2026-11-05; both schedules were re-enabled. Independent human review was deferred, with the frozen review packet prepared for later.
