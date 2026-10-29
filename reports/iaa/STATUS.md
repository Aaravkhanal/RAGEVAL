# IAA report

This folder is the diagnostic output of:

```bash
rageval iaa \
  --rater-a data/gold/iaa/annotator_a_verifier_eval_v1.json \
  --rater-b data/gold/iaa/annotator_b_template.json \
  --output reports/iaa/iaa.md
```

Cohen's kappa is **null**. Rater B is unfilled. See `data/gold/iaa/STATUS.md`. This is not confirmatory IAA.
