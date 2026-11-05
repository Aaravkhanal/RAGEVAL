# Independent claim review protocol

`data/gold/review/claim_review_v1.jsonl` contains 40 generated answers from the recorded real-model dense baseline. It shows the proposed claim spans, retrieved chunks, and citations. The three `human_*` fields are deliberately null: no independent human judgment has been collected.

For each answer, a reviewer should mark the exact character spans of every factual claim in `human_claim_spans`, then label each claim against **all retrieved chunks** as `supported`, `partially_supported`, `unsupported`, `contradicted`, or `ambiguous` in `human_support_labels`. Record whether each cited chunk supports its specific claim in `human_citation_labels`. Reviewers should work independently and should not see the model verifier's predicted labels. A second reviewer and adjudication are needed before reporting confirmatory agreement or accuracy.

The queue can be regenerated with:

```bash
python scripts/export_claim_review.py \
  --summaries reports/phase7/live_matrix_v1/summaries.json \
  --config Dense_Chunk256_Baseline \
  --output data/gold/review/claim_review_v1.jsonl
```

Until independent labels are supplied, the existing 24-pair verifier evaluation remains a development diagnostic. After tuning on these examples, the lexical verifier makes 4 errors out of 24 (macro-F1 0.8529); this is not independent test accuracy. See `reports/release_20261104/ANALYSIS.md`. The code checks faithfulness against all retrieved chunks and audits whether the cited subset supports the claim separately.
