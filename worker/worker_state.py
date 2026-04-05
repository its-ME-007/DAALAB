"""Worker state management with thread-safe operations.

This module maintains the execution state of a worker including queue cost,
active jobs, and resource utilization metrics.
"""

import threading
import time
import psutil
from datetime import datetime, timezone
from typing import Optional
from common.models import WorkerState as WorkerStateModel


class WorkerState:
    """
    Thread-safe worker state tracker.
    
    Maintains:
    - queue_cost_ms: Total estimated execution time in queue
    - active_jobs: Number of currently executing jobs
    - cpu_util: Optional CPU utilization (0-1)
    - mem_util: Optional memory utilization (0-1)
    
    All state modifications are protected by a lock to prevent race conditions.
    """
    
    def __init__(self, worker_id: str, enable_resource_monitoring: bool = False):
        """
        Initialize worker state.
        
        Args:
            worker_id: Unique identifier for this worker
            enable_resource_monitoring: Whether to track CPU/memory utilization
        """
        self.worker_id = worker_id
        self.enable_resource_monitoring = enable_resource_monitoring
        
        # State variables (protected by lock)
        self._queue_cost_ms: float = 0.0
        self._active_jobs: int = 0
        self._lock = threading.Lock()
        
        # Health tracking
        self._is_healthy = True
        self._last_heartbeat = datetime.now(timezone.utc)
        
        # Resource monitoring (optional)
        self._cpu_util: Optional[float] = None
        self._mem_util: Optional[float] = None
        
        if self.enable_resource_monitoring:
            self._start_resource_monitoring()
    
    def increment_queue_cost(self, estimated_cost_ms: float) -> None:
        """
        Add estimated cost to queue when job is accepted.
        
        Args:
            estimated_cost_ms: Estimated execution time in milliseconds
        """
        with self._lock:
            self._queue_cost_ms += estimated_cost_ms
            self._active_jobs += 1
    
    def decrement_queue_cost(self, estimated_cost_ms: float) -> None:
        """
        Remove estimated cost from queue when job completes.
        
        Args:
            estimated_cost_ms: Estimated execution time that was added
        """
        with self._lock:
            self._queue_cost_ms = max(0.0, self._queue_cost_ms - estimated_cost_ms)
            self._active_jobs = max(0, self._active_jobs - 1)
    
    def get_state(self) -> WorkerStateModel:
        """
        Get current worker state as Pydantic model.
        
        Returns:
            WorkerStateModel with current state
            
        Note: CPU/memory utilization is updated by the background monitoring 
        thread every 5 seconds. We do NOT call _update_resource_utilization()
        here because psutil.cpu_percent(interval=0.1) blocks for 100ms,
        which would block the async event loop on every /status request.
        """
        with self._lock:
            return WorkerStateModel(
                worker_id=self.worker_id,
                queue_cost_ms=self._queue_cost_ms,
                active_jobs=self._active_jobs,
                cpu_util=self._cpu_util,
                mem_util=self._mem_util,
                is_healthy=self._is_healthy,
                last_heartbeat=self._last_heartbeat
            )
    
    def update_heartbeat(self) -> None:
        """Update last heartbeat timestamp."""
        with self._lock:
            self._last_heartbeat = datetime.now(timezone.utc)
    
    def mark_unhealthy(self) -> None:
        """Mark worker as unhealthy (e.g., after repeated failures)."""
        with self._lock:
            self._is_healthy = False
    
    def mark_healthy(self) -> None:
        """Mark worker as healthy."""
        with self._lock:
            self._is_healthy = True
    
    def _update_resource_utilization(self) -> None:
        """
        Update CPU and memory utilization.
        
        Note: This method is NOT thread-safe by itself and should only be
        called while holding the lock.
        """
        try:
            self._cpu_util = psutil.cpu_percent(interval=0.1) / 100.0
            self._mem_util = psutil.virtual_memory().percent / 100.0
        except Exception:
            # If psutil fails, leave as None
            self._cpu_util = None
            self._mem_util = None
    
    def _start_resource_monitoring(self) -> None:
        """Start background thread for resource monitoring."""
        def monitor_loop():
            while True:
                time.sleep(5.0)  # Update every 5 seconds
                with self._lock:
                    if not self._is_healthy:
                        break  # Stop monitoring if worker is unhealthy
                    self._update_resource_utilization()
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    # ========================================================================
    # Convenience properties for read-only access
    # ========================================================================
    
    @property
    def queue_cost_ms(self) -> float:
        """Get current queue cost (thread-safe read)."""
        with self._lock:
            return self._queue_cost_ms
    
    @property
    def active_jobs(self) -> int:
        """Get current active job count (thread-safe read)."""
        with self._lock:
            return self._active_jobs
    
    @property
    def is_healthy(self) -> bool:
        """Get health status (thread-safe read)."""
        with self._lock:
            return self._is_healthy
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        state = self.get_state()
        return (
            f"WorkerState(id={state.worker_id}, "
            f"queue_cost={state.queue_cost_ms:.0f}ms, "
            f"active_jobs={state.active_jobs}, "
            f"cpu={state.cpu_util:.2f if state.cpu_util else 'N/A'}, "
            f"healthy={state.is_healthy})"
        )


# ============================================================================
# Testing and Diagnostics
# ============================================================================

if __name__ == "__main__":
    import time
    
    print("Testing WorkerState...")
    
    # Create worker with resource monitoring
    worker = WorkerState("worker-test-1", enable_resource_monitoring=True)
    
    print(f"Initial state: {worker}")
    
    # Simulate job acceptance
    print("\n➕ Adding job with 1000ms estimated cost")
    worker.increment_queue_cost(1000.0)
    print(f"State: {worker}")
    
    # Simulate another job
    print("\n➕ Adding job with 500ms estimated cost")
    worker.increment_queue_cost(500.0)
    print(f"State: {worker}")
    
    # Wait and check resource monitoring
    print("\n⏳ Waiting 6 seconds for resource monitoring update...")
    time.sleep(6)
    print(f"State: {worker}")
    
    # Simulate job completion
    print("\n➖ Completing job (1000ms)")
    worker.decrement_queue_cost(1000.0)
    print(f"State: {worker}")
    
    print("\n➖ Completing job (500ms)")
    worker.decrement_queue_cost(500.0)
    print(f"State: {worker}")
    
    print("\n[OK] WorkerState test complete!")
