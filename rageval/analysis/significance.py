"""Statistical significance analysis (Paired t-tests & Wilcoxon signed-rank tests) for ablation comparisons."""

from __future__ import annotations
from typing import List, Dict, Any
import numpy as np
from scipy import stats
from rageval.core.schemas import BenchmarkRunSummary


class SignificanceAnalyzer:
    """Evaluates whether differences in retrieval recall, faithfulness, or hallucination

    between RAG pipeline configurations are statistically significant (p < 0.05).
    """

    @staticmethod
    def compare_runs(
        baseline: BenchmarkRunSummary,
        treatment: BenchmarkRunSummary,
        metric: str = "faithfulness",
        *,
        independent: bool = False,
    ) -> Dict[str, Any]:
        """Compares paired per-query scores between baseline and treatment configurations.

        Confirmatory (`is_significant` may be true) only when n≥MIN_N_CONFIRMATORY
        **and** `independent=True`. Items that share documents are not i.i.d.;
        leave `independent` false (the default).
        """
        if len(baseline.results) != len(treatment.results):
            raise ValueError("Baseline and treatment must have identical query evaluation counts.")
        pairs = list(zip(baseline.results, treatment.results))
        if any(left.query_id != right.query_id for left, right in pairs):
            raise ValueError("Baseline and treatment query ids must match in order.")

        if metric in {"recall", "evidence_recall"}:
            pairs = [
                (left, right)
                for left, right in pairs
                if left.test_type.value != "unanswerable"
                and right.test_type.value != "unanswerable"
                and left.retrieval_metrics.no_answer_empty_retrieval is None
                and right.retrieval_metrics.no_answer_empty_retrieval is None
            ]
            if not pairs:
                raise ValueError("No answerable paired queries for retrieval comparison.")

        if metric == "faithfulness":
            vals_a = [left.faithfulness_score for left, _ in pairs]
            vals_b = [right.faithfulness_score for _, right in pairs]
        elif metric == "recall":
            vals_a = [left.retrieval_metrics.recall_at_5 for left, _ in pairs]
            vals_b = [right.retrieval_metrics.recall_at_5 for _, right in pairs]
        elif metric == "evidence_recall":
            pairs = [(left, right) for left, right in pairs if left.retrieval_metrics.evidence_recall_at_5 is not None and right.retrieval_metrics.evidence_recall_at_5 is not None]
            if not pairs:
                raise ValueError("No paired evidence-recall scores.")
            vals_a = [left.retrieval_metrics.evidence_recall_at_5 for left, _ in pairs]
            vals_b = [right.retrieval_metrics.evidence_recall_at_5 for _, right in pairs]
        elif metric == "latency":
            vals_a = [left.total_latency_ms for left, _ in pairs]
            vals_b = [right.total_latency_ms for _, right in pairs]
        else:
            vals_a = [left.hallucination_rate for left, _ in pairs]
            vals_b = [right.hallucination_rate for _, right in pairs]

        diffs = np.array(vals_b) - np.array(vals_a)
        mean_diff = float(np.mean(diffs))
        from rageval.metrics.bootstrap import MIN_N_CONFIRMATORY, bootstrap_mean_ci

        n = int(len(diffs))
        confirmatory = n >= MIN_N_CONFIRMATORY and independent
        underpowered = not confirmatory
        if n < MIN_N_CONFIRMATORY:
            note = (
                f"n={n} < {MIN_N_CONFIRMATORY}: tests are diagnostic; "
                "is_significant stays false."
            )
        elif not independent:
            note = (
                f"n={n} but items are not treated as i.i.d.; tests are diagnostic; "
                "is_significant stays false."
            )
        else:
            note = None

        if n < 2:
            return {
                "metric": metric,
                "baseline_name": baseline.config_name,
                "treatment_name": treatment.config_name,
                "n": n,
                "mean_baseline": round(float(np.mean(vals_a)), 4),
                "mean_treatment": round(float(np.mean(vals_b)), 4),
                "mean_diff": round(mean_diff, 4),
                "p_value_ttest": None,
                "p_value_wilcoxon": None,
                "is_significant": False,
                "underpowered": True,
                "confirmatory": False,
                "independent_items_assumed": independent,
                "note": "A paired significance test requires at least two answerable queries.",
            }

        # If identical values across all queries, p-value is 1.0
        if np.all(diffs == 0):
            return {
                "metric": metric,
                "baseline_name": baseline.config_name,
                "treatment_name": treatment.config_name,
                "n": n,
                "mean_diff": 0.0,
                "p_value_ttest": 1.0,
                "p_value_wilcoxon": 1.0,
                "is_significant": False,
                "underpowered": underpowered,
                "confirmatory": confirmatory,
                "independent_items_assumed": independent,
                "note": note,
            }

        # 1. Paired t-test
        t_stat, p_ttest = stats.ttest_rel(vals_b, vals_a)

        # 2. Wilcoxon signed-rank test (non-parametric)
        try:
            w_stat, p_wilcoxon = stats.wilcoxon(diffs)
        except Exception:
            p_wilcoxon = p_ttest

        return {
            "metric": metric,
            "baseline_name": baseline.config_name,
            "treatment_name": treatment.config_name,
            "n": n,
            "mean_baseline": round(float(np.mean(vals_a)), 4),
            "mean_treatment": round(float(np.mean(vals_b)), 4),
            "mean_diff": round(mean_diff, 4),
            "t_statistic": round(float(t_stat), 4),
            "p_value_ttest": round(float(p_ttest), 4),
            "p_value_wilcoxon": round(float(p_wilcoxon), 4),
            "is_significant": confirmatory and bool(p_ttest < 0.05),
            "underpowered": underpowered,
            "confirmatory": confirmatory,
            "independent_items_assumed": independent,
            "bootstrap_mean_diff": bootstrap_mean_ci(diffs, independent=independent),
            "note": note,
        }


def compare_summaries_by_name(
    summaries: List[BenchmarkRunSummary],
    baseline_name: str,
    treatment_name: str,
    metric: str = "faithfulness",
) -> Dict[str, Any]:
    by_name = {s.config_name: s for s in summaries}
    if baseline_name not in by_name or treatment_name not in by_name:
        raise KeyError(f"Need {baseline_name!r} and {treatment_name!r} in run summaries")
    return SignificanceAnalyzer.compare_runs(
        by_name[baseline_name], by_name[treatment_name], metric=metric, independent=False
    )
