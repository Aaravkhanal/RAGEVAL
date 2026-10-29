# Inter-annotator agreement — rater B missing

Schema: `rageval.iaa.v1`. CLI: `rageval iaa --rater-a … --rater-b … --output reports/iaa/iaa.md`.

| File | Role |
| --- | --- |
| `annotator_a_verifier_eval_v1.json` | Export of `data/gold/verifier_eval_v1.json` (single author) |
| `annotator_b_template.json` | Blank labels (`gold_label: null`) for an independent human |
| `annotator_b_verifier_eval_v1.json` | **Not present.** Do not copy rater A into this file. |

Cohen's kappa on the template is **null** (undefined), not zero. A self-repeat or a filled copy of rater A is not a second annotator.

`reports/iaa/` holds the diagnostic report from A vs the unfilled template. Confirmatory IAA still requires an independent human.
