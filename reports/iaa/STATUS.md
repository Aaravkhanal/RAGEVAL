# IAA report

This folder is the diagnostic output of:

```bash
rageval iaa \
  --rater-a data/gold/iaa/annotator_a_verifier_eval_v1.json \
  --rater-b data/gold/iaa/annotator_b_verifier_eval_v1.json \
  --output reports/iaa/iaa.md
```

| Field | Value |
| --- | --- |
| Rater A | `single-author, disclosed` |
| Rater B | `rater_b_llm_grok` (disclosed LLM, 2026-10-30) |
| n labeled both | 24 / 24 |
| Percent agreement | 0.9583 |
| Cohen's kappa | 0.9423 |
| Disagreements | 1 (`ve_020`: A `unsupported`, B `contradicted`) |

Rater B labeled from claim+premise only; rater A labels were not copied. This is **not confirmatory human IAA**. Keep `annotator_b_template.json` for a future independent human.
