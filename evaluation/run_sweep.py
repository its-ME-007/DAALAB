"""Sweep the simulator across algorithms x worker-count x concurrency x seeds.

Produces the headline evaluation artifact: a metrics table (with 95% confidence
intervals across seeds) and a CSV, comparing the proposed queue-cost scheduler
against the random / round-robin / queue-length baselines under a heterogeneous
workload at a fixed target utilization.

Every (workers, concurrency) cell uses the SAME arrival rate across algorithms
(derived from a target utilization rho), so algorithms are compared at equal
offered load.

Examples:
    python -m evaluation.run_sweep
    python -m evaluation.run_sweep --jobs 3000 --seeds 10 --workers 2,4,8 --concurrency 1,4
    python -m evaluation.run_sweep --algos queue_length,queue_cost --rho 0.9
"""

from __future__ import annotations

import argparse
import csv
import os
from typing import Dict, List

from common.models import SchedulingMode
from evaluation.simulator import SimConfig, run_simulation, rate_for_utilization
from evaluation.metrics import mean_ci

# Metrics aggregated across seeds (reported with CIs).
_METRIC_KEYS = [
    "p50_ms", "p95_ms", "p99_ms", "mean_latency_ms",
    "throughput_jobs_s", "fairness", "makespan_ms", "mean_utilization",
]


def _parse_list(s: str, cast):
    return [cast(x.strip()) for x in s.split(",") if x.strip()]


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Scheduler evaluation sweep (simulation).")
    p.add_argument("--jobs", type=int, default=3000, help="Jobs per run.")
    p.add_argument("--rho", type=float, default=0.8, help="Target utilization (open-loop).")
    p.add_argument("--rate", type=float, default=None, help="Override arrival rate (jobs/s).")
    p.add_argument("--workers", type=str, default="2,4,8", help="Comma-separated worker counts.")
    p.add_argument("--concurrency", type=str, default="1", help="Comma-separated per-worker concurrency.")
    p.add_argument("--algos", type=str,
                   default="random,round_robin,queue_length,queue_cost",
                   help="Comma-separated scheduling modes.")
    p.add_argument("--seeds", type=int, default=10, help="Number of seeds per cell.")
    p.add_argument("--arrival", type=str, default="poisson", choices=["poisson", "closed"])
    p.add_argument("--out", type=str, default="results/sim_results.csv", help="CSV output path.")
    return p.parse_args(argv)


def run_sweep(args) -> List[Dict]:
    worker_counts = _parse_list(args.workers, int)
    concurrencies = _parse_list(args.concurrency, int)
    algos = [SchedulingMode(a) for a in _parse_list(args.algos, str)]

    rows: List[Dict] = []

    for n in worker_counts:
        for c in concurrencies:
            # Derive one arrival rate per (n, c) cell so all algos see equal load.
            ref = SimConfig(mode=SchedulingMode.QUEUE_COST, num_workers=n, concurrency=c,
                            num_jobs=args.jobs, arrival=args.arrival, seed=0)
            rate = args.rate if args.rate is not None else rate_for_utilization(ref, args.rho)

            for algo in algos:
                per_run: List[Dict[str, float]] = []
                for seed in range(args.seeds):
                    cfg = SimConfig(
                        mode=algo, num_workers=n, concurrency=c, num_jobs=args.jobs,
                        arrival=args.arrival, rate=rate, seed=seed,
                    )
                    per_run.append(run_simulation(cfg).as_dict())

                agg = {k: mean_ci([r[k] for r in per_run]) for k in _METRIC_KEYS}
                rows.append({
                    "algo": algo.value, "workers": n, "concurrency": c,
                    "rho": args.rho, "rate_jobs_s": round(rate, 3),
                    "seeds": args.seeds, **{k: agg[k] for k in _METRIC_KEYS},
                })
    return rows


def write_csv(rows: List[Dict], path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    fieldnames = ["algo", "workers", "concurrency", "rho", "rate_jobs_s", "seeds"]
    for k in _METRIC_KEYS:
        fieldnames += [f"{k}_mean", f"{k}_ci95"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            flat = {k: r[k] for k in ("algo", "workers", "concurrency", "rho", "rate_jobs_s", "seeds")}
            for k in _METRIC_KEYS:
                mean, ci = r[k]
                flat[f"{k}_mean"] = round(mean, 3)
                flat[f"{k}_ci95"] = round(ci, 3)
            w.writerow(flat)


def print_table(rows: List[Dict]) -> None:
    print("\n" + "=" * 116)
    print("SCHEDULER EVALUATION SWEEP (simulation)  --  mean +/- 95% CI across seeds")
    print("=" * 116)
    header = (f"{'algo':<13}{'N':>3}{'C':>3}{'rate/s':>8}  "
              f"{'p50(ms)':>16}{'p95(ms)':>18}{'p99(ms)':>18}{'thru/s':>14}{'fairness':>16}")
    last_cell = None
    for r in rows:
        cell = (r["workers"], r["concurrency"])
        if cell != last_cell:
            print("-" * 116)
            print(header)
            print("-" * 116)
            last_cell = cell

        def fmt(key, width, prec=1):
            mean, ci = r[key]
            return f"{mean:.{prec}f}+/-{ci:.{prec}f}".rjust(width)

        print(f"{r['algo']:<13}{r['workers']:>3}{r['concurrency']:>3}{r['rate_jobs_s']:>8.2f}  "
              f"{fmt('p50_ms',16)}{fmt('p95_ms',18)}{fmt('p99_ms',18)}"
              f"{fmt('throughput_jobs_s',14,2)}{fmt('fairness',16,3)}")
    print("=" * 116)


def main(argv=None):
    args = parse_args(argv)
    rows = run_sweep(args)
    print_table(rows)
    write_csv(rows, args.out)
    print(f"\n[OK] Wrote {len(rows)} rows to {args.out}")


if __name__ == "__main__":
    main()
