# Annotation guidelines (benchmark_v1)

Single-author annotation. Disclosed. Not a multi-rater gold standard.

A second independent human is required for confirmatory IAA. Export rater A and a blank rater-B template live under `data/gold/iaa/`. `rageval iaa` reports Cohen's kappa on aligned 5-way labels; unfilled B yields `kappa=null`, not 0. A self-repeat is not a second annotator. The filled file `annotator_b_verifier_eval_v1.json` is a disclosed LLM annotator (`rater_b_llm_grok`); treat that kappa as diagnostic.

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
- Paired conflict: same `question` as a control item, `pair_id` shared, `pair_role=with_conflict`, plus the added conflict document.

## Other adversarial scenarios

- Lexical distractor (`scenario_type=distractor`): gold lives in a small subset; other corpus docs share little more than tokens.
- Numerical/negation: gold hinges on a number or a negation (`not`, `no`, `never`).
- Empty context: `scenario_type=empty_context`; the harness drops retrieved chunks before generation.
- Instruction-like: a document contains assistant instructions that contradict gold. Gold stays on the evidence document.

Reviewed exemplars set `reviewed=true`. Synthetic `PerturbationEngine` items stay `reviewed=false`.

## Answer-level gold

`gold_answer` is the string used for EM/F1. It should be fully supported for standard and mixed-support items. Do not put unsupported clauses into `gold_answer`.
