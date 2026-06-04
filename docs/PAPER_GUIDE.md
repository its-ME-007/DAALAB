# Paper Drafting Guide — Complexity-Aware Scheduling for Code Execution

A roadmap for turning this system into a defensible research paper. It is opinionated
about *framing* because that is where this project will live or die under review: the
engineering is sound, but the contribution must be scoped honestly.

> **TL;DR of the framing.** Do **not** pitch "complexity analysis beats CPU-aware
> scheduling." Pitch a **hybrid**: a cheap *predictive* cost prior (from code
> complexity) **corrected by** *reactive* load signals (CPU/queue), and show it beats
> both naive baselines and pure queue-length on *heterogeneous, unbounded* workloads —
> with the advantage growing with cluster size and shrinking with per-worker
> concurrency. Treat bounded-time judges (LeetCode) as a *contrast* case, not the hero
> workload.

---

## 1. The thesis (write this sentence first, refine everything to it)

> *Predictive, complexity-derived cost estimates — combined with reactive load
> feedback — improve tail latency and load fairness over reactive-only scheduling for
> heterogeneous, unbounded code-execution workloads; the benefit scales with worker
> count and diminishes as per-worker concurrency rises.*

Every section exists to support or qualify that sentence. If a paragraph doesn't, cut it.

---

## 2. Claims → evidence map (the spine of the paper)

Make a table like this and fill the "Evidence" column with a specific figure/table
*before* writing prose. If a claim has no evidence artifact, either generate it or drop
the claim.

| # | Claim | Evidence (artifact) | Status |
|---|---|---|---|
| C1 | Cost-aware routing reduces tail latency vs naive baselines (random, round-robin) | Sweep table p95/p99, `evaluation/run_sweep.py` | strong (sim shows 2–3x) |
| C2 | Cost-aware beats pure queue-length on heterogeneous load | Sweep p50/p95 at C=1 | **modest (~8–10%)** — state honestly |
| C3 | The advantage grows with worker count N | Sweep across N∈{2,4,8} | strong (sim) |
| C4 | The advantage shrinks as concurrency rises | Sweep across C∈{1,4} | strong (sim) — the concurrency confound |
| C5 | It improves load fairness | Jain's index column (sim + real) | strong (queue_cost ≈ 1.000) |
| C6 | Static-first analysis removes the LLM from the latency path | Offline service smoke + latency breakdown | strong |
| C7 | Trends hold on the real deployed system | Multi-VM locust runs, `evaluation/analyze_results.py` | **to run** |

Reviewers reward a paper whose claims are *exactly* as strong as its evidence — no more.

---

## 3. Recommended section outline

### Abstract (~200 words)
Problem (heterogeneous code-execution jobs, head-of-line blocking), gap (reactive
schedulers are blind to cost at admission time), approach (predict cost from
complexity + correct with load feedback), key result (quantified: "Xx lower p95 vs
random, Y% vs queue-length, fairness ~1.0; benefit grows with N"), and one honest
scope line ("for unbounded heterogeneous workloads; bounded-time judges benefit less").

### 1. Introduction
- The problem with a concrete motivating example: a worker handed one expensive job,
  then small jobs piled behind it → head-of-line blocking. (This is your scenario test
  in [tests/unit/test_worker_selection_scenarios.py](../tests/unit/test_worker_selection_scenarios.py).)
- Why reactive scheduling has a blind spot: it can't see a job's cost until execution
  is underway and the placement is already committed.
- Contributions, as a bulleted list (3–4): (i) a static-first complexity estimator
  usable on the hot path, (ii) a hybrid cost-aware scheduler, (iii) a reproducible
  simulator that drives the *real* scheduler code, (iv) an evaluation quantifying when
  prediction helps.

### 2. Background & Motivation
- Reactive vs predictive scheduling; head-of-line blocking; the cost-estimation idea.
- Establish *when* prediction can beat reaction (the four conditions): heterogeneous &
  unbounded cost, cost unobservable early, head-of-line blocking (low concurrency),
  cheap to predict. This frames your whole evaluation and pre-empts the "why not just
  use k8s CPU limits?" question.

### 3. System Design
- Architecture diagram: API gateway → load balancer → scheduler(s) → workers → Docker.
  Files: [scheduler/scheduler_server.py](../scheduler/scheduler_server.py),
  [load_balancer/balancer.py](../load_balancer/balancer.py),
  [worker/worker_server.py](../worker/worker_server.py).
- Make explicit which parts are *push* (your scheduler) vs the *pull-queue* industry
  alternative, and justify push (enables cost-aware placement, priority, affinity).

### 4. Scheduling Algorithms
- Baselines: random, round-robin, queue-length (all in
  [scheduler/scheduler.py](../scheduler/scheduler.py)).
- Proposed: queue-cost with the CPU penalty — present it explicitly as the **hybrid**
  (predictive prior `queue_cost_ms` + reactive `CPU_PENALTY`). Don't bury the reactive
  half; it's your strongest defense.
- Cost model: [scheduler/cost_model.py](../scheduler/cost_model.py) — Big-O × input
  size × language multiplier. Be candid that it's a *relative routing weight*, not a
  runtime predictor, and note the overflow cap.

### 5. Complexity Analysis
- Static-first, LLM-fallback design ([code_assist/static_analyzer.py](../code_assist/static_analyzer.py),
  [code_assist/complexity_service.py](../code_assist/complexity_service.py)).
- Honest accuracy discussion: loop-nesting heuristic is reliable for iterative code,
  defers recursion/data-dependent code to the LLM, and **ignores constants** — which
  matters for short jobs. This candor is a strength.

### 6. Implementation
- Brief: FastAPI services, Docker-per-job isolation, the worker semaphore concurrency
  knob ([worker/worker_server.py](../worker/worker_server.py)), env-driven config.

### 7. Evaluation — the core of the paper
See §4 below; this is where most of your effort goes.

### 8. Discussion / Threats to Validity
Be exhaustive and specific (§5).

### 9. Related Work
- Cluster schedulers (Kubernetes bin-packing, Borg, YARN), load balancing, pull-queue
  systems (Celery/SQS), code-execution sandboxes (Firecracker microVMs, gVisor),
  cost/complexity estimation. Position yourself as *predictive admission-time placement*
  vs reactive resource-based placement.

### 10. Limitations & Future Work
Container pooling / microVMs (kills the Docker cold-start tax), push-based heartbeats,
Redis-backed multi-scheduler state, learned cost models calibrated on `actual_runtime_ms`,
and the bounded-judge case where prediction helps least.

### 11. Conclusion
Restate the thesis with the quantified result and the scoping caveat.

---

## 4. Evaluation methodology (write this section carefully — reviewers read it first)

### Two-layer design — explain why both exist
- **Simulation layer** ([evaluation/simulator.py](../evaluation/simulator.py)) drives the
  **real** `Scheduler` + `cost_model`, isolating the scheduling decision from system
  noise → shows the algorithm's *true* effect, fully reproducible (seeded).
- **Real-system layer** (multi-VM + locust, `scripts/`) measures end-to-end *including*
  Docker cold-start and contention → shows what a user actually experiences.
- State the expected relationship: **sim gap ≥ real gap**, because real overhead
  partially masks the routing effect. If the real gap is much smaller, that's a finding
  (overhead-bound → motivates container pooling), not a failure.

### Metrics (all in [evaluation/metrics.py](../evaluation/metrics.py))
- Latency p50/p95/p99 (tail is where scheduling shows up), throughput, makespan,
  **Jain's fairness index** over per-worker load, mean utilization.
- Always report **mean ± 95% CI across ≥10 seeds/repeats**. A single run is not a result.

### Experimental factors (sweep these)
- **Algorithm** ∈ {random, round_robin, queue_length, queue_cost} — full baseline set.
- **Worker count N** ∈ {2,4,8} — for the scaling story (C3).
- **Concurrency C** ∈ {1,4} — for the confound (C4).
- **Load** at a fixed target utilization ρ (e.g. 0.8) so algorithms are compared at
  equal offered load (`rate_for_utilization` in the simulator handles this).
- **Workload mix** — heterogeneous complexity classes (the regime where prediction
  helps); optionally a homogeneous control to show the gap *vanishes* (honest).

### Figures/tables to produce
1. **Table 1** — full sweep (the `run_sweep.py` output) with CIs. The headline.
2. **Fig 1** — p95 latency vs N, one line per algorithm (scaling curve). Shows C3.
3. **Fig 2** — p95 gap (queue_cost vs queue_length) vs concurrency. Shows C4 (the confound).
4. **Fig 3** — Jain's fairness per algorithm. Shows C5.
5. **Fig 4** — latency-vs-offered-load curves (sweep ρ from 0.3→0.95) showing where each
   algorithm saturates. The classic systems figure.
6. **Table 2** — sim vs real side-by-side (`analyze_results.py` emits the same columns).
7. **Optional Fig 5** — a complexity-analysis accuracy table (static vs LLM vs ground
   truth on a labeled set) to support C6.

### Reproducibility paragraph
State seeds, exact commands (`python -m evaluation.run_sweep ...`), VM specs/core counts
per role, and that the simulator is deterministic. Reviewers love a one-command repro.

---

## 5. Threats to validity (write these *before* a reviewer finds them)

- **Shared-host contention** — addressed by multi-VM (or cgroup `cpuset` pinning);
  report exact core counts per role.
- **Single scheduler & single complexity service** are shared bottlenecks
  ([scheduler_server.py:72](../scheduler/scheduler_server.py#L72)); the multi-scheduler
  launch + saturation analysis locate where the ceiling actually sits.
- **Docker cold-start** is in every real latency number and may dominate; this is the
  motivation for the microVM/pooling future work, and why the sim complements the real runs.
- **Simulator service-time model** is a documented assumption (bounded nominal +
  log-normal noise), *separate* from the routing weight so estimation error is explicit.
  Validate its trend against the real runs.
- **Cost-model fidelity** — Big-O ignores constants; weakest for short jobs. State it.
- **Workload realism** — synthetic mix; ideally replay a real trace if obtainable.

---

## 6. What NOT to claim (each of these sinks papers)

- ❌ "Beats Kubernetes / production schedulers." You compare against *your* baselines,
  not industrial systems. Say so.
- ❌ "Complexity analysis is better than CPU-based scheduling." It's a *complement*; the
  CPU penalty is reactive scheduling, and it's part of your own system.
- ❌ "Ideal for LeetCode." Bounded time limits compress heterogeneity, fixed overhead
  dominates, and historical per-problem runtimes beat static Big-O. Use judges as a
  *contrast* ("where prediction helps least"), not the hero workload.
- ❌ Unbounded claims from N=2. The two-worker case is near-degenerate; lead with N≥4.
- ❌ Single-run numbers, or numbers without CIs.

---

## 7. Suggested workload framing (pick one, commit early)

- **(Recommended) Unbounded heterogeneous execution** — autograders for open-ended
  assignments, notebook/sandbox backends, batch compute. Satisfies all four "prediction
  helps" conditions. Strongest fit.
- **Hybrid thesis, workload-agnostic** — center the paper on *predict-prior + react-correct*
  and show across mixes when each component contributes.
- **Judges as contrast** — keep a bounded-time-limit experiment that demonstrates the
  advantage *shrinks*, turning a weakness into an honest scoping result.

---

## 8. Drafting order (don't write top-to-bottom)

1. Fill the **claims→evidence table** (§2).
2. Run the **experiments**, produce the **figures/tables** (§4).
3. Write **Evaluation** around the figures.
4. Write **Threats to Validity** (§5) and **Limitations**.
5. Write **System Design / Algorithms** (you know these cold).
6. Write **Related Work**.
7. Write **Intro** last-but-one (now you know the real story).
8. Write **Abstract** last.

---

## 9. Commands that generate paper artifacts

```bash
# Headline sweep table + CSV (Table 1, Figs 1-3)
python -m evaluation.run_sweep --jobs 3000 --seeds 10 --workers 2,4,8 --concurrency 1,4

# Saturation curves (Fig 4): sweep load
for r in 0.3 0.5 0.7 0.85 0.95; do
  python -m evaluation.run_sweep --rho $r --workers 4 --concurrency 1 --out results/sat_$r.csv
done

# Real-system runs (Table 2) — after multi-VM deploy (see docs/DEPLOYMENT path)
./scripts/run_load_experiment.ps1 -LoadBalancer http://<lb> -SchedulerAdmin http://<sched>
python -m evaluation.analyze_results results/

# Unit/reproducibility checks cited in the repro paragraph
python -m pytest tests/unit/ -q
```

---

## 10. Venue & length notes
- This is a **systems / scheduling** paper. Target workshop or short-paper venues first
  (the contribution is focused, not a full new system). 6–8 pages.
- The reproducible simulator + one-command sweeps are a genuine asset — lead with
  reproducibility; many scheduling papers can't.
