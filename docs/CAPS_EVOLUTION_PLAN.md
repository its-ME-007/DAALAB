# CAPS Evolution Plan: Heterogeneous Parallel Scheduling

> Status: **proposal under review**. No implementation has started.
> Scope: evolve CAPS from job-level routing into a framework that partitions one
> computational job across heterogeneous CPU/GPU workers, with the smallest
> possible change set to existing code.

---

## 1. Existing Architecture Assessment

### 1.1 What CAPS implements today

| Area | Files | Current behaviour |
|---|---|---|
| Coordinator | `scheduler/scheduler_server.py` | FastAPI service. Receives a job, queries the complexity service, estimates cost, selects **one** worker, POSTs to `/execute`, polls for the result. |
| Placement policies | `scheduler/scheduler.py` | `Scheduler.select_worker` with four modes: `queue_length`, `queue_cost`, `random`, `round_robin`. Decisions are per job, not per partition. |
| Complexity estimator | `scheduler/cost_model.py`, `common/constants.py` | Maps Big-O class, language and input size to an estimated runtime. `complexity_growth()` converts a complexity class and `n` into an operation count. |
| Resource manager | `scheduler/worker_registry.py` | Static `WORKER_URLS`, concurrent `/status` polling, 3 s cache, `worker_id -> url` map. `register_worker()` exists but no endpoint calls it. |
| Worker | `worker/worker_server.py`, `worker/worker_state.py`, `worker/container_runner.py` | Runs arbitrary user code in a fresh Docker container per job. Tracks queue cost, active jobs and CPU/memory (psutil). Has no notion of device type or capacity. |
| Shared models | `common/models.py` | Pydantic `WorkerState`, `ExecutionRequest`, `ExecutionResult`, `SchedulingMode`. |
| Evaluation | `evaluation/simulator.py`, `evaluation/metrics.py`, `evaluation/run_sweep.py` | Discrete-event simulator that drives the real scheduler; percentiles, Jain's fairness index, `mean_ci`. |
| Monolith and UI | `api_server.py`, `static/`, `code_assist/`, `load_balancer/` | Code-runner web app, Supabase authentication, LLM assistant, round-robin load balancer. |

Available hardware: NVIDIA RTX 4070 Laptop GPU (8 GB) and Docker 28.3. This is
sufficient for one real CUDA worker plus multiple CPU containers.

### 1.2 The core gap

CAPS currently routes **whole jobs to a single worker**. The proposal requires
**decomposing one job into chunks executed across many workers** and aggregating
the partial results. This is added as a new layer beside the existing per-job
scheduler; nothing existing is rewritten.

### 1.3 Retain unchanged

- `/execute`, `/job/{id}`, `/api/run-code`, `/api/submit-job` (existing app and paper results depend on them).
- `SchedulingMode` values and `Scheduler.select_worker` (used by the simulator, `run_sweep` and the published evaluation).
- `api_server.py`, `auth.py`, `code_assist/`, `load_balancer/` (not required for the new work).
- The `/status` response shape: only **optional** fields with defaults are added, so existing schedulers and tests remain compatible.

---

## 2. Architecture Evolution

### 2.1 Target architecture

```
                 ┌───────────────────── scheduler_server.py (Coordinator) ──────────────────────┐
 Dashboard  ───► │ POST /api/parallel-jobs        (NEW)   ──► coordinator.py (NEW)              │
 parallel.html   │ GET  /api/parallel-jobs/{id}   (NEW)        └─ partitioner.py (NEW)          │
                 │ POST /api/workers/register     (NEW, wraps registry.register_worker)         │
                 │ /api/submit-job, /api/run-code ── UNCHANGED (Scheduler.select_worker)         │
                 └──────────────┬───────────────────────────────────────────────────────────────┘
                                │ HTTP/JSON (httpx)
        ┌───────────────────────┼─────────────────────────┬────────────────────────────┐
  worker (Docker, cpus=0.5)  worker (Docker, cpus=2)   worker (native, CUDA)       worker (cloud VM)
  POST /execute_chunk (NEW)                            device=gpu (CuPy)           device=cpu
  GET  /status (+ device, capacity fields)             existing /execute retained; disabled on public hosts
        └──── workloads/ (NEW): monte_carlo.py, later matmul.py — split / run_chunk / merge
```

### 2.2 Module mapping

| Proposal component | Existing module | Change |
|---|---|---|
| A. Central coordinator | `scheduler_server.py` | Modify (~60 lines): three endpoints delegating to new `coordinator.py`. |
| B. Complexity estimator | `cost_model.py` | Extend (~15 lines): `estimate_chunk_ms(ops, capacity, latency)`. Workloads declare their operation count through the existing `complexity_growth()` (Monte Carlo is `O(n)`, matrix multiply is `O(n^3)`). |
| C. Heterogeneous resource manager | `worker_registry.py`, `WorkerState` | Extend: per-worker EWMA of measured capacity and round-trip latency; the registration endpoint reuses `register_worker()`. |
| D. Intelligent scheduler | `scheduler.py` (unchanged) + new `scheduler/partitioner.py` | Pure functions `equal()`, `capacity_aware()`, `dynamic_chunks()`. Kept separate because partitioning ("split N") has a different shape from placement ("pick one"). |
| E. Distributed workers | `worker_server.py`, `worker_state.py` | Extend (~70 lines): `/execute_chunk`, startup calibration, device detection, fault injection. |
| F. Aggregation and monitoring | new `coordinator.py`, `metrics.py` | Extend `metrics.py` (~30 lines): speedup, efficiency, imbalance, utilisation. |
| Workload definitions | none | New `workloads/` package: one module per benchmark exposing `split`, `run_chunk`, `merge`. |

### 2.3 Coordinator–worker protocol

Chunks execute **in-process** on the worker, not in a new Docker container.
`container_runner` costs roughly 0.5–1 s per invocation, which would dominate
chunk runtimes and hide any speedup. The worker process itself already runs in a
container (Compose), on a host (GPU) or on a VM (cloud). It executes only
**registered** kernels with numeric parameters — never user-supplied code.

```python
# common/models.py (additions)
class ChunkRequest(BaseModel):
    job_id: str
    chunk_id: int
    workload: str               # "monte_carlo"
    params: Dict[str, Any]      # {"n": 2_000_000, "seed_index": 7, "base_seed": 42}

class ChunkResult(BaseModel):
    job_id: str
    chunk_id: int
    worker_id: str
    partial: Dict[str, Any]     # {"hits": ..., "n": ...}
    compute_ms: float           # measured on the worker
    device: str                 # "cpu" | "gpu"

# WorkerState: optional additions; defaults keep existing payloads valid
device: str = "cpu"
device_name: Optional[str] = None
capacity_ops_s: Optional[float] = None   # from calibration
throttle: Optional[str] = None           # e.g. "docker cpus=0.5", "injected latency 50ms"
```

- **Synchronous request/response per chunk**, no polling; chunks are short. The worker runs the kernel via `asyncio.to_thread` so `/status` stays responsive (NumPy and CuPy release the GIL).
- **No clock synchronisation required.** Communication overhead is computed as coordinator-measured round-trip time minus the worker-reported `compute_ms`.
- **Push model.** In dynamic mode the coordinator runs one async loop per worker: take the next chunk, POST it, record the result, repeat. This is semantically equivalent to workers requesting more work on completion, but does not require workers to reach the coordinator (the development laptop is behind NAT).

### 2.4 Representing CPU and GPU workers honestly

- `device` is set by **detection**, never configuration: `cupy.cuda.runtime.getDeviceCount() > 0`, with the real `device_name` reported. Without CUDA the worker is `cpu`.
- CPU heterogeneity comes from **real resource limits** (Docker `cpus: 0.5 / 1 / 2`), not declared numbers.
- Any artificial slowdown or injected latency populates the `throttle` field, which is shown in the dashboard and recorded in every results CSV.
- Capacity is always **measured** (Section 3.1), never declared.

---

## 3. Scheduling Design

**Cost model.** Worker *i* has measured throughput *Cᵢ* (ops/s) and round-trip
latency *Lᵢ*. Finishing *nᵢ* operations takes

    Tᵢ = Lᵢ + nᵢ / Cᵢ,       makespan = maxᵢ Tᵢ

### 3.1 Measuring worker capacity

1. **Startup calibration:** warm-up, then three runs of a fixed kernel (1e6 samples on CPU, 1e8 on GPU); the median throughput is reported as `capacity_ops_s` in `/status`.
2. **Online refinement:** after every chunk the coordinator updates `Cᵢ ← 0.7·Cᵢ + 0.3·(n / compute_ms)` and updates `Lᵢ` the same way from `RTT − compute_ms`. This tracks slowdowns and thermal throttling.

### 3.2 Strategy 1 — Equal partitioning (baseline)

`nᵢ = ⌊N / P⌋`, remainder distributed over the first workers.

### 3.3 Strategy 2 — Latency-aware capacity-proportional (static)

Choose a common finish time *T\** such that every worker finishes together:

    Σᵢ Cᵢ (T* − Lᵢ) = N   ⇒   T* = (N + Σᵢ CᵢLᵢ) / Σᵢ Cᵢ,   nᵢ = Cᵢ (T* − Lᵢ)

Workers with `nᵢ ≤ 0` are dropped and the equation is re-solved over the rest
(water-filling). With `L = 0` this reduces to `nᵢ = N·Cᵢ / ΣC`. The drop rule gives
a closed-form explanation of why adding nodes can increase execution time.

### 3.4 Strategy 3 — Dynamic (guided self-scheduling, capacity-scaled minimum)

A shared queue holds *R* remaining operations. When a worker becomes idle it
receives

    chunk = min(R, max(min_chunkᵢ, ⌈R / (2P)⌉)),     min_chunkᵢ = Cᵢ · 10·Lᵢ

so each chunk computes for at least ~10× its round-trip time, bounding
communication overhead near 10%. Failed or timed-out chunks are re-queued,
giving fault tolerance with no extra mechanism.

### 3.5 Failure handling for static strategies

A failed partition is retried on the fastest healthy worker. This simple,
documented fallback makes the cost of faults under static scheduling visible.

### 3.6 Proposed contribution

The latency-aware finish-time model, plus an experimental characterisation of
**when each strategy wins**:

- capacity-aware static beats equal partitioning under stable heterogeneity;
- dynamic beats static under worker slowdown or failure;
- static beats dynamic under high latency, where many small chunks are costly.

Out of scope: learned/ML schedulers, inter-worker work stealing, DAG scheduling.

---

## 4. Benchmark Design

### 4.1 Workload 1 — Monte Carlo estimation of π (`workloads/monte_carlo.py`)

- **Decomposition:** a chunk is `(n, seed_index)`. Each chunk uses an independent random stream from `np.random.SeedSequence(base_seed).spawn(...)[seed_index]` (GPU streams seeded from the same entropy), so results are reproducible and streams never overlap.
- **Kernel:** vectorised batches (1e6 on CPU, ~5e7 float32 on GPU, well within 8 GB) to bound memory; returns `hits`.
- **Aggregation:** `π̂ = 4·Σhits / Σn`; correctness check `|π̂ − π| < 3σ` with `σ = 4·√(p(1−p)/N)`, `p = π/4`.
- **Known limitation:** the workload is embarrassingly parallel with negligible communication, so speedup will appear near-linear. Experiments E6–E8 and Workload 2 address this.

### 4.2 Workload 2 — Blocked matrix multiplication (optional, Phase P7)

Row-block decomposition of `C = A·B`; each chunk ships its rows of `A`, and `B` is
sent once and cached per worker. With O(n³) compute against O(n²) data,
communication cost is non-trivial and the latency term matters. Running it
through the same coordinator demonstrates that the framework is not coupled to
one workload.

### 4.3 Baselines

- **B0:** sequential NumPy, single process, single core on the laptop (defines `T_seq`).
- **B1:** single local GPU, no network (best single resource).

### 4.4 Metrics (added to `evaluation/metrics.py`)

| Metric | Definition |
|---|---|
| Total execution time | `T_par`, coordinator wall clock |
| Throughput | `N / T_par` (samples/s) |
| Speedup | `S = T_seq / T_par` |
| Parallel efficiency | `E = S / P` for homogeneous runs; for heterogeneous runs, capacity-normalised `E_h = (N / ΣCᵢ) / T_par` (plain `S/P` is meaningless when one GPU is ~100× a CPU core) |
| Load imbalance | `λ = max tᵢ / mean tᵢ` (1.0 = perfect) |
| Resource utilisation | `Σ busyᵢ / (P · T_par)` |
| Scheduling overhead | time spent in partitioning and dispatch |
| Communication overhead | `Σ (RTT − compute_ms)` |

### 4.5 Experiments

Each cell is repeated 10 times; results reported with 95% confidence intervals
using the existing `mean_ci`.

| # | Configuration | Purpose |
|---|---|---|
| E0 | B0 sequential | `T_seq` reference |
| E1 | B1 single GPU | best single device |
| E2 | 3 heterogeneous CPU containers, equal | baseline imbalance |
| E3 | same, capacity-aware | static gain |
| E4 | same, dynamic | dynamic gain or overhead |
| E5 | GPU + CPU containers, all strategies | hybrid execution; equal is bounded by the slowest CPU, capacity-aware assigns most work to the GPU |
| E6 | workload size sweep, 1e5–1e10 | crossover point where distribution starts to pay off |
| E7 | injected latency 0 / 20 / 100 ms | effect of `Lᵢ`; static vs dynamic |
| E8 | mid-run slowdown or removal of one worker | robustness of dynamic scheduling |
| E9 | P = 1..k workers | scaling, including where adding workers stops helping |
| E10 (optional) | remote cloud workers | real WAN latency |

**Fault injection:** worker environment variables `INJECT_LATENCY_MS` and
`SLOWDOWN_FACTOR`, plus `POST /admin/fault {slowdown, down_for_s}` for mid-run
changes. All set the `throttle` field. `tc netem` is an optional alternative (it
requires `NET_ADMIN`).

---

## 5. Deployment Strategy

### 5.1 Local Docker Compose

New `Dockerfile.worker` and `docker-compose.yml`:

- Image: `python:3.13-slim` with NumPy and FastAPI; command `python -m worker.worker_server`.
- Services `cpu-small` (`cpus: 0.5`), `cpu-med` (`cpus: 1`), `cpu-large` (`cpus: 2`), each on its own port.
- `ENABLE_CODE_EXEC=false`; chunk execution does not need the Docker socket.
- The coordinator runs on the host with `WORKER_URLS` listing the container ports and the GPU worker.

### 5.2 Local CUDA worker

Run natively on Windows (not Docker): `pip install cupy-cuda12x`, then
`WORKER_ID=gpu-0 python -m worker.worker_server`. Docker GPU on Windows requires
WSL2 and `--gpus all`; it works but adds a failure mode with no research value,
so it remains optional. CuPy lives in a separate `requirements-gpu.txt` and is
imported optionally, so CPU workers never require CUDA.

### 5.3 Remote CPU workers

Free or low-cost VMs: Oracle Cloud Always Free (Ampere ARM — build an arm64
image or install with pip), GCP e2-micro, AWS/Azure student credits. Verify
current free-tier terms before relying on them.

- **Topology:** the coordinator on the laptop pushes to the cloud workers' public addresses; no inbound connection to the laptop is needed.
- **Security (mandatory):**
  - The existing `/execute` endpoint runs arbitrary user code and **must be disabled on any public host** (`ENABLE_CODE_EXEC=false`).
  - `/execute_chunk` requires a shared `X-CAPS-Token` header.
  - Firewall the worker port to the coordinator's IP only.

### 5.4 Infrastructure limitations

- Free VMs are small (often 1 burstable vCPU); burst credits make capacity drift. This exercises the EWMA and dynamic scheduling but reduces repeatability, so variance must be reported.
- Free GPU notebooks (Colab, Kaggle) have no inbound ports and are not persistent. Cloud GPUs are out of scope unless credits are available. **The only real GPU is the local RTX 4070.**
- Laptop thermals and power plan affect results; fix the power plan, stay on mains power, and record both.
- Docker Desktop CPU limits on Windows are real but noisy; calibration measures the capacity actually delivered.

---

## 6. Implementation Roadmap

| Phase | Deliverable | Files | Completion criteria |
|---|---|---|---|
| **P0** Workload core + rename | Monte Carlo `split / run_chunk / merge` (CPU); rename legacy "DAALAB" strings to CAPS in one `chore` commit | New `workloads/__init__.py`, `workloads/monte_carlo.py`, `tests/unit/test_monte_carlo.py`; string-only edits across README, docs, scripts and FastAPI titles | Merging any split equals a single full run with the same seed; `π̂` within 3σ at N = 1e7; `grep -r DAALAB` empty outside `paper/`; existing tests pass |
| **P1** Worker chunk path | `/execute_chunk`, calibration, device detection, optional `/status` fields, fault-injection variables | `worker/worker_server.py` (~70), `worker/worker_state.py` (~15), `common/models.py` (~25) | `/execute_chunk` returns hits; `/status` reports `device` and `capacity_ops_s`; **all existing tests pass unchanged** |
| **P2** Coordinator + strategies (**MVP**) | Partitioner, async coordinator, endpoints, per-chunk event log | New `scheduler/partitioner.py`, `scheduler/coordinator.py`, `tests/unit/test_partitioner.py`; `scheduler_server.py` (~60), `worker_registry.py` (~20), `cost_model.py` (~15) | Three local workers: all strategies produce a correct π; partitions sum to N; unit test shows water-filling drops a high-latency worker |
| **P3** Compose heterogeneity | Worker image and Compose file with CPU limits | New `Dockerfile.worker`, `docker-compose.yml` | `docker compose up` yields three workers with calibrated capacities ≈ 1 : 2 : 4; E2–E4 runnable |
| **P4** GPU worker | CuPy kernel path with optional import | `workloads/monte_carlo.py` (~20), new `requirements-gpu.txt` | `/status` reports `device=gpu` and the real device name; GPU `π̂` statistically matches CPU; GPU capacity ≫ CPU |
| **P5** Experiment harness | Runner, metrics, CSV, plots, fault toggles | New `evaluation/run_parallel_experiments.py`; `metrics.py` (~30); reuse `analyze_results.py` | E0–E9 produce CSV with 10 repetitions and CIs; plots: speedup vs P, time vs N, per-strategy Gantt chart |
| **P6** Dashboard | Job submission, strategy selection, worker table, live chunk Gantt (polls the job endpoint) | New `static/parallel.html`, `static/parallel.js`; `scheduler_server.py` serves the page (~3) | Live demo shows chunks being assigned per worker for each strategy |
| **P7** Second workload (optional) | Row-block matrix multiplication | New `workloads/matmul.py` | Runs through the same harness with no coordinator change |
| **P8** Cloud workers (optional) | One or two remote CPU workers | Deployment notes in `docs/` | At least one remote worker completes chunks; measured WAN RTT appears in E10 |

**Dependencies:** P0 → P1 → P2 → (P3 ∥ P4) → P5. P6 depends only on P2 and can
proceed in parallel with P5. P7 depends on P2. P8 depends on P3.

**Minimum viable prototype:** P0–P3 — correct distributed π over heterogeneous
containers with three measurable strategies (estimated 2–3 weeks). P4–P5 turn it
into a parallel-computing result; P6–P8 are presentation and extension.

**Estimated footprint:** ~200 added lines across 7 existing files (all additive),
~800 lines in ~10 new files. No existing code is rewritten or deleted.

> Note: `api_server.py` currently has uncommitted local edits. The P0 rename
> commit excludes it until those edits are committed or stashed.

---

## 7. Risks and Feasibility

### 7.1 Potential bottlenecks

- **Container startup per chunk** — avoided by in-process kernels; this must be preserved.
- **Coordinator fan-out** — a single asyncio loop handles thousands of chunks per second; no message queue needed.
- **GPU dominance** — in hybrid mode capacity-aware scheduling assigns nearly all work to the GPU. This is a finding, not a defect; CPU-only heterogeneous configurations (E2–E4) keep the strategy comparison meaningful.
- **Workload too easy** — mitigated by E6 (crossover), E7 (latency), E8 (faults) and P7 (matrix multiplication).

### 7.2 Complexity deliberately excluded

Redis or message queues, Kubernetes, a React rewrite, gRPC, worker-initiated
registration and heartbeats (push plus existing `/status` polling suffices),
Docker GPU on Windows, a search for cloud GPUs, and any change to the existing
per-job `Scheduler`.

### 7.3 Essential vs optional

- **Essential:** P0–P5 and honest device/throttle labelling.
- **Optional:** dashboard polish, matrix multiplication workload, cloud workers, `tc netem`.

### 7.4 Focus

Every phase except P6 and P8 produces a parallel-computing measurement. Cloud
deployment and the UI are capped at one phase each and serve as demonstration
and validation, not the core contribution.

### 7.5 Interaction with the existing paper

The current queue-cost scheduling paper remains reproducible because
`Scheduler`, `SchedulingMode` and `evaluation/simulator.py` are untouched. The
new work could supply the "≥30% new material" required for a journal extension
(see `docs/publish_plan_and_strat.md`); that is a separate decision.
