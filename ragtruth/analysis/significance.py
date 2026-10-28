"""Statistical significance analysis (Paired t-tests & Wilcoxon signed-rank tests) for ablation comparisons."""

from __future__ import annotations
from typing import List, Dict, Any
import numpy as np
from scipy import stats
from ragtruth.core.schemas import BenchmarkRunSummary


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

        # If identical values across all queries, p-value is 1.0
        if np.all(diffs == 0):
            return {
                "metric": metric,
                "baseline_name": baseline.config_name,
                "treatment_name": treatment.config_name,
                "mean_diff": 0.0,
                "p_value_ttest": 1.0,
                "p_value_wilcoxon": 1.0,
                "is_significant": False,
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
            "mean_baseline": round(float(np.mean(vals_a)), 4),
            "mean_treatment": round(float(np.mean(vals_b)), 4),
            "mean_diff": round(mean_diff, 4),
            "t_statistic": round(float(t_stat), 4),
            "p_value_ttest": round(float(p_ttest), 4),
            "p_value_wilcoxon": round(float(p_wilcoxon), 4),
            "is_significant": bool(p_ttest < 0.05),
        }
