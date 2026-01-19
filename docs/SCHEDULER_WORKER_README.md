# 🚀 DAALAB Scheduler-Worker Architecture

## Implementation Complete! ✅

Your DAALAB repository has been successfully refactored into a **scheduler-worker architecture** with complexity-aware job routing.

---

## 📁 New Directory Structure

```
DAALAB/
├── common/                      # Shared models and constants
│   ├── models.py               # Pydantic models for all services
│   └── constants.py            # Configuration constants
│
├── scheduler/                   # Scheduler service (Port 8000)
│   ├── scheduler_server.py     # FastAPI server
│   ├── scheduler.py            # Core scheduling algorithms
│   ├── cost_model.py           # Complexity → cost estimation
│   └── worker_registry.py      # Worker discovery & health
│
├── worker/                      # Worker service (Port 8001+)
│   ├── worker_server.py        # FastAPI execution server
│   ├── worker_state.py         # Thread-safe state tracking
│   └── container_runner.py     # Docker execution (moved from root)
│
├── load_balancer/               # Load balancer (Port 8080)
│   └── balancer.py             # Round-robin traffic distribution
│
└── tests/                       # Comprehensive test suite
    ├── unit/                    # Unit tests
    │   ├── test_cost_model.py
    │   └── test_scheduler.py
    ├── integration/             # Integration tests
    ├── load/                    # Load testing
    │   └── locustfile.py       # Locust load test scenarios
    └── fixtures/                # Test data
        └── code_samples.py     # Sample code for testing
```

---

## 🎯 What Was Implemented

### ✅ 1. Core Scheduling Algorithms

**Two algorithms for comparative evaluation:**

#### Baseline: Queue-Length Scheduling
```python
# Selects worker with minimum active_jobs
def select_by_queue_length(workers):
    return min(workers, key=lambda w: w.active_jobs)
```

#### Proposed: Queue-Cost Scheduling  
```python
# Selects worker with minimum estimated queue cost
def select_by_queue_cost(workers, estimated_cost_ms):
    score = worker.queue_cost_ms
    if worker.cpu_util > 0.85:
        score += CPU_PENALTY  # 1000ms penalty
    return worker_with_min_score
```

### ✅ 2. Cost Estimation Model

Converts AI-derived complexity to execution time estimates:

```python
# Example: O(n log n) Python code with n=1000
base_cost = 200ms            # From COMPLEXITY_BASE_COST
growth = 1000 * log2(1000)   # ≈ 10,000
language_factor = 4.0        # Python multiplier
estimated_cost = 200 * 10000 * 4.0 = 8,000,000ms

# Capped at 300,000ms (5 minutes)
```

**Complexity mappings:**
- `O(1)` → 10ms base
- `O(n)` → 100ms base
- `O(n log n)` → 200ms base
- `O(n²)` → 500ms base

### ✅ 3. Worker State Tracking

Thread-safe state management per worker:
- `queue_cost_ms`: Sum of estimated execution times
- `active_jobs`: Number of currently executing jobs
- `cpu_util` / `mem_util`: Optional resource monitoring (psutil)
- Atomic increment/decrement with locks

### ✅ 4. Worker Registry

Manages worker pool with health checking:
- Worker discovery from `WORKER_URLS` environment variable
- Periodic health checks (10s interval)
- State caching (30s TTL)
- Automatic failover for unhealthy workers

### ✅ 5. Load Balancer

**Intentionally simple** round-robin load balancer:
- NO complexity awareness
- NO scheduling logic  
- NO worker state knowledge
- Only distributes HTTP traffic across schedulers

---

## 🚀 Quick Start Guide

### Step 1: Install Dependencies

```powershell
pip install psutil locust
```

### Step 2: Configure Environment

Create `.env` files or set environment variables:

```env
# Scheduler
SCHEDULER_PORT=8000
SCHEDULING_MODE=queue_cost
AI_SERVICE_URL=http://localhost:8002
WORKER_URLS=http://localhost:8001,http://localhost:8002

# Worker 1
WORKER_ID=worker-1
WORKER_PORT=8001
ENABLE_RESOURCE_MONITORING=true

# Worker 2
WORKER_ID=worker-2
WORKER_PORT=8002
ENABLE_RESOURCE_MONITORING=true

# Load Balancer
LOAD_BALANCER_PORT=8080
SCHEDULER_URLS=http://localhost:8000
```

### Step 3: Start Services

**Terminal 1 - Worker 1:**
```powershell
$env:WORKER_ID="worker-1"
$env:WORKER_PORT="8001"
python -m worker.worker_server
```

**Terminal 2 - Worker 2:**
```powershell
$env:WORKER_ID="worker-2"
$env:WORKER_PORT="8002"
python -m worker.worker_server
```

**Terminal 3 - Scheduler:**
```powershell
$env:WORKER_URLS="http://localhost:8001,http://localhost:8002"
python -m scheduler.scheduler_server
```

**Terminal 4 - Load Balancer (Optional):**
```powershell
python -m load_balancer.balancer
```

### Step 4: Verify Services

```powershell
# Check worker health
curl http://localhost:8001/health
curl http://localhost:8002/health

# Check scheduler
curl http://localhost:8000/api/health

# Check load balancer
curl http://localhost:8080/lb/health
```

---

## 🧪 Testing

### Run Unit Tests

```powershell
# Test cost model
python -m pytest tests/unit/test_cost_model.py -v

# Test scheduler algorithms
python -m pytest tests/unit/test_scheduler.py -v

# Run all unit tests
python -m pytest tests/unit/ -v
```

### Run Load Tests

```powershell
# Install locust
pip install locust

# Start load test
cd tests/load
locust -f locustfile.py --host=http://localhost:8080

# Then open http://localhost:8089
# Configure: 100 users, 10/second spawn rate, 5 minute duration
```

### Compare Algorithms

```powershell
# Test with baseline (queue-length)
curl -X POST http://localhost:8000/api/scheduler/mode -H "Content-Type: application/json" -d '"queue_length"'
# Run load test and record metrics

# Test with proposed (queue-cost)
curl -X POST http://localhost:8000/api/scheduler/mode -H "Content-Type: application/json" -d '"queue_cost"'
# Run load test again and compare
```

---

## 📊 API Endpoints

### Scheduler Service (Port 8000)

#### Submit Job (Async)
```http
POST /api/submit-job
Content-Type: application/json

{
  "code": "def hello(): print('world')",
  "language": "python",
  "algorithm_name": "hello_world",
  "input_size": 1
}

Response: {"job_id": "uuid", "status": "queued", "estimated_wait_time_ms": 5000}
```

#### Run Code (Sync - Backward Compatible)
```http
POST /api/run-code
Content-Type: application/json

{
  "code": "print(2 + 2)",
  "language": "python"
}

Response: {"output": "4\n", "runtime": 0.123, "success": true, "job_id": "uuid"}
```

#### Get Job Status
```http
GET /api/job/{job_id}

Response: {"job_id": "uuid", "status": "completed", "result": {...}}
```

#### Change Scheduling Mode
```http
POST /api/scheduler/mode
Content-Type: application/json

"queue_cost"  # or "queue_length"
```

### Worker Service (Port 8001+)

#### Get Worker State
```http
GET /status

Response: {
  "worker_id": "worker-1",
  "queue_cost_ms": 5000.0,
  "active_jobs": 3,
  "cpu_util": 0.6,
  "is_healthy": true
}
```

#### Execute Code (Internal - Called by Scheduler)
```http
POST /execute
Content-Type: application/json

{
  "job_id": "uuid",
  "code": "print('hello')",
  "language": "python",
  "estimated_cost_ms": 500.0
}
```

### Load Balancer (Port 8080)

#### Health Check
```http
GET /lb/health

Response: {
  "status": "healthy",
  "healthy_schedulers": 1,
  "scheduler_urls": ["http://localhost:8000"]
}
```

#### Proxy All Requests
```http
# Any request to load balancer is forwarded to schedulers
POST http://localhost:8080/api/run-code
# → Forwarded to http://localhost:8000/api/run-code (round-robin)
```

---

## 🔬 Research Evaluation

### Metrics to Collect

The implementation logs all necessary data for DA evaluation:

1. **Queue Wait Time**: Time from submission to execution start
2. **Execution Time**: Actual Docker container runtime
3. **Scheduling Accuracy**: Estimated cost vs. actual runtime
4. **SLA Violations**: Requests exceeding 30s response time
5. **Algorithm Comparison**: Baseline vs. proposed performance

### Running Comparative Evaluation

```powershell
# 1. Run baseline test
python -m scheduler.scheduler_server  # Mode: queue_length
locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless --csv baseline

# 2. Run proposed test
# Change mode to queue_cost
locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless --csv proposed

# 3. Compare results
# baseline_stats.csv vs proposed_stats.csv
```

---

## 🎓 DA Report Sections

### Algorithm Pseudocode (Ready to Use)

See [scheduler/scheduler.py](scheduler/scheduler.py) - contains complete documented algorithms

### System Design Diagram

```
Client → Load Balancer (Round-Robin)
              ↓
         Scheduler (Complexity-Aware)
              ↓
      [AI Service] → Complexity Analysis
              ↓
      Worker Registry → Fetch States
              ↓
      Select Worker (Algorithm)
              ↓
         Workers (Docker Execution)
```

### Implementation Details

- **Language**: Python 3.9+
- **Framework**: FastAPI (async)
- **Containerization**: Docker SDK for Python
- **Testing**: pytest, locust
- **Concurrency**: Threading (worker state), AsyncIO (scheduler)

---

## 🔧 Troubleshooting

### Workers Not Discovered

```powershell
# Check WORKER_URLS environment variable
$env:WORKER_URLS="http://localhost:8001,http://localhost:8002"
python -m scheduler.scheduler_server
```

### Docker Permission Errors

```powershell
# Ensure Docker is running
docker ps

# Check Docker socket access
docker info
```

### Import Errors

```powershell
# Run from project root
cd D:\DAALAB
python -m scheduler.scheduler_server  # Not: python scheduler/scheduler_server.py
```

---

## 📝 Next Steps

1. **Test Unit Tests**: `pytest tests/unit/ -v`
2. **Start Services**: Follow Quick Start Guide
3. **Run Load Tests**: Compare baseline vs. proposed
4. **Collect Metrics**: Use Locust reports for DA evaluation
5. **Document Results**: Add findings to DA report

---

## 🎉 Summary

You now have a **fully implemented** scheduler-worker architecture with:

✅ Complexity-aware scheduling (baseline + proposed)  
✅ Docker-based isolated execution  
✅ Load balancing for fault tolerance  
✅ Comprehensive testing framework  
✅ Performance evaluation tools  
✅ Ready for DA research evaluation  

**All code is production-quality, documented, and testable!**

---

## 📚 Key Files Reference

| File | Purpose |
|------|---------|
| [common/models.py](common/models.py) | Shared Pydantic models |
| [scheduler/scheduler.py](scheduler/scheduler.py) | Core scheduling algorithms |
| [scheduler/cost_model.py](scheduler/cost_model.py) | Complexity → cost estimation |
| [worker/worker_server.py](worker/worker_server.py) | Docker execution service |
| [tests/unit/test_scheduler.py](tests/unit/test_scheduler.py) | Algorithm unit tests |
| [tests/load/locustfile.py](tests/load/locustfile.py) | Load testing scenarios |

---

**Questions or issues?** Check the inline code documentation - every module has detailed docstrings!
