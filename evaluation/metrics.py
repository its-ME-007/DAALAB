"""Shared metric helpers for both the simulator and real-system analysis.

Stdlib-only (no numpy) so results are reproducible and dependency-light. Used by
``evaluation.simulator`` / ``evaluation.run_sweep`` and ``evaluation.analyze_results``
so simulated and measured numbers are computed identically.
"""

from __future__ import annotations

import math
from statistics import NormalDist
from typing import Dict, Iterable, List, Sequence, Tuple

# Two-sided 95% t-critical values by degrees of freedom (n-1). Falls back to the
# normal approximation (1.96) for df beyond the table, which is accurate to ~1%.
_T_CRITICAL_95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
    8: 2.306, 9: 2.262, 10: 2.228, 12: 2.179, 15: 2.131, 20: 2.086, 25: 2.060,
    30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980,
}


def percentile(values: Sequence[float], p: float) -> float:
    """Linear-interpolation percentile (p in [0, 100]). Empty -> 0.0."""
    if not values:
        return 0.0
    if p <= 0:
        return float(min(values))
    if p >= 100:
        return float(max(values))
    ordered = sorted(values)
    rank = (p / 100.0) * (len(ordered) - 1)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return float(ordered[int(rank)])
    frac = rank - low
    return float(ordered[low] * (1 - frac) + ordered[high] * frac)


def percentiles(values: Sequence[float], ps: Iterable[float] = (50, 95, 99)) -> Dict[str, float]:
    """Return {'p50': ..., 'p95': ..., 'p99': ...} for the requested percentiles."""
    return {f"p{int(p)}": percentile(values, p) for p in ps}


def jains_fairness(values: Sequence[float]) -> float:
    """Jain's fairness index: (Σx)² / (n·Σx²), in (0, 1]. 1.0 = perfectly equal.

    For n workers all-on-one yields 1/n. Empty or all-zero input -> 1.0 (treated as
    trivially fair — no load to distribute).
    """
    vals = list(values)
    n = len(vals)
    if n == 0:
        return 1.0
    sum_sq = sum(x * x for x in vals)
    if sum_sq == 0:
        return 1.0
    total = sum(vals)
    return (total * total) / (n * sum_sq)


def throughput(num_jobs: int, wall_time_s: float) -> float:
    """Completed jobs per second. wall_time_s <= 0 -> 0.0."""
    if wall_time_s <= 0:
        return 0.0
    return num_jobs / wall_time_s


def mean_ci(samples: Sequence[float], confidence: float = 0.95) -> Tuple[float, float]:
    """Return (mean, half_width) for a two-sided confidence interval.

    Uses a small-sample t-interval (95% table) and falls back to the normal
    approximation for other confidence levels or large df. n<2 -> half_width 0.0.
    """
    data = list(samples)
    n = len(data)
    if n == 0:
        return (0.0, 0.0)
    mean = sum(data) / n
    if n < 2:
        return (mean, 0.0)

    variance = sum((x - mean) ** 2 for x in data) / (n - 1)
    std_err = math.sqrt(variance) / math.sqrt(n)
    df = n - 1

    if abs(confidence - 0.95) < 1e-9:
        crit = _T_CRITICAL_95.get(df)
        if crit is None:
            # Nearest tabulated df at or below, else normal approximation.
            below = [k for k in _T_CRITICAL_95 if k <= df]
            crit = _T_CRITICAL_95[max(below)] if below else 1.96
    else:
        crit = NormalDist().inv_cdf(1 - (1 - confidence) / 2)

    return (mean, crit * std_err)


def aggregate_runs(per_run: Sequence[Dict[str, float]], keys: Sequence[str]) -> Dict[str, Tuple[float, float]]:
    """Aggregate a list of per-run metric dicts into {key: (mean, ci_half_width)}."""
    out: Dict[str, Tuple[float, float]] = {}
    for key in keys:
        out[key] = mean_ci([run[key] for run in per_run if key in run])
    return out
