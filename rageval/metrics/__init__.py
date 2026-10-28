"""Pure metric functions with documented formulas."""

from rageval.metrics.answer import (
    answer_em_f1,
    exact_match,
    mixed_support_answer_gap,
    normalize_answer,
    token_f1,
)
from rageval.metrics.claims import (
    claim_coverage,
    claim_support_rate,
    contradiction_rate,
    unsupported_claim_rate,
)
from rageval.metrics.retrieval import mrr, ndcg_at_k, noise_ratio, recall_at_k
from rageval.metrics.citation import citation_completeness, citation_existence_precision
from rageval.metrics.classification import (
    accuracy,
    confusion_matrix,
    macro_f1,
    per_class_scores,
)

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
    "normalize_answer",
    "exact_match",
    "token_f1",
    "answer_em_f1",
    "mixed_support_answer_gap",
    "confusion_matrix",
    "per_class_scores",
    "macro_f1",
    "accuracy",
]
