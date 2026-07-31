# Brandium — Phase 3: AI Pipeline Architecture Specification

**Status:** v1.1 — FROZEN (corrects one internal contradiction identified in the pre-Phase-4 independent architecture review; see §6 note)
**Depends on:** PRD v1.0; Phase 0 v0.2 FROZEN (+ additive `context_tags` on AssetVersion); Phase 1 v0.2 FROZEN (+ additive `applicability_scope` on Genome elements); Phase 2 v1.0 FROZEN (+ Applicability Set correction, §3.3–3.5/§4.2/§10 rule 5; + Critical Rule/Applicability addendum)
**Scope:** Conceptual pipeline architecture only. No AI models, prompts, databases, APIs, queues, infrastructure, frameworks, or programming languages are discussed or implied anywhere in this document.
**Blocks:** Phase 4 (Platform Engineering — execution/queueing, sized against this pipeline's actual shape)

---

## 0. Purpose and Boundary

Phase 3 defines how an AssetVersion becomes Observations, then Evidence, ready for Phase 2's Decision Engine to consume — and how the Applicability Determination step is actually performed. It stops the moment Evidence exists and an AnalysisRun reaches `complete` or `failed`; everything from there onward is already specified in Phase 2.

---

## 1. Conceptual Pipeline

```
AssetVersion submitted
  │
  ▼
1. Applicability Determination
   (which Genome elements are even in scope for this asset)
  │
  ▼
2. Planning
   (which workers must run to attempt evidence for the in-scope elements)
  │
  ▼
3. Worker Execution
   (each assigned worker produces Observations)
  │
  ▼
4. Evidence Normalization & Fusion
   (Observations become Evidence, deduplicated, mapped to Assertions)
  │
  ▼
5. Completeness Verification
   (every in-scope Assertion has a terminal outcome; no silent gaps)
  │
  ▼
AnalysisRun → complete (handoff to Phase 2) or failed (terminal, per Phase 0 §3.11)
```

---

## 2. Stage 1 — Applicability Determination

**Responsibility:** for the active Genome version and this AssetVersion, determine the **Applicability Set** — the subset of Categories/Components/Assertions in scope for this specific asset.

**Inputs — the Evaluation Context:** the active Genome version's `applicability_scope` values (Phase 1 addendum), and this AssetVersion's **Evaluation Context** — its `modality` (Phase 0, pre-existing) and `context_tags` (Phase 0 addendum), taken together. This is the same Evaluation Context that Phase 2's reproducibility contract pins alongside `genome_version_id`, `policy_version_id`, and `decision_function_version`; Applicability Determination is the stage that actually consumes it.

**Rule:** a Genome element is in the Applicability Set if it has no `applicability_scope` (universally applicable — the default), or if its `applicability_scope` condition is satisfied by the Evaluation Context. Scope is inherited downward through Category → Component → Assertion unless a lower level further restricts it.

**Output:** the Applicability Set — a derived, deterministic result, not a persisted entity. Given the same Genome version and the same Evaluation Context, recomputing this set must always yield an identical result.

**Why this must happen before Planning:** the Planner (Stage 2) must not attempt to schedule work for out-of-scope elements — doing so would waste effort at best and risk a worker emitting a misaligned finding for a rule that was never in scope, at worst.

---

## 3. Stage 2 — Planning

**Responsibility:** given the Applicability Set and this asset's Evaluation Context, construct the set of workers that must run to attempt Evidence production for every in-scope Assertion — and no others.

**Principle:** never run every worker against every asset. A text-only asset naturally requires no Visual workers; an image asset requires no transcript-based Verbal analysis unless it contains on-image text. Planning is where modality and Applicability jointly determine the minimum necessary set of workers.

**Ordering dependency (conceptual, not a scheduling mechanism):** for video assets, worker assignment for Visual and Verbal analysis logically depends on this asset's representative frames and transcript first being derived — video is a composite of its own image-like and text-like content, not a wholly separate analytical category.

**Output:** an assignment of workers to the in-scope Assertions each is responsible for attempting evidence on, granular at the Assertion level. Two workers may share a Category (see §4 note) as long as no single Assertion is ever assigned to more than one worker.

---

## 4. Stage 3 — Worker Execution and Responsibilities

| Worker (conceptual role) | Genome Categories addressed | Notes |
|---|---|---|
| **Visual Worker** | Visual Identity | Logo usage, color palette, typography, imagery/photography style, layout — applies only to image content and to video's derived representative frames |
| **Verbal Worker** | Verbal Identity (Voice & Tone), Messaging & Positioning | Tone, vocabulary, prohibited language, core messaging — applies to text content and to video's derived transcript |
| **Compliance & Accessibility Worker** | Compliance & Legal, Accessibility | Mandatory disclaimers, trademark/attribution usage, contrast/alt-text/readability conventions |
| **Distinctiveness Worker** | Specific Assertions typically under Verbal Identity or Messaging & Positioning concerned with brand-distinctiveness vs. generic/formulaic patterning | This is where "AI slop" detection lives — as evidence produced against a specific Genome Assertion, not a separate ungrounded signal. The AI Slop Knowledge Base (DR-004) may be consulted here as a shared reference corpus, never as a scoring dimension that bypasses the Genome. This worker's scope shares Categories with the Verbal Worker by design — Planning's per-Assertion assignment (§3) is what keeps this unambiguous, since no single Assertion is ever handed to both |
| **Values & Mission Worker** | Values & Mission | Only relevant where a Brand has populated this optional category concretely enough to evaluate |

**A worker never evaluates an Assertion outside its assigned scope**, and never evaluates an Assertion outside the Applicability Set for this run — both are structural boundaries on what a worker may attempt.

---

## 5. Evidence Production and Assertion Outcomes

**Observation → Evidence:** a worker's raw output (an Observation, Phase 0 §3.12) is normalized into one or more Evidence items (Phase 0 §3.13, shaped per Phase 1 §6), each referencing exactly one Assertion.

**Confidence assignment — principle only:** every Observation, and the Evidence normalized from it, must carry a calibrated confidence value reflecting genuine certainty, not a fixed placeholder. How that calibration is performed is out of scope for this document.

**Every in-scope (Applicable) Assertion resolves to exactly one of three terminal outcome types** — this taxonomy is named explicitly here because §6's completion invariants depend on all three being distinguishable, not just the first two:

1. **Evidence outcome** — Evidence produced with an alignment_indicator (aligned / partially_aligned / misaligned). The normal case; feeds Phase 2's aggregation directly.
2. **Attempted-no-signal outcome** — the worker ran, the Assertion was in scope, but the asset's content didn't contain enough material to judge it (e.g., a short text ad and a "storytelling approach" Assertion). Not a failure; legitimately discounts Coverage/Confidence per Phase 2 §4.4.
3. **Worker-failure outcome** — the assigned worker crashed, timed out, or was never actually invoked despite being scheduled. This is never conflated with outcome 2: outcome 2 is a legitimate property of the content, outcome 3 is a defect in the platform's own execution.

Assertions excluded from the Applicability Set at Stage 1 are not part of this taxonomy at all — they are **Not Applicable**, excluded entirely from scoring, Coverage, and Confidence discounting, and are recorded as such rather than as any of the three outcomes above.

**Evidence Fusion responsibility:** where multiple Observations map to the same Assertion, Fusion aggregates them into that Assertion's Evidence set and explicitly does **not double-count near-identical redundant Observations as independent corroborating evidence**, which would artificially inflate confidence.

---

## 6. Completeness Verification and Invariants Before `complete`

> **Correction note (v1.1):** the invariants below replace v1.0's wording, which stated invariant 1 as requiring "outcome 1 or outcome 2" for every in-scope Assertion, and invariant 3(a) as requiring only "at least one" in-scope Assertion in a Required category to reach outcome 1/2. Both understated what Failure Routing (below) already required, and neither had room for a legitimate, survivable worker-failure outcome in an Optional category. The wording below is corrected to be internally consistent; no new stage, entity, or behavior is introduced — this is a wording fix to match the behavior the document always intended.

An AnalysisRun may only transition to `complete` (Phase 0 §3.11) if all of the following hold:

1. **Every Assertion in the Applicability Set has reached one of the three terminal outcome types defined in §5** (evidence outcome, attempted-no-signal outcome, or worker-failure outcome). No in-scope Assertion may simply have no record at all. A worker-failure outcome *is* a valid terminal record for the purpose of this invariant — whether it is also *acceptable* for completion is governed entirely by invariants 2 and 3 below, not by this one.
2. **Worker-failure outcomes are recorded distinctly and never conflated with attempted-no-signal outcomes**, because the two have opposite implications: one is a legitimate property of the content, the other is a defect in the platform's own execution.
3. **Required-category check:** for each Genome category marked Required (Phase 1 §3), either (a) **all** of its in-scope Assertions have reached an evidence outcome or an attempted-no-signal outcome — i.e., none of them have a worker-failure outcome — or (b) the entire category has zero Assertions in the Applicability Set for this asset (legitimately Not Applicable — e.g., Visual Identity on a text-only asset). If neither holds — the category has in-scope Assertions and at least one of them has a worker-failure outcome — the run must not be marked complete.

**Failure routing:** any in-scope Assertion with a worker-failure outcome, belonging to a **Required** category, routes the AnalysisRun to `failed` (terminal, Phase 0 §3.11) rather than allowing a Decision to be computed from an incomplete picture. A worker-failure outcome affecting only an in-scope Assertion in an **Optional** category does not fail the run — but must still be recorded distinctly (not silently dropped) so a pattern of optional-category worker failures remains visible for operational attention, even though it doesn't block completion.

**Why this distinction matters:** a Decision computed while quietly missing a Required dimension due to a pipeline defect would look identical, on its face, to a properly-computed low-confidence Decision — the report would show a discounted Coverage/Confidence figure either way, with nothing visibly indicating something actually broke. Separating "the content didn't give us enough to work with" from "our own pipeline didn't do its job" is what keeps a low-confidence score honest rather than a symptom silently disguised as a normal result.

---

## 7. Worker Orchestration (Conceptual)

- Workers assigned to independent Genome categories (e.g., Visual and Verbal, for an image asset with on-image text) may proceed without depending on one another's output.
- Video's derived-content workers (operating on representative frames and transcript) depend on that derivation happening first (§3) — a genuine ordering dependency, not an implementation detail of how it's scheduled or parallelized.
- No worker's assignment or execution depends on another worker's *findings* (only, where applicable, on another stage's *derived input*) — this keeps worker responsibilities cleanly separable.

---

## 8. Failure Handling Summary

| Situation | Outcome |
|---|---|
| Assertion not in Applicability Set | Not Applicable; excluded entirely from scoring/coverage — not a failure |
| Assertion in scope, content insufficient to evaluate | Attempted-no-signal outcome; discounts Coverage/Confidence; does not fail the run |
| Assertion in scope, worker fails, category Optional | Worker-failure outcome, recorded distinctly; does not fail the run; remains visible for operational review |
| Assertion in scope, worker fails, category Required | AnalysisRun routes to `failed` (terminal) — no Decision is computed |
| Entire Required category has zero in-scope Assertions | Legitimate (e.g., Visual Identity on text-only asset); category excluded from this run's aggregation; not a failure |

---

## 9. What Remains Explicitly Out of Scope for Phase 3

Consistent with this document's implementation-agnostic mandate: the actual mechanism a worker uses to detect a logo, assess tone, or judge photography style; how confidence is numerically calibrated internally; how workers are scheduled, parallelized, retried, or scaled; and any specific technology, model, or framework. These are Phase 4 and later concerns, sized against the pipeline shape this document defines.

---

*End of Phase 3 — AI Pipeline Architecture Specification, v1.1 FROZEN.*