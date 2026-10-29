"""Official metric registry: every named metric has a formula test and no overall score."""

from rageval.metrics.registry import (
    compute,
    get_metric,
    has_overall_score,
    official_metrics,
)


def test_no_official_overall_score():
    assert has_overall_score() is False
    assert all(spec.name != "overall_score" for spec in official_metrics())


def test_registry_covers_expected_families():
    names = {spec.name for spec in official_metrics()}
    assert "recall_at_k" in names
    assert "claim_support_rate" in names
    assert "citation_support_precision" in names
    assert "exact_match" in names
    assert "abstention_accuracy" in names
    assert "estimated_cost_usd" in names
    assert get_metric("citation_marker_recall").legacy is True


def test_compute_dispatch_hand_examples():
    assert compute("recall_at_k", ["d1", "d9", "d2"], {"d1", "d2"}, 1) == 0.5
    assert compute("citation_existence_precision", 1, 2) == 0.5
    assert compute("claim_coverage", 0, 0) == 1.0
    cost, source = compute("estimated_cost_usd", 1000, 500, None, None, None)
    assert cost is None and source is None
