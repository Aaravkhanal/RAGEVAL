# Verifier evaluation — verifier_eval_v1 (RQ2)

Labeled set: 24 claim–premise pairs (`data/gold/verifier_eval_v1.json`). Single-author gold. Context-bounded.

| Method | Accuracy | Macro-F1 | Failures |
| --- | ---: | ---: | ---: |
| DeBERTa NLI | 0.7917 | 0.6921 | 5/24 |
| Lexical heuristic | 0.5833 | 0.5140 | 10/24 |

On this set the NLI macro-F1 is higher than the heuristic, so the RQ2 hypothesis is **not falsified here**. Partial-support F1 is 0.0 for both methods. n=24 is underpowered; do not treat this as a confirmatory result.

Details:

- NLI: `reports/verifier_eval_nli.md`
- Heuristic: `reports/verifier_eval_heuristic.md`

NLI failures: `ve_012` (supported→unsupported), `ve_017` (partial→contradicted), `ve_018` (partial→supported), `ve_020` (unsupported→contradicted), `ve_024` (partial→unsupported).
