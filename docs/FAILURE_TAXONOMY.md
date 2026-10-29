# Failure taxonomy

Use this taxonomy when a score drops or an item is wrong. Name a **stage**, not only a metric.

Implemented in `rageval/analysis/failure_taxonomy.py`. The tagger is a documented heuristic. It does not prove causation.

## Stages

| Stage | What went wrong |
| --- | --- |
| `dataset` | Gold, span, license, or item construction is wrong (wrong split, non-verbatim span, unlabeled conflict). |
| `retrieval` | Gold documents are missing from the retrieved pool, or unanswerable items still retrieve context. |
| `generation` | The model answered from context when it should abstain, copied one side of a conflict, followed instruction-like document text, or emitted unsupported claims. |
| `decomposition` | Claims were not split, or a claim was emitted that was never verified. |
| `verifier` | NLI/heuristic label disagrees with gold on a supplied premise (RQ2), or a silent fallback ran. |
| `citation` | Citation tokens are not in the retrieved pool, or the cited chunk does not support the claim. |
| `eval_bug` | Harness error: empty-context protocol left chunks in place, generator saw `test_type`, metric denominator mismatch. |

## Reviewed scenario types

Each of these has at least one **reviewed** `benchmark_v1` item (`reviewed=true`):

| `scenario_type` | What it tests |
| --- | --- |
| `unanswerable` | Question not answered by the corpus; expect abstention. |
| `conflicting` | Two documents cannot both be true; gold states the conflict. |
| `distractor` | Lexical neighbors that are off-domain relative to gold. |
| `mixed_support` | Gold answer is fully supported; an example mixed string keeps token F1 high. |
| `numerical_negation` | Negated or numerically precise gold (CDC “not known to cause”). |
| `empty_context` | Harness protocol: retrieve, then drop all chunks before generation. |
| `instruction_like` | A document contains assistant instructions that contradict gold. |

Paired items share `pair_id` and the **same question**. The `with_conflict` member adds a conflict document. Loader: `DatasetLoader.load_paired_items()`.

## Attribution rules (heuristic)

1. `empty_context` with `retrieved_count > 0` → `eval_bug`.
2. Unanswerable with retrieved context → `retrieval`; answered instead of abstaining → `generation`.
3. Conflicting answer without hedge language (`conflict`, `disagree`, `whereas`, …) → `generation`.
4. Mixed-support with answer F1 ≥ 0.5 and claim support < 1 → `generation`.
5. Answerable item with Recall@5 = 0 → `retrieval`.
6. Hallucinated citation tokens or support precision < 1 → `citation`.
7. Claims with no verifications → `decomposition`.

Primary stage is the first match in this order. Record every matching stage in `stages`.

## What not to do

- Do not treat a faithfulness drop as a retriever ranking without checking retrieval metrics.
- Do not invent per-item causes that are not in a run file.
- Do not leak `test_type` into the generator to “fix” unanswerable items.
