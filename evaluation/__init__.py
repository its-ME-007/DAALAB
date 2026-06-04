"""Research evaluation harness for the complexity-aware scheduler.

Two layers share this package:
- A pure-Python discrete-event simulator (``simulator``, ``run_sweep``) that drives
  the *real* scheduler over heterogeneous workloads, fully reproducible (seeded,
  no Docker).
- An analyzer (``analyze_results``) for real-system locust/worker CSVs, emitting the
  same metric table as the simulator for apples-to-apples comparison.

Both reuse ``evaluation.metrics`` so sim and real numbers are computed identically.
"""
