# Annotation guidelines (benchmark_v1)

Single-author annotation. Disclosed. Not a multi-rater gold standard.

## Document rules

- Every document has `license` and either `source_url` or `provenance`.
- U.S. government excerpts stay close to the retrieved page. Record URL and retrieval date.
- Original fiction is labeled CC-BY-4.0 and uses invented names.
- Do not paste Wikipedia (CC-BY-SA) or other share-alike text.

## Question rules

- The question must be answerable from the cited gold documents, or explicitly unanswerable.
- Do not drop hard items (unanswerable, conflicting, mixed-support).
- `split=test` items are frozen: do not retune NLI thresholds or prompts on them.

## Evidence spans

- `gold_evidence_spans[].span` must be a **verbatim substring** of the source document.
- Ellipsis (`...`) is allowed only in smoke_v1. v1 forbids it.

## Claims

Labels measure **support by the supplied documents**, not world knowledge.

| Label | Use when |
| --- | --- |
| `supported` | The document entails the claim. |
| `partially_supported` | Some but not all of the claim is entailed. |
| `unsupported` | The documents neither entail nor contradict the claim. |
| `contradicted` | A document entails the negation. |
| `ambiguous` | The documents are insufficient to decide, including genuine conflicts inside one span. |

Mixed-support items: at least one `supported` gold claim and at least one non-supported gold claim. The `gold_answer` remains the fully supported answer. Put the mixed string in `metadata.example_mixed_answer`.

## Unanswerable and conflicting

- Unanswerable: `expected_abstention=true`, empty gold spans, `gold_answer=null`.
- Conflicting: two documents that cannot both be true; gold answer must state the conflict.

## Answer-level gold

`gold_answer` is the string used for EM/F1. It should be fully supported for standard and mixed-support items. Do not put unsupported clauses into `gold_answer`.
