# Brandium — Phase 6: Security, Trust & Operational Governance Architecture
 
**Status:** v1.0 — Draft for review
**Depends on:** PRD v1.0; Phase 0 v0.2 FROZEN (+ addenda); Phase 1 v0.2 FROZEN; Phase 2 v1.0 FROZEN (+ addenda); Phase 3 v1.1 FROZEN; Phase 4 v1.0 FROZEN; Phase 5 v1.0 FROZEN
**Scope:** Conceptual security, trust, and governance architecture only. No encryption, authentication protocols, OAuth, SSO, MFA, JWT, TLS, databases, APIs, cloud providers, Kubernetes, containers, secrets management, firewalls, SIEM, networking, monitoring products, deployment architecture, programming languages, or frameworks are discussed or implied anywhere in this document.
**Blocks:** Phase 7 (Product Experience & Ops)
 
---
 
## 0. Relationship to Frozen Phase 0–5 and Consistency Review Outcome
 
The pre-Phase-6 review found no contradiction requiring correction to Phases 0–5. It surfaced four genuinely open questions — none of them conflicts, all of them things Phase 5 correctly left for this phase to close:
 
1. Who may grant a RoleAssignment, and what stops an actor from escalating their own privilege — resolved in §3.
2. Whether AuditLogEntry's platform-wide existence (Phase 0 §6) implies any exemption from tenant-read isolation — resolved in §2 (it does not).
3. What happens to an AnalysisRun already `running` at the moment its Organization is suspended — resolved in §4.
4. To whom Work Unit observability (Phase 4 §11) is actually visible — resolved in §2.
 
**Phase 5 is frozen without modification.** Nothing below introduces a new entity, field, or lifecycle state; every mechanism here is expressed using constructs Phases 0–5 already define.
 
---
 
## 1. Security Architecture Principles
 
**Trust boundaries:** Enumerated fully in §2. The principle stated here is that every one is explicit and named — none is assumed by proximity (e.g., being in the same Workspace) or by seniority (e.g., an administrative role does not imply content access).
 
**Security domains:** Exactly two, cleanly separated: the **Tenant Domain** (everything rooted under an Organization) and the **Platform Domain** (InternalOperator, the AI Slop Knowledge Base, and the Genome taxonomy scaffolding — Phase 1 §2). Nothing spans both; anything that appears to is actually two separate things wearing one name (§2's shared-resource boundaries make this precise).
 
**Defense in depth:** Isolation is enforced independently at four layers — domain (Phase 0's org_id rooting), access (Phase 5's RoleAssignment scope evaluation), execution (Phase 4 §7's per-AnalysisRun Work Unit isolation), and observability (§2, new) — such that a failure at any single layer does not, by itself, compromise the guarantee the others independently provide.
 
**Least privilege:** Restated from Phase 5 §2, now extended in §3 to cover the act of *granting* privilege, not only the privilege itself.
 
**Secure-by-default:** No access exists without an explicit RoleAssignment (Phase 5 §2); the default posture for any unassigned actor is total denial.
 
**Fail-safe behavior:** Any check that cannot be conclusively resolved — an authorization evaluation, a Completeness Verification gate, a validation rule — resolves to denial or failure, never to a permissive default. This generalizes a principle Phase 3 §6 already applied narrowly (an incomplete Required category routes to `failed`, never to a silently-degraded Decision) into a platform-wide philosophy: uncertainty is never treated as permission.
 
**Zero implicit trust:** Every boundary crossing (§2) is evaluated on its own terms, every time. Prior successful access, organizational seniority, or being "already inside" a boundary never substitutes for an explicit check at the next one.
 
**Separation of duties:** Three distinct mechanisms, at three different layers, none of which substitutes for the others: (a) InternalOperator's structural, exception-free exclusion from tenant content (Phase 0 §3.4, reaffirmed in §3); (b) the optional Genome/Policy maker-checker overlay (Phase 5 §4); (c) the new self-escalation prohibition on RoleAssignment grants (§3).
 
**Security invariants:** Consolidated in §9.
 
---
 
## 2. Trust Boundary Architecture
 
| Boundary | What may cross | What may never cross |
|---|---|---|
| **Platform ↔ Organization** | Organization-lifecycle signals (suspend/reactivate, Phase 5 §1); shared taxonomy scaffolding and AI Slop KB references (read-only, into the pipeline only) | Any Brand-scoped content, in either direction |
| **Organization ↔ Workspace** | RoleAssignment scope and Membership status, gating what a Workspace-scoped actor may see | Visibility into sibling Workspaces, absent an Organization-scoped grant |
| **Workspace ↔ Brand** | Brand-scoped RoleAssignment gates visibility of that Brand's Genome/Policy/Campaigns | Visibility into sibling Brands within the same Workspace, absent a broader grant |
| **Human ↔ Platform** | Genome/Policy authoring and activation (subject to gates); Asset upload; Report review/flag | Direct authorship of a Decision's score or verdict — always computed, never hand-written |
| **Platform ↔ AI Workers** | A worker's assigned in-scope Assertions only (Phase 3 §3/§4) | Policy weights, Critical Rules, or another worker's findings — no worker ever receives these |
| **Decision Engine ↔ Execution Layer** | Evidence, pinned Genome/Policy versions, `decision_function_version` | Work Unit execution metadata (retry counts, timing, failure reasons) — operational noise never influences a score |
| **Internal Operator ↔ Tenant** | Organization-lifecycle actions; aggregate/structural operational health signals | Any tenant content, under any circumstance, including support or incident response (§3) |
| **Shared Knowledge Base ↔ Tenant-owned Knowledge** | The Distinctiveness Worker may *read* the Slop KB while forming an Observation | Nothing from any tenant's BrandHistory enters the Slop KB, ever — including content that happens to be independently public elsewhere |
| **Observability ↔ Tenant** *(new)* | Work Unit/AnalysisRun execution state (Phase 4 §11), visible only through the same RoleAssignment scope check as any other tenant-scoped read | Observability is never a side channel — no actor sees execution state for a run outside their authorized scope |
| **AuditLogEntry (global construct) ↔ Tenant** *(new)* | InternalOperator's structural/existence-only view, for platform-health purposes | Tenant-side actors never see another Organization's audit entries; a global storage construct is not an exemption from tenant-read isolation, only an operational convenience for cross-tenant health signals that carry no content |
 
---
 
## 3. Authorization and Trust Model
 
**Authorization evaluation:** For any tenant-scoped action, evaluate the acting User's applicable RoleAssignments at the narrowest matching scope tier (brand, else workspace, else organization — Phase 0 addendum). Permissions from multiple applicable assignments **union**; there is no explicit-deny construct anywhere in the model, so there is no genuine conflict to arbitrate (see "privilege conflict handling," below).
 
**Trust assumptions:** Zero implicit trust (§1) — every action is re-evaluated against current RoleAssignments; nothing is cached as a standing grant beyond the RoleAssignment's own continued existence.
 
**Privilege inheritance:** Flows one direction only — an Organization-scoped grant applies uniformly to every Workspace and Brand beneath it. It never flows upward (a Brand-scoped grant implies nothing about the Workspace) or sideways (a grant on one Brand implies nothing about a sibling Brand).
 
**Privilege denial:** The default state for any actor with no applicable RoleAssignment is complete denial — this is what "secure by default" means concretely, not just aspirationally.
 
**Privilege revocation:** Immediate and total upon RoleAssignment removal or Membership removal (cascading per Phase 5 §9). A revoked grant is never honored retroactively, and revocation never invalidates historical attributions already recorded (an `activated_by` reference to a now-revoked User remains a permanent historical fact, per Phase 5 §9's general rule).
 
**Privilege conflict handling:** Because Roles are purely additive grants with no deny concept, there is no scenario where two applicable RoleAssignments genuinely conflict — they simply union.
 
**Temporary access principles:** Achieved entirely through the existing RoleAssignment mechanism — grant, then explicitly revoke when the need ends. No separate "temporary" entity or expiry field is introduced; the commitment to revoke is a governance practice, tracked through the same audit trail as any other RoleAssignment change, consistent with the architecture's standing preference against unnecessary constructs.
 
**Exceptional / break-glass administrative access philosophy:** There is none for InternalOperator. Phase 0 §3.4's structural exclusion admits no exception — not for support, not for incident response, not for any circumstance. This is a deliberate, permanent design choice, not an oversight: any legitimate support need is met by a tenant-side actor (a Brand Administrator or Organization Administrator) granting a RoleAssignment to whoever needs temporary visibility — never by the platform reaching across the boundary from outside it.
 
**Privilege escalation prevention (new — resolves the review's central finding):** Granting a RoleAssignment is itself a governance action, fully audited. An actor may grant a Role to another User within their own authorized scope as an ordinary administrative act (an OrganizationAdministrator granting Workspace- or Brand-scoped roles to other Members, for instance). **An actor may never grant themselves a RoleAssignment that increases their own effective privilege.** Any grant that would expand the requesting actor's own access must be performed by a second, distinct actor holding equal-or-broader authority. This closes the one concrete escalation path the review identified — an OrganizationAdministrator quietly self-granting Brand-level content access — without adding any friction to the ordinary, single-actor case of administering other Members' access.
 
---
 
## 4. Operational Governance
 
**Administrative oversight:** OrganizationAdministrator (membership/access) and BrandAdministrator (content/governance) remain structurally distinct (Phase 5 §5); neither role implies the other's authority.
 
**Governance ownership:** Genome/Policy governance is owned by BrandAdministrator at Brand scope. Platform-wide operational health is owned by InternalOperator. These never overlap.
 
**Policy enforcement responsibilities:** The Decision Engine (Phase 2) is the sole enforcer of an activated Policy's rules. No human or operational actor may override a computed verdict outside the versioned Genome/Policy/`decision_function_version` channel.
 
**Organizational accountability:** An Organization is accountable, through its own BrandAdministrators and OrganizationAdministrators, for its Genome/Policy content and Membership. BrandGuard is never accountable for tenant-authored content — only for the platform's correct, deterministic application of it.
 
**Operational accountability:** BrandGuard, through InternalOperator, is accountable for platform health, for Organization-lifecycle transitions it initiates, and for the integrity of the execution and decision mechanisms themselves.
 
**Escalation principles:** A flagged Report (Phase 2 §9) escalates to a tenant-side Brand Administrator — never to BrandGuard's platform operators. Escalation stays within the tenant boundary; if a tenant has no available Brand Administrator, that is a Membership/administration gap for the tenant's own OrganizationAdministrator to resolve, not a BrandGuard responsibility.
 
**Governance checkpoints:** Three, each with exactly one owner, never merged: Genome/Policy activation (BrandAdministrator, gated by DR-006 plus any optional maker-checker overlay); Completeness Verification before a Decision may be computed (the platform's own pipeline, Phase 3 §6 — no human checkpoint here by design, since it's a structural gate, not a judgment call); and publication approval (Marketing Manager, PRD §11.4).
 
**Organization suspension and in-flight execution (resolves review finding 3):** Suspending an Organization halts acceptance of new AssetVersions and new AnalysisRuns. It does **not** interrupt an AnalysisRun already `running` at the moment of suspension — that run proceeds to its natural `complete` or `failed` outcome under Phase 3/4's existing rules, unaffected. This keeps a business-governance event (suspension) from ever triggering Phase 4's platform-level interruption/recovery pathway (Phase 4 §8), which exists specifically for platform-initiated interruptions, not tenant-governance ones — conflating the two would blur a boundary Phase 4 deliberately kept narrow.
 
---
 
## 5. Audit and Evidence Integrity
 
**Immutable audit philosophy:** Restated from NFR-003/Phase 0 §3.15, now explicitly covering RoleAssignment-granting actions — including a denied self-escalation attempt (§3), which is itself an auditable event, never silently dropped.
 
**Evidence integrity:** Evidence, once produced, is never edited in place — a correction is a new AnalysisRun, never a mutation (Phase 0 §3.13). No actor, including InternalOperator, has any write path to alter existing Evidence.
 
**Observation integrity:** The same guarantee one level down — Observations are immutable once recorded (Phase 0 §3.12); Fusion's deduplication (Phase 3 §5) selects and combines source Observations, it never rewrites them.
 
**Decision traceability:** DR-005's version-pinning and `decision_function_version` (Phase 2 §8) are restated here as a security guarantee, not merely a UX one: every Decision's full lineage is reconstructable by design, which is precisely what makes it auditable rather than merely asserted.
 
**Configuration traceability:** Genome and Policy version chains (append-only, superseded rather than deleted) already constitute a complete configuration history — no separate mechanism is introduced.
 
**Lifecycle traceability:** Every entity's lifecycle transition — Organization, Membership, Genome, Policy, AnalysisRun, Work Unit — is an auditable event per Phase 0/4/5, restated here as one unified guarantee spanning all of them.
 
**Actor accountability:** Every governance and access action — grant, revoke, activate, flag, suspend — is attributable to a specific actor, now explicitly including RoleAssignment-granting actions themselves (closing the gap that made §3's escalation-prevention rule enforceable rather than merely stated).
 
**Chain of evidence:** The full reconstructable path — Report ← Decision ← Evidence ← Observation ← Genome Assertion ← BrandHistoryItem or `human_override` (Phase 1 §8) — is restated here as a security and compliance guarantee: this chain may never be broken, truncated, or partially deleted for any AnalysisRun that reached `complete`.
 
---
 
## 6. Failure and Risk Governance
 
**Platform failures:** An execution-layer defect on a Required category (Phase 3 §6) routes the AnalysisRun to `failed`, never to a silently-degraded Decision — restated here as a trust guarantee, not only a data-quality one.
 
**Execution failures:** Isolated at the Work Unit level (Phase 4 §7); one AnalysisRun's execution failure never cascades to another's, another Brand's, or another Organization's.
 
**Governance failures:** A Genome or Policy that fails validation (Phase 1 §10) or referential integrity (Phase 2 §10) is blocked from activation outright — never activated with a warning and allowed to proceed regardless.
 
**Authorization failures:** Any authorization check that cannot be conclusively resolved defaults to denial (§1's fail-safe principle applied concretely).
 
**Policy violations:** A Critical Rule override (Phase 2 §2.3) is the platform's structural mechanism here — a policy violation always produces an explicit, attributable verdict override, never a silent score adjustment.
 
**Security incidents:** Specific tooling is out of scope (§10). The conceptual principle: any suspected tenant-isolation or authorization breach halts the affected operation immediately and escalates to InternalOperator's operational accountability (§4); affected tenant-side actors are informed, consistent with governance transparency (Phase 5 §8) — the platform never hides that something occurred, even while any investigation mechanism itself remains outside this document's scope.
 
**Tenant isolation failures:** The single most severe category. Any confirmed cross-tenant exposure is a platform-level failure requiring InternalOperator escalation — never a tenant-level or Brand-level governance matter, since no tenant-side actor has the visibility or authority to address a cross-tenant breach.
 
**Recovery principles:** Execution-layer recovery is exactly Phase 4 §8's existing mechanism (resumed Work Unit execution, never rewriting completed work). Governance-layer recovery is simply a new, corrected draft re-entering the existing Genome/Policy lifecycle (Phase 1 §5) — there is no separate "governance recovery" mechanism, because the existing draft/revision cycle already is the recovery path.
 
---
 
## 7. Trustworthiness of AI Decisions
 
**Evidence-grounded decisions:** No Decision originates from unconstrained model judgment (PRD §12, DR-002); every component of every score traces to specific Evidence.
 
**Deterministic decision computation and reproducibility preservation:** Restated from Phase 2 §5.3/§8 as a trust guarantee: a Decision can always be independently re-derived and checked, which is what makes it auditable rather than merely asserted.
 
**Explainability preservation:** Restated from Phase 2 §7 as a trust property: nothing about a Decision is a black box by architectural construction — not by policy promise, which could be violated, but by the structure of how a Decision is computed at all.
 
**Confidence integrity:** Restated from Phase 2 §4.1 — score and confidence are never blended into one figure. A reviewer is never handed a falsely-simple number that hides genuine uncertainty.
 
**Handling incomplete evidence:** Phase 3 §5/§6's outcome taxonomy (evidence outcome, attempted-no-signal, worker-failure, Not Applicable) is the trust-preserving mechanism that keeps "we genuinely don't know" from ever being mistaken for either "it failed" or "it's fine."
 
**Handling conflicting evidence:** Two mechanisms, at two levels, both principled rather than silent: Phase 1 §5's Consolidation precedence (explicit sources over exemplar, recent over old, else flagged for human resolution) at the Genome level, and Phase 3 §5's Fusion deduplication at the Evidence level. Conflicting signals are always resolved by an explicit rule or surfaced to a human — never silently averaged away in a way that hides the disagreement.
 
---
 
## 8. Cross-Tenant Security Principles
 
**Tenant isolation:** The supreme invariant, enforced independently at every layer named in §1's defense-in-depth principle.
 
**Shared taxonomy safety:** The Genome Category/Component taxonomy (Phase 1 §2) is shared shape only. A taxonomy change is forward-only and platform-versioned (Phase 1 §9) — it can never retroactively alter one tenant's Genome based on another tenant's needs.
 
**Shared AI Slop Knowledge Base boundaries:** DR-004's exclusivity is restated with the ambiguity the review found now closed: no tenant's BrandHistory content ever enters the Slop KB, regardless of whether that content is independently public elsewhere. The Slop KB's provenance is public/synthetic corpora only, full stop — never "public because a tenant published it."
 
**Data ownership:** Restated from Phase 5 §6 — the tenant owns all Brand-scoped content without exception; the platform owns only the Slop KB and the taxonomy scaffolding.
 
**Data visibility:** Gated entirely by RoleAssignment scope (§3); no role, including OrganizationAdministrator, has visibility beyond its own Organization — this follows directly from Phase 0's org_id-rooted structure, not from any additional rule.
 
**Administrative visibility:** InternalOperator sees structural and operational metadata only, never content, and never through any exception to the boundary (§3).
 
**Prevention of tenant influence on other tenants:** No tenant's Genome, Policy, Evidence, or Decision computation can be affected by another tenant's data, activity, or volume. Decision reproducibility (Phase 2 §8.2) and Work Unit isolation (Phase 4 §7) jointly guarantee this at both the business and execution layers.
 
---
 
## 9. Security Invariants
 
1. Tenant isolation can never be violated, at any layer — domain, access, execution, observability, or audit.
2. Audit history is never rewritten, truncated, or deleted, for any Organization.
3. Decisions remain reproducible given their pinned Genome version, Policy version, and `decision_function_version`, permanently.
4. Every governance action — activation, flagging, suspension, RoleAssignment grant or revoke — remains attributable to a specific actor, without exception.
5. Authorization never expands implicitly: every grant is explicit, inheritance flows one direction only (broad to narrow), and no actor may escalate their own privilege.
6. Evidence is never detached from its originating AnalysisRun; Evidence and Observations are never mutated in place.
7. No privileged operation — including InternalOperator's own Organization-lifecycle actions — bypasses audit.
8. Trust boundaries are always explicit and checked on every crossing; none is assumed safe by proximity, prior success, or actor seniority.
9. InternalOperator's exclusion from tenant-scoped content admits no exception, including for support or incident response.
10. The AI Slop Knowledge Base never contains any tenant's private content, regardless of that content's independent public availability elsewhere.
 
---
 
## 10. Out of Scope
 
Encryption, authentication protocols, OAuth, SSO, MFA, JWT, TLS, databases, APIs, cloud providers, Kubernetes, containers, secrets management technologies, firewalls, SIEM, networking, monitoring products, deployment architecture, programming languages, and frameworks. These are later implementation and infrastructure phases' responsibility, to be built in service of the guarantees this document defines.
 
---
 
## 11. Consistency Check Against Frozen Phase 0–5
 
- No entity, field, or lifecycle state from any prior phase is altered.
- All four items surfaced in the pre-Phase-6 review are resolved as new content in this document (§2, §3, §4), not as corrections to what was already frozen.
- Every "restated" guarantee in this document (tenant isolation, reproducibility, explainability, evidence integrity) already existed structurally in an earlier phase; this document adds no redundant enforcement mechanism, only the security/trust framing those guarantees were always going to need.
 
**No contradiction requiring Phases 0–5 to reopen was found.**
 
---
 
*End of Phase 6 — Security, Trust & Operational Governance Architecture, v1.0. Awaiting your review before this becomes the frozen baseline Phase 7 (Product Experience & Ops) builds against.*