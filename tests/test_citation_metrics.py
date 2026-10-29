"""Hand-computed citation formula tests."""

from rageval.metrics.citation import (
    citation_completeness,
    citation_existence_precision,
    citation_marker_recall,
    citation_support_precision,
)


def test_citation_formulas_hand_computed():
    assert citation_existence_precision(3, 4) == 0.75
    assert citation_existence_precision(0, 0) == 1.0
    assert citation_support_precision(1, 2) == 0.5
    assert citation_support_precision(0, 0) == 1.0
    assert citation_completeness(2, 4) == 0.5
    assert citation_completeness(0, 0) == 1.0
    assert citation_marker_recall(2, 4) == 0.5
    assert citation_marker_recall(0, 0) == 1.0
