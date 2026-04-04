"""Core scheduling algorithms for complexity-aware job routing.

This module implements both baseline and proposed scheduling algorithms:
- Baseline: Queue-length scheduling (select by active_jobs count)
- Proposed: Queue-cost scheduling (select by estimated queue cost)

This dual implementation enables comparative evaluation for research.
"""

import time
from typing import List, Optional, Tuple
from common.models import (
    WorkerState,
    SchedulingMode,
    SchedulingDecision,
    ComplexityAnalysis,
    Language
)
from common.constants import CPU_OVERLOAD_THRESHOLD, CPU_PENALTY


class Scheduler:
    """
    Complexity-aware job scheduler with multiple algorithms.
    
    Provides both baseline (queue-length) and proposed (queue-cost) scheduling
    algorithms for comparative evaluation.
    """
    
    def __init__(self, mode: SchedulingMode = SchedulingMode.QUEUE_COST):
        """
        Initialize scheduler.
        
        Args:
            mode: Scheduling algorithm to use (QUEUE_LENGTH or QUEUE_COST)
        """
        self.mode = mode
        self._round_robin_counter = 0  # For tie-breaking with equal costs
        self._worker_load_map = {}  # Tracks estimated load per worker
    
    def select_worker(
        self,
        workers: List[WorkerState],
        estimated_cost_ms: float,
        worker_load_map: dict = None
    ) -> Optional[Tuple[WorkerState, SchedulingDecision]]:
        """
        Select best worker for executing a job.
        
        Args:
            workers: List of available worker states
            estimated_cost_ms: Estimated execution cost in milliseconds
            worker_load_map: Optional map of worker_id -> estimated load (overrides worker-reported state)
        
        Returns:
            Tuple of (selected_worker, scheduling_decision) or None if no workers
        """
        if not workers:
            return None
        
        # Use provided load map if available
        if worker_load_map:
            self._worker_load_map = worker_load_map
        
        start_time = time.time()
        
        # Dispatch to appropriate algorithm
        if self.mode == SchedulingMode.QUEUE_LENGTH:
            selected_worker, reasoning = self._select_by_queue_length(workers)
        else:  # QUEUE_COST
            selected_worker, reasoning = self._select_by_queue_cost(
                workers, estimated_cost_ms
            )
        
        decision_time_ms = (time.time() - start_time) * 1000
        
        # Create scheduling decision record
        decision = SchedulingDecision(
            selected_worker_id=selected_worker.worker_id,
            selected_worker_url=f"http://{selected_worker.worker_id}",  # Placeholder
            scheduling_mode=self.mode,
            decision_time_ms=decision_time_ms,
            worker_state_at_decision=selected_worker,
            reasoning=reasoning
        )
        
        return selected_worker, decision
    
    def _select_by_queue_length(
        self,
        workers: List[WorkerState]
    ) -> Tuple[WorkerState, str]:
        """
        Baseline algorithm: Select worker with fewest active jobs.
        
        Args:
            workers: List of available worker states
        
        Returns:
            Tuple of (selected_worker, reasoning_string)
        
        Algorithm:
            1. Filter out unhealthy workers
            2. Find worker with minimum active_jobs
            3. Tie-break by worker_id (deterministic)
        """
        # Filter healthy workers
        healthy_workers = [w for w in workers if w.is_healthy]
        
        if not healthy_workers:
            healthy_workers = workers  # Fallback to all workers
        
        # Select worker with minimum active jobs
        selected = min(healthy_workers, key=lambda w: (w.active_jobs, w.worker_id))
        
        reasoning = (
            f"Baseline (queue-length): Selected {selected.worker_id} with "
            f"{selected.active_jobs} active jobs (lowest among {len(workers)} workers)"
        )
        
        return selected, reasoning
    
    def _select_by_queue_cost(
        self,
        workers: List[WorkerState],
        estimated_cost_ms: float
    ) -> Tuple[WorkerState, str]:
        """
        Proposed algorithm: Select worker with minimum queue cost.
        
        Args:
            workers: List of available worker states
            estimated_cost_ms: Estimated cost of incoming job
        
        Returns:
            Tuple of (selected_worker, reasoning_string)
        
        Algorithm:
            1. Filter out unhealthy workers
            2. For each worker, calculate score = queue_cost_ms
            3. Apply CPU_PENALTY if cpu_util > CPU_OVERLOAD_THRESHOLD
            4. Select worker with minimum score
            5. Tie-break by worker_id (deterministic)
        """
        # Filter healthy workers
        healthy_workers = [w for w in workers if w.is_healthy]
        
        if not healthy_workers:
            healthy_workers = workers  # Fallback to all workers
        
        # Calculate scores with CPU penalty
        worker_scores = []
        
        for worker in healthy_workers:
            # Use scheduler-tracked load if available, otherwise use worker-reported
            if self._worker_load_map and worker.worker_id in self._worker_load_map:
                score = self._worker_load_map[worker.worker_id]
            else:
                score = worker.queue_cost_ms
            
            # Apply CPU overload penalty
            if worker.cpu_util is not None and worker.cpu_util > CPU_OVERLOAD_THRESHOLD:
                score += CPU_PENALTY
            
            worker_scores.append((score, worker))
        
        # Find minimum score
        min_score = min(s[0] for s in worker_scores)
        
        # Get all workers with minimum score
        best_workers = [w for s, w in worker_scores if s == min_score]
        
        # Round-robin tie-breaking for equal scores
        selected = best_workers[self._round_robin_counter % len(best_workers)]
        self._round_robin_counter += 1
        cpu_penalty_applied = (
            selected.cpu_util is not None and 
            selected.cpu_util > CPU_OVERLOAD_THRESHOLD
        )
        
        reasoning = (
            f"Proposed (queue-cost): Selected {selected.worker_id} with "
            f"{selected.queue_cost_ms:.0f}ms queue cost"
        )
        
        if cpu_penalty_applied:
            reasoning += f" (CPU penalty applied: {selected.cpu_util:.2f} > {CPU_OVERLOAD_THRESHOLD})"
        
        reasoning += f" (lowest among {len(workers)} workers)"
        
        return selected, reasoning
    
    def set_mode(self, mode: SchedulingMode) -> None:
        """
        Change scheduling algorithm mode.
        
        Args:
            mode: New scheduling mode
        """
        self.mode = mode
        print(f"[MODE] Scheduler mode changed to: {mode.value}")


# ============================================================================
# High-Level Scheduling Functions
# ============================================================================

def select_worker_simple(
    workers: List[WorkerState],
    estimated_cost_ms: float,
    mode: str = "queue_cost"
) -> Optional[WorkerState]:
    """
    Simplified worker selection function.
    
    Args:
        workers: List of available workers
        estimated_cost_ms: Estimated job cost
        mode: "queue_length" or "queue_cost"
    
    Returns:
        Selected worker or None
    """
    scheduler_mode = (
        SchedulingMode.QUEUE_LENGTH if mode == "queue_length" 
        else SchedulingMode.QUEUE_COST
    )
    
    scheduler = Scheduler(mode=scheduler_mode)
    result = scheduler.select_worker(workers, estimated_cost_ms)
    
    if result:
        selected_worker, _ = result
        return selected_worker
    
    return None


# ============================================================================
# Algorithm Comparison Utilities
# ============================================================================

def compare_scheduling_algorithms(
    workers: List[WorkerState],
    estimated_cost_ms: float
) -> dict:
    """
    Compare baseline and proposed algorithms for the same worker states.
    
    Useful for evaluation and debugging.
    
    Args:
        workers: List of worker states
        estimated_cost_ms: Job cost estimate
    
    Returns:
        Dictionary with comparison results
    """
    baseline_scheduler = Scheduler(mode=SchedulingMode.QUEUE_LENGTH)
    proposed_scheduler = Scheduler(mode=SchedulingMode.QUEUE_COST)
    
    baseline_result = baseline_scheduler.select_worker(workers, estimated_cost_ms)
    proposed_result = proposed_scheduler.select_worker(workers, estimated_cost_ms)
    
    return {
        "baseline": {
            "worker_id": baseline_result[0].worker_id if baseline_result else None,
            "reasoning": baseline_result[1].reasoning if baseline_result else None,
            "decision_time_ms": baseline_result[1].decision_time_ms if baseline_result else None
        },
        "proposed": {
            "worker_id": proposed_result[0].worker_id if proposed_result else None,
            "reasoning": proposed_result[1].reasoning if proposed_result else None,
            "decision_time_ms": proposed_result[1].decision_time_ms if proposed_result else None
        },
        "same_selection": (
            baseline_result[0].worker_id == proposed_result[0].worker_id
            if baseline_result and proposed_result else False
        )
    }


# ============================================================================
# Testing and Diagnostics
# ============================================================================

def test_scheduler():
    """Test scheduler with synthetic worker states."""
    from datetime import datetime
    
    print("=" * 80)
    print("SCHEDULER ALGORITHM COMPARISON TEST")
    print("=" * 80)
    
    # Create synthetic worker states
    workers = [
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
    
    print("\nWorker States:")
    for w in workers:
        print(f"  {w.worker_id}: {w.active_jobs} jobs, {w.queue_cost_ms}ms, CPU: {w.cpu_util:.2f}")
    
    print("\n" + "-" * 80)
    print("Test Case: Job with 1000ms estimated cost")
    print("-" * 80)
    
    # Compare algorithms
    comparison = compare_scheduling_algorithms(workers, 1000.0)
    
    print("\n🔵 Baseline (Queue-Length):")
    print(f"   Selected: {comparison['baseline']['worker_id']}")
    print(f"   Reasoning: {comparison['baseline']['reasoning']}")
    print(f"   Decision time: {comparison['baseline']['decision_time_ms']:.3f}ms")
    
    print("\n🟢 Proposed (Queue-Cost):")
    print(f"   Selected: {comparison['proposed']['worker_id']}")
    print(f"   Reasoning: {comparison['proposed']['reasoning']}")
    print(f"   Decision time: {comparison['proposed']['decision_time_ms']:.3f}ms")
    
    print("\n" + "=" * 80)
    if comparison['same_selection']:
        print("[OK] Both algorithms selected the same worker")
    else:
        print("❗ Algorithms selected DIFFERENT workers (expected for this test case)")
    print("=" * 80)


if __name__ == "__main__":
    test_scheduler()
