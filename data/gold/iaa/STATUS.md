# Inter-annotator agreement — disclosed LLM rater B

Schema: `rageval.iaa.v1`. CLI: `rageval iaa --rater-a … --rater-b … --output reports/iaa/iaa.md`.

| File | Role |
| --- | --- |
| `annotator_a_verifier_eval_v1.json` | Export of `data/gold/verifier_eval_v1.json` (single author) |
| `annotator_b_template.json` | Blank labels (`gold_label: null`) for an independent **human** |
| `annotator_b_verifier_eval_v1.json` | Filled by `rater_b_llm_grok` (2026-10-30). Labeled from claim+premise only; rater A labels were not copied. |

Report: `reports/iaa/iaa.md` (kappa **0.9423**, percent agreement **0.9583**, n=24, 1 disagreement on `ve_020`).

This is **diagnostic IAA**, not confirmatory human IAA. Cohen's kappa is confirmatory only when rater B is an independent human. A template or a copy of rater A is not a second annotator.
