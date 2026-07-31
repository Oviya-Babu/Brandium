# Brandium — Phase 2: Decision Architecture Specification

**Status:** v1.0 — Draft for review
**Depends on:** PRD v1.0; Phase 0 Business Domain Specification v0.2 FROZEN; Phase 1 Knowledge Model Specification v0.2 FROZEN
**Scope:** Conceptual reasoning architecture only. No AI models, prompts, databases, APIs, queues, infrastructure, frameworks, or programming languages are discussed or implied anywhere in this document.
**Blocks:** Phase 3 (AI Pipeline — workers producing the Observations/Evidence this document consumes)

---

## 0. Relationship to Frozen Phase 0 and Phase 1

This document does not alter any entity, field, invariant, or lifecycle frozen in Phase 0 v0.2 or Phase 1 v0.2. It resolves two items those documents explicitly deferred:

- **Policy's `rules` payload shape** (Phase 0 v0.2 §3.7: "shape deferred to Phase 2") — defined in §2 below.
- **A versioning scheme for `decision_function_version`** (Phase 1 v0.2 §12, open question 4) — defined in §8 below.

One governance question is surfaced, not resolved, because resolving it would require adding a field to the frozen Policy entity: see §11.

No contradiction was found that makes implementation impossible with Phase 0/1 as they stand.

---

## 1. Decision Engine (BDI) — Overview

The Decision Engine's sole responsibility is to convert a completed AnalysisRun's Evidence set into exactly one Decision (score + verdict), reproducibly, and to do so in two clearly separated stages:

1. **Evidence Aggregation** (§3) — purely a function of *Evidence* and the *Genome* it was evaluated against. Produces raw aggregate alignment values and confidence values at every level of the Genome hierarchy (Assertion → Component → Category), independent of any tenant-specific governance preference.
2. **Policy Evaluation** (§2) — applies the tenant's *Policy* (importance weights, critical rules, verdict thresholds) to the aggregates produced in stage 1, yielding the final score and verdict.

**Why this separation matters, architecturally:** it means "what the content actually contains, measured against the brand's own asserted identity" (stage 1) is completely independent of "how much the organization has chosen to care about each dimension, and what verdict that implies" (stage 2). The same Evidence aggregation could, in principle, be re-evaluated under a different Policy without recomputing anything about the content itself — a clean separation of *fact* from *governance preference*, and the reason Phase 0 pinned `policy_version_id` and `genome_version_id` as two independent fields on AnalysisRun rather than one.

Both stages together, plus Confidence Propagation (§4) and the Critical Rule mechanism (§2.3), constitute what `decision_function_version` (§8) actually versions.

---

## 2. Policy Evaluation

### 2.1 Policy Content (resolving Phase 0's deferred `rules` shape)

A Policy version conceptually contains four components:

| Component | Purpose |
|---|---|
| **Category Weights** | Relative importance of each of the six Genome Categories (Phase 1 §2) to the overall score. Must be non-negative and normalized (sum to a whole) — see §10. |
| **Component Weights** | Relative importance of each Component *within* its Category. Normalized within each Category independently. |
| **Assertion Weights** | Relative importance of each Assertion *within* its Component. Defaults to uniform if the Policy does not specify otherwise — a Policy is not required to weight every Assertion explicitly. |
| **Critical Rules** | A designated subset of Categories, Components, or specific Assertions marked *critical*, each with its own critical threshold and an override verdict (§2.3). |
| **Verdict Thresholds** | A monotonically ordered set of score bands mapping the overall score to a verdict label (§5.2). |

A Policy is therefore a governance configuration, not a scoring algorithm — the algorithm (how weights and thresholds are applied) is fixed platform behavior, defined once in this document, and is what `decision_function_version` tracks (§8). Only the *values* of weights/thresholds/critical rules vary per tenant, per Policy version.

### 2.2 Why Weighting Lives in Policy, Not in the Genome

Phase 1 deliberately left Assertions without an importance-weight field. This was correct: the Genome asserts *what is true about the brand*; it should not also encode *how much the organization currently chooses to weight that truth in scoring*. Two organizations could share an identical Genome shape (unlikely in practice, but architecturally possible) and legitimately want different scoring emphasis — e.g., a highly regulated brand weighting Compliance & Legal far more heavily than a consumer lifestyle brand would. Keeping weighting in Policy, versioned independently of the Genome, is what makes that possible without duplicating brand-identity content.

### 2.3 Critical Rules and Verdict Override

A Critical Rule designates a specific Genome element (Category, Component, or Assertion) as one whose failure should override the aggregate-score-derived verdict, regardless of how well the content scores elsewhere. Each Critical Rule specifies:

- The Genome element it applies to.
- A **critical threshold** — if that element's aggregate alignment value (§3) falls below this threshold, the rule *fires*.
- An **override verdict** — the verdict applied if the rule fires (e.g., a missing mandatory disclaimer firing a "Non-Compliant" override, independent of an otherwise-strong overall score).

**Multiple-rule resolution:** if more than one Critical Rule fires simultaneously, Policy must define a severity ranking among its own override verdicts; the most severe fired override applies. This prevents an ambiguous "which critical failure wins" situation from ever reaching an unversioned, ad hoc resolution.

**Overrides are never silent:** an override is itself an explainability fact — the Report must state plainly that the verdict was determined by a Critical Rule override, name the rule, and cite the Evidence that caused it to fire (§7). A verdict that came from an override must never be presented identically to one that came from the ordinary threshold lookup — these are different provenances and the Report distinguishes them.

---

## 3. Evidence Aggregation and Weighting

### 3.1 Alignment Value Function

Each Evidence item's `alignment_indicator` (Phase 1 §6: aligned / partially aligned / misaligned) is mapped to a fixed numeric value via a deterministic lookup — not a model, not a judgment call:

| alignment_indicator | Alignment Value |
|---|---|
| aligned | 1.0 |
| partially_aligned | 0.5 |
| misaligned | 0.0 |

This mapping is fixed platform behavior, versioned as part of `decision_function_version` (§8) — a future revision to this table (e.g., a finer-grained indicator scale) is a version bump, not a silent change.

### 3.2 Assertion-Level Aggregation

An Assertion may have multiple Evidence items referencing it (e.g., several sentences of text, multiple frames of a video). These are combined via a **confidence-weighted mean**:

> Assertion Aggregate Value = ( Σ confidence_i × alignment_value_i ) / ( Σ confidence_i ), across all Evidence items i referencing that Assertion.

This is deliberately simple and auditable: evidence the platform is more confident about naturally has more influence on the aggregate, without any exotic or opaque combination rule.

**No evidence for an Assertion is not the same as failing it.** If zero Evidence items reference an Assertion, that Assertion is marked **not covered** for this AnalysisRun (§4.2) and is excluded from the aggregation above — it contributes to Coverage tracking, never to a penalized score. Absence of a signal must never be silently treated as a negative signal; conflating the two would make a short piece of content (which simply doesn't contain enough material to evaluate every Assertion) score unfairly low through no fault of its own.

### 3.3 Component-Level Aggregation

> Component Aggregate Value = ( Σ assertion_weight_j × assertion_aggregate_value_j ) / ( Σ assertion_weight_j ), across covered Assertions j within the Component.

Only *covered* Assertions (§3.2) participate; uncovered Assertions are excluded from both numerator and denominator, so a Component's score reflects only what was actually evaluated.

### 3.4 Category-Level Aggregation

> Category Aggregate Value = ( Σ component_weight_k × component_aggregate_value_k ) / ( Σ component_weight_k ), across evaluated Components k within the Category.

### 3.5 Overall (Pre-Verdict) Aggregation

> Overall Aggregate Value = ( Σ category_weight_c × category_aggregate_value_c ) / ( Σ category_weight_c ), across evaluated Categories c.

This Overall Aggregate Value, scaled to a 0–100 presentation range (a trivial, non-substantive transform: `presented_score = overall_aggregate_value × 100`), is the **BDI Score** referenced throughout the PRD.

---

## 4. Confidence Propagation

### 4.1 Principle: Score and Confidence Are Never Blended

The platform produces two orthogonal outputs at every level of the hierarchy: **how well the content aligns** (§3) and **how sure the platform is about that assessment**. These are computed via entirely separate aggregation rules and are never combined into a single number. A Report must be able to say, distinctly, "this scored low, and we're highly confident in that" versus "this scored low, but confidence is limited" — collapsing these into one figure would hide exactly the information an enterprise reviewer needs to decide how much weight to place on the result.

### 4.2 Coverage

**Coverage** at the Assertion level is binary: 1 if at least one Evidence item references it, 0 otherwise (§3.2). At the Component, Category, and Overall levels, Coverage is the weight-proportional share of covered child elements (using the same weights as §3's score aggregation):

> Coverage(level) = ( Σ weight_of_covered_children ) / ( Σ weight_of_all_children_at_that_level )

### 4.3 Confidence Aggregation Rule

Raw confidence is propagated as an unweighted arithmetic mean of the confidences of covered child elements at each level (deliberately *not* self-weighted by confidence, to avoid the circularity of confidence reinforcing itself):

> Raw Confidence(level) = mean( confidence of covered children at that level )

### 4.4 Coverage Discount

The confidence actually reported at any level is the raw confidence discounted by that level's Coverage:

> Reported Confidence(level) = Raw Confidence(level) × Coverage(level)

This ensures that a Category evaluated on only a fraction of its Components — even if the fraction evaluated scored with high individual confidence — is honestly reported as lower-confidence overall, reflecting the genuine incompleteness of the picture.

---

## 5. Decision Formation (Score & Verdict)

### 5.1 Score

The BDI Score is the Overall Aggregate Value from §3.5, presented on a 0–100 scale. It is accompanied, always, by the Overall Reported Confidence (§4.4) — never presented alone.

### 5.2 Verdict Determination

1. Look up the BDI Score against the Policy's Verdict Thresholds (§2.1) to obtain a baseline verdict.
2. Evaluate all Critical Rules (§2.3) against their respective aggregate values. If any fire, apply the override-verdict resolution (§2.3) in place of the baseline verdict.
3. The final verdict, together with a record of whether it came from ordinary threshold lookup or a Critical Rule override (and if so, which rule), is what populates the Decision entity's `verdict` field (Phase 0 v0.2 §3.14).

### 5.3 What Is Persisted vs. Derived

Per Phase 0 v0.2, the Decision entity stores only `score`, `verdict`, `decision_function_version`, and `computed_at`. The full aggregation tree (every Assertion/Component/Category aggregate, coverage, and confidence value computed along the way) is **deliberately not persisted as new stored fields or entities**. Because the entire computation is deterministic and fully reproducible given (Evidence set, `genome_version_id`, `policy_version_id`, `decision_function_version`) — which are all already pinned per Phase 0's DR-005 and this document's §8 — the aggregation tree can always be exactly regenerated on demand. This avoids reopening the frozen Decision entity to add fields, and avoids a second, redundant place where the aggregation result could ever drift out of sync with what Evidence and Policy actually say.

---

## 6. Recommendation Generation

### 6.1 Triggering

For every Component (the chosen granularity — fine enough to be actionable, coarse enough to avoid one recommendation per Assertion becoming noise) whose Component Aggregate Value (§3.3) falls below a Policy-defined **improvement threshold**, exactly one Recommendation is triggered, grounded in the specific covered Assertions — and their underlying Evidence — that pulled that Component's score down.

### 6.2 Priority (Deterministic)

> Priority = Component Weight (within its Category, §2.1) × max(0, improvement_threshold − component_aggregate_value)

This is a fixed, auditable formula: a Recommendation is more urgent both because the dimension it addresses matters more to the organization (weight) and because the gap between current and expected performance is larger. No language model participates in deciding *whether* a recommendation exists or *how urgent* it is — only in how it is worded (§6.3).

### 6.3 The Deterministic/Generative Boundary Within Recommendation

Recommendation is the one entity that straddles both worlds, and this document states the boundary explicitly rather than leaving it implicit:

- **Deterministic and covered by `decision_function_version`:** whether a Recommendation is triggered at all (§6.1), its priority (§6.2), and its grounding (`related_evidence_ids`, Phase 0 v0.2 §3.15).
- **Generative and not subject to byte-for-byte reproducibility:** the narrated `text` field — the natural-language phrasing of the recommendation. Regenerating a Recommendation's text is expected to vary in wording even under identical inputs; regenerating *whether it exists and at what priority* must not.

This distinction must be visible to anyone auditing the system: two different runs producing differently-worded recommendation text for the same underlying finding is not a reproducibility violation; two different runs disagreeing on whether a finding was flagged at all, or at what priority, is.

---

## 7. Explainability Architecture

Every Decision must support on-demand reconstruction of its full reasoning chain (Phase 1 v0.2 §8's traceability model), at every level:

- **Assertion level:** which specific Evidence items contributed, their individual alignment values and confidences, and the Assertion they were compared against (with its own provenance back to a BrandHistoryItem or `human_override` — Phase 1 §7).
- **Component / Category level:** which child aggregate values and weights combined to produce this level's figure, and this level's Coverage and Reported Confidence.
- **Overall level:** the same, plus — where applicable — an explicit statement of any Critical Rule that fired, which rule, and what it overrode.
- **Recommendation level:** the Component it addresses, the Priority formula's inputs (weight and gap), and the specific Evidence cited as grounding.

Because §5.3 establishes that this entire tree is derived rather than stored, the Explainability Engine's responsibility is to **reconstruct** this chain on demand from Evidence, the pinned Genome/Policy versions, and `decision_function_version` — not to read it from a persisted copy. This keeps there being exactly one source of truth for "why did this Decision come out this way."

---

## 8. Decision Reproducibility and Versioning

### 8.1 What `decision_function_version` Covers

A single `decision_function_version` is an atomic package covering all of the following as one unit (deliberately not versioned independently of each other, to keep reproducibility simple — one version number to pin per Decision, not several):

1. The Alignment Value Function (§3.1).
2. The aggregation formulas at every level (§3.2–3.5).
3. The Confidence Aggregation Rule and Coverage Discount Function (§4).
4. The Critical Rule override-resolution mechanism (§2.3).
5. The Recommendation triggering and priority formula (§6.1–6.2).

**Rule:** any change to any one of the five constitutes a new `decision_function_version`. Historical Decisions remain permanently, correctly interpretable under the version they recorded (Phase 0 v0.2 §3.14); a version change never retroactively reinterprets a past Decision.

### 8.2 Reproducibility Guarantee (the concrete, testable form of NFR-004)

Given an identical (Evidence set, `genome_version_id`, `policy_version_id`, `decision_function_version`), recomputing a Decision's `score` and `verdict` must produce an identical result, every time. Recommendation *triggering and priority* are covered by the same guarantee (§6.3); Recommendation *text* is explicitly not.

### 8.3 Versioning Scheme

`decision_function_version` is a simple monotonically increasing integer (v1, v2, …), not a semantic-versioning scheme with major/minor distinctions — at this stage of the platform's maturity, every change to any of the five covered mechanisms is consequential enough to warrant a full version bump, and introducing a "minor vs. major" distinction would only create ambiguity about which changes require re-validation. This can be revisited if, in production, a clear category of genuinely inconsequential changes emerges.

---

## 9. Human Review and Feedback Integration

### 9.1 Principle: No Feedback Loop Is Automatic

A flagged Report (Phase 0 v0.2 §3.16's `review_status = flagged`) never automatically alters the Genome, Policy, or `decision_function_version` that produced it. Automatic incorporation of human corrections into future scoring — however well-intentioned — would (a) silently break the reproducibility guarantee for the Decision being corrected, and (b) create an unaudited path by which a single reviewer's judgment call quietly reshapes future behavior for every subsequent asset. This mirrors, at the tenant-internal level, the same discipline DR-004 already applies at the cross-tenant level: no learning happens through a silent, automatic pipeline.

### 9.2 The Mediated Path

Flagged Reports are architecturally treated as **input to a deliberate, human-authored revision**, not as training signal consumed automatically:

- A Brand Administrator reviewing a pattern of flagged Reports may choose to author a `human_override` Assertion correction (Phase 1 §7) — producing a new, explicitly human-authored draft Genome version, which re-enters the existing compilation/activation lifecycle (Phase 1 §5, Phase 0 §3.6) including the DR-006 human sign-off gate.
- Equally, a pattern of flagged Reports may lead a Brand Administrator to author a new Policy version (adjusting weights, thresholds, or Critical Rules) — again re-entering Policy's existing lifecycle (Phase 0 §3.7).

In both cases, the review feedback loop is real and valuable, but it is always mediated by an explicit, versioned, human-authored change — never an automatic model update.

---

## 10. Validation Rules and Business Invariants

1. **Policy weight normalization:** Category Weights must sum to a fixed whole; within each Category, Component Weights must sum to a fixed whole; where specified, Assertion Weights within a Component must sum to a fixed whole. A Policy failing this cannot be activated.
2. **Critical Rule referential integrity:** every Critical Rule must reference a Category, Component, or Assertion that exists in the Genome version active at the time the Policy is activated. A Policy referencing a non-existent Genome element cannot be activated.
3. **Verdict Threshold completeness:** Verdict Thresholds must be monotonically ordered and must cover the entire score range with no gaps — every possible score must resolve to exactly one baseline verdict.
4. **Recommendation grounding:** no Recommendation may exist without at least one `related_evidence_id` (reinforces the field already defined in Phase 0 v0.2 §3.15).
5. **Absence-vs-failure distinction (critical validation rule):** zero Coverage for an *optional* Genome Category is acceptable and simply reflected in that Category's Coverage/Confidence figures. Zero Coverage for a *Required* Category (Phase 1 §3) on a `complete` AnalysisRun must never happen by design — a Required Category with no Evidence at all indicates a Phase 3 pipeline failure (e.g., a worker crashed or was never scheduled), not a legitimate absence of signal. An AnalysisRun in this state must not be allowed to reach `complete` with a Decision computed from it; it must be routed to `failed` instead. Silently producing a Decision from an incomplete Required Category would misrepresent a pipeline defect as a low-confidence-but-valid score — this is exactly the kind of failure mode that would quietly erode trust in the platform's outputs without ever being visibly wrong.
6. **Decision uniqueness:** exactly one Decision per AnalysisRun (already structural per Phase 0's 1:1 cardinality; restated here as a Phase 2 evaluation-time check, not merely a schema constraint).

---

## 11. Flagged for Your Decision — Not Resolved Here

Phase 0 v0.2 §9 left open whether Policy activation requires a human-review gate equivalent to Genome's (`activated_by`). This document did not need to resolve that to specify the Decision Architecture — but it raises the stakes on that open question, because Policy now directly determines scoring weights and Critical Rule overrides, not just "some configuration." Recommending you make this call explicitly before Phase 3 begins:

- **If yes:** Policy would need an `activated_by` field mirroring Genome's — a small, additive change to the frozen Phase 0 entity, requiring your explicit sign-off to reopen it (per your own instruction to only revisit Phase 0/1 on a genuine implementation-blocking contradiction — this is not one, so it waits for your call rather than being made unilaterally).
- **If no:** Policy changes remain author-and-activate in one step, same as today, and the governance gap stays open with eyes open.

---

*End of Phase 2 — Decision Architecture Specification, v1.0. Awaiting your review before this becomes the frozen baseline Phase 3 (AI Pipeline) builds against.*

Introduce a new conceptual step: Applicability Resolution before Evidence Aggregation.
Build a derived Applicable Assertion Set (not persisted, fully reproducible).
Update Coverage, Aggregation, and Confidence calculations to consider only applicable assertions.
Distinguish between Not Applicable and Not Evaluated, preventing valid assets from being treated as pipeline failures.
Update Required Category validation to fail only when applicable assertions were expected but not evaluated.
Extend Explainability to explicitly report "Not Applicable" assertions.
Ensure Recommendation Generation only considers applicable components.
Include Evaluation Context in the Decision reproducibility contract.
Phase 3: Perform Applicability Resolution before worker execution so workers analyze only the assertions relevant to the current asset.

Net effect: Introduces a single missing business concept—Applicability—without redesigning the architecture, preserving reproducibility, explainability, aggregation logic, and all existing Phase 0–2 principles.