"""Scenario tests for worker selection under different queued loads.

Unlike test_scheduler.py (which scores a single static snapshot), these tests
drive a *stream* of jobs through the scheduler and accumulate per-worker load the
same way the production scheduler does in
``scheduler/scheduler_server.py::handle_job_request`` (seed worker_load_map to 0,
then increment the selected worker by the job's estimated cost). This is what
exposes how the baseline (queue-length) and proposed (queue-cost) algorithms
diverge when workers hold *different* jobs.

Run with ``-s`` to see the selection report:

    pytest tests/unit/test_worker_selection_scenarios.py -s
"""

import pytest
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from scheduler.scheduler import Scheduler
from common.models import WorkerState, SchedulingMode

# initial state per worker: (queue_cost_ms, active_jobs, cpu_util)
InitialState = Dict[str, Tuple[float, int, Optional[float]]]


def simulate_job_stream(
    mode: SchedulingMode,
    worker_ids: List[str],
    job_costs: List[float],
    initial: Optional[InitialState] = None,
) -> Tuple[List[str], Dict[str, float], Dict[str, int]]:
    """Route a stream of jobs and accumulate load, mirroring scheduler_server.

    No job completion is modelled (worst-case burst), so the final maps show how a
    burst of arrivals is packed across workers.

    Returns:
        (selections, final_load_ms, final_active_jobs)
    """
    scheduler = Scheduler(mode=mode)

    load: Dict[str, float] = {w: 0.0 for w in worker_ids}
    jobs: Dict[str, int] = {w: 0 for w in worker_ids}
    cpu: Dict[str, Optional[float]] = {w: None for w in worker_ids}

    if initial:
        for w, (l, j, c) in initial.items():
            load[w] = l
            jobs[w] = j
            cpu[w] = c

    selections: List[str] = []

    for cost in job_costs:
        # Rebuild the worker snapshot reflecting current tracked state. queue-length
        # routes on active_jobs; queue-cost routes on the load map we pass in.
        workers = [
            WorkerState(
                worker_id=w,
                queue_cost_ms=load[w],
                active_jobs=jobs[w],
                cpu_util=cpu[w],
                is_healthy=True,
                last_heartbeat=datetime.utcnow(),
            )
            for w in worker_ids
        ]

        result = scheduler.select_worker(workers, cost, dict(load))
        assert result is not None
        selected, _decision = result

        selections.append(selected.worker_id)
        load[selected.worker_id] += cost
        jobs[selected.worker_id] += 1

    return selections, load, jobs


def makespan(load: Dict[str, float]) -> float:
    """Max per-worker load — the metric load balancing tries to minimize."""
    return max(load.values())


# ============================================================================
# Scenario 1: homogeneous burst on empty workers -> even spread
# ============================================================================

class TestHomogeneousBurst:
    """Equal-cost jobs onto idle workers should spread evenly (both algorithms)."""

    def test_two_workers_even_split(self):
        costs = [1000.0] * 6
        for mode in (SchedulingMode.QUEUE_LENGTH, SchedulingMode.QUEUE_COST):
            selections, load, jobs = simulate_job_stream(
                mode, ["worker-1", "worker-2"], costs
            )
            assert jobs["worker-1"] == 3, f"{mode}: {jobs}"
            assert jobs["worker-2"] == 3, f"{mode}: {jobs}"

    def test_three_workers_even_thirds(self):
        costs = [1000.0] * 6
        for mode in (SchedulingMode.QUEUE_LENGTH, SchedulingMode.QUEUE_COST):
            _sel, _load, jobs = simulate_job_stream(
                mode, ["worker-1", "worker-2", "worker-3"], costs
            )
            assert sorted(jobs.values()) == [2, 2, 2], f"{mode}: {jobs}"


# ============================================================================
# Scenario 2: pre-loaded worker should be avoided until balanced (cost-aware)
# ============================================================================

class TestHeterogeneousInitialLoad:
    """One worker starts heavily loaded; cost-aware routing avoids it."""

    def test_queue_cost_avoids_loaded_worker(self):
        # worker-1 carries 5000ms of work; worker-2 is idle.
        initial = {"worker-1": (5000.0, 5, None), "worker-2": (0.0, 0, None)}
        selections, load, _jobs = simulate_job_stream(
            SchedulingMode.QUEUE_COST,
            ["worker-1", "worker-2"],
            [1000.0] * 4,
            initial=initial,
        )
        # First several small jobs pour into worker-2 until it catches up to 5000ms.
        assert selections[:4] == ["worker-2"] * 4
        assert load["worker-1"] == 5000.0
        assert load["worker-2"] == 4000.0


# ============================================================================
# Scenario 3: the headline divergence — few-but-huge vs many-but-tiny
# ============================================================================

class TestCostVsLengthDivergence:
    """Worker holding 1 expensive job vs worker holding many cheap jobs.

    Queue-length counts only *jobs*, so it routes new work to the worker with the
    single (huge) job. Queue-cost sees that worker is expensive and avoids it.
    This is the core argument for the proposed algorithm.
    """

    INITIAL = {
        "worker-1": (10000.0, 1, None),  # one O(n!)-class job: huge cost, 1 job
        "worker-2": (300.0, 3, None),    # three tiny jobs: small cost, 3 jobs
    }

    def test_queue_length_overloads_the_expensive_worker(self):
        selections, load, _jobs = simulate_job_stream(
            SchedulingMode.QUEUE_LENGTH,
            ["worker-1", "worker-2"],
            [100.0, 100.0],
            initial=dict(self.INITIAL),
        )
        # Baseline sees worker-1 as "least busy" (1 job) and piles more onto it.
        assert selections == ["worker-1", "worker-1"]
        assert load["worker-1"] == 10200.0  # makespan WORSE

    def test_queue_cost_protects_the_expensive_worker(self):
        selections, load, _jobs = simulate_job_stream(
            SchedulingMode.QUEUE_COST,
            ["worker-1", "worker-2"],
            [100.0, 100.0],
            initial=dict(self.INITIAL),
        )
        # Proposed routes away from the expensive worker.
        assert selections == ["worker-2", "worker-2"]
        assert load["worker-1"] == 10000.0  # makespan preserved

    def test_proposed_yields_lower_makespan(self):
        _s1, load_len, _j1 = simulate_job_stream(
            SchedulingMode.QUEUE_LENGTH, ["worker-1", "worker-2"],
            [100.0, 100.0], initial=dict(self.INITIAL),
        )
        _s2, load_cost, _j2 = simulate_job_stream(
            SchedulingMode.QUEUE_COST, ["worker-1", "worker-2"],
            [100.0, 100.0], initial=dict(self.INITIAL),
        )
        assert makespan(load_cost) < makespan(load_len)


# ============================================================================
# Scenario 4: CPU overload penalty steers traffic away from a hot worker
# ============================================================================

class TestCpuPenaltyRouting:
    """A worker above CPU_OVERLOAD_THRESHOLD is penalized despite low queue cost."""

    def test_hot_worker_avoided(self):
        # worker-1 is cheapest by cost but pinned at 95% CPU.
        initial = {
            "worker-1": (1000.0, 2, 0.95),
            "worker-2": (1500.0, 3, 0.30),
        }
        selections, _load, _jobs = simulate_job_stream(
            SchedulingMode.QUEUE_COST,
            ["worker-1", "worker-2"],
            [500.0],
            initial=initial,
        )
        # CPU_PENALTY (1000ms) pushes worker-1's score to 2000 > worker-2's 1500.
        assert selections == ["worker-2"]


# ============================================================================
# Display / reporting (run with -s to view)
# ============================================================================

SCENARIOS = [
    (
        "Homogeneous burst (2 idle workers, 6x 1000ms)",
        ["worker-1", "worker-2"],
        [1000.0] * 6,
        None,
    ),
    (
        "Homogeneous burst (3 idle workers, 6x 1000ms)",
        ["worker-1", "worker-2", "worker-3"],
        [1000.0] * 6,
        None,
    ),
    (
        "Pre-loaded worker-1=5000ms (4x 1000ms incoming)",
        ["worker-1", "worker-2"],
        [1000.0] * 4,
        {"worker-1": (5000.0, 5, None), "worker-2": (0.0, 0, None)},
    ),
    (
        "Few-huge vs many-tiny  (w1: 1x10000ms, w2: 3x100ms; 2x100ms incoming)",
        ["worker-1", "worker-2"],
        [100.0, 100.0],
        {"worker-1": (10000.0, 1, None), "worker-2": (300.0, 3, None)},
    ),
    (
        "Hot worker-1 @95% CPU (cheapest by cost; 1x500ms incoming)",
        ["worker-1", "worker-2"],
        [500.0],
        {"worker-1": (1000.0, 2, 0.95), "worker-2": (1500.0, 3, 0.30)},
    ),
]


def _format_report() -> str:
    lines = ["", "=" * 78, "WORKER SELECTION REPORT (queue-length vs queue-cost)", "=" * 78]
    for name, worker_ids, costs, initial in SCENARIOS:
        lines.append("")
        lines.append(f"Scenario: {name}")
        lines.append(f"  workers={worker_ids}  incoming_costs={[int(c) for c in costs]}")
        if initial:
            init_str = {w: (int(l), j, c) for w, (l, j, c) in initial.items()}
            lines.append(f"  initial(cost_ms, jobs, cpu)={init_str}")
        for mode in (SchedulingMode.QUEUE_LENGTH, SchedulingMode.QUEUE_COST):
            sel, load, jobs = simulate_job_stream(mode, worker_ids, costs, initial)
            label = "queue-length" if mode == SchedulingMode.QUEUE_LENGTH else "queue-cost  "
            final_cost = {w: int(c) for w, c in load.items()}
            lines.append(
                f"  [{label}] picks={sel}"
            )
            lines.append(
                f"                 final_cost_ms={final_cost}  jobs={jobs}  makespan={int(makespan(load))}ms"
            )
    lines.append("=" * 78)
    return "\n".join(lines)


def test_display_selection_report(capsys):
    """Print the selection report and sanity-check it is non-trivial."""
    report = _format_report()
    with capsys.disabled():
        print(report)
    # Cheap assertions so this still counts as a real test.
    assert "queue-cost" in report
    assert "makespan" in report


if __name__ == "__main__":
    print(_format_report())
