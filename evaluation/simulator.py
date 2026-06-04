"""Discrete-event simulator for the complexity-aware scheduler.

The simulator drives the **real** ``scheduler.Scheduler`` and the **real**
``scheduler.cost_model.estimate_execution_cost``, so the routing logic under test
is identical to production. Only the execution *environment* is modelled (workers
with bounded concurrency, a workload generator, and an arrival process) — there is
no Docker, no network, and everything is seeded, so a given ``SimConfig`` is fully
reproducible.

Two cost notions are kept deliberately separate (this mirrors reality and lets us
study estimation error):

- **routing weight** = ``estimate_execution_cost(...)`` — exactly what the scheduler
  sees and routes on (capped/imperfect, just like production).
- **true service time** — the actual execution duration used for completion timing,
  drawn from a bounded per-complexity model with multiplicative log-normal noise.

Usage:
    from evaluation.simulator import SimConfig, run_simulation
    res = run_simulation(SimConfig(mode=SchedulingMode.QUEUE_COST, num_workers=4))
    print(res.as_dict())
"""

from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass, field
from itertools import count
from typing import Dict, List, Optional, Tuple

from common.models import WorkerState, SchedulingMode, ComplexityAnalysis, Language
from scheduler.scheduler import Scheduler
from scheduler.cost_model import estimate_execution_cost
from evaluation.metrics import percentiles, jains_fairness, throughput

# Default weighted complexity mix (matches the locust workload weights).
DEFAULT_MIX: Dict[str, float] = {
    "O(1)": 1.0,
    "O(n)": 4.0,
    "O(n log n)": 2.0,
    "O(n^2)": 2.0,
}

# Bounded, realistic per-class nominal execution time (ms) at input_size=1000.
# Deliberately NOT the cost-model weights (those are routing weights and cap out);
# these keep simulated service times in a sane ms range so latency metrics mean
# something. Scaled by input_size and perturbed by log-normal noise per job.
NOMINAL_SERVICE_MS: Dict[str, float] = {
    "O(1)": 5.0,
    "O(log n)": 10.0,
    "O(n)": 50.0,
    "O(n log n)": 150.0,
    "O(n^2)": 600.0,
    "O(n^3)": 2500.0,
}


@dataclass
class SimConfig:
    """Parameters for a single simulation run."""

    mode: SchedulingMode
    num_workers: int
    concurrency: int = 1
    num_jobs: int = 2000
    arrival: str = "poisson"          # "poisson" (open-loop) | "closed" (closed-loop)
    rate: float = 50.0                # jobs/sec, open-loop arrival rate
    users: int = 50                   # closed-loop concurrent users
    think_time_s: float = 0.2         # closed-loop think time between submissions
    seed: int = 0
    mix: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_MIX))
    languages: Dict[str, float] = field(default_factory=lambda: {"python": 1.0})
    input_sizes: List[int] = field(default_factory=lambda: [500, 1000, 2000])
    cpu_from_utilization: bool = False  # synthesize cpu_util from slot usage
    service_noise_sigma: float = 0.3    # log-normal sigma for true service time


@dataclass
class Job:
    job_id: int
    arrival_time: float
    routing_weight_ms: float
    service_ms: float
    complexity: str
    language: str
    user_id: Optional[int] = None
    start_time: Optional[float] = None
    completion_time: Optional[float] = None

    @property
    def latency_ms(self) -> float:
        return (self.completion_time or 0.0) - self.arrival_time


@dataclass
class _WorkerSim:
    worker_id: str
    concurrency: int
    running: int = 0
    assigned_not_done: int = 0      # queued + running -> active_jobs signal
    load_ms: float = 0.0            # scheduler's outstanding-cost bookkeeping
    completed_count: int = 0
    completed_work_ms: float = 0.0  # sum of true service times completed here
    waitq: List[Job] = field(default_factory=list)


@dataclass
class SimResult:
    mode: str
    num_workers: int
    concurrency: int
    num_jobs: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_latency_ms: float
    p95_wait_ms: float
    throughput_jobs_s: float
    makespan_ms: float
    fairness: float
    mean_utilization: float
    per_worker_jobs: Dict[str, int]

    def as_dict(self) -> Dict[str, float]:
        d = dict(self.__dict__)
        d.pop("per_worker_jobs", None)
        return d


# ============================================================================
# Workload generation
# ============================================================================

def _weighted_choice(rng: random.Random, weights: Dict[str, float]) -> str:
    items = list(weights.items())
    total = sum(w for _, w in items)
    r = rng.uniform(0, total)
    upto = 0.0
    for key, w in items:
        upto += w
        if r <= upto:
            return key
    return items[-1][0]


def _make_job(rng: random.Random, cfg: SimConfig, job_id: int, arrival_time: float,
              user_id: Optional[int] = None) -> Job:
    complexity = _weighted_choice(rng, cfg.mix)
    language = _weighted_choice(rng, cfg.languages)
    input_size = rng.choice(cfg.input_sizes)

    # Routing weight: exactly what the real scheduler sees.
    analysis = ComplexityAnalysis(time_complexity=complexity, confidence=0.9)
    lang_enum = Language.PYTHON if language == "python" else Language.CPP
    routing_weight = estimate_execution_cost(analysis, lang_enum, input_size)

    # True service time: bounded nominal model, scaled by input size, log-normal noise.
    nominal = NOMINAL_SERVICE_MS.get(complexity, 100.0)
    lang_factor = 4.0 if language == "python" else 1.0
    size_factor = input_size / 1000.0
    noise = math.exp(rng.gauss(0.0, cfg.service_noise_sigma))
    service_ms = max(1.0, nominal * lang_factor * size_factor * noise)

    return Job(
        job_id=job_id,
        arrival_time=arrival_time,
        routing_weight_ms=routing_weight,
        service_ms=service_ms,
        complexity=complexity,
        language=language,
        user_id=user_id,
    )


def estimate_mean_service_ms(cfg: SimConfig, samples: int = 5000) -> float:
    """Monte-Carlo estimate of mean true service time for cfg's workload.

    Used to set an arrival rate that targets a given system utilization, so every
    sweep cell is compared at equal offered load (correct experimental design).
    """
    rng = random.Random((cfg.seed ^ 0x5BD1E995) & 0xFFFFFFFF)
    total = sum(_make_job(rng, cfg, i, 0.0).service_ms for i in range(samples))
    return total / samples


def rate_for_utilization(cfg: SimConfig, rho: float) -> float:
    """Arrival rate (jobs/sec) that loads the system to utilization rho.

    capacity = (workers * concurrency) / mean_service_seconds; rate = rho * capacity.
    """
    mean_service_s = estimate_mean_service_ms(cfg) / 1000.0
    capacity = (cfg.num_workers * cfg.concurrency) / mean_service_s
    return rho * capacity


# ============================================================================
# Core event-driven simulation
# ============================================================================

# event kinds
_ARRIVAL = 0
_COMPLETION = 1


def run_simulation(cfg: SimConfig) -> SimResult:
    rng = random.Random(cfg.seed)
    scheduler = Scheduler(mode=cfg.mode, seed=cfg.seed)

    workers = [
        _WorkerSim(worker_id=f"worker-{i + 1}", concurrency=cfg.concurrency)
        for i in range(cfg.num_workers)
    ]
    wmap = {w.worker_id: w for w in workers}

    events: List[Tuple[float, int, int, object]] = []  # (time, seq, kind, payload)
    seq = count()
    jobs: List[Job] = []

    def push(t: float, kind: int, payload: object) -> None:
        heapq.heappush(events, (t, next(seq), kind, payload))

    # ---- seed arrivals -----------------------------------------------------
    created = 0
    if cfg.arrival == "poisson":
        t = 0.0
        for _ in range(cfg.num_jobs):
            t += rng.expovariate(cfg.rate) * 1000.0  # seconds -> ms
            job = _make_job(rng, cfg, created, t)
            jobs.append(job)
            push(t, _ARRIVAL, job)
            created += 1
    elif cfg.arrival == "closed":
        for u in range(cfg.users):
            job = _make_job(rng, cfg, created, 0.0, user_id=u)
            jobs.append(job)
            push(0.0, _ARRIVAL, job)
            created += 1
    else:
        raise ValueError(f"Unknown arrival process: {cfg.arrival}")

    # ---- worker helpers ----------------------------------------------------
    def snapshot() -> List[WorkerState]:
        states = []
        for w in workers:
            cpu = None
            if cfg.cpu_from_utilization and w.concurrency > 0:
                cpu = min(1.0, w.running / w.concurrency)
            states.append(WorkerState(
                worker_id=w.worker_id,
                queue_cost_ms=w.load_ms,
                active_jobs=w.assigned_not_done,
                cpu_util=cpu,
                is_healthy=True,
            ))
        return states

    def start_job(w: _WorkerSim, job: Job, now: float) -> None:
        job.start_time = now
        w.running += 1
        push(now + job.service_ms, _COMPLETION, (w.worker_id, job))

    # ---- event loop --------------------------------------------------------
    while events:
        now, _s, kind, payload = heapq.heappop(events)

        if kind == _ARRIVAL:
            job: Job = payload  # type: ignore
            load_map = {w.worker_id: w.load_ms for w in workers}
            result = scheduler.select_worker(snapshot(), job.routing_weight_ms, load_map)
            assert result is not None
            selected_state, _decision = result
            w = wmap[selected_state.worker_id]

            w.load_ms += job.routing_weight_ms
            w.assigned_not_done += 1

            if w.running < w.concurrency:
                start_job(w, job, now)
            else:
                w.waitq.append(job)

        else:  # _COMPLETION
            worker_id, job = payload  # type: ignore
            w = wmap[worker_id]
            job.completion_time = now
            w.running -= 1
            w.assigned_not_done -= 1
            w.load_ms = max(0.0, w.load_ms - job.routing_weight_ms)
            w.completed_count += 1
            w.completed_work_ms += job.service_ms

            # Start next queued job, if any.
            if w.waitq:
                nxt = w.waitq.pop(0)
                start_job(w, nxt, now)

            # Closed-loop: re-arm this user with a new submission after think time.
            if cfg.arrival == "closed" and created < cfg.num_jobs:
                nxt_arrival = now + cfg.think_time_s * 1000.0
                new_job = _make_job(rng, cfg, created, nxt_arrival, user_id=job.user_id)
                jobs.append(new_job)
                push(nxt_arrival, _ARRIVAL, new_job)
                created += 1

    # ---- metrics -----------------------------------------------------------
    done = [j for j in jobs if j.completion_time is not None]
    latencies = [j.latency_ms for j in done]
    waits = [(j.start_time - j.arrival_time) for j in done if j.start_time is not None]

    first_arrival = min((j.arrival_time for j in done), default=0.0)
    last_completion = max((j.completion_time for j in done), default=0.0)
    makespan = last_completion - first_arrival
    wall_s = makespan / 1000.0

    pct = percentiles(latencies)
    total_service = sum(w.completed_work_ms for w in workers)
    denom = cfg.num_workers * cfg.concurrency * makespan if makespan > 0 else 0.0
    mean_util = (total_service / denom) if denom > 0 else 0.0

    return SimResult(
        mode=cfg.mode.value,
        num_workers=cfg.num_workers,
        concurrency=cfg.concurrency,
        num_jobs=len(done),
        p50_ms=pct["p50"],
        p95_ms=pct["p95"],
        p99_ms=pct["p99"],
        mean_latency_ms=(sum(latencies) / len(latencies)) if latencies else 0.0,
        p95_wait_ms=percentiles(waits, (95,))["p95"],
        throughput_jobs_s=throughput(len(done), wall_s),
        makespan_ms=makespan,
        fairness=jains_fairness([w.completed_work_ms for w in workers]),
        mean_utilization=mean_util,
        per_worker_jobs={w.worker_id: w.completed_count for w in workers},
    )
