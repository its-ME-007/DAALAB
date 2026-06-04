"""Poll worker /status (and the scheduler's load map) during a load run -> CSV.

Produces the time series used for real-system fairness (Jain's index over
per-worker load / CPU) and to locate the saturation point (which role's CPU/queue
saturates first). Run this alongside scripts/run_load_experiment.ps1.

Example:
    python scripts/collect_worker_stats.py \
        --workers http://10.0.0.11:8001,http://10.0.0.12:8001 \
        --scheduler http://10.0.0.30:8000 \
        --interval 1 --duration 300 --out results/worker_stats_queue_cost.csv
"""

from __future__ import annotations

import argparse
import csv
import time
from datetime import datetime, timezone

import httpx


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Poll worker/scheduler state into a CSV.")
    p.add_argument("--workers", required=True,
                   help="Comma-separated worker base URLs (…:8001).")
    p.add_argument("--scheduler", default=None,
                   help="Optional scheduler base URL for /api/scheduler/assignments.")
    p.add_argument("--interval", type=float, default=1.0, help="Seconds between polls.")
    p.add_argument("--duration", type=float, default=300.0, help="Total seconds to poll.")
    p.add_argument("--out", default="results/worker_stats.csv", help="CSV output path.")
    return p.parse_args(argv)


def poll_worker(client: httpx.Client, url: str) -> dict:
    try:
        r = client.get(f"{url}/status", timeout=3.0)
        r.raise_for_status()
        d = r.json()
        return {
            "worker_id": d.get("worker_id", url),
            "queue_cost_ms": d.get("queue_cost_ms"),
            "active_jobs": d.get("active_jobs"),
            "cpu_util": d.get("cpu_util"),
            "mem_util": d.get("mem_util"),
            "reachable": 1,
        }
    except Exception:
        return {"worker_id": url, "queue_cost_ms": None, "active_jobs": None,
                "cpu_util": None, "mem_util": None, "reachable": 0}


def poll_scheduler_loadmap(client: httpx.Client, url: str) -> dict:
    try:
        r = client.get(f"{url}/api/scheduler/assignments", timeout=3.0)
        r.raise_for_status()
        return r.json().get("worker_load_map", {})
    except Exception:
        return {}


def main(argv=None):
    args = parse_args(argv)
    worker_urls = [u.strip() for u in args.workers.split(",") if u.strip()]

    import os
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)

    fieldnames = ["ts", "elapsed_s", "worker_url", "worker_id", "queue_cost_ms",
                  "active_jobs", "cpu_util", "mem_util", "reachable",
                  "scheduler_load_ms"]

    start = time.time()
    rows_written = 0
    with httpx.Client() as client, open(args.out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        while time.time() - start < args.duration:
            now = time.time()
            elapsed = now - start
            ts = datetime.now(timezone.utc).isoformat()
            load_map = poll_scheduler_loadmap(client, args.scheduler) if args.scheduler else {}

            for url in worker_urls:
                row = poll_worker(client, url)
                row.update({
                    "ts": ts,
                    "elapsed_s": round(elapsed, 2),
                    "worker_url": url,
                    "scheduler_load_ms": load_map.get(row["worker_id"]),
                })
                writer.writerow(row)
                rows_written += 1

            f.flush()
            # Sleep the remainder of the interval (account for poll time).
            sleep_for = args.interval - (time.time() - now)
            if sleep_for > 0:
                time.sleep(sleep_for)

    print(f"[OK] Wrote {rows_written} rows to {args.out}")


if __name__ == "__main__":
    main()
