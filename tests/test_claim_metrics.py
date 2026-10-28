"""Unit tests for claim-level metric formulas."""

from rageval.core.labels import VerificationLabel
from rageval.metrics.claims import (
    claim_coverage,
    claim_support_rate,
    contradiction_rate,
    unsupported_claim_rate,
)


def test_claim_rates_mixed_labels():
    labels = [
        VerificationLabel.SUPPORTED,
        VerificationLabel.SUPPORTED,
        VerificationLabel.UNSUPPORTED,
        VerificationLabel.CONTRADICTED,
        VerificationLabel.PARTIALLY_SUPPORTED,
    ]
    assert claim_support_rate(labels) == 0.4
    assert claim_support_rate(labels, count_partial_as_supported=True) == 0.6
    assert unsupported_claim_rate(labels, include_partial=True) == 0.4
    assert contradiction_rate(labels) == 0.2


def test_empty_labels_and_coverage():
    assert claim_support_rate([]) == 0.0
    assert claim_coverage(0, 0) == 1.0
    assert claim_coverage(4, 4) == 1.0
    assert claim_coverage(4, 2) == 0.5
