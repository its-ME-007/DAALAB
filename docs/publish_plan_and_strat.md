# Publication Plan & Strategy

> Strategy notes for publishing the complexity-aware scheduling paper.
> Author: Anushruth V. Date of plan: 2026-06-09.

---

## 1. What this paper currently is

A **simulation-first** systems paper on **complexity-aware predictive scheduling**
(queue-cost routing) for a distributed code-execution service, compared against
reactive baselines (random, round-robin, queue-length). Results come from a
reproducible discrete-event simulator that drives the **real** scheduler and
cost model; a real-system (multi-VM) harness exists but has not yet produced
headline numbers.

**Honest current state:** strong, reproducible *simulation* contribution; single
language family on the eval; one known technical flaw (cost-model saturation,
see §5). This is a solid **conference / megajournal** paper today, not a top-tier
journal paper.

---

## 2. Venue ladder (for THIS paper)

```
TOCS, TPDS         <- highest prestige, OUT OF REACH (needs a landmark contribution)
TCC, TOMPECS       <- realistic REACH (needs real-system results + cost-model fix)
IEEE Access        <- realistic SAFE target (megajournal, soundness-only review)
CSITSS             <- submit NOW (conference, fast turnaround)
```

| Venue | Type | Prestige | Reach for this paper | Notes |
|-------|------|----------|----------------------|-------|
| **ACM TOCS** | Journal | Top | **Out of reach** | *Transactions on Computer Systems.* Landmark-only. Aspiration, not this submission. |
| **IEEE TPDS** | Journal | Top | Out of reach | Parallel & Distributed Systems. Same bar as TOCS. |
| **IEEE TCC** | Journal | Upper-mid | Reach | *Transactions on Cloud Computing.* Best thematic fit; **demands real cloud deployment results** — sim-only won't pass. |
| **ACM TOMPECS** | Journal | Upper-mid | Reach | Modeling & Performance Evaluation. Good fit for the simulation/queuing angle. |
| **IEEE Access** | Megajournal | Moderate | **Safe** | Soundness-only review, fast, APC-funded. Realistic journal home today. |
| **CSITSS** | Conference | Regional | **Submit now** | Fast, gets the work on record, enables an extended journal version later. |

### Key distinctions
- **Top-tier vs megajournal:** top-tier (TOCS/TPDS) is *selective and
  significance-gated* — reviewers reject technically-correct work that isn't
  important enough. A megajournal (IEEE Access) is *soundness-only* — high volume,
  publishes anything correct. Megajournal is NOT higher prestige; it's the safe
  floor, not the ceiling.
- **Journal vs conference:** journals are rolling (no deadline, slow, multiple
  revision rounds); conferences are deadline-driven (fixed date, fast, single
  decision). Plan timelines accordingly.

---

## 3. Recommended path (two stages)

**Stage 1 — now:** Submit to **CSITSS** (conference). Fast, low-risk, puts the
work on record and gives a citable result. Fix the email typo and defuse the
Table II framing first (see §5).

**Stage 2 — later:** Extend into a journal version with **≥30% new material**
(this is the standard conference→journal bar). The extension must add:
1. The **cost-model saturation fix** + re-run sweep (§5).
2. **Real-system (multi-VM) results** validating the simulator — mandatory for TCC.
3. Sharper **novelty framing** vs existing predictive schedulers.
4. Ideally a **second language** on the eval to kill the single-language threat.

Target for the journal version: **IEEE Access** (safe) or **TCC / TOMPECS**
(reach, if the real-system results are strong).

### Can I present at CSITSS and still journal it later?
Yes — conference→extended-journal is a standard, accepted pipeline, provided the
journal version adds ≥30% new material and cites the conference paper. The
conference publication does **not** burn the journal option.

---

## 4. Double-blind review (reminder)

Some venues (e.g. HiPC main track) are double-blind: **neither** authors nor
reviewers see each other's identities. Before submitting to such a venue, strip:
- Author names, affiliations, emails from the PDF.
- Self-citations phrased as "our prior work" (use third person).
- Acknowledgements, funding lines, and identifying repo URLs.

---

## 5. Blocking issues to fix before any journal above CSITSS

1. **Cost-model saturation (#1 technical vulnerability).** Both `O(n log n)` and
   `O(n²)` routing weights cap at **3,600,000 ms**, making them indistinguishable
   at large input sizes (Table II). Rescale the cost model so distinct complexity
   classes stay separable across the input range, then **re-run the sweep**.
   - Fix locations: `scheduler/cost_model.py` (`estimate_execution_cost` ~L117,
     `estimate_cost_simple` ~L142).
2. **Sim-only results.** Produce real-system numbers via the multi-VM harness
   (`scripts/run_load_experiment.ps1` + `collect_worker_stats.py` +
   `evaluation/analyze_results.py`). **Mandatory for TCC.**
3. **Single-language eval.** Add a second language to weaken the generality threat.
4. **Author email typo.** Fix in the draft before any submission.

---

## 6. One-line summary

> **TOCS = best, but not this paper.** Submit to **CSITSS now**; extend to
> **TCC / TOMPECS** (reach) or **IEEE Access** (safe) later — but only after the
> cost-model fix and real-system results. The deciding factor is doing the
> upgrades, not the journal name.
