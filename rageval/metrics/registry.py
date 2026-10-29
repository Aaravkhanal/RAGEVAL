"""Official metric registry. There is no composite ranking score."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class MetricSpec:
    name: str
    family: str
    description: str
    empty_policy: str
    official: bool = True
    legacy: bool = False


def _specs() -> List[MetricSpec]:
    return [
        MetricSpec(
            "recall_at_k",
            "retrieval",
            "|gold docs in retrieved[:k]| / |gold docs|.",
            "Empty gold → 0.0 in the pure function. Unanswerable items (no gold spans) are special-cased in RetrievalMetricsCalculator: 1.0 if nothing retrieved, else 0.0.",
        ),
        MetricSpec(
            "mrr",
            "retrieval",
            "1 / rank of the first gold document.",
            "No gold or no hit → 0.0.",
        ),
        MetricSpec(
            "ndcg_at_k",
            "retrieval",
            "Binary-relevance nDCG@k at document id.",
            "Empty gold or k<=0 → 0.0.",
        ),
        MetricSpec(
            "noise_ratio",
            "retrieval",
            "Fraction of retrieved[:k] docs that are not gold.",
            "Empty retrieval → 0.0.",
        ),
        MetricSpec(
            "claim_support_rate",
            "claim",
            "supported / assessable labels (faithfulness). Partial is not supported unless flagged.",
            "Caller must drop abstention claims. Empty assessable → 0.0 in the pure function; evaluator uses 1.0 if the answer is empty or an abstention.",
        ),
        MetricSpec(
            "unsupported_claim_rate",
            "claim",
            "unsupported (+ partial by default) / assessable.",
            "Empty assessable → 0.0.",
        ),
        MetricSpec(
            "contradiction_rate",
            "claim",
            "contradicted / assessable.",
            "Empty assessable → 0.0.",
        ),
        MetricSpec(
            "claim_coverage",
            "claim",
            "verified records / generated claims.",
            "No generated claims → 1.0.",
        ),
        MetricSpec(
            "citation_existence_precision",
            "citation",
            "In-pool citation tokens / all citation tokens.",
            "No citations → 1.0.",
        ),
        MetricSpec(
            "citation_support_precision",
            "citation",
            "Citations whose chunk supports the claim / evaluated claim-citation pairs.",
            "No evaluated citations → 1.0.",
        ),
        MetricSpec(
            "citation_completeness",
            "citation",
            "Factual claims with ≥1 supporting citation / claims that require a citation.",
            "No requiring claims → 1.0.",
        ),
        MetricSpec(
            "citation_marker_recall",
            "citation",
            "Sentences with a citation token / sentences (legacy marker recall).",
            "No sentences → 1.0.",
            legacy=True,
        ),
        MetricSpec(
            "exact_match",
            "answer",
            "1 if normalized prediction equals normalized gold.",
            "Unanswerable with no gold string: 1 if abstained else 0. Missing gold on an answerable item → undefined (None).",
        ),
        MetricSpec(
            "token_f1",
            "answer",
            "Bag-of-tokens F1 after SQuAD-style normalize.",
            "Empty/empty → 1.0. Unanswerable same as exact_match.",
        ),
        MetricSpec(
            "abstention_accuracy",
            "answer",
            "Among unanswerable items, fraction with abstained=True.",
            "No unanswerable items → 1.0.",
        ),
        MetricSpec(
            "estimated_cost_usd",
            "system",
            "Token cost from configured USD-per-million prices.",
            "Null unless both prices and pricing_source are set.",
        ),
        MetricSpec(
            "macro_f1",
            "verifier",
            "Unweighted mean of per-class F1 on verifier_eval gold.",
            "Missing class with no gold and no predictions → F1 0.0 for that class.",
        ),
    ]


REGISTRY: Dict[str, MetricSpec] = {spec.name: spec for spec in _specs()}


def get_metric(name: str) -> MetricSpec:
    if name not in REGISTRY:
        raise KeyError(f"Unknown metric {name!r}. Official names: {sorted(REGISTRY)}")
    return REGISTRY[name]


def official_metrics(*, include_legacy: bool = True) -> List[MetricSpec]:
    return [
        spec
        for spec in REGISTRY.values()
        if spec.official and (include_legacy or not spec.legacy)
    ]


def has_overall_score() -> bool:
    """The project has no official composite ranking score."""
    return False


def compute(name: str, *args, **kwargs):
    """Dispatch to the pure function for `name`."""
    from rageval.metrics.abstention import abstention_accuracy
    from rageval.metrics.answer import exact_match, token_f1
    from rageval.metrics.citation import (
        citation_completeness,
        citation_existence_precision,
        citation_marker_recall,
        citation_support_precision,
    )
    from rageval.metrics.claims import (
        claim_coverage,
        claim_support_rate,
        contradiction_rate,
        unsupported_claim_rate,
    )
    from rageval.metrics.classification import macro_f1
    from rageval.metrics.retrieval import mrr, ndcg_at_k, noise_ratio, recall_at_k
    from rageval.metrics.system import estimated_cost_usd

    fns = {
        "recall_at_k": recall_at_k,
        "mrr": mrr,
        "ndcg_at_k": ndcg_at_k,
        "noise_ratio": noise_ratio,
        "claim_support_rate": claim_support_rate,
        "unsupported_claim_rate": unsupported_claim_rate,
        "contradiction_rate": contradiction_rate,
        "claim_coverage": claim_coverage,
        "citation_existence_precision": citation_existence_precision,
        "citation_support_precision": citation_support_precision,
        "citation_completeness": citation_completeness,
        "citation_marker_recall": citation_marker_recall,
        "exact_match": exact_match,
        "token_f1": token_f1,
        "abstention_accuracy": abstention_accuracy,
        "estimated_cost_usd": estimated_cost_usd,
        "macro_f1": macro_f1,
    }
    if name not in fns:
        raise KeyError(name)
    return fns[name](*args, **kwargs)


def metric_names() -> List[str]:
    return sorted(REGISTRY)
