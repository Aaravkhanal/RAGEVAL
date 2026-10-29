"""Latency/cost helpers. Cost is null unless both prices and a source are set."""

from __future__ import annotations

from typing import Optional, Tuple


def estimated_cost_usd(
    prompt_tokens: int,
    completion_tokens: int,
    prompt_usd_per_million: Optional[float],
    completion_usd_per_million: Optional[float],
    pricing_source: Optional[str],
) -> Tuple[Optional[float], Optional[str]]:
    """Return (cost, source). Any missing price or source → (None, None)."""
    if (
        prompt_usd_per_million is None
        or completion_usd_per_million is None
        or not pricing_source
    ):
        return None, None
    cost = (
        (prompt_tokens * prompt_usd_per_million)
        + (completion_tokens * completion_usd_per_million)
    ) / 1_000_000.0
    return round(cost, 6), pricing_source
