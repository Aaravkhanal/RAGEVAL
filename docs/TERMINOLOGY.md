# RAGeval terminology

All support judgments are relative to **supplied evidence**, not the web.

| Term | Definition |
| --- | --- |
| **Claim** | An atomic factual proposition extracted from a generated answer, with offsets into that answer when available. |
| **Evidence passage** | A retrieved chunk (or gold span) identified by document id and optional passage/chunk id. |
| **Supporting evidence** | A passage from which the claim is a reasonable reading (NLI entailment or gold `supported`). |
| **Contradictory evidence** | A passage that asserts the negation or an incompatible value. |
| **Partial support** | Some constraints of the claim match the evidence; others are missing or weaker. |
| **Ambiguous** | The evidence is insufficient to choose among the other labels, including abstention statements. |
| **Faithfulness** | Fraction of *assessable factual claims* labeled `supported`. Distinct from world truth. |
| **Factual correctness** | Agreement with a gold answer or world knowledge. Not computed unless a gold answer metric is enabled. |
| **Citation precision (existence)** | Citation tokens that resolve to an in-pool chunk / all citation tokens. |
| **Citation support precision** | Evaluated citations whose cited chunk is in `supporting_chunk_ids` / evaluated citations. |
| **Citation completeness** | Factual claims with ≥1 supporting citation / factual claims (citation required by default). |
| **Retrieval relevance** | Document-id overlap with gold evidence documents unless a gold `chunk_id` is present. |
| **Answerability** | Whether the document set contains enough evidence to answer. |
| **Abstention** | The answer refuses to assert a fact, typically for unanswerable items. Stored on the query result, not as `supported`. |
| **Unreliable answer** | An answer with unsupported or contradicted assessable claims, invalid citations, or missing required abstention. |

Deprecated prototype aliases: `ENTAILEMENT` → `supported`, `NEUTRAL` → `unsupported`, `CONTRADICTION` → `contradicted`. Loaders still accept the old strings.
