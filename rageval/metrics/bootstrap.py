"""Bootstrap mean CIs. Confirmatory use requires n and independence (see docs)."""

from __future__ import annotations

from typing import Any, Dict, Sequence

import numpy as np

# Documented in METRIC_DEFINITIONS.md. Below this, CIs are diagnostic only.
MIN_N_CONFIRMATORY = 30


def bootstrap_mean_ci(
    values: Sequence[float],
    *,
    n_bootstrap: int = 1000,
    ci: float = 0.95,
    seed: int = 0,
    independent: bool = True,
) -> Dict[str, Any]:
    """Percentile bootstrap CI for the mean.

    `assumptions_met` is True only when n >= MIN_N_CONFIRMATORY and
    `independent` is True. Smaller samples still return an interval but
    it is labeled diagnostic.
    """
    arr = np.asarray(list(values), dtype=float)
    n = int(arr.size)
    if n == 0:
        return {
            "n": 0,
            "mean": None,
            "ci_low": None,
            "ci_high": None,
            "ci_level": ci,
            "n_bootstrap": n_bootstrap,
            "assumptions_met": False,
            "assumption_notes": f"Empty sample. Confirmatory CI requires n>={MIN_N_CONFIRMATORY} i.i.d. items.",
        }
    rng = np.random.default_rng(seed)
    means = np.empty(n_bootstrap, dtype=float)
    for i in range(n_bootstrap):
        sample = rng.choice(arr, size=n, replace=True)
        means[i] = float(np.mean(sample))
    alpha = (1.0 - ci) / 2.0
    lo, hi = np.quantile(means, [alpha, 1.0 - alpha])
    met = n >= MIN_N_CONFIRMATORY and independent
    notes = (
        f"n={n}, independent={independent}. "
        f"Confirmatory CI requires n>={MIN_N_CONFIRMATORY} i.i.d. query items "
        "(items that share documents are not independent)."
    )
    if not met:
        notes = "Diagnostic only. " + notes
    return {
        "n": n,
        "mean": round(float(np.mean(arr)), 4),
        "ci_low": round(float(lo), 4),
        "ci_high": round(float(hi), 4),
        "ci_level": ci,
        "n_bootstrap": n_bootstrap,
        "assumptions_met": met,
        "assumption_notes": notes,
    }
