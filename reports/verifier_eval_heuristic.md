# Verifier evaluation — verifier_eval_v1

**Method:** `heuristic`  
**n:** 24  
**Accuracy:** 0.5833  
**Macro-F1:** 0.5140  
**Annotator:** single-author, disclosed  
**Gold file:** `/Users/aaravkhanal/Desktop/RAGEVAL/data/gold/verifier_eval_v1.json`

Primary metrics are context-bounded: each item supplies one premise passage. This is not a world-knowledge fact check.

## Per-class scores

| Label | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| supported | 0.600 | 0.900 | 0.720 | 10 |
| partially_supported | 0.000 | 0.000 | 0.000 | 3 |
| unsupported | 0.600 | 0.600 | 0.600 | 5 |
| contradicted | 0.333 | 0.200 | 0.250 | 5 |
| ambiguous | 1.000 | 1.000 | 1.000 | 1 |

## Confusion matrix (rows = gold)

gold\pred | supported | partially_supported | unsupported | contradicted | ambiguous
--- | --- | --- | --- | --- | ---
supported | 9 | 0 | 1 | 0 | 0
partially_supported | 3 | 0 | 0 | 0 | 0
unsupported | 0 | 0 | 3 | 2 | 0
contradicted | 3 | 0 | 1 | 1 | 0
ambiguous | 0 | 0 | 0 | 0 | 1

## Failures (10)

- `ve_003` gold=contradicted pred=supported: Influenza D viruses cause seasonal epidemics in people.
- `ve_008` gold=contradicted pred=supported: The Eagle landed in the Ocean of Storms.
- `ve_011` gold=contradicted pred=unsupported: Yellowstone contains no hydrothermal features.
- `ve_012` gold=supported pred=unsupported: Yellowstone has 67 mammal species and 285 bird species.
- `ve_015` gold=contradicted pred=supported: HarborNet Q2 2025 subscription revenue was $50 million.
- `ve_017` gold=partially_supported pred=supported: HarborNet Q2 2025 subscription revenue was $412 million and monthly churn was 9.8%.
- `ve_018` gold=partially_supported pred=supported: Influenza A, B, C, and D viruses cause seasonal epidemics in people.
- `ve_020` gold=unsupported pred=contradicted: LumenGrid is deployed in 40 availability zones.
- `ve_022` gold=unsupported pred=contradicted: Five-year overall survival for pediatric Nerexin patients was 81%.
- `ve_024` gold=partially_supported pred=supported: CedarRail opened unsupervised light-rail service in Tacoma with 40 driverless cars and a perfect five-year safety record.

Do not treat these numbers as confirmatory RQ2 results beyond this labeled set.
