"""Findings generator refuses canned 16.4% Recall@5 unless metrics compute it."""

import json

import pytest

from rageval.analysis.findings import (
    assert_findings_text_allowed,
    recall_relative_lift_pct,
    render_findings,
    write_findings,
)
from rageval.benchmark.reporter import BenchmarkReporter


def _metrics_from_recalls(baseline: float, treatment: float) -> dict:
    return {
        "label": "pilot",
        "dataset_id": "toy",
        "n_items": 2,
        "by_config": {
            "Dense_Chunk256_Baseline": {
                "n": 2,
                "recall_at_5": {"mean": baseline},
                "mrr": {"mean": 0.5},
                "claim_support_rate": {"mean": 0.5},
                "unsupported_claim_rate": {"mean": 0.5},
                "contradiction_rate": {"mean": 0.0},
                "abstention_accuracy": 0.0,
                "mean_latency_ms": 10.0,
                "by_scenario": {},
            },
            "Hybrid_RRF_Chunk256": {
                "n": 2,
                "recall_at_5": {"mean": treatment},
                "mrr": {"mean": 0.5},
                "claim_support_rate": {"mean": 0.5},
                "unsupported_claim_rate": {"mean": 0.5},
                "contradiction_rate": {"mean": 0.0},
                "abstention_accuracy": 0.0,
                "mean_latency_ms": 12.0,
                "by_scenario": {},
            },
        },
    }


def test_refuses_uncomputed_16_4_sentence():
    metrics = _metrics_from_recalls(0.8333, 0.8333)
    with pytest.raises(ValueError, match="16.4"):
        assert_findings_text_allowed(
            "hybrid retrieval with cross-encoder reranking yields a 16.4% boost in Recall@5",
            metrics,
        )


def test_allows_16_4_when_computed_from_metrics():
    # 0.812 * 1.164 = 0.945168
    metrics = _metrics_from_recalls(0.812, 0.945168)
    lift = recall_relative_lift_pct(metrics, "Dense_Chunk256_Baseline", "Hybrid_RRF_Chunk256")
    assert lift is not None and abs(lift - 16.4) <= 0.15
    assert_findings_text_allowed(
        f"Relative Recall@5 lift of Hybrid_RRF_Chunk256 vs Dense_Chunk256_Baseline is {lift:.1f}%.",
        metrics,
    )


def test_refuses_sota():
    metrics = _metrics_from_recalls(0.5, 0.6)
    with pytest.raises(ValueError, match="ranking language"):
        assert_findings_text_allowed("We achieve SOTA faithfulness.", metrics)


def test_v1_export_findings_have_no_canned_lift(tmp_path):
    metrics = BenchmarkReporter.load_metrics("reports/phase7/v1_matrix/metrics.json")
    lift = recall_relative_lift_pct(metrics, "Dense_Chunk256_Baseline", "Hybrid_RRF_Reranked")
    assert lift == 0.0
    path = write_findings(metrics, str(tmp_path), run_id="20261028T183042Z_a97ad68f")
    text = path.read_text() if hasattr(path, "read_text") else open(path).read()
    assert "16.4%" not in text
    assert "SOTA" not in text
    assert "{run_id}" not in text
    assert "20261028T183042Z_a97ad68f" in text
    assert "identical" in text.lower()
    assert "not identifiable" in text.lower()


def test_render_includes_run_id():
    metrics = _metrics_from_recalls(0.8, 0.8)
    text = render_findings(metrics, run_id="abc", case_studies=[], significance=None)
    assert "`abc`" in text
    assert_findings_text_allowed(text, metrics)


def test_v11_findings_do_not_claim_new_items_unscored():
    metrics = _metrics_from_recalls(0.5, 0.5)
    metrics["dataset_id"] = "benchmark_v1"
    metrics["dataset_version"] = "1.1.0"
    metrics["n_items"] = 28
    metrics["n_documents"] = 18
    metrics["label"] = "v1"
    text = render_findings(metrics, run_id="run_v11", case_studies=[], significance=None)
    assert "v1_025" not in text or "unscored" not in text.split("v1_025")[1][:80]
    assert "unscored" not in text
    assert "28" in text
    assert "18 documents" in text
    assert "v1_1_matrix" in text
    assert "20261028T183042Z_a97ad68f" in text
    assert_findings_text_allowed(text, metrics)
