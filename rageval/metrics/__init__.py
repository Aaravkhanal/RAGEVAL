"""Pure metric functions with documented formulas."""

from rageval.metrics.claims import (
    claim_coverage,
    claim_support_rate,
    contradiction_rate,
    unsupported_claim_rate,
)
from rageval.metrics.retrieval import mrr, ndcg_at_k, noise_ratio, recall_at_k
from rageval.metrics.citation import citation_completeness, citation_existence_precision

__all__ = [
    "claim_support_rate",
    "unsupported_claim_rate",
    "contradiction_rate",
    "claim_coverage",
    "recall_at_k",
    "mrr",
    "ndcg_at_k",
    "noise_ratio",
    "citation_existence_precision",
    "citation_completeness",
]
