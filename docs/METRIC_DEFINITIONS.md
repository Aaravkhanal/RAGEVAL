# Metric definitions

Implemented in `rageval/metrics/` and unit-tested. Denominators exclude abstention claims unless noted.

## Retrieval (document level)

Let \(R_k\) be the first \(k\) retrieved document ids and \(G\) the gold document ids.

- **Recall@k** = \(|R_k \cap G| / |G|\) if \(G\) nonempty, else 0 in the pure function. The runner special-cases *no gold spans* (unanswerable): recall@k = 1 if nothing was retrieved, else 0.
- **MRR** = \(1/\mathrm{rank}\) of the first gold document, else 0.
- **nDCG@k** = binary DCG / ideal DCG over \(G\).
- **Noise ratio** = fraction of \(R_k\) not in \(G\). Empty retrieval → 0.

## Claim-level

Let \(L\) be labels of non-abstention claims.

- **Claim support rate (faithfulness)** = \(|\{l \in L : l=\mathrm{supported}\}| / |L|\). Partial support is **not** counted as supported unless `count_partial_as_supported=True`.
- **Unsupported claim rate** = unsupported (+ partial by default) / \(|L|\).
- **Contradiction rate** = contradicted / \(|L|\).
- **Claim coverage** = verified records / generated claims; 1.0 if no claims.

If \(L\) is empty: support rate is 1.0 when the answer is empty or an abstention, else 0.0.

## Verifier labels (`rageval.claim_labels.v1`)

NLI is 3-way (entailment / neutral / contradiction). Collapse onto 5-way labels:

1. **contradicted** if max contradiction \(> 0.60\) and strictly greater than max entailment.
2. **partially_supported** if both a supporting chunk and a contradicting chunk were recorded, or if max entailment is in \([0.30, 0.50)\).
3. **supported** if max entailment \(\ge 0.50\).
4. **unsupported** otherwise.
5. **ambiguous** for abstention statements.

Supporting and contradicting chunk id lists are **always retained** when both exist. Multi-hop fusion runs only when `evaluator.enable_multi_hop=true` and records `verifier_method=nli_multihop_pair`.

RQ2 scoring uses `rageval/metrics/classification.py` on `data/gold/verifier_eval_v1.json`.

## Citation

- **Existence precision** = in-pool citation tokens / all citation tokens (1.0 if none).
- **Marker recall** (legacy `citation_recall`) = sentences with a citation token / sentences.
- **Support precision** = citations whose chunk supports the associated claim / evaluated claim-citation pairs (1.0 if none).
- **Completeness** = factual claims with ≥1 supporting citation / factual claims (1.0 if none).

## Answer-level

Implemented in `rageval/metrics/answer.py`.

Normalize: lowercase, strip punctuation, drop English articles `a`/`an`/`the`, collapse whitespace, split on spaces.

- **Exact match (EM)** = 1 if normalized prediction equals normalized gold, else 0.
- **Token F1** = bag-of-tokens F1 after the same normalize. Empty/empty is 1.0.
- **Unanswerable items** (expected abstention and no gold string): EM/F1 = 1 if the system abstained, else 0.

These scores ignore retrieved evidence. A mixed-support answer can keep token F1 high while claim-level labels are mixed (`mixed_support_answer_gap`).

Abstention accuracy = fraction of unanswerable items with `abstained=True`.

## System

Stage latencies from `perf_counter`. `estimated_cost_usd` is **null** unless `prompt_usd_per_million` and `completion_usd_per_million` are set on `EvaluatorConfig`, with `pricing_source` recorded.

## Empty-set and abstention denominators

| Metric | Empty / edge policy |
| --- | --- |
| recall_at_k / MRR / nDCG (pure) | Empty gold → 0 |
| recall_at_k on unanswerable items | 1 if nothing retrieved, else 0 |
| noise_ratio | Empty retrieval → 0 |
| claim support / unsupported / contradiction (pure) | Empty assessable → 0. Caller drops abstention claims. |
| claim support in the evaluator | 1 if the answer is empty or an abstention and there are no factual claims |
| claim coverage | No generated claims → 1 |
| citation existence / support precision / completeness / marker recall | Empty denominator → 1 |
| abstention accuracy | No unanswerable items → 1 |
| answer EM/F1 | Unanswerable, no gold string: 1 if abstained else 0 |
| estimated_cost_usd | Null unless both USD/million prices **and** `pricing_source` are set |

## Aggregation

Means over examples. There is **no official composite / overall score**. Compare named metrics from `rageval.metrics.registry`.

Bootstrap percentile CIs (`rageval/metrics/bootstrap.py`) are **confirmatory** only when \(n \ge 30\) **and** items are treated as i.i.d. Items that share documents are not independent. Smaller \(n\) still emits an interval labeled `assumptions_met=false`. Significance p-values in `analysis/significance.py` are uncorrected; `confirmatory` is false when \(n < 30\).

The smoke set (\(n=8\)) and `benchmark_v1` (v1.0.0 \(n=24\); v1.1.0 \(n=28\); v1.2.0 \(n=32\), items share documents) are underpowered for confirmatory inference.

Robustness tables are **named-metric means sliced by `scenario_type`** (`rageval.metrics.aggregate.robustness_by_scenario_type`). They are not an overall score.

Official run tables are generated from `metrics.json` (`rageval.benchmark.reporter.markdown_from_metrics`). Significance tests with \(n < 30\) are diagnostic (`underpowered=true`).
