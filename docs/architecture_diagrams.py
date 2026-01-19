"""
DAALAB Scheduler-Worker Architecture Diagram

ASCII diagram for documentation and presentations
"""

ARCHITECTURE_DIAGRAM = r"""
┌──────────────────────────────────────────────────────────────────────────┐
│                          CLIENT (Web Browser)                             │
│                     HTML/CSS/JS Frontend (Port 80)                        │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ HTTP POST /api/run-code
                                 │ {code, language, algorithm_name}
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    LOAD BALANCER (Port 8080)                              │
│                         ⚖️ Round-Robin                                    │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Algorithm: Select next healthy scheduler                        │    │
│  │ • NO complexity awareness                                       │    │
│  │ • NO job inspection                                             │    │
│  │ • ONLY traffic distribution                                     │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ Forward request
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     SCHEDULER (Port 8000)                                 │
│                    🧠 Complexity-Aware Routing                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │ Step 1: AI Complexity Analysis                                  │    │
│  │         ├→ Call AI Service (Port 8002)                          │    │
│  │         └→ Get: O(n log n), confidence: 0.92                    │    │
│  │                                                                  │    │
│  │ Step 2: Cost Estimation                                         │    │
│  │         cost = base × growth(n) × lang_multiplier               │    │
│  │         = 200ms × 1000log(1000) × 4.0 = 8000ms                  │    │
│  │                                                                  │    │
│  │ Step 3: Fetch Worker States                                     │    │
│  │         GET /status from all workers                            │    │
│  │         Worker-1: queue_cost=5000ms, active_jobs=3              │    │
│  │         Worker-2: queue_cost=8000ms, active_jobs=2              │    │
│  │                                                                  │    │
│  │ Step 4: Select Worker (Algorithm Choice)                        │    │
│  │                                                                  │    │
│  │   ┌─────────────────────┐  ┌──────────────────────┐            │    │
│  │   │ BASELINE            │  │ PROPOSED             │            │    │
│  │   │ (Queue-Length)      │  │ (Queue-Cost)         │            │    │
│  │   ├─────────────────────┤  ├──────────────────────┤            │    │
│  │   │ Select by:          │  │ Select by:           │            │    │
│  │   │ min(active_jobs)    │  │ min(queue_cost_ms)   │            │    │
│  │   │                     │  │ + CPU penalty        │            │    │
│  │   │ Worker-2 chosen     │  │ Worker-1 chosen      │            │    │
│  │   │ (2 < 3 jobs)        │  │ (5000 < 8000 ms)     │            │    │
│  │   └─────────────────────┘  └──────────────────────┘            │    │
│  │                                                                  │    │
│  │ Step 5: Dispatch Job                                            │    │
│  │         POST /execute to selected worker                        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────┬────────────────────────────┬──────────────────────────────────┘
           │                            │
           │ POST /execute              │ POST /execute
           │ {job_id, code,             │ {job_id, code,
           │  estimated_cost_ms}        │  estimated_cost_ms}
           ▼                            ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│   WORKER 1 (Port 8001)  │   │   WORKER 2 (Port 8002)  │
│   🐳 Docker Execution   │   │   🐳 Docker Execution   │
├─────────────────────────┤   ├─────────────────────────┤
│ State Management:       │   │ State Management:       │
│ • queue_cost_ms: 5000   │   │ • queue_cost_ms: 8000   │
│ • active_jobs: 3        │   │ • active_jobs: 2        │
│ • cpu_util: 0.6         │   │ • cpu_util: 0.9         │
│                         │   │                         │
│ Execution Flow:         │   │ Execution Flow:         │
│ 1. Increment queue_cost │   │ 1. Increment queue_cost │
│ 2. Write code to file   │   │ 2. Write code to file   │
│ 3. docker.run()         │   │ 3. docker.run()         │
│    ├→ python:3.13-slim  │   │    ├→ python:3.13-slim  │
│    └→ gcc:latest        │   │    └→ gcc:latest        │
│ 4. Capture output       │   │ 4. Capture output       │
│ 5. Measure runtime      │   │ 5. Measure runtime      │
│ 6. Decrement queue_cost │   │ 6. Decrement queue_cost │
│ 7. Return result        │   │ 7. Return result        │
└─────────────────────────┘   └─────────────────────────┘
           │                            │
           │ Result                     │ Result
           │ {output, runtime}          │ {output, runtime}
           └────────────┬───────────────┘
                        ▼
           ┌────────────────────────┐
           │   RESPONSE TO CLIENT   │
           │  {output: "...",       │
           │   runtime: 0.123,      │
           │   success: true}       │
           └────────────────────────┘

LEGEND:
━━━━━  Critical path (job submission → execution → response)
┈┈┈┈┈  Optional/monitoring connections
🧠     Intelligence/decision-making component
🐳     Docker-based isolation
⚖️      Load distribution
"""

COST_MODEL_DIAGRAM = r"""
┌──────────────────────────────────────────────────────────────┐
│                    COST ESTIMATION MODEL                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  INPUT: Complexity Analysis from AI                          │
│         ├─ time_complexity: "O(n log n)"                     │
│         ├─ confidence: 0.92                                  │
│         └─ language: "python"                                │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ STEP 1: Get Base Cost                               │    │
│  │                                                      │    │
│  │  COMPLEXITY_BASE_COST = {                           │    │
│  │    "O(1)":       10 ms                              │    │
│  │    "O(log n)":   50 ms                              │    │
│  │    "O(n)":      100 ms                              │    │
│  │    "O(n log n)": 200 ms  ← Selected                │    │
│  │    "O(n^2)":    500 ms                              │    │
│  │  }                                                   │    │
│  │                                                      │    │
│  │  base_cost = 200 ms                                 │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                   │
│                           ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ STEP 2: Calculate Growth                            │    │
│  │                                                      │    │
│  │  For "O(n log n)" with n = 1000:                    │    │
│  │    growth = n × log₂(n)                             │    │
│  │           = 1000 × log₂(1000)                       │    │
│  │           = 1000 × 9.97                             │    │
│  │           ≈ 9970                                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                   │
│                           ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ STEP 3: Apply Language Multiplier                   │    │
│  │                                                      │    │
│  │  LANGUAGE_MULTIPLIER = {                            │    │
│  │    "python": 4.0  ← Selected                        │    │
│  │    "cpp":    1.0                                    │    │
│  │  }                                                   │    │
│  │                                                      │    │
│  │  language_factor = 4.0                              │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                   │
│                           ▼                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ STEP 4: Final Calculation                           │    │
│  │                                                      │    │
│  │  estimated_cost = base_cost × growth × lang_factor  │    │
│  │                 = 200 ms × 9970 × 4.0               │    │
│  │                 = 7,976,000 ms                      │    │
│  │                 ≈ 8,000,000 ms (8 seconds)          │    │
│  │                                                      │    │
│  │  Capped at: 300,000 ms (5 minutes max)             │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                   │
│                           ▼                                   │
│  OUTPUT: 8000 ms (used by scheduler for worker selection)    │
│                                                               │
└──────────────────────────────────────────────────────────────┘

EXAMPLE COMPARISONS:

┌──────────┬─────────┬───────┬───────────┬─────────────────┐
│ Code     │ Cmplx   │ Lang  │ n         │ Estimated Cost  │
├──────────┼─────────┼───────┼───────────┼─────────────────┤
│ Hash get │ O(1)    │ Py    │ 1         │ 40 ms           │
│ Linear   │ O(n)    │ Py    │ 1,000     │ 400,000 ms      │
│ Sort     │ O(nlogn)│ Py    │ 1,000     │ 8,000,000 ms    │
│ Bubble   │ O(n²)   │ Py    │ 100       │ 2,000,000 ms    │
│ Sort     │ O(nlogn)│ C++   │ 1,000     │ 2,000,000 ms    │
└──────────┴─────────┴───────┴───────────┴─────────────────┘
"""

def print_all_diagrams():
    """Print all diagrams."""
    print(ARCHITECTURE_DIAGRAM)
    print("\n" * 3)
    print(COST_MODEL_DIAGRAM)


if __name__ == "__main__":
    print_all_diagrams()
