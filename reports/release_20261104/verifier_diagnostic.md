# Verifier evaluation — verifier_eval_v1

**Method:** `heuristic`  
**n:** 24  
**Accuracy:** 0.8333  
**Macro-F1:** 0.8529  
**Annotator:** single-author, disclosed  
**Gold file:** `/Users/aaravkhanal/Desktop/RAGEVAL/data/gold/verifier_eval_v1.json`

Primary metrics are context-bounded: each item supplies one premise passage. This is not a world-knowledge fact check.

## Per-class scores

| Label | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| supported | 0.800 | 0.800 | 0.800 | 10 |
| partially_supported | 0.667 | 0.667 | 0.667 | 3 |
| unsupported | 0.833 | 1.000 | 0.909 | 5 |
| contradicted | 1.000 | 0.800 | 0.889 | 5 |
| ambiguous | 1.000 | 1.000 | 1.000 | 1 |

## Confusion matrix (rows = gold)

gold\pred | supported | partially_supported | unsupported | contradicted | ambiguous
--- | --- | --- | --- | --- | ---
supported | 8 | 1 | 1 | 0 | 0
partially_supported | 1 | 2 | 0 | 0 | 0
unsupported | 0 | 0 | 5 | 0 | 0
contradicted | 1 | 0 | 0 | 4 | 0
ambiguous | 0 | 0 | 0 | 0 | 1

## Failures (4)

- `ve_003` gold=contradicted pred=supported: Influenza D viruses cause seasonal epidemics in people.
- `ve_010` gold=supported pred=unsupported: The Greater Yellowstone Ecosystem is 28,000 square miles.
- `ve_012` gold=supported pred=partially_supported: Yellowstone has 67 mammal species and 285 bird species.
- `ve_018` gold=partially_supported pred=supported: Influenza A, B, C, and D viruses cause seasonal epidemics in people.

Do not treat these numbers as confirmatory RQ2 results beyond this labeled set.
