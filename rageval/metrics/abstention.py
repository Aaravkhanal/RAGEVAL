"""Abstention accuracy on unanswerable items."""

from __future__ import annotations

from typing import Sequence


def abstention_accuracy(
    abstained: Sequence[bool],
    unanswerable: Sequence[bool],
) -> float:
    """Fraction of unanswerable items with abstained=True.

    No unanswerable items → 1.0 (undefined; reported as vacuously complete).
    Lengths must match.
    """
    if len(abstained) != len(unanswerable):
        raise ValueError("abstained and unanswerable must have the same length")
    flags = [did_abstain for did_abstain, is_unans in zip(abstained, unanswerable) if is_unans]
    if not flags:
        return 1.0
    return sum(1 for flag in flags if flag) / len(flags)
