# Inter-annotator agreement

**Rater A:** `single-author, disclosed`. **Rater B:** `rater_b_llm_grok`.
**Labeled both:** 24 / shared 24.
**Complete:** True.
**Percent agreement:** 0.9583.
**Cohen's kappa:** 0.9423.

Rater B is a disclosed LLM annotator. Cohen's kappa is diagnostic, not confirmatory human IAA. A template or self-repeat is not a second annotator.

This is not Niu et al. 2024 RAGTruth. Labels measure evidence support.

**Disagreements:** 1.

| id | rater A | rater B |
| --- | --- | --- |
| `ve_020` | unsupported | contradicted |

**Confusion (rows = rater A, columns = rater B):**

| A \ B | supported | partially_supported | unsupported | contradicted | ambiguous |
| --- | --- | --- | --- | --- | --- |
| supported | 10 | 0 | 0 | 0 | 0 |
| partially_supported | 0 | 3 | 0 | 0 | 0 |
| unsupported | 0 | 0 | 4 | 1 | 0 |
| contradicted | 0 | 0 | 0 | 5 | 0 |
| ambiguous | 0 | 0 | 0 | 0 | 1 |
