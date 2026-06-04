"""Unit tests for evaluation/metrics.py."""

import pytest

from evaluation.metrics import (
    percentile,
    percentiles,
    jains_fairness,
    throughput,
    mean_ci,
)


class TestPercentile:
    def test_basic_percentiles(self):
        data = list(range(1, 101))  # 1..100
        assert percentile(data, 50) == pytest.approx(50.5)
        assert percentile(data, 0) == 1
        assert percentile(data, 100) == 100

    def test_empty(self):
        assert percentile([], 95) == 0.0

    def test_percentiles_dict(self):
        d = percentiles([10, 20, 30, 40], (50, 95, 99))
        assert set(d) == {"p50", "p95", "p99"}
        assert d["p50"] == pytest.approx(25.0)


class TestJainsFairness:
    def test_perfectly_equal_is_one(self):
        assert jains_fairness([5, 5, 5, 5]) == pytest.approx(1.0)

    def test_all_on_one_is_one_over_n(self):
        assert jains_fairness([10, 0, 0, 0]) == pytest.approx(0.25)
        assert jains_fairness([7, 0]) == pytest.approx(0.5)

    def test_empty_and_zero_are_trivially_fair(self):
        assert jains_fairness([]) == 1.0
        assert jains_fairness([0, 0, 0]) == 1.0

    def test_partial_imbalance_between_bounds(self):
        f = jains_fairness([8, 2])
        assert 0.5 < f < 1.0


class TestThroughput:
    def test_basic(self):
        assert throughput(100, 10.0) == pytest.approx(10.0)

    def test_zero_time(self):
        assert throughput(100, 0.0) == 0.0


class TestMeanCI:
    def test_constant_sample_zero_width(self):
        mean, half = mean_ci([5.0, 5.0, 5.0, 5.0])
        assert mean == pytest.approx(5.0)
        assert half == pytest.approx(0.0)

    def test_single_sample(self):
        mean, half = mean_ci([42.0])
        assert mean == 42.0
        assert half == 0.0

    def test_empty(self):
        assert mean_ci([]) == (0.0, 0.0)

    def test_ci_positive_for_varied_data(self):
        mean, half = mean_ci([1.0, 2.0, 3.0, 4.0, 5.0])
        assert mean == pytest.approx(3.0)
        assert half > 0.0
