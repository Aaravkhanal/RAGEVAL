"""Citation metric formulas."""

from __future__ import annotations

from typing import Sequence


def citation_existence_precision(n_valid: int, n_total: int) -> float:
    """Valid (in-pool) citations / all citation tokens. No citations → 1.0."""
    if n_total <= 0:
        return 1.0
    if n_valid < 0:
        return 0.0
    return n_valid / n_total


def citation_completeness(n_claims_with_supporting_cite: int, n_claims_requiring_cite: int) -> float:
    """Claims with ≥1 supporting citation / claims that require a citation.

    No claims requiring a citation → 1.0.
    """
    if n_claims_requiring_cite <= 0:
        return 1.0
    return n_claims_with_supporting_cite / n_claims_requiring_cite


def citation_support_precision(n_citations_that_support: int, n_evaluated_citations: int) -> float:
    """Citations whose cited passage supports the associated claim / evaluated citations."""
    if n_evaluated_citations <= 0:
        return 1.0
    return n_citations_that_support / n_evaluated_citations
