# Brandium — Phase 1: Brand Intelligence Repository
## Knowledge Model Specification

**Status:** v0.2 — **FROZEN** (supersedes v0.1)
**Depends on:** PRD v1.0; Phase 0 Business Domain Specification **v0.2 FROZEN**
**Scope:** Conceptual knowledge architecture only. No AI models, databases, queues, APIs, or implementation technologies are discussed or implied anywhere in this document.
**Blocks:** Phase 2 (Decision Architecture — BDI Engine, Policy Engine, Explainability Engine)

---

## Changelog from v0.1

| # | Change | Rationale |
|---|---|---|
| 1 | Traceability chain (§8) updated to include **Decision** and **Recommendation** explicitly | Phase 0 v0.2 formalized both as first-class entities; this document's traceability model must reflect that, not just informally reference "Decision" as it did in v0.1 |
| 2 | §8 and §0 updated to state explicitly: **Report is a persisted read model built from Decision + Evidence + Recommendation** | Aligns with Phase 0 v0.2's redefinition of Report; removes the residual v0.1 framing of Report as if it held decision content directly |
| 3 | Reference to Report's review metadata (`review_status`, `reviewed_by`, `flag_reason`, `reviewed_at`) added where Report is discussed | Supports the PRD's reviewer feedback workflow; these fields live on Report per Phase 0 v0.2 §3.16 — this document only needs to acknowledge them for traceability completeness, not redefine them |

No change to Genome structure (§1–§3), Brand History model (§4), Compilation Workflow (§5), Evidence Schema (§6), or Provenance Model (§7). Those sections are unaffected by the Phase 0 revision and remain exactly as in v0.1.

---

## 0. Relationship to Frozen Phase 0 (Updated)

This document elaborates the internal structure of entities Phase 0 establishes as versioned/aggregate boundaries: **BrandGenome**, **BrandHistory**, and **Evidence**. It does not alter any aggregate root, ownership boundary, or invariant frozen in Phase 0 v0.2. Specifically:

- BrandGenome remains a whole-snapshot versioned entity, now pointed to by `Brand.active_genome_version_id` rather than a stored `status = active` value (Phase 0 v0.2, §3.5–3.6). Nothing below introduces independent sub-versioning.
- Evidence remains owned by the **Analysis & Decision** bounded context (now explicitly named in Phase 0 v0.2 §7, alongside Observation, Decision, and Recommendation). This document defines Evidence's *shape*, because that shape is what Genome Assertions must be compatible with — it does not move Evidence's ownership.
- **Report is a persisted read model, not an independently-computed entity** (Phase 0 v0.2 §3.16): it materializes exactly one **Decision** (deterministic score/verdict, versioned via `decision_function_version`), the **Evidence** that Decision was computed from, and the **Recommendation**(s) grounded in that Evidence — all reachable through the shared `analysis_run_id`. This document's traceability model (§8) reflects that chain explicitly.
- One additive extension is required and is called out explicitly rather than silently applied: `BrandHistory.source_type` is extended to include `guideline_document` and `design_system_spec`, alongside the original `campaign`/`ad`/`social`/`video` values. This is required because FR-001 names these as onboarding inputs and Section 5 (Genome Compilation Workflow) cannot be specified without a place to put them. No existing value is changed or removed.

---

## 1. Brand Genome Structure

*(Unchanged from v0.1)*

A Genome version is a self-contained snapshot, internally composed as a three-level hierarchy:

```
BrandGenome (version N, frozen structure per Phase 0)
  └─ GenomeCategory (e.g., Visual Identity)
       └─ GenomeComponent (e.g., "Primary Color Palette")
            └─ Assertion (the atomic knowledge claim)
```

**GenomeCategory** — a top-level dimension of brand identity (enumerated in §2). Fixed taxonomy, platform-defined.

**GenomeComponent** — a named unit of knowledge within a category. Platform-defined per category, so every Genome has a predictable shape for the Decision Architecture (Phase 2) to evaluate against.

**Assertion** — the atomic, evaluable knowledge claim: carries its own confidence value, its own provenance record (§7), can be individually flagged as unresolved/conflicting during compilation (§5), and is what Evidence (§6) is ultimately compared against.

A GenomeComponent may hold one or more Assertions. A GenomeComponent with zero Assertions is **not populated** — relevant to §3 and §10.

**Why this three-level shape:** Category and Component give the Decision Architecture a stable, predictable addressing scheme without requiring per-tenant taxonomy customization. Only the Assertion level varies per tenant.

---

## 2. Brand Genome Categories

*(Unchanged from v0.1)*

| Category | Represents |
|---|---|
| **Visual Identity** | Logo usage rules, color palette, typography, imagery/photography style, layout/composition conventions |
| **Verbal Identity (Voice & Tone)** | Tone attributes, vocabulary preferences, prohibited/discouraged language, sentence-level style conventions |
| **Messaging & Positioning** | Core value propositions, approved taglines/key messages, positioning statements |
| **Values & Mission** | Mission statement, stated organizational values, cause/purpose alignment |
| **Compliance & Legal** | Regulatory constraints, mandatory disclaimers, trademark/attribution usage rules |
| **Accessibility** | Brand-content accessibility requirements — the brand-knowledge counterpart to NFR-011, which governs the platform's own UI, not tenant content |

Closed and complete for v1.

---

## 3. Required vs. Optional Genome Components

*(Unchanged from v0.1)*

| Category | Status | Rationale |
|---|---|---|
| Visual Identity | **Required** | Image and video evaluation are structurally impossible without it |
| Verbal Identity (Voice & Tone) | **Required** | Text and video evaluation are structurally impossible without it |
| Messaging & Positioning | **Required** | Core to what "authentically represents the brand" means |
| Values & Mission | Optional | Enriches scoring but doesn't block core evaluation |
| Compliance & Legal | Optional (strongly recommended) | High value for regulated tenants, not universal |
| Accessibility | Optional | Doesn't block core evaluative capability |

**Activation gate:** a Genome draft may enter `pending_review` only if all three Required categories have at least one populated Component with at least one Assertion. This gates entry *into* `pending_review`; it does not alter the `pending_review → (pointed-to)` activation mechanism defined in Phase 0 v0.2 §3.6.

**Completeness Index:** a derived, non-stored guidance metric — unchanged.

---

## 4. Brand History Model

*(Unchanged from v0.1, other than the §0 additive `source_type` extension already noted)*

| Field (conceptual) | Purpose |
|---|---|
| source_type | `guideline_document`, `design_system_spec`, `campaign`, `ad`, `social`, `video` |
| modality | text / image / video |
| era_tag | approximate time period the asset represents |
| authority_level | see below |
| ingested_at | |

**Authority levels:**
1. **Explicit** — current, deliberately-authored guideline documents and design system specs. Highest authority.
2. **Exemplar** — historical campaigns, ads, social content, video: observational, not prescriptive.

---

## 5. Genome Compilation Workflow

*(Unchanged from v0.1)*

```
1. Ingestion — BrandHistoryItems accepted and tagged.
2. Candidate Assertion Formation — candidates formed per GenomeComponent, possibly conflicting.
3. Consolidation — reconciled by:
     a. Explicit outranks Exemplar.
     b. Among equal authority, more recent era_tag outranks older.
     c. Genuine remaining conflicts marked "conflicted," surfaced to human review, not auto-resolved.
4. Draft Assembly — consolidated Assertions assembled into a draft BrandGenome version,
   which then enters Phase 0's lifecycle: draft → pending_review (gated by §3/§10)
   → pointed-to by Brand.active_genome_version_id, requiring DR-006's human sign-off
   (Phase 0 v0.2 §3.6 activation operation).
```

---

## 6. Evidence Schema

*(Unchanged from v0.1)*

| Field (conceptual) | Purpose |
|---|---|
| assertion_reference | Which specific Genome Assertion this Evidence item evaluates against |
| observed_characteristic | Structured description of what was found, shaped to be directly comparable to the referenced Assertion |
| alignment_indicator | aligned / partially aligned / misaligned |
| confidence | explicit, calibrated (DR-002) |
| source_observation_refs | traceability back to raw Observation(s) |

**Why Evidence must reference a specific Assertion, not just a Category:** explainability (NFR-002) requires reports to cite the specific asserted rule a piece of content conflicts with, not just a category-level miss.

---

## 7. Provenance Model

*(Unchanged from v0.1)*

Applies to both Genome Assertions and Evidence items.

| Field | For an Assertion | For an Evidence item |
|---|---|---|
| origin_type | `explicit_source` / `exemplar_source` / `human_override` | `derived_from_observation` |
| source_reference(s) | Specific BrandHistoryItem(s) | Specific Observation(s) |
| confidence | At formation time | At comparison time |
| recorded_at | | |

`human_override` remains the necessary third origin_type for Assertions manually authored or corrected by a Brand Administrator during review.

---

## 8. Traceability Model (Revised)

A single directed chain must be walkable, end to end, for every completed AnalysisRun — this is the concrete mechanism satisfying NFR-002, and updated to reflect Phase 0 v0.2's first-class Decision and Recommendation entities and Report's status as a read model:

```
Report (persisted read model — Phase 0 v0.2 §3.16)
  ← Decision (deterministic score/verdict, versioned via decision_function_version
              — Phase 0 v0.2 §3.14; reproducibility applies here, not to narration)
  ← Recommendation (LLM-narrated, evidence-grounded, schema-constrained
              — Phase 0 v0.2 §3.15)
     ← Evidence (per-item; both Decision and Recommendation trace back to it)
        ← Observation (raw worker output)
        ← Genome Assertion (what it was compared against)
           ← BrandHistoryItem or human_override
              (the actual source material or human decision)
```

**Invariant (unchanged in substance, restated against the revised chain):** no link in this chain may be missing for a completed AnalysisRun. A Decision or Recommendation with even one Evidence reference lacking a resolvable path back to a source BrandHistoryItem (or explicit human_override) is not eligible to be marked part of a `complete` AnalysisRun.

**Report's review overlay (new — Phase 0 v0.2 §3.16) sits outside this evidentiary chain by design:** `review_status`, `reviewed_by`, `reviewed_at`, and `flag_reason` are workflow annotations on top of an otherwise-immutable Report projection. Reviewing or flagging a Report never mutates the Decision, Evidence, or Recommendation it was built from — a flagged Report is still the same immutable projection, now carrying a human note about it. This preserves the traceability invariant above without exception.

---

## 9. Versioning Strategy

*(Unchanged from v0.1, restated against pointer-based activation)*

- A new Genome version is a complete, self-contained snapshot — not a delta.
- A diff between two Genome versions is a derived view, never a stored entity.
- Category/Component taxonomy changes are platform-level and forward-only; existing Genome versions (active or superseded) are never retroactively reshaped, which would break DR-005 pinning on every report ever generated against them.
- This is unaffected by Phase 0 v0.2's switch from stored `status = active` to `Brand.active_genome_version_id` — the pointer changes *how* a version's currency is represented, not the snapshot/immutability model itself.

---

## 10. Knowledge Validation Rules

*(Unchanged from v0.1)*

1. **Category coverage:** all three Required categories have at least one populated Component with at least one Assertion.
2. **No orphan Assertions:** every Assertion has a resolvable provenance record.
3. **No unresolved conflicts:** no GenomeComponent may remain `conflicted` when submitted for review.
4. **Confidence validity:** every Assertion and Evidence confidence value falls within the defined calibrated range.
5. **No duplicate contradictory Assertions left standing** within one Component — treated as an unresolved conflict under rule 3.

A draft failing any rule cannot proceed to `pending_review`, independent of and prior to the DR-006 human sign-off gate.

---

## 11. Consistency Check Against Frozen Phase 0 (Re-verified against v0.2)

- No aggregate root, ownership boundary, or lifecycle state machine from this document (Phase 1) required alteration by the Phase 0 v0.2 revision.
- The Phase 0 v0.2 additions (Decision, Recommendation, Report-as-read-model, pointer-based activation, denormalized `org_id`, named Bounded Contexts) are all either downstream of, or orthogonal to, the Genome/Evidence/Provenance model this document defines. None of them require Genome, Evidence, or Provenance to be reshaped.
- The one additive change this document itself introduces (`BrandHistory.source_type` extension, §0) remains unchanged by the Phase 0 revision.
- DR-005 (version pinning) and DR-006 (human review gate) are both reinforced by Phase 0 v0.2, not modified — §9 and §10 here remain concretely enforceable exactly as before.

**No contradiction requiring this document to reopen was found. Phase 1 is FROZEN as of this revision.**

---

## 12. Open Questions Carried to Phase 2

*(Unchanged from v0.1)*

1. How `alignment_indicator` values and Evidence confidence combine into a Decision's score is explicitly Phase 2's to define — this document stops at Evidence's shape and Decision's reproducibility contract (Phase 0 v0.2 §3.14), not its math.
2. Component-level taxonomy detail (full list of GenomeComponents per Category) is left to a companion schema reference, to be finalized before Phase 2 needs to address specific components by name.
3. Whether `human_override` Assertions should be weighted differently than compiled Assertions in scoring is a Phase 2 decision; this document only ensures the provenance distinction exists so Phase 2 can make that choice.
4. **New, carried from Phase 0 v0.2's changelog:** Decision's `decision_function_version` field means Phase 2 must define a versioning scheme for the BDI formula itself (e.g., semantic versioning, with rules for what constitutes a version bump) — this is now a concrete Phase 2 deliverable, not just an implied one.

---

*End of Phase 1 — Knowledge Model Specification, v0.2. FROZEN. This is the baseline Phase 2 (Decision Architecture) builds against.*