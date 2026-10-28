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

## Aggregation

Means over examples. Significance tests exist in `analysis/significance.py` but require adequate \(n\); the smoke set (\(n=8\)) is underpowered.
