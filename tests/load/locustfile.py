"""
Load Testing Configuration for Scheduler-Worker Architecture

This file uses Locust (https://locust.io/) for load testing.

Installation:
    pip install locust

Usage:
    # Start load test
    locust -f locustfile.py --host=http://localhost:8080

    # Then open http://localhost:8089 and configure:
    # - Number of users: 100
    # - Spawn rate: 10/second
    # - Duration: 5 minutes

    # Or run headless:
    locust -f locustfile.py --host=http://localhost:8080 \
           --users 100 --spawn-rate 10 --run-time 5m --headless

Test Scenarios:
    1. Baseline algorithm (queue-length)
    2. Proposed algorithm (queue-cost)
    3. Mixed workload (different complexity classes)
"""

from locust import HttpUser, task, between
import random
import json


# Sample code snippets with known complexities
CODE_SAMPLES = {
    "O(1)": """
def constant_time():
    return 42
print(constant_time())
""",
    "O(n)": """
def linear_search(n):
    total = 0
    for i in range(n):
        total += i
    return total
print(linear_search(1000))
""",
    "O(n log n)": """
def merge_sort_simulation(n):
    arr = list(range(n, 0, -1))
    return sorted(arr)
result = merge_sort_simulation(100)
print(len(result))
""",
    "O(n^2)": """
def bubble_sort_simulation(n):
    count = 0
    for i in range(n):
        for j in range(n):
            count += 1
    return count
result = bubble_sort_simulation(50)
print(result)
""",
}


class CodeExecutionUser(HttpUser):
    """
    Simulated user submitting code for execution.
    
    Behavior:
    - Randomly selects code with different complexity classes
    - Submits via /api/run-code endpoint
    - Waits between 1-3 seconds between requests
    """
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    @task(4)  # Weight 4 - most common
    def submit_linear_code(self):
        """Submit O(n) code - most common case."""
        # name= groups stats per complexity class in locust's CSV (per-class p50/95/99).
        self.client.post(
            "/api/run-code",
            json={
                "code": CODE_SAMPLES["O(n)"],
                "language": "python",
                "algorithm_name": "linear_search",
                "input_size": 1000
            },
            headers={"Content-Type": "application/json"},
            name="run-code:O(n)"
        )

    @task(2)  # Weight 2
    def submit_linearithmic_code(self):
        """Submit O(n log n) code."""
        self.client.post(
            "/api/run-code",
            json={
                "code": CODE_SAMPLES["O(n log n)"],
                "language": "python",
                "algorithm_name": "merge_sort",
                "input_size": 100
            },
            headers={"Content-Type": "application/json"},
            name="run-code:O(n log n)"
        )

    @task(2)  # Weight 2
    def submit_quadratic_code(self):
        """Submit O(n^2) code."""
        self.client.post(
            "/api/run-code",
            json={
                "code": CODE_SAMPLES["O(n^2)"],
                "language": "python",
                "algorithm_name": "bubble_sort",
                "input_size": 50
            },
            headers={"Content-Type": "application/json"},
            name="run-code:O(n^2)"
        )

    @task(1)  # Weight 1 - least common
    def submit_constant_code(self):
        """Submit O(1) code."""
        self.client.post(
            "/api/run-code",
            json={
                "code": CODE_SAMPLES["O(1)"],
                "language": "python",
                "algorithm_name": "constant",
                "input_size": 1
            },
            headers={"Content-Type": "application/json"},
            name="run-code:O(1)"
        )
    
    @task(1)
    def check_health(self):
        """Periodically check scheduler health."""
        self.client.get("/api/health")


class AsyncJobSubmissionUser(HttpUser):
    """
    User that submits jobs asynchronously and polls for results.
    
    Tests the async API pattern.
    """
    
    wait_time = between(2, 5)
    
    @task
    def submit_and_poll(self):
        """Submit job and poll for completion."""
        # Submit job
        response = self.client.post(
            "/api/submit-job",
            json={
                "code": CODE_SAMPLES["O(n)"],
                "language": "python",
                "algorithm_name": "async_test",
                "input_size": 1000
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            job_id = response.json().get("job_id")
            
            # Poll for result (max 5 attempts)
            for _ in range(5):
                status_response = self.client.get(f"/api/job/{job_id}")
                
                if status_response.status_code == 200:
                    data = status_response.json()
                    if data.get("status") in ["completed", "failed"]:
                        break
                
                # Wait between polls
                self.wait()


# ============================================================================
# Test Scenarios
# ============================================================================

def run_baseline_test():
    """
    Run load test with baseline (queue-length) scheduling.
    
    Before running, set scheduler mode:
        curl -X POST http://localhost:8000/api/scheduler/mode \\
             -H "Content-Type: application/json" \\
             -d '{"mode": "queue_length"}'
    """
    print("""
    ========================================
    BASELINE TEST (Queue-Length Scheduling)
    ========================================
    
    1. Set scheduler mode to 'queue_length'
    2. Run: locust -f locustfile.py --host=http://localhost:8080 --users 100 --spawn-rate 10 --run-time 5m --headless
    3. Collect metrics from locust_report
    """)


def run_proposed_test():
    """
    Run load test with proposed (queue-cost) scheduling.
    
    Before running, set scheduler mode:
        curl -X POST http://localhost:8000/api/scheduler/mode \\
             -H "Content-Type: application/json" \\
             -d '{"mode": "queue_cost"}'
    """
    print("""
    ========================================
    PROPOSED TEST (Queue-Cost Scheduling)
    ========================================
    
    1. Set scheduler mode to 'queue_cost'
    2. Run: locust -f locustfile.py --host=http://localhost:8080 --users 100 --spawn-rate 10 --run-time 5m --headless
    3. Collect metrics from locust_report
    4. Compare with baseline results
    """)


# ============================================================================
# Custom Metrics Collection
# ============================================================================

class MetricsCollector:
    """
    Custom metrics collector for DA evaluation.
    
    Tracks:
    - Queue wait time
    - Execution time
    - Scheduling accuracy (estimated vs actual)
    - SLA violations (>30s response time)
    """
    
    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0,
            "sla_violations": 0,
            "complexity_distribution": {},
        }
    
    def record_request(self, complexity: str, response_time: float, success: bool):
        """Record a request for metrics."""
        self.metrics["total_requests"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        self.metrics["total_response_time"] += response_time
        
        # SLA: Response time should be < 30 seconds
        if response_time > 30000:  # 30 seconds in ms
            self.metrics["sla_violations"] += 1
        
        # Track complexity distribution
        if complexity not in self.metrics["complexity_distribution"]:
            self.metrics["complexity_distribution"][complexity] = 0
        self.metrics["complexity_distribution"][complexity] += 1
    
    def get_summary(self):
        """Get metrics summary."""
        total = self.metrics["total_requests"]
        
        if total == 0:
            return {}
        
        return {
            "total_requests": total,
            "success_rate": self.metrics["successful_requests"] / total,
            "failure_rate": self.metrics["failed_requests"] / total,
            "avg_response_time_ms": self.metrics["total_response_time"] / total,
            "sla_violation_rate": self.metrics["sla_violations"] / total,
            "complexity_distribution": self.metrics["complexity_distribution"],
        }


if __name__ == "__main__":
    print("""
    DAALAB Load Testing Suite
    =========================
    
    Available scenarios:
    1. Baseline (queue-length) scheduling
    2. Proposed (queue-cost) scheduling
    3. Mixed workload comparison
    
    Usage:
        locust -f locustfile.py --host=http://localhost:8080
    
    Then open http://localhost:8089 to configure and start the test.
    """)
