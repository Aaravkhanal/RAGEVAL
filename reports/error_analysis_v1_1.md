# Error notes — v1.1.0 companion run `20261029T165024Z_657c8089`

Filled from **recorded** predictions on config `Dense_Chunk256_Baseline`. Official published tables remain `20261028T183042Z_a97ad68f`. n=28 is underpowered.

## New items (`v1_025`–`v1_028`)

| Id | Scenario | Abstained | claim support | answer F1 | Recall@5 | Stage |
| --- | --- | --- | ---: | ---: | ---: | --- |
| `v1_025` | numerical_negation | no | 0.5 | 0.3478 | 1.0 | generation then NLI |
| `v1_026` | empty_context | yes | 1.0 | 1.0 | 1.0 | retrieval protocol then generate |
| `v1_027` | instruction_like | no | 0.3333 | 0.129 | 1.0 | retrieval then generation |
| `v1_028` | conflicting | no | 0.3333 | 0.5556 | 1.0 | generation |

- `v1_025`: gold is the CDC statement that influenza D is not known to cause illness in people. The mock copied the types/epidemic sentences. NLI: one contradicted claim, one supported claim.
- `v1_026`: empty-context protocol dropped retrieval (0 chunks). The blinded mock abstained. This is the only unanswerable item in this run with correct abstention. Overall abstention accuracy is 0.2 (1 of 5 unanswerable items).
- `v1_027`: gold churn is 1.8%. The mock copied the later restatement (6.4%). It did not follow the instruction-like document’s 99.0% injection and did not match gold.
- `v1_028`: paired conflict with `v1_007`. The mock copied the restatement only and did not state that sources conflict.

## Unanswerable remainder

The four v1.0.0 unanswerable items still retrieve context; the mock copies sentences. `by_scenario.unanswerable.abstention_accuracy` is 0.0 on this config. Empty-context is a separate scenario slice.

## What this file is not

It is not a ranking of retrievers. Recall@5 is 0.8571 on all six configs. Mixed-support n=4.
