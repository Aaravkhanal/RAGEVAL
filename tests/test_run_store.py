"""Run directories refuse to overwrite."""

import os

import pytest

from rageval.benchmark.run_store import create_run_dir, save_run
from rageval.core.schemas import (
    BenchmarkRunSummary,
    CitationMetric,
    QueryEvaluationResult,
    RetrievalMetrics,
    TestType,
)


def test_create_run_dir_unique(tmp_path):
    path = create_run_dir(str(tmp_path), run_id="run_a")
    assert os.path.isdir(path)
    with pytest.raises(FileExistsError):
        create_run_dir(str(tmp_path), run_id="run_a")


def _summary() -> BenchmarkRunSummary:
    result = QueryEvaluationResult(
        query_id="q0",
        question="Q",
        test_type=TestType.STANDARD,
        generated_answer="A",
        faithfulness_score=1.0,
        hallucination_rate=0.0,
        contradiction_rate=0.0,
        citation_metrics=CitationMetric(
            total_citations=0,
            valid_citations=0,
            citation_precision=1.0,
            citation_recall=1.0,
        ),
        retrieval_metrics=RetrievalMetrics(recall_at_5=1.0, mrr=1.0),
    )
    return BenchmarkRunSummary(
        config_name="toy",
        total_queries=1,
        mean_faithfulness=1.0,
        mean_hallucination_rate=0.0,
        mean_contradiction_rate=0.0,
        mean_citation_precision=1.0,
        mean_citation_recall=1.0,
        mean_recall_at_5=1.0,
        mean_mrr=1.0,
        mean_latency_ms=1.0,
        p95_latency_ms=1.0,
        abstention_accuracy=1.0,
        conflicting_detection_rate=1.0,
        results=[result],
    )


def test_save_run_does_not_clobber_completed(tmp_path):
    run_dir = create_run_dir(str(tmp_path), run_id="done")
    save_run(run_dir, [_summary()], extra_manifest={"label": "pilot"}, label="pilot")
    assert os.path.isfile(os.path.join(run_dir, "metrics.json"))
    with pytest.raises(FileExistsError):
        save_run(run_dir, [_summary()], label="pilot")
