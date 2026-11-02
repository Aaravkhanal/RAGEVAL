# Inter-annotator agreement — disclosed LLM rater B

Schema: `rageval.iaa.v1`. CLI: `rageval iaa --rater-a … --rater-b … --output reports/iaa/iaa.md`. Apply human labels with `rageval iaa-label --template data/gold/iaa/annotator_b_template.json --output data/gold/iaa/annotator_b_human.json --set ve_001=supported` (repeat `--set`; does not invent labels).

| File | Role |
| --- | --- |
| `annotator_a_verifier_eval_v1.json` | Export of `data/gold/verifier_eval_v1.json` (single author) |
| `annotator_b_template.json` | Blank labels (`gold_label: null`) for an independent **human** |
| `annotator_b_verifier_eval_v1.json` | Filled by `rater_b_llm_grok` (2026-10-30). Labeled from claim+premise only; rater A labels were not copied. |

Report: `reports/iaa/iaa.md` (kappa **0.9423**, percent agreement **0.9583**, n=24, 1 disagreement on `ve_020`).

This is **diagnostic IAA**, not confirmatory human IAA. Cohen's kappa is confirmatory only when rater B is an independent human. A template or a copy of rater A is not a second annotator.

Human rater B is still unfilled. Do not invent labels. Protocol:

1. Copy `annotator_b_template.json` (do not overwrite `annotator_b_verifier_eval_v1.json`).
2. Label from claim+premise only.
3. Write with `rageval iaa-label --template data/gold/iaa/annotator_b_template.json --output data/gold/iaa/annotator_b_human.json --set id=label` (repeat `--set`).
4. Score with `rageval iaa --rater-a data/gold/iaa/annotator_a_verifier_eval_v1.json --rater-b data/gold/iaa/annotator_b_human.json`.

`data/gold/review/claim_review_v1.jsonl` is a separate unfilled claim-review export (`human_claim_spans`, `human_support_labels`, and `human_citation_labels` are null).
