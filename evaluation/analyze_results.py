"""Analyze REAL-system experiment CSVs into the same table as the simulator.

Reads locust stats CSVs (``real_<algo>_N<n>_r<rep>_stats.csv`` from
scripts/run_load_experiment.ps1) and, when present, worker-stats CSVs
(``worker_stats_<algo>.csv`` from scripts/collect_worker_stats.py). Emits per
(algo, N) latency percentiles + throughput with 95% CIs across repeats, plus a
real-system Jain's fairness index — directly comparable to
``evaluation.run_sweep`` output to validate the simulation.

Usage:
    python -m evaluation.analyze_results results/
"""

from __future__ import annotations

import argparse
import csv
import glob
import os
import re
from collections import defaultdict
from typing import Dict, List, Optional

from evaluation.metrics import mean_ci, jains_fairness

_STATS_RE = re.compile(r"real_(?P<algo>.+)_N(?P<n>\d+)_r(?P<rep>\d+)_stats\.csv$")


def _read_locust_aggregated(path: str) -> Optional[Dict[str, float]]:
    """Return p50/p95/p99 (ms) + throughput from a locust _stats.csv Aggregated row."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    agg = next((r for r in rows if r.get("Name") == "Aggregated"), None)
    if agg is None and rows:
        agg = rows[-1]
    if agg is None:
        return None

    def num(*keys):
        for k in keys:
            if k in agg and agg[k] not in ("", "N/A"):
                try:
                    return float(agg[k])
                except ValueError:
                    pass
        return 0.0

    return {
        "p50_ms": num("50%", "Median Response Time"),
        "p95_ms": num("95%"),
        "p99_ms": num("99%"),
        "throughput_jobs_s": num("Requests/s"),
    }


def _worker_fairness(results_dir: str, algo: str) -> Optional[float]:
    """Jain's index over per-worker time-averaged load, if a worker_stats CSV exists."""
    candidates = glob.glob(os.path.join(results_dir, f"worker_stats*{algo}*.csv"))
    if not candidates:
        return None
    per_worker_vals: Dict[str, List[float]] = defaultdict(list)
    with open(candidates[0], newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            wid = row.get("worker_id") or row.get("worker_url")
            # Prefer cpu_util; fall back to active_jobs as the load proxy.
            val = row.get("cpu_util") or row.get("active_jobs")
            if wid and val not in (None, "", "None"):
                try:
                    per_worker_vals[wid].append(float(val))
                except ValueError:
                    pass
    if not per_worker_vals:
        return None
    means = [sum(v) / len(v) for v in per_worker_vals.values()]
    return jains_fairness(means)


def collect(results_dir: str) -> List[Dict]:
    # group repeats: (algo, N) -> list of per-run metric dicts
    groups: Dict[tuple, List[Dict[str, float]]] = defaultdict(list)
    for path in glob.glob(os.path.join(results_dir, "real_*_stats.csv")):
        m = _STATS_RE.search(os.path.basename(path))
        if not m:
            continue
        metrics = _read_locust_aggregated(path)
        if metrics:
            groups[(m["algo"], int(m["n"]))].append(metrics)

    keys = ["p50_ms", "p95_ms", "p99_ms", "throughput_jobs_s"]
    rows: List[Dict] = []
    for (algo, n), runs in sorted(groups.items(), key=lambda x: (x[0][1], x[0][0])):
        agg = {k: mean_ci([r[k] for r in runs if k in r]) for k in keys}
        rows.append({
            "algo": algo, "workers": n, "repeats": len(runs),
            "fairness": _worker_fairness(results_dir, algo), **agg,
        })
    return rows


def print_table(rows: List[Dict]) -> None:
    print("\n" + "=" * 104)
    print("REAL-SYSTEM RESULTS  --  mean +/- 95% CI across repeats")
    print("=" * 104)
    last_n = None
    header = (f"{'algo':<13}{'N':>3}{'reps':>5}  "
              f"{'p50(ms)':>16}{'p95(ms)':>18}{'p99(ms)':>18}{'thru/s':>14}{'fairness':>10}")
    for r in rows:
        if r["workers"] != last_n:
            print("-" * 104)
            print(header)
            print("-" * 104)
            last_n = r["workers"]

        def fmt(key, width, prec=1):
            mean, ci = r[key]
            return f"{mean:.{prec}f}+/-{ci:.{prec}f}".rjust(width)

        fair = "n/a".rjust(10) if r["fairness"] is None else f"{r['fairness']:.3f}".rjust(10)
        print(f"{r['algo']:<13}{r['workers']:>3}{r['repeats']:>5}  "
              f"{fmt('p50_ms',16)}{fmt('p95_ms',18)}{fmt('p99_ms',18)}"
              f"{fmt('throughput_jobs_s',14,2)}{fair}")
    print("=" * 104)


def main(argv=None):
    p = argparse.ArgumentParser(description="Analyze real-system experiment CSVs.")
    p.add_argument("results_dir", nargs="?", default="results",
                   help="Directory containing real_*_stats.csv (and optional worker_stats_*.csv).")
    args = p.parse_args(argv)

    rows = collect(args.results_dir)
    if not rows:
        print(f"[WARN] No real_*_stats.csv found in {args.results_dir}. "
              f"Run scripts/run_load_experiment.ps1 first.")
        return
    print_table(rows)


if __name__ == "__main__":
    main()
