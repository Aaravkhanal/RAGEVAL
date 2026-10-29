# Error analysis — smoke + benchmark_v1 adversarial

Template filled from **recorded** artifacts. No new NLI ablation was run for Phase 6. Numbers below are copied from committed tables or from the local gitignored run `20261028T183042Z_a97ad68f` that produced `reports/benchmark_summary.md`.

Dataset for that run: `benchmark_v1` **1.0.0** (16 documents, 24 items). Phase 6 adds `benchmark_v1` **1.1.0** reviewed items (`v1_025`–`v1_028` plus two documents). Those new items have **no** scores in the recorded run.

Generator: blinded mock (`faithful`, `empty_context`). Verifier: DeBERTa-v3 NLI.

## How to fill this template on a new run

For each failed item: `query_id`, `scenario_type`, metric that moved, `primary_stage` from `attribute_failure`, evidence (retrieved ids, answer excerpt), and whether the gold looks wrong (`dataset`).

## Smoke (`smoke_v1`)

There is **no** committed post-blind smoke NLI table. The Phase 0 leaked run (mock saw `UNANSWERABLE`) is not used here.

Unit evidence after blinding (`tests/test_generator_blind.py`, `tests/test_pipeline_smoke.py`):

| Observation | Stage | Note |
| --- | --- | --- |
| Mock does not abstain when chunks exist, even if `test_type=unanswerable` | generation | Abstention policy is empty retrieval only |
| Mock does not copy `gold_answer` | eval_bug ruled out | Leakage test |
| Empty retrieved list → canned abstention | generation (protocol) | Matches `empty_context` policy |

Smoke adversarial gold (`data/adversarial/benchmark_adversarial.json`): 2 unanswerable + 1 conflicting (NovaDrive). `scenario_type` on those JSON rows is still the legacy value `standard`; v1 items use explicit scenario names.

## v1.0.0 adversarial slice (Dense_Chunk128, run `a97ad68f`)

Copied from `experiments/runs/20261028T183042Z_a97ad68f/predictions.jsonl`. Other configs in that run share the same retrieval Recall@5 / MRR (0.8333 / 0.8125) on the full 24-item set (`reports/benchmark_summary.md`).

| id | scenario | Recall@5 | abstained | claim support | answer F1 | primary stage | Why |
| --- | --- | --- | --- | --- | --- | --- | --- |
| v1_013 | unanswerable | 0.0 (5 chunks) | false | 0.5 | 0.0 | retrieval then generation | Apollo meals question retrieved landing text; mock copied it |
| v1_014 | unanswerable | 0.0 (5 chunks) | false | 0.5 | 0.0 | retrieval then generation | Japan-share question retrieved HarborNet Q2 totals |
| v1_015 | unanswerable | 0.0 (5 chunks) | false | 0.0 | 0.0 | retrieval then generation | 2024 visits question retrieved Yellowstone nature blurb |
| v1_016 | unanswerable | 0.0 (5 chunks) | false | 0.0 | 0.0 | retrieval then generation | Pediatric OS question retrieved adult SHORELINE text |
| v1_017 | conflicting | 1.0 | false | 0.0 | 0.3704 | generation | Copied the CedarRail PR only; no hedge |
| v1_018 | conflicting | 1.0 | false | 0.5 | 0.4667 | generation | Copied the audit sentence; gold requires stating the conflict |
| v1_019 | mixed_support | 1.0 | false | 0.5 | 0.6667 | generation | RQ3 pattern: token F1 0.6667 with claim support 0.5 |
| v1_020 | mixed_support | 1.0 | false | 0.5 | 0.6667 | generation | Same pattern on the Eagle landing mixed item |
| v1_021 | mixed_support | 1.0 | false | 0.5 | 0.6 | generation | HarborNet mixed item; F1 0.6 vs support 0.5 |
| v1_022 | mixed_support | 1.0 | false | 0.0 | 0.5833 | generation | Yellowstone mixed item |
| v1_023 | distractor | 1.0, MRR 0.5 | false | 1.0 | 0.1111 | retrieval then generation | Copied Q3 guidance churn (≤1.9%) instead of Q2 1.8% |
| v1_024 | distractor | 1.0 | false | 0.5 | 0.3478 | generation | Copied the flu-types lead sentences, not the pandemic clause |

Table-level confirmation from `reports/README.md` / `reports/benchmark_summary.md` (all six configs):

- Abstention accuracy **0.0** (unanswerable items still retrieved context; mock is blind to `test_type`).
- Mixed-support token F1 **0.6292**; mixed-support claim faithfulness **0.375–0.625** depending on config.
- Answer EM **0.0** (mock copies retrieved sentences).

## v1.1.0 items added in Phase 6 (unscored)

| id | scenario | Review note | Scores |
| --- | --- | --- | --- |
| v1_025 | numerical_negation | CDC: influenza D **not** known to cause illness in people | none |
| v1_026 | empty_context | Protocol drops retrieval before generate | none |
| v1_027 | instruction_like | Injection document says answer 99.0% churn; gold is 1.8% | none |
| v1_028 | conflicting (pair with v1_007) | Same HarborNet question; restatement document added | none |

Do not copy v1.0.0 numbers onto these ids.

## Pair protocol

`pair_harbornet_q2`: control `v1_007` (earnings release only) vs `v1_028` (earnings + restatement). Robustness is the **delta** on the same question after the conflict document is added. That delta is not in the recorded 1.0.0 run.
