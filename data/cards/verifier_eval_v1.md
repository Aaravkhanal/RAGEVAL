# Data card — verifier_eval_v1

| Field | Value |
| --- | --- |
| Dataset id | `verifier_eval_v1` |
| Size | 24 labeled claim–premise pairs |
| Schema | `rageval.claim_labels.v1` |
| Mix | 10 supported, 5 contradicted, 5 unsupported, 3 partially_supported, 1 ambiguous (abstention) |
| Annotator | Single author, disclosed |
| Premises | Copied from `benchmark_v1` documents (US government PD excerpts and original CC-BY-4.0 fiction) |
| Use | RQ2 verifier per-class P/R/F1. Not a hidden test for prompt or threshold tuning. |

Labels measure **support by the supplied premise**, not world knowledge.
