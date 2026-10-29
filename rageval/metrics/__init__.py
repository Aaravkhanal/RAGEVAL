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
from rageval.metrics.abstention import abstention_accuracy
from rageval.metrics.bootstrap import MIN_N_CONFIRMATORY, bootstrap_mean_ci
from rageval.metrics.citation import (
    citation_completeness,
    citation_existence_precision,
    citation_marker_recall,
    citation_support_precision,
)
from rageval.metrics.aggregate import robustness_by_scenario_type, summarize_results
from rageval.metrics.registry import (
    REGISTRY,
    get_metric,
    has_overall_score,
    official_metrics,
)
from rageval.metrics.system import estimated_cost_usd
from rageval.metrics.classification import (
    accuracy,
    confusion_matrix,
    macro_f1,
    per_class_scores,
)
from rageval.metrics.agreement import cohen_kappa, percent_agreement, summarize_agreement

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
    "citation_support_precision",
    "citation_completeness",
    "citation_marker_recall",
    "abstention_accuracy",
    "estimated_cost_usd",
    "bootstrap_mean_ci",
    "MIN_N_CONFIRMATORY",
    "REGISTRY",
    "get_metric",
    "official_metrics",
    "has_overall_score",
    "summarize_results",
    "robustness_by_scenario_type",
    "normalize_answer",
    "exact_match",
    "token_f1",
    "answer_em_f1",
    "mixed_support_answer_gap",
    "confusion_matrix",
    "per_class_scores",
    "macro_f1",
    "accuracy",
    "cohen_kappa",
    "percent_agreement",
    "summarize_agreement",
]
