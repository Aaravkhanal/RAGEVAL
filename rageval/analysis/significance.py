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
    ) -> Dict[str, Any]:
        """Compares paired per-query scores between baseline and treatment configurations."""
        if len(baseline.results) != len(treatment.results):
            raise ValueError("Baseline and treatment must have identical query evaluation counts.")

        if metric == "faithfulness":
            vals_a = [r.faithfulness_score for r in baseline.results]
            vals_b = [r.faithfulness_score for r in treatment.results]
        elif metric == "recall":
            vals_a = [r.retrieval_metrics.recall_at_5 for r in baseline.results]
            vals_b = [r.retrieval_metrics.recall_at_5 for r in treatment.results]
        elif metric == "latency":
            vals_a = [r.total_latency_ms for r in baseline.results]
            vals_b = [r.total_latency_ms for r in treatment.results]
        else:
            vals_a = [r.hallucination_rate for r in baseline.results]
            vals_b = [r.hallucination_rate for r in treatment.results]

        diffs = np.array(vals_b) - np.array(vals_a)
        mean_diff = float(np.mean(diffs))
        from rageval.metrics.bootstrap import MIN_N_CONFIRMATORY, bootstrap_mean_ci

        n = int(len(diffs))
        underpowered = n < MIN_N_CONFIRMATORY

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
                "confirmatory": not underpowered,
                "note": (
                    f"n={n} < {MIN_N_CONFIRMATORY}: significance tests are diagnostic only."
                    if underpowered
                    else None
                ),
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
            "is_significant": (not underpowered) and bool(p_ttest < 0.05),
            "underpowered": underpowered,
            "confirmatory": not underpowered,
            "bootstrap_mean_diff": bootstrap_mean_ci(diffs, independent=False),
            "note": (
                f"n={n} < {MIN_N_CONFIRMATORY}: tests are diagnostic; is_significant stays false."
                if underpowered
                else None
            ),
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
        by_name[baseline_name], by_name[treatment_name], metric=metric
    )
