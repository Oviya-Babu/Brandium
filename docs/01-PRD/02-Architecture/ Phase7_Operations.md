# Brandium — Phase 7: Product Experience & Operations Architecture
 
**Status:** v1.0 — Draft for review
**Depends on:** PRD v1.0; Phase 0 v0.2 FROZEN (+ addenda incl. Pre-Phase-7 correction 4); Phase 1 v0.2 FROZEN; Phase 2 v1.0 FROZEN (+ addenda incl. Pre-Phase-7 correction 1); Phase 3 v1.1 FROZEN (+ Pre-Phase-7 correction 5); Phase 4 v1.0 FROZEN; Phase 5 v1.0 FROZEN; Phase 6 v1.0 FROZEN (+ Pre-Phase-7 corrections 2–3)
**Scope:** Conceptual product and operations architecture only. No UI frameworks, API technologies, SDK languages, monitoring products, support ticketing systems, or infrastructure are discussed or implied anywhere in this document.
**Status of the overall architecture:** This is the final phase of the conceptual architecture roadmap (PRD §21). No further business, execution, security, or product-conceptual phase follows — Phase 8 onward is implementation.
 
---
 
## 0. Relationship to Frozen Phase 0–6
 
This document introduces no new entities, lifecycle states, or invariants. It defines how the guarantees Phases 0–6 already established are surfaced to the people and systems that consume them — the product and operational layer sitting on top of an otherwise-complete conceptual architecture.
 
---
 
## 1. Product Experience Principles
 
**Inspectability as a structural requirement, not a UI preference.** PRD §3.3 states a user should never see a score without being one click away from the evidence behind it. This document treats that as a direct consequence of Phase 2 §7's Explainability Architecture: because the full reasoning chain is always reconstructable on demand, the product surface's job is to *expose* that reconstruction, not to compute anything new. Any product surface that shows a score without a path to its Evidence would be hiding a capability the architecture already guarantees, not merely a missing feature.
 
**Role-appropriate views, derived from RoleAssignment scope, not duplicated.** What a person sees is exactly what their RoleAssignment (Phase 5 §2, Phase 6 §2) already permits — a Brand Administrator sees Genome/Policy governance surfaces, a Marketing Manager sees Report review surfaces, an Executive sees trend aggregates, an OrganizationAdministrator sees Membership and org-status surfaces and nothing Brand-content-facing. The product layer does not define a second permission model; it renders the one that already exists.
 
**Recommendation actionability.** A Recommendation (Phase 2 §6) is only useful if the path from "here's what's wrong" to "here's the next AssetVersion" is short. The product experience must surface a Recommendation's grounding (its `related_evidence_ids`) directly alongside it — never as a separate lookup step — since the deterministic/generative boundary (Phase 2 §6.3) means the grounding is exactly as trustworthy as the score itself, even though the wording is not.
 
**Confidence must never be hidden behind the score.** Phase 2 §4.1 established that score and confidence are never blended into one number. The product surface must preserve that separation visually and structurally — presenting only a score, without its accompanying confidence, would silently discard a guarantee the architecture went out of its way to make.
 
**Not Applicable is not silence.** Phase 3 §5's three-outcome taxonomy (plus Not Applicable) exists specifically so that "we didn't check this" is never confused with "this failed" or "this is fine." The product surface must represent all four states distinctly wherever Coverage or Confidence is shown — collapsing them back into a single "not evaluated" bucket at the presentation layer would undo the distinction Phase 3 was built to preserve.
 
---
 
## 2. API & Integration Architecture (Conceptual)
 
**Symmetry principle:** restated directly from Phase 0 §9's Architecture Readiness assumption — the UI is a client of the same capability surface as any external integration, never a privileged path. Anything achievable through the product surface must be achievable programmatically, and vice versa.
 
**Conceptual capability surface** (not an API specification — a list of what must be exposable, regardless of mechanism):
- Content submission (AssetVersion creation, subject to the Pre-Phase-7 correction 4 precondition)
- Report retrieval, including full Evidence/Decision traceability (Phase 1 §8, Phase 2 §7)
- Genome and Policy draft authoring, submission for review, and activation (subject to DR-006 and any enterprise maker-checker overlay, Phase 5 §4)
- Membership and RoleAssignment management (subject to Phase 6 §3's authorization and self-escalation rules — the API surface enforces the identical rules the product surface does, never a looser variant)
- Campaign/trend data retrieval (FR-010)
- Audit trail retrieval, scoped exactly as §8 of Phase 5/6 already specify
 
**Notification/webhook concept:** referenced only as a capability, not a mechanism — the platform must be able to signal that an AnalysisRun reached a terminal state, so that external systems (including a future pre-publication gate, PRD §5.3) can react without polling. The specific delivery mechanism is explicitly Phase 8+.
 
**No capability may bypass a trust boundary.** Every item above is gated by the exact same RoleAssignment scope and Membership-status checks (Phase 6 §3, Pre-Phase-7 correction 2) regardless of whether it's invoked through the product surface or directly — the API is not a second, less-audited path into the system.
 
---
 
## 3. Observability & Reliability Architecture (Product/Operations Layer)
 
This is distinct from — and sits above — Phase 4 §11's execution-layer observability, which concerns Work Unit and AnalysisRun state during a single run. This layer concerns the platform's health and reliability as experienced by tenants over time.
 
**Tenant-facing status visibility:** a tenant-side actor with appropriate scope should be able to see, for their own Organization only, whether the platform is currently operating normally, degraded, or experiencing an incident affecting their AnalysisRuns — sourced from the same execution-layer state Phase 4 already tracks, never a separate, potentially inconsistent operational data path.
 
**Reliability targets are inherited, not independently asserted.** NFR-005 (latency targets) and NFR-007 (availability target) remain the governing figures. This document does not set new numbers; it establishes that any future formal SLA (PRD §18's remaining Known Gap) must be expressed in terms of the platform invariants already guaranteed (Phase 5 §10, Phase 6 §9) — an SLA that promised something those invariants don't structurally support would be a commitment the architecture can't actually back.
 
**Incident communication principle:** ties directly to Phase 6 §6's security-incident governance — affected tenant-side actors are informed that something occurred, consistent with governance transparency (Phase 5 §8), without requiring InternalOperator to cross the content boundary (Phase 6 §2) to do so. Operational communication and content access remain separate capabilities.
 
---
 
## 4. Continuous Learning & Platform Improvement
 
This formalizes, as an ongoing operational program, two things Phases 2 and earlier deliberately left as manual, human-mediated processes rather than automatic ones — and this document does not change that.
 
**The Mediated Path, operationalized (Phase 2 §9.1/§9.2):** a recurring (not continuous, not automatic) review process in which Brand Administrators examine patterns across flagged Reports and, where warranted, author new Genome or Policy drafts through the existing lifecycle. This document adds no new mechanism — it names the existing Mediated Path as a program a tenant can run on a cadence of their choosing, rather than an ad hoc response to individual flags.
 
**Platform-level quality review (PRD §12's deferred spot-audit process):** BrandGuard's own operators may periodically sample production Decisions for calibration review — but per Phase 6 §2/§3, this sampling is structural/aggregate only for InternalOperator; any review requiring actual tenant content remains something only tenant-side actors, or explicitly-granted collaborators, can perform. A calibration finding that suggests `decision_function_version` itself should change goes through Phase 2 §8.1's versioning discipline — a deliberate, versioned change, never a silent model update.
 
**No feedback loop is ever automatic, restated at the program level:** exactly as Phase 2 §9.1 established for individual flags, a *pattern* of flags or calibration findings still only ever produces a new, explicit, human-authored draft — never an automatic adjustment to a live Genome, Policy, or `decision_function_version`.
 
---
 
## 5. Support and Customer Success Boundaries
 
**What BrandGuard support can see:** operational/structural facts only — that an AnalysisRun exists and its terminal state, that an Organization is suspended and why (an administrative fact, not content), that an audit event occurred. Exactly what Phase 6 §2/§8 already define as InternalOperator's visibility.
 
**What BrandGuard support can never see:** any Brand's Genome, Policy, Evidence, Decision content, or Report content — regardless of the reason offered for wanting to see it (Phase 6 §3's no-exception rule, restated here in customer-facing terms). A support interaction that appears to require content access is, architecturally, always resolved by a tenant-side actor granting scoped, temporary access to a specific person (Phase 6 §3's "temporary access principles") — never by BrandGuard reaching in from outside.
 
**Escalation, restated for the support context:** a tenant's own OrganizationAdministrator or BrandAdministrator is the first and primary point of resolution for anything content-related (Phase 6 §4); BrandGuard support's role is limited to the operational/structural facts above, plus confirming the last-administrator-standing safeguard (Pre-Phase-7 correction 3) hasn't been inadvertently triggered.
 
---
 
## 6. Onboarding and Offboarding Experience
 
**Onboarding**, from the product-facing side, is the guided self-serve flow already specified in PRD §11.1 and Phase 0/1 §5 — this document adds no new step, only frames the existing Ingestion → Compilation → Human Review → Activation sequence as the first-run product experience, including the Pre-Phase-7 correction 4 reality that content evaluation is unavailable until both a Genome and a Policy are active.
 
**Offboarding**, from the product-facing side, follows Phase 5 §1's Organization lifecycle (`provisioned → active → suspended → offboarded`). The product experience during offboarding must make explicit what Phase 5 already guarantees structurally: offboarding halts forward activity but never discards history — a tenant retains the ability to retrieve their own historical Reports and audit trail through the offboarded state, until any explicit, separately-governed data-retention/erasure action (Phase 6/7+, out of scope here) is taken.
 
---
 
## 7. Platform Invariants — Product/Operations Layer
 
1. No product or API surface may ever expose a score without its accompanying confidence and Evidence path (§1).
2. No product or API surface may collapse Not Applicable, attempted-no-signal, worker-failure, and evidence-outcome into a single undifferentiated state (§1).
3. The API surface enforces every trust boundary and authorization rule the product surface does — no capability, at any layer, offers a looser path (§2).
4. No continuous-learning or support process, however well-intentioned, produces an automatic change to a live Genome, Policy, or `decision_function_version` (§4, §5).
5. Reliability commitments are always expressed in terms of the platform invariants Phases 5/6 already guarantee, never asserted independently of them (§3).
 
---
 
## 8. Out of Scope
 
UI frameworks, specific API technologies or protocols, SDK languages, monitoring/observability products, support ticketing systems, notification delivery mechanisms, data retention/erasure tooling, and any other implementation or infrastructure technology. These are Phase 8+ engineering decisions, made in service of the guarantees this document — and every phase before it — defines.
 
---
 
## 9. Consistency Check Against Frozen Phase 0–6
 
- No entity, field, lifecycle state, or invariant from any prior phase is altered.
- Every principle in this document is a direct, traceable consequence of a guarantee an earlier phase already established — this document's contribution is exposure and operational framing, not new architectural substance.
- The Pre-Phase-7 corrections (dangling Critical Rules, Membership-aware authorization, last-administrator-standing, AnalysisRun creation precondition, Work Unit retry clarity) are all referenced here as already-incorporated baseline, not reopened.
 
**No contradiction requiring Phases 0–6 to reopen was found.**
 
---
 
## 10. Closing Note — Conceptual Architecture Complete
 
With Phase 7, the conceptual architecture defined in PRD §21 (Phases 0 through 7) is complete: Business Domain, Knowledge Model, Decision Architecture, AI Pipeline, Platform Engineering, Enterprise SaaS, Security/Trust/Governance, and Product Experience & Operations, each frozen with the minimal additive corrections each successive review required and none other. Every mechanism in the system — from a single Assertion's provenance to an enterprise tenant's last-administrator safeguard — traces to a specific, load-bearing requirement rather than a speculative abstraction. This baseline is what any subsequent implementation-phase engineering work (Phase 8+) should be built against, and measured for consistency with, going forward.
 
*End of Phase 7 — Product Experience & Operations Architecture, v1.0. Awaiting your review before this becomes the frozen conceptual-architecture baseline for implementation.*