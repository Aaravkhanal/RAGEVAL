"""Unit tests for statistical significance calculations."""

from rageval.core.schemas import BenchmarkRunSummary, QueryEvaluationResult, CitationMetric, RetrievalMetrics, TestType
from rageval.analysis.significance import SignificanceAnalyzer


def _mock_summary(name: str, faiths: list[float], recalls: list[float]) -> BenchmarkRunSummary:
    results = []
    for i, (f, r) in enumerate(zip(faiths, recalls)):
        results.append(
            QueryEvaluationResult(
                query_id=f"q_{i}",
                question="Q",
                test_type=TestType.STANDARD,
                generated_answer="A",
                faithfulness_score=f,
                hallucination_rate=1.0 - f,
                contradiction_rate=0.0,
                citation_metrics=CitationMetric(total_citations=1, valid_citations=1, citation_precision=1.0, citation_recall=1.0),
                retrieval_metrics=RetrievalMetrics(recall_at_5=r),
            )
        )
    return BenchmarkRunSummary(
        config_name=name,
        total_queries=len(results),
        mean_faithfulness=sum(faiths) / len(faiths),
        mean_hallucination_rate=0.1,
        mean_contradiction_rate=0.0,
        mean_citation_precision=1.0,
        mean_citation_recall=1.0,
        mean_recall_at_5=sum(recalls) / len(recalls),
        mean_mrr=0.8,
        mean_latency_ms=50.0,
        p95_latency_ms=65.0,
        abstention_accuracy=1.0,
        conflicting_detection_rate=1.0,
        total_estimated_cost_usd=0.001,
        results=results,
    )


def test_significance_analyzer():
    baseline = _mock_summary("Baseline", [0.6, 0.65, 0.7, 0.6, 0.55], [0.7, 0.7, 0.8, 0.6, 0.7])
    treatment = _mock_summary("Improved", [0.85, 0.90, 0.95, 0.90, 0.88], [0.95, 0.95, 1.0, 0.9, 0.95])

    res = SignificanceAnalyzer.compare_runs(baseline, treatment, metric="faithfulness")
    assert res["mean_diff"] > 0
    assert "p_value_ttest" in res
    assert res["n"] == 5
    assert res["underpowered"] is True
    assert res["confirmatory"] is False
    assert res["is_significant"] is False
