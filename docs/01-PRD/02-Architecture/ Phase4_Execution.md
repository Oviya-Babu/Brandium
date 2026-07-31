# Brandium — Phase 4: Platform Engineering Architecture Specification
 
**Status:** v1.0 — Draft for review
**Depends on:** PRD v1.0; Phase 0 v0.2 FROZEN; Phase 1 v0.2 FROZEN; Phase 2 v1.0 FROZEN (+ Critical Rule/Applicability addendum); Phase 3 v1.1 FROZEN
**Scope:** Conceptual execution architecture only. No databases, queues, APIs, programming languages, frameworks, cloud services, orchestration platforms, AI models, prompts, networking, deployment, containers, or infrastructure technologies are discussed or implied anywhere in this document.
**Blocks:** Phase 5 (Enterprise SaaS Layer — multi-tenancy enforcement, RBAC, workflow), which will size its infrastructure choices against the execution shape defined here.
 
---
 
## 0. Relationship to Frozen Phase 0–3
 
This document does not add, remove, or alter any AnalysisRun state (`queued → running → {complete, failed}`, Phase 0 §3.11/§5), any Genome/Policy lifecycle, or any Phase 2/3 conceptual mechanism. Its job is narrower and sits entirely *underneath* the `running` state: it defines the execution substrate that carries Phase 3's five stages from Applicability Determination through Completeness Verification, in a way that's platform-agnostic.
 
Everywhere Phase 3 said "how a worker is scheduled/parallelized/retried is out of scope," this document is where that scope begins — conceptually, not technologically.
 
---
 
## 1. Execution Lifecycle of an AnalysisRun
 
The frozen AnalysisRun states remain exactly `queued → running → {complete, failed}`. What Phase 4 adds is a description of what happens *inside* `running`, expressed as a conceptual execution sequence rather than new persisted states:
 
```
queued
  │  (accepted, not yet begun)
  ▼
running
  │
  ├─ Applicability Determination executes
  ├─ Planning executes, producing an Execution Plan (§5)
  ├─ Work Units execute per the Plan (§2, §4)
  ├─ Evidence Fusion executes as Work Units complete
  └─ Completeness Verification executes
  │
  ▼
complete  or  failed
```
 
**Why no new top-level state is introduced:** Phase 0 deliberately kept AnalysisRun's lifecycle coarse — `running` is the single state that covers "work is happening." Splitting it into many persisted sub-states would mean re-opening a frozen entity for a distinction that observability (§10) can provide without touching the domain model at all. The execution states below are a *reporting and coordination* concept, not a business-domain one.
 
---
 
## 2. Execution States: The Work Unit
 
The **Work Unit** is the execution-layer concept this document introduces: one worker's assignment to attempt evidence for one or more in-scope Assertions (Phase 3 §3's Planning output, made concrete for execution purposes). A Work Unit is *not* a new domain entity — it does not appear in Phase 0's model, has no independent versioning, and exists only for the duration of one AnalysisRun's execution.
 
**Work Unit states:**
 
```
assigned → executing → { succeeded, failed, timed_out }
```
 
- **assigned** — the Work Unit exists as part of the Execution Plan but has not yet begun.
- **executing** — the worker is actively attempting to produce Observations for its assigned Assertions.
- **succeeded** — the worker completed; its Observations are available to Evidence Fusion. A succeeded Work Unit may still result in a per-Assertion attempted-no-signal outcome (Phase 3 §5) — succeeding as a Work Unit and finding a positive signal are different things.
- **failed** — the worker did not complete (crashed or errored). Feeds Phase 3's worker-failure outcome for its assigned Assertions.
- **timed_out** — the worker did not complete within its allotted attempt window. Treated identically to `failed` for the purpose of Phase 3's worker-failure outcome — the distinction between "errored" and "took too long" matters for operational diagnosis (§10) but not for the business-level outcome it produces.
 
**Monotonicity invariant:** a Work Unit's state only moves forward through this sequence and never reverts. A `succeeded` Work Unit is never re-opened; a retry (§6) creates a new Work Unit attempt, not a mutation of the prior one.
 
---
 
## 3. Platform Orchestration Responsibilities
 
The **Orchestrator** is the conceptual responsibility — not a named technology — that carries an AnalysisRun through `running`:
 
1. Invoke Applicability Determination and receive the Applicability Set.
2. Invoke Planning and receive the Execution Plan (§5): a set of Work Units, plus the ordering dependencies among them (Phase 3 §3, e.g., video frame/transcript derivation before dependent workers).
3. Release each Work Unit for execution once its dependencies (if any) have reached `succeeded`.
4. Track every Work Unit's state as it executes.
5. Hand completed Work Units' Observations to Evidence Fusion as they become available — fusion does not need to wait for every Work Unit before beginning, only for the ones feeding a given Assertion.
6. Once all Work Units have reached a terminal state (`succeeded`, `failed`, or `timed_out`), invoke Completeness Verification.
7. Apply Completeness Verification's result: transition the AnalysisRun to `complete` (handing off to Phase 2) or `failed`.
 
**The Orchestrator does not itself decide business outcomes.** It does not decide whether a Required category's worker failure should fail the run — that rule is Phase 3 §6's, fixed and versioned there. The Orchestrator's job is purely to carry Work Units through their lifecycle and apply a rule that already exists, not to encode judgment of its own.
 
---
 
## 4. Worker Lifecycle Management
 
A "worker," at this layer, is a conceptual capability invoked for a Work Unit — not a specific implementation. Its lifecycle from the platform's perspective:
 
1. **Invocation** — the Orchestrator releases a Work Unit for execution once its dependencies are satisfied.
2. **Attempt** — the worker runs against its assigned in-scope Assertions.
3. **Resolution** — the worker either produces Observations and reaches `succeeded`, errors and reaches `failed`, or exceeds its attempt window and reaches `timed_out`.
4. **Handoff** — on `succeeded`, its Observations become available to Evidence Fusion (Phase 3 §5).
 
**Isolation principle:** one Work Unit's internal behavior must never be visible to, or capable of affecting, another's. This is the execution-layer expression of Phase 3 §7's finding that no worker's assignment or execution depends on another worker's *findings* — at the execution layer, this becomes a stronger guarantee: no Work Unit's failure, slowness, or retry activity may alter another Work Unit's state, inputs, or outputs.
 
---
 
## 5. Execution Planning and Coordination
 
Planning's conceptual output (Phase 3 §3) becomes, at this layer, an **Execution Plan**: the set of Work Units for this AnalysisRun, together with the dependency relationships among them established in Phase 3 (video's derived-content ordering being the only ordering dependency Phase 3 defines; independent categories have no ordering constraint between them).
 
**Coordination responsibility:** ensure a dependent Work Unit is never released for execution before its prerequisite has reached `succeeded`. If a prerequisite Work Unit reaches `failed` or `timed_out`, every Work Unit depending on it is never released at all — it is recorded directly as a worker-failure outcome for its assigned Assertions (Phase 3 §5, outcome 3), since attempting it would be meaningless without its required input. This is not a new business rule; it is the mechanical consequence of Phase 3's existing dependency description, made explicit for execution purposes.
 
The Execution Plan itself, like the Applicability Set (Phase 3 §2), is **derived and reproducible** — given the same Applicability Set and the same worker-scope table (Phase 3 §4), recomputing the Execution Plan yields an identical set of Work Units and dependencies every time. It is not a stored, versioned entity in its own right.
 
---
 
## 6. Retry Philosophy
 
**What may be retried:** a Work Unit that reaches `failed` or `timed_out` may be attempted again, up to a bounded number of attempts. A retry is a **new attempt of the same Work Unit**, not a new Work Unit and not a mutation of the failed attempt's record — the failed attempt's state remains exactly as it was; a fresh attempt begins alongside it.
 
**What may never be retried:** a `succeeded` Work Unit is never retried. There is no concept of "retrying" Evidence Fusion, Completeness Verification, or Decision computation themselves — these are deterministic functions over already-produced Evidence (Phase 2 §5.3), so there is nothing about them that failure or retry applies to; if their inputs are unchanged, re-invoking them is simply re-deriving the same result, not a retry in the failure-recovery sense.
 
**Idempotency requirement (the reason retry is safe at all):** a retried Work Unit's Observations must be safe to hand to Evidence Fusion without producing duplicate or double-counted Evidence. This is not a new obligation invented here — Phase 3 §5 already requires Fusion to avoid double-counting near-identical redundant Observations for exactly this reason. Retry philosophy simply depends on that requirement holding; it does not add a new one.
 
**Exhaustion:** once a Work Unit has exhausted its bounded retry attempts without reaching `succeeded`, it is recorded as a final worker-failure outcome (Phase 3 §5) and Completeness Verification (Phase 3 §6) applies exactly as already specified — Required-category exhaustion fails the run; Optional-category exhaustion is recorded and the run proceeds.
 
---
 
## 7. Failure Isolation
 
Failure isolation operates at exactly the Work Unit granularity — no coarser, no finer:
 
- One Work Unit's failure never blocks, delays, or affects a Work Unit it has no dependency relationship with (§4's isolation principle).
- One Work Unit's failure only propagates to Work Units that explicitly depend on it (§5's coordination rule), and even then only by preventing their release — never by corrupting their eventual attempt.
- A failure at the Work Unit level never propagates upward to affect *other AnalysisRuns* — each AnalysisRun's execution is entirely self-contained, consistent with the tenant- and asset-level isolation already established in Phase 0.
 
This is a boundary worth stating explicitly because it is what makes Phase 3's "Optional-category failure doesn't fail the run" rule actually implementable: isolation at the Work Unit level is the mechanism that lets one failure be contained rather than cascading.
 
---
 
## 8. Cancellation, Interruption, and Recovery Semantics
 
**Cancellation** (an operator or the platform deliberately stopping an in-progress AnalysisRun) is represented as a routing to the existing frozen `failed` state (Phase 0 §3.11) — no new top-level AnalysisRun state is introduced for this. What distinguishes a cancellation from a pipeline-defect failure is a reason annotation carried alongside the terminal state, conceptually, not a different lifecycle branch. This keeps the frozen state machine intact while still letting the two situations be told apart during review.
 
**Interruption** (execution stops mid-run for a reason unrelated to any individual Work Unit's own outcome — e.g., the platform itself pausing) is not a new terminal state either. An interrupted AnalysisRun's Work Units are simply resumed: any Work Unit that had not reached a terminal state before the interruption is re-released for execution once the platform resumes, following exactly the same coordination rules (§5) and idempotency requirement (§6) that ordinary retry already relies on. Recovery is not a separate mechanism from retry — it is retry applied to a broader set of Work Units at once.
 
**Why this is sufficient without new states:** because the Execution Plan (§5) and Applicability Set (§2 of Phase 3) are both fully reproducible from stable inputs, "resuming" a run after interruption requires no memory of *why* execution stopped — only of which Work Units had already reached a terminal state. Recomputing the rest is safe by construction.
 
---
 
## 9. Idempotency and Reproducibility Guarantees
 
This document's entire contribution to reproducibility (already guaranteed at the business level by Phase 2 §8.2) is to ensure the execution layer introduces no non-determinism that could leak into it:
 
- The Applicability Set and Execution Plan are both derived, not stored, and both reproducible from stable inputs (§5, and Phase 3 §2).
- Retries and recovery (§6, §8) never produce duplicate Evidence, because Fusion's deduplication requirement (Phase 3 §5) is unconditional, not retry-specific.
- A Work Unit's state transitions are monotonic (§2) — nothing about re-attempting a Work Unit can alter the recorded outcome of a prior attempt.
 
Put plainly: the execution layer's entire job, from a reproducibility standpoint, is to not break the guarantee Phase 2 already made — not to make a new guarantee of its own.
 
---
 
## 10. Scalability Principles
 
Scalability, at this conceptual level, is a direct consequence of the isolation already established (§7): Work Units with no dependency relationship between them have no reason to wait on one another, and one AnalysisRun's execution has no reason to interact with another's. This means the number of Work Units (and AnalysisRuns) that can proceed concurrently is limited only by however much execution capacity is made available to them — a statement about the *shape* of the workload's independence, not a claim about any specific scaling mechanism, which is explicitly a Phase 5-and-beyond engineering decision.
 
The only genuine ordering constraint on concurrency this architecture defines is Phase 3's video derived-content dependency (§5, §3 of Phase 3) — everything else is embarrassingly parallel by design.
 
---
 
## 11. Observability Responsibilities
 
Three things must be inspectable at any point during execution, not merely reconstructable after the fact:
 
1. **Work Unit state** — for any AnalysisRun currently `running`, the state of every Work Unit (assigned/executing/succeeded/failed/timed_out) must be visible in real time, not only after Completeness Verification runs.
2. **AnalysisRun-level progress** — a coarse view (how many Work Units are in each state) sufficient to distinguish "proceeding normally," "stuck," and "degrading toward a Required-category failure" without needing to inspect every Work Unit individually.
3. **Auditability of transitions** — every Work Unit and AnalysisRun state transition is itself an auditable event, consistent with Phase 0's AuditLogEntry philosophy (§3.15, immutable/append-only). This is what lets an operator later distinguish "this run failed because of a genuine content issue" from "this run failed because of a platform defect" without needing anything beyond what was already being recorded during execution.
 
This document deliberately does not specify *how* this visibility is implemented (no monitoring technology, no specific tooling) — only that these three things must be true of whatever implementation Phase 5/6 chooses.
 
---
 
## 12. Boundary Between Execution Architecture and Future Infrastructure
 
Explicitly out of scope for this document, and left to Phase 5 and later:
 
- The specific technology or mechanism used to track and coordinate Work Unit state.
- Concurrency limits, specific timeout durations, and retry backoff behavior (this document establishes *that* retries are bounded and idempotent — not the specific bound or timing).
- How workers are physically invoked, distributed, or scaled.
- Any storage, messaging, or orchestration technology whatsoever.
 
Phase 5 and later engineering decisions must satisfy the conceptual guarantees established here (isolation, monotonicity, idempotency, reproducibility, observability) — but the specific means of satisfying them is not decided by this document, consistent with its implementation-agnostic mandate.
 
---
 
## 13. Consistency Check Against Frozen Phase 0–3
 
- No AnalysisRun state, Genome/Policy lifecycle, or Phase 2/3 mechanism is altered.
- Work Unit is introduced as an execution-layer concept only — it is not a new domain entity and requires no change to Phase 0's frozen model.
- Retry and recovery both depend on, and do not weaken, Phase 3 §5's Fusion deduplication requirement.
- Cancellation and interruption are represented using the existing `failed` state and ordinary re-execution, respectively — neither requires reopening Phase 0's frozen lifecycle.
 
**No contradiction requiring Phase 0–3 to reopen was found.**
 
---
 
## 14. Open Questions Carried to Phase 5
 
1. Retry bound (how many attempts before exhaustion) is deliberately left unspecified here as a tuning decision, not an architectural one — Phase 5 should set it, informed by production behavior rather than fixed prematurely.
2. Whether cancellation should eventually warrant its own first-class AnalysisRun state (rather than reusing `failed` with an annotation) is worth revisiting only if operational experience shows the reason-annotation approach is insufficient for review purposes — not a decision to make preemptively.
3. The precise mechanism for real-time Work Unit visibility (§11) is intentionally undefined here; Phase 5/6 should confirm it doesn't require any change to what this document already commits to recording.
 
---
 
*End of Phase 4 — Platform Engineering Architecture Specification, v1.0. Awaiting your review before this becomes the frozen baseline Phase 5 (Enterprise SaaS Layer) builds against.*