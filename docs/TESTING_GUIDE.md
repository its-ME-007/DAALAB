# 🧪 Testing Guide for Scheduler-Worker Architecture

Complete testing strategy for DAALAB scheduler-worker implementation with baseline vs. proposed algorithm comparison.

---

## 📋 Test Categories

### 1. Unit Tests
Test individual components in isolation

### 2. Integration Tests  
Test service-to-service communication

### 3. Load Tests
Performance testing under concurrent load

### 4. Comparative Evaluation
Baseline vs. proposed algorithm comparison for DA research

---

## 🔬 Unit Testing

### Setup

```powershell
# Install test dependencies
pip install pytest pytest-asyncio

# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_scheduler.py -v

# Run with coverage
pytest tests/unit/ --cov=scheduler --cov=worker --cov-report=html
```

### Test Files

#### `tests/unit/test_cost_model.py`
Tests complexity-to-cost estimation:
- Growth functions (O(1), O(n), O(n²), etc.)
- Language multipliers (Python vs C++)
- Cost capping and defaults
- Low confidence handling

**Key Test Cases:**
```python
def test_python_vs_cpp_multiplier():
    # Python should be 4x more expensive than C++
    analysis = ComplexityAnalysis(time_complexity="O(n)", confidence=0.9)
    python_cost = estimate_execution_cost(analysis, Language.PYTHON, 1000)
    cpp_cost = estimate_execution_cost(analysis, Language.CPP, 1000)
    assert python_cost / cpp_cost == pytest.approx(4.0)
```

#### `tests/unit/test_scheduler.py`
Tests scheduling algorithms:
- Queue-length selection (baseline)
- Queue-cost selection (proposed)
- CPU penalty application
- Tie-breaking determinism
- Algorithm comparison

**Key Test Cases:**
```python
def test_applies_cpu_penalty():
    # Worker with high CPU should get penalty
    # Even if it has lower queue cost initially
    workers = [
        WorkerState(worker_id="low-cost-high-cpu", queue_cost_ms=1000, cpu_util=0.95),
        WorkerState(worker_id="medium-cost-low-cpu", queue_cost_ms=1500, cpu_util=0.3)
    ]
    scheduler = Scheduler(mode=SchedulingMode.QUEUE_COST)
    selected, _ = scheduler.select_worker(workers, 1000.0)
    assert selected.worker_id == "medium-cost-low-cpu"  # CPU penalty avoids overloaded worker
```

### Running Tests

```powershell
# Quick test run
pytest tests/unit/ -v

# Detailed output with print statements
pytest tests/unit/ -v -s

# Stop on first failure
pytest tests/unit/ -x

# Run only tests matching pattern
pytest tests/unit/ -k "test_cpu"
```

---

## 🔗 Integration Testing

Test complete workflow across services.

### Prerequisites

```powershell
# Start all services
.\start_all.ps1

# Wait for services to be ready (~10 seconds)
```

### Manual Integration Tests

#### Test 1: Health Checks

```powershell
# Worker 1
curl http://localhost:8001/health

# Worker 2
curl http://localhost:8002/health

# Scheduler
curl http://localhost:8000/api/health

# Expected: All return 200 with "status": "healthy"
```

#### Test 2: Worker State Polling

```powershell
# Get worker state
curl http://localhost:8001/status

# Expected response:
# {
#   "worker_id": "worker-1",
#   "queue_cost_ms": 0.0,
#   "active_jobs": 0,
#   "cpu_util": 0.23,
#   "is_healthy": true
# }
```

#### Test 3: End-to-End Execution

```powershell
# Submit code
curl -X POST http://localhost:8000/api/run-code `
  -H "Content-Type: application/json" `
  -d '{
    "code": "print(\"Hello from worker!\")",
    "language": "python",
    "algorithm_name": "hello",
    "input_size": 1
  }'

# Expected: Success response with output
```

#### Test 4: Algorithm Mode Switching

```powershell
# Check current mode
curl http://localhost:8000/api/scheduler/mode

# Switch to queue-length (baseline)
curl -X POST http://localhost:8000/api/scheduler/mode `
  -H "Content-Type: application/json" `
  -d '"queue_length"'

# Switch to queue-cost (proposed)
curl -X POST http://localhost:8000/api/scheduler/mode `
  -H "Content-Type: application/json" `
  -d '"queue_cost"'
```

### Automated Integration Test

```powershell
# Run integration test script
.\test_architecture.ps1

# This tests:
# - Health checks
# - O(1) code execution
# - O(n) code execution  
# - O(n²) code execution
# - Scheduling mode verification
```

---

## 🚀 Load Testing with Locust

### Installation

```powershell
pip install locust
```

### Test Scenarios

The `tests/load/locustfile.py` includes:

1. **CodeExecutionUser**: Submits mixed complexity code (O(1), O(n), O(n log n), O(n²))
2. **AsyncJobSubmissionUser**: Tests async job submission and polling

### Running Load Tests

#### Interactive Mode (Recommended)

```powershell
cd tests/load
locust -f locustfile.py --host=http://localhost:8000

# Open http://localhost:8089
# Configure:
#   - Number of users: 100
#   - Spawn rate: 10 users/second
#   - Host: http://localhost:8000
# Click "Start Swarming"
```

#### Headless Mode (For Automation)

```powershell
# Run 5-minute test with 100 concurrent users
locust -f tests/load/locustfile.py `
  --host=http://localhost:8000 `
  --users 100 `
  --spawn-rate 10 `
  --run-time 5m `
  --headless `
  --csv results/baseline

# Results saved to:
#   results/baseline_stats.csv
#   results/baseline_failures.csv
#   results/baseline_stats_history.csv
```

### Load Test Metrics

Locust automatically tracks:
- **Request count**: Total requests sent
- **Failure rate**: Percentage of failed requests
- **Response time**: Min, max, median, 95th percentile
- **Requests per second**: Throughput

Additional custom metrics in `locustfile.py`:
- Queue wait time
- Scheduling accuracy
- SLA violations (>30s response)
- Complexity distribution

---

## 📊 Comparative Evaluation (DA Research)

### Objective

Compare **baseline** (queue-length) vs. **proposed** (queue-cost) scheduling under identical load.

### Evaluation Protocol

#### Step 1: Prepare Environment

```powershell
# Ensure clean state
# Stop all services, clear logs
Remove-Item logs/* -Force

# Start services
.\start_all.ps1

# Wait for stabilization (30 seconds)
Start-Sleep -Seconds 30
```

#### Step 2: Run Baseline Test

```powershell
# Set scheduler to baseline mode
curl -X POST http://localhost:8000/api/scheduler/mode `
  -H "Content-Type: application/json" `
  -d '"queue_length"'

# Run load test
cd tests/load
locust -f locustfile.py `
  --host=http://localhost:8000 `
  --users 100 `
  --spawn-rate 10 `
  --run-time 10m `
  --headless `
  --csv ../../results/baseline

# Wait for completion
```

#### Step 3: Reset Environment

```powershell
# Stop and restart services to clear state
# This ensures fair comparison
```

#### Step 4: Run Proposed Test

```powershell
# Set scheduler to proposed mode
curl -X POST http://localhost:8000/api/scheduler/mode `
  -H "Content-Type: application/json" `
  -d '"queue_cost"'

# Run identical load test
locust -f locustfile.py `
  --host=http://localhost:8000 `
  --users 100 `
  --spawn-rate 10 `
  --run-time 10m `
  --headless `
  --csv ../../results/proposed
```

#### Step 5: Analyze Results

```powershell
# Compare CSV files
# results/baseline_stats.csv vs results/proposed_stats.csv

# Key metrics to compare:
# 1. Median response time
# 2. 95th percentile response time
# 3. Failure rate
# 4. Requests per second
```

### Visualization (Python)

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load results
baseline = pd.read_csv('results/baseline_stats.csv')
proposed = pd.read_csv('results/proposed_stats.csv')

# Compare median response times
comparison = pd.DataFrame({
    'Baseline': baseline.groupby('Name')['Median Response Time'].mean(),
    'Proposed': proposed.groupby('Name')['Median Response Time'].mean()
})

comparison.plot(kind='bar', title='Response Time Comparison')
plt.ylabel('Response Time (ms)')
plt.xlabel('Endpoint')
plt.savefig('results/comparison.png')
plt.show()

# Calculate improvement
improvement = (baseline['Median Response Time'].mean() - 
               proposed['Median Response Time'].mean()) / \
              baseline['Median Response Time'].mean() * 100

print(f"Average improvement: {improvement:.2f}%")
```

---

## 📈 Expected Results

### Hypothesis

**Queue-cost scheduling (proposed)** should outperform queue-length scheduling (baseline) when:

1. **Workload has mixed complexity**: O(1), O(n), O(n²) jobs intermixed
2. **Job execution times vary significantly**: Orders of magnitude difference
3. **Workers have imbalanced state**: Some busy, some idle

**Why?**
- Queue-length ignores execution time → Can route expensive jobs to busy workers
- Queue-cost considers estimated time → Routes expensive jobs to workers with lower queue cost

### Sample Expected Data

| Metric | Baseline (Queue-Length) | Proposed (Queue-Cost) | Improvement |
|--------|------------------------|----------------------|-------------|
| Median Response Time | 2,500 ms | 1,800 ms | **28% faster** |
| 95th Percentile | 12,000 ms | 8,000 ms | **33% faster** |
| SLA Violations (<30s) | 5% | 2% | **60% reduction** |
| Throughput (req/s) | 38 | 45 | **18% increase** |

---

## 🎓 DA Report Integration

### Algorithm Section

```
Algorithm 1: Baseline (Queue-Length Scheduling)
Input: Workers W = {w₁, w₂, ..., wₙ}
Output: Selected worker wₛ

1: wₛ ← arg min_{w∈W} w.active_jobs
2: return wₛ
```

```
Algorithm 2: Proposed (Queue-Cost Scheduling)
Input: Workers W = {w₁, w₂, ..., wₙ}, Job cost C
Output: Selected worker wₛ

1: for each w ∈ W do
2:     score[w] ← w.queue_cost_ms
3:     if w.cpu_util > CPU_THRESHOLD then
4:         score[w] ← score[w] + CPU_PENALTY
5:     end if
6: end for
7: wₛ ← arg min_{w∈W} score[w]
8: return wₛ
```

### Evaluation Section Template

```
5. EVALUATION

5.1 Experimental Setup
- Platform: Windows 11, Docker Desktop
- Workers: 2 instances (ports 8001-8002)
- Load: 100 concurrent users, 10-minute duration
- Workload: Mixed complexity (O(1): 10%, O(n): 40%, O(n log n): 20%, O(n²): 20%)

5.2 Metrics
- Response Time: Time from submission to completion
- Throughput: Successful requests per second
- SLA Violations: Requests exceeding 30-second threshold
- Scheduling Accuracy: |estimated_cost - actual_runtime| / actual_runtime

5.3 Results
[Insert comparison table and graphs from Locust results]

5.4 Discussion
The queue-cost scheduling algorithm demonstrated X% improvement in median 
response time compared to the baseline queue-length approach. This improvement 
is attributed to...
```

---

## 🔧 Troubleshooting Tests

### Tests Fail Due to Services Not Running

```powershell
# Check if services are up
curl http://localhost:8001/health
curl http://localhost:8000/api/health

# If not, start them
.\start_all.ps1
```

### Docker Container Errors

```powershell
# Check Docker is running
docker ps

# Check Docker images exist
docker images | Select-String "python|gcc"

# Pull images if missing
docker pull python:3.13-slim
docker pull gcc:latest
```

### Import Errors in Tests

```powershell
# Run tests from project root
cd D:\DAALAB
pytest tests/unit/ -v

# Add project to PYTHONPATH if needed
$env:PYTHONPATH = "D:\DAALAB"
```

### Locust Web UI Not Accessible

```powershell
# Ensure no firewall blocking port 8089
# Open browser to: http://localhost:8089

# Or use headless mode
locust --headless --users 10 --spawn-rate 1 --run-time 30s
```

---

## ✅ Testing Checklist

Before submitting DA project:

- [ ] All unit tests pass (`pytest tests/unit/ -v`)
- [ ] Integration test script passes (`.\test_architecture.ps1`)
- [ ] Baseline load test completed (10 minutes, 100 users)
- [ ] Proposed load test completed (10 minutes, 100 users)
- [ ] Results compared and documented
- [ ] Graphs generated for DA report
- [ ] Code coverage >80% (`pytest --cov`)
- [ ] All services start without errors
- [ ] Docker containers execute successfully

---

## 📚 Additional Resources

- **Locust Documentation**: https://docs.locust.io/
- **pytest Guide**: https://docs.pytest.org/
- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
- **Docker SDK**: https://docker-py.readthedocs.io/

---

## 🎯 Summary

This testing suite provides:

1. ✅ **Unit Tests**: Validate algorithms and cost models
2. ✅ **Integration Tests**: End-to-end workflow verification
3. ✅ **Load Tests**: Performance under concurrent load
4. ✅ **Comparative Evaluation**: Baseline vs. proposed comparison
5. ✅ **DA Report Data**: Ready-to-use metrics and graphs

**All tests are automated, reproducible, and aligned with DA research objectives!**
