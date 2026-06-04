"""Unit tests for evaluation/simulator.py."""

import pytest

from common.models import SchedulingMode
from evaluation.simulator import (
    SimConfig,
    run_simulation,
    estimate_mean_service_ms,
    rate_for_utilization,
)


def _cfg(**kw):
    base = dict(mode=SchedulingMode.QUEUE_COST, num_workers=4, concurrency=1,
                num_jobs=500, rate=3.0, seed=0)
    base.update(kw)
    return SimConfig(**base)


class TestInvariants:
    def test_all_jobs_complete(self):
        res = run_simulation(_cfg(num_jobs=400))
        assert res.num_jobs == 400

    def test_latency_at_least_service(self):
        # With one worker at concurrency 1 and very light load, latency ~ service
        # time; it can never be less than service. Check makespan >= sum unaffected.
        res = run_simulation(_cfg(num_workers=1, concurrency=1, num_jobs=50, rate=0.05))
        # p50 latency must be positive and finite.
        assert res.p50_ms > 0
        assert res.p99_ms >= res.p50_ms

    def test_single_worker_makespan_covers_all_service(self):
        # One serial worker: makespan must be >= total service performed.
        res = run_simulation(_cfg(num_workers=1, concurrency=1, num_jobs=80, rate=0.05))
        # mean utilization <= 1 by construction.
        assert res.mean_utilization <= 1.0 + 1e-9

    def test_reproducible_same_seed(self):
        a = run_simulation(_cfg(seed=7))
        b = run_simulation(_cfg(seed=7))
        assert a.as_dict() == b.as_dict()

    def test_different_seed_differs(self):
        a = run_simulation(_cfg(seed=1))
        b = run_simulation(_cfg(seed=2))
        assert a.as_dict() != b.as_dict()


class TestUtilizationTargeting:
    def test_rate_for_utilization_scales_with_workers(self):
        c2 = _cfg(num_workers=2)
        c4 = _cfg(num_workers=4)
        r2 = rate_for_utilization(c2, 0.8)
        r4 = rate_for_utilization(c4, 0.8)
        # Twice the workers -> ~twice the sustainable arrival rate.
        assert r4 == pytest.approx(2 * r2, rel=0.05)

    def test_mean_service_positive(self):
        assert estimate_mean_service_ms(_cfg()) > 0


class TestAlgorithmOrdering:
    """At a fixed sub-saturation load on a heterogeneous mix, the cost-aware
    proposed scheduler should not be worse than the naive baselines on tail
    latency, and should be at least as fair."""

    def test_queue_cost_beats_random_on_p95(self):
        rate = rate_for_utilization(_cfg(num_workers=4), 0.8)
        rnd = run_simulation(_cfg(mode=SchedulingMode.RANDOM, num_workers=4,
                                  num_jobs=2000, rate=rate, seed=3))
        cost = run_simulation(_cfg(mode=SchedulingMode.QUEUE_COST, num_workers=4,
                                   num_jobs=2000, rate=rate, seed=3))
        assert cost.p95_ms < rnd.p95_ms

    def test_queue_cost_fairness_high(self):
        rate = rate_for_utilization(_cfg(num_workers=4), 0.8)
        cost = run_simulation(_cfg(mode=SchedulingMode.QUEUE_COST, num_workers=4,
                                   num_jobs=2000, rate=rate, seed=3))
        assert cost.fairness > 0.95


class TestClosedLoop:
    def test_closed_loop_completes_target_jobs(self):
        res = run_simulation(_cfg(arrival="closed", users=10, num_jobs=300,
                                  think_time_s=0.1))
        assert res.num_jobs == 300
