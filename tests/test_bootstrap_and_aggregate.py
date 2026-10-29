"""Bootstrap CIs stay diagnostic under n=30; aggregate JSON has no overall score."""

from rageval.core.schemas import (
    CitationMetric,
    QueryEvaluationResult,
    RetrievalMetrics,
    TestType,
)
from rageval.metrics.aggregate import summarize_results, write_metrics_bundle
from rageval.metrics.bootstrap import MIN_N_CONFIRMATORY, bootstrap_mean_ci
from rageval.core.schemas import BenchmarkRunSummary


def test_bootstrap_small_n_is_not_confirmatory():
    ci = bootstrap_mean_ci([0.4, 0.5, 0.6], independent=True, seed=0)
    assert ci["n"] == 3
    assert ci["assumptions_met"] is False
    assert ci["ci_low"] <= ci["mean"] <= ci["ci_high"]
    assert MIN_N_CONFIRMATORY == 30


def test_bootstrap_large_n_independent():
    values = [0.5] * 30
    ci = bootstrap_mean_ci(values, independent=True, seed=1)
    assert ci["assumptions_met"] is True
    ci_dep = bootstrap_mean_ci(values, independent=False, seed=1)
    assert ci_dep["assumptions_met"] is False


def _result(fid: str, faith: float) -> QueryEvaluationResult:
    return QueryEvaluationResult(
        query_id=fid,
        question="Q",
        test_type=TestType.STANDARD,
        generated_answer="A",
        faithfulness_score=faith,
        hallucination_rate=1.0 - faith,
        contradiction_rate=0.0,
        citation_metrics=CitationMetric(
            total_citations=0,
            valid_citations=0,
            citation_precision=1.0,
            citation_recall=1.0,
            citation_support_precision=1.0,
        ),
        retrieval_metrics=RetrievalMetrics(recall_at_5=1.0, mrr=1.0),
        estimated_cost_usd=None,
    )


def test_summarize_results_null_overall_and_null_cost():
    summary = summarize_results([_result("a", 0.5), _result("b", 1.0)], independent=False)
    assert summary["overall_score"] is None
    assert summary["has_official_overall_score"] is False
    assert summary["claim_support_rate"]["mean"] == 0.75
    assert summary["total_estimated_cost_usd"] is None
    assert summary["claim_support_rate"]["bootstrap"]["assumptions_met"] is False


def test_write_metrics_bundle(tmp_path):
    run = BenchmarkRunSummary(
        config_name="toy",
        total_queries=2,
        mean_faithfulness=0.75,
        mean_hallucination_rate=0.25,
        mean_contradiction_rate=0.0,
        mean_citation_precision=1.0,
        mean_citation_recall=1.0,
        mean_recall_at_5=1.0,
        mean_mrr=1.0,
        mean_latency_ms=1.0,
        p95_latency_ms=1.0,
        abstention_accuracy=1.0,
        conflicting_detection_rate=1.0,
        total_estimated_cost_usd=None,
        results=[_result("a", 0.5), _result("b", 1.0)],
    )
    path = write_metrics_bundle(str(tmp_path), [run], independent=False)
    assert path.endswith("metrics.json")
    assert (tmp_path / "metrics" / "aggregate.json").is_file()
    text = (tmp_path / "metrics" / "aggregate.json").read_text()
    assert '"overall_score": null' in text
    assert '"by_scenario"' in text
    lines = (tmp_path / "metrics" / "per_example.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
