"""Claim-level support rates.

Denominators exclude abstention claims. Empty assessable set yields 0.0
except claim_coverage, which is 1.0 when there are no generated claims.
"""

from __future__ import annotations

from typing import Sequence

from rageval.core.labels import VerificationLabel


def _assessable(labels: Sequence[VerificationLabel]) -> list[VerificationLabel]:
    return [VerificationLabel(label.value) for label in labels]


def claim_support_rate(
    labels: Sequence[VerificationLabel],
    count_partial_as_supported: bool = False,
) -> float:
    assessable = _assessable(labels)
    if not assessable:
        return 0.0
    supported = {VerificationLabel.SUPPORTED}
    if count_partial_as_supported:
        supported.add(VerificationLabel.PARTIALLY_SUPPORTED)
    return sum(1 for label in assessable if label in supported) / len(assessable)


def unsupported_claim_rate(
    labels: Sequence[VerificationLabel],
    include_partial: bool = True,
) -> float:
    """Unsupported (+ optional partial) / assessable."""
    assessable = _assessable(labels)
    if not assessable:
        return 0.0
    target = {VerificationLabel.UNSUPPORTED}
    if include_partial:
        target.add(VerificationLabel.PARTIALLY_SUPPORTED)
    return sum(1 for label in assessable if label in target) / len(assessable)


def contradiction_rate(labels: Sequence[VerificationLabel]) -> float:
    assessable = _assessable(labels)
    if not assessable:
        return 0.0
    return sum(1 for label in assessable if label == VerificationLabel.CONTRADICTED) / len(assessable)


def claim_coverage(n_generated_claims: int, n_verified_records: int) -> float:
    if n_generated_claims <= 0:
        return 1.0
    return min(1.0, n_verified_records / n_generated_claims)
