"""Unit tests for scheduler algorithms."""

import pytest
from datetime import datetime
from scheduler.scheduler import Scheduler, compare_scheduling_algorithms
from common.models import WorkerState, SchedulingMode


@pytest.fixture
def sample_workers():
    """Create sample worker states for testing."""
    return [
        WorkerState(
            worker_id="worker-1",
            queue_cost_ms=5000.0,
            active_jobs=5,
            cpu_util=0.6,
            mem_util=0.5,
            is_healthy=True,
            last_heartbeat=datetime.utcnow()
        ),
        WorkerState(
            worker_id="worker-2",
            queue_cost_ms=8000.0,
            active_jobs=3,
            cpu_util=0.9,  # Overloaded!
            mem_util=0.7,
            is_healthy=True,
            last_heartbeat=datetime.utcnow()
        ),
        WorkerState(
            worker_id="worker-3",
            queue_cost_ms=2000.0,
            active_jobs=8,
            cpu_util=0.4,
            mem_util=0.3,
            is_healthy=True,
            last_heartbeat=datetime.utcnow()
        ),
    ]


class TestQueueLengthScheduling:
    """Test baseline queue-length scheduling algorithm."""
    
    def test_selects_minimum_active_jobs(self, sample_workers):
        """Should select worker with fewest active jobs."""
        scheduler = Scheduler(mode=SchedulingMode.QUEUE_LENGTH)
        result = scheduler.select_worker(sample_workers, 1000.0)
        
        assert result is not None
        selected_worker, decision = result
        
        # worker-2 has 3 active jobs (minimum)
        assert selected_worker.worker_id == "worker-2"
        assert decision.scheduling_mode == SchedulingMode.QUEUE_LENGTH
    
    def test_empty_worker_list(self):
        """Should return None for empty worker list."""
        scheduler = Scheduler(mode=SchedulingMode.QUEUE_LENGTH)
        result = scheduler.select_worker([], 1000.0)
        
        assert result is None
    
    def test_deterministic_tie_breaking(self, sample_workers):
        """Tie-breaking should be deterministic (by worker_id)."""
        # Create workers with same active_jobs
        workers = [
            WorkerState(
                worker_id="worker-b",
                queue_cost_ms=1000.0,
                active_jobs=5,
                is_healthy=True,
                last_heartbeat=datetime.utcnow()
            ),
            WorkerState(
                worker_id="worker-a",
                queue_cost_ms=2000.0,
                active_jobs=5,
                is_healthy=True,
                last_heartbeat=datetime.utcnow()
            ),
        ]
        
        scheduler = Scheduler(mode=SchedulingMode.QUEUE_LENGTH)
        result = scheduler.select_worker(workers, 1000.0)
        
        assert result is not None
        selected_worker, _ = result
        
        # Should select worker-a (alphabetically first)
        assert selected_worker.worker_id == "worker-a"


class TestQueueCostScheduling:
    """Test proposed queue-cost scheduling algorithm."""
    
    def test_selects_minimum_queue_cost(self, sample_workers):
        """Should select worker with lowest queue cost."""
        scheduler = Scheduler(mode=SchedulingMode.QUEUE_COST)
        result = scheduler.select_worker(sample_workers, 1000.0)
        
        assert result is not None
        selected_worker, decision = result
        
        # worker-3 has 2000ms queue cost (minimum)
        assert selected_worker.worker_id == "worker-3"
        assert decision.scheduling_mode == SchedulingMode.QUEUE_COST
    
    def test_applies_cpu_penalty(self):
        """Should apply penalty for high CPU utilization."""
        workers = [
            WorkerState(
                worker_id="worker-low-cost-high-cpu",
                queue_cost_ms=1000.0,
                active_jobs=2,
                cpu_util=0.95,  # Very high CPU
                is_healthy=True,
                last_heartbeat=datetime.utcnow()
            ),
            WorkerState(
                worker_id="worker-medium-cost-low-cpu",
                queue_cost_ms=1500.0,
                active_jobs=3,
                cpu_util=0.3,  # Low CPU
                is_healthy=True,
                last_heartbeat=datetime.utcnow()
            ),
        ]
        
        scheduler = Scheduler(mode=SchedulingMode.QUEUE_COST)
        result = scheduler.select_worker(workers, 1000.0)
        
        assert result is not None
        selected_worker, decision = result
        
        # Should select worker-medium despite higher queue cost
        # because worker-low gets CPU_PENALTY
        assert selected_worker.worker_id == "worker-medium-cost-low-cpu"
    
    def test_handles_missing_cpu_util(self):
        """Should handle workers without CPU utilization data."""
        workers = [
            WorkerState(
                worker_id="worker-1",
                queue_cost_ms=1000.0,
                active_jobs=2,
                cpu_util=None,  # No CPU data
                is_healthy=True,
                last_heartbeat=datetime.utcnow()
            ),
            WorkerState(
                worker_id="worker-2",
                queue_cost_ms=2000.0,
                active_jobs=3,
                cpu_util=None,
                is_healthy=True,
                last_heartbeat=datetime.utcnow()
            ),
        ]
        
        scheduler = Scheduler(mode=SchedulingMode.QUEUE_COST)
        result = scheduler.select_worker(workers, 1000.0)
        
        assert result is not None
        selected_worker, _ = result
        
        # Should select based on queue cost alone
        assert selected_worker.worker_id == "worker-1"


class TestSchedulerModeChanging:
    """Test switching between scheduling modes."""
    
    def test_mode_switching(self, sample_workers):
        """Should be able to switch modes dynamically."""
        scheduler = Scheduler(mode=SchedulingMode.QUEUE_LENGTH)
        
        # First selection with queue-length
        result1 = scheduler.select_worker(sample_workers, 1000.0)
        assert result1[1].scheduling_mode == SchedulingMode.QUEUE_LENGTH
        
        # Switch to queue-cost
        scheduler.set_mode(SchedulingMode.QUEUE_COST)
        
        # Second selection with queue-cost
        result2 = scheduler.select_worker(sample_workers, 1000.0)
        assert result2[1].scheduling_mode == SchedulingMode.QUEUE_COST


class TestAlgorithmComparison:
    """Test algorithm comparison utilities."""
    
    def test_compare_scheduling_algorithms(self, sample_workers):
        """Should compare both algorithms on same input."""
        comparison = compare_scheduling_algorithms(sample_workers, 1000.0)
        
        assert "baseline" in comparison
        assert "proposed" in comparison
        assert "same_selection" in comparison
        
        # Both should return valid worker_id
        assert comparison["baseline"]["worker_id"] is not None
        assert comparison["proposed"]["worker_id"] is not None
        
        # Decision times should be measured
        assert comparison["baseline"]["decision_time_ms"] >= 0
        assert comparison["proposed"]["decision_time_ms"] >= 0
    
    def test_different_selections_possible(self, sample_workers):
        """Algorithms should make different selections for some inputs."""
        comparison = compare_scheduling_algorithms(sample_workers, 1000.0)
        
        # For our sample workers, algorithms should differ
        # (worker-2 has few jobs but high queue cost)
        assert not comparison["same_selection"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
