# Brandium  — Phase 5: Enterprise SaaS Architecture Specification
 
**Status:** v1.0 — Draft for review
**Depends on:** PRD v1.0; Phase 0 v0.2 FROZEN (+ RoleAssignment scope addendum); Phase 1 v0.2 FROZEN; Phase 2 v1.0 FROZEN (+ addenda); Phase 3 v1.1 FROZEN; Phase 4 v1.0 FROZEN
**Scope:** Conceptual enterprise SaaS architecture only. No databases, APIs, programming languages, frameworks, cloud providers, networking, authentication protocols, containers, orchestration platforms, message queues, storage technologies, monitoring tools, or deployment architecture are discussed or implied anywhere in this document.
**Blocks:** Phase 6 (Security & Governance hardening — formal STRIDE threat model, secrets management, audit logging hardening) and Phase 7 (Product Experience & Ops).
 
---
 
## 0. Relationship to Frozen Phase 0–4
 
This document introduces two new conceptual constructs, both additive and both directly required by the sections below:
 
- **Membership** — the lifecycle of a User's relationship to an Organization (§2, §9), distinct from RoleAssignment, which governs what that User can *do* once their membership is active.
- **OrganizationAdministrator** — a new Role value, scoped at the `organization` tier (enabled by the pre-Phase-5 RoleAssignment addendum), for tenant-side administration that has no business reaching into any single Brand's content (§2, §7).
 
It also elaborates Organization's `status` field (Phase 0 §3.1: `active | suspended`) into a fuller lifecycle (§9) — an additive widening of the same field's meaning, not a contradiction of it.
 
Nothing else in Phase 0–4 is altered. AnalysisRun's lifecycle, Genome/Policy lifecycles, Decision reproducibility, and Work Unit isolation are all referenced here exactly as frozen.
 
---
 
## 1. Tenant Architecture
 
**Organization isolation model:** Organization remains the sole tenant boundary (Phase 0 §3.1, NFR-001). Every tenant-scoped entity traces back to exactly one Organization, directly or transitively — restated here as the architecture's supreme invariant because everything in this document operates inside that boundary.
 
**Tenant boundaries:** Unchanged from Phase 0 §6 — Workspace, User, Membership, Brand, BrandGenome, Policy, BrandHistory, Campaign, Asset, AssetVersion, AnalysisRun, Observation, Evidence, Decision, Report, and every RoleAssignment are all tenant-scoped.
 
**Shared platform vs. tenant-owned resources:** Two distinct kinds of "shared" exist, and conflating them would be a real error:
- The **AI Slop Knowledge Base** (DR-004) is genuinely shared *content* — a cross-tenant reference corpus, structurally outside the Organization tree.
- The **Genome Category/Component taxonomy** (Phase 1 §2, §9) is shared *scaffolding* — a platform-defined structure every tenant's Genome is shaped by — but the Assertions filling that scaffolding are exclusively tenant-owned content. The taxonomy is shared shape; nothing shared is ever shared substance.
 
**Cross-tenant isolation guarantees:** Generalizing DR-003 across every layer now defined: no tenant-scoped read or write may ever resolve using another tenant's identifier, whether at the domain layer (Phase 0), the execution layer (Phase 4 §7's per-AnalysisRun isolation), or the access layer (§2 below). This is one guarantee restated consistently at three layers, not three separate guarantees.
 
**Tenant lifecycle:** `provisioned → active → suspended → offboarded` (offboarded is terminal). This is an additive elaboration of Phase 0's `active | suspended` field (§0). Suspension halts new Membership invitations, new AnalysisRuns, and new Genome/Policy activations — it never hides, deletes, or reinterprets historical data; suspension freezes forward progress only. Offboarding is a deliberate, audited terminal transition, not silent deletion — any data retention or erasure mechanism is explicitly a Phase 6/7 concern, out of scope here.
 
---
 
## 2. Identity and Access Architecture
 
**Users:** Tenant-side, per Phase 0 §3.3 — one Organization per User, unchanged.
 
**Organizations:** Per §1.
 
**Membership (new):** The record of a User's relationship to an Organization, with its own lifecycle: `invited → active → suspended → removed`. Membership is deliberately separate from RoleAssignment — Membership answers "is this person part of this Organization at all," RoleAssignment answers "what can they do, and where." Removing a Membership immediately revokes every RoleAssignment that User held at that Organization (§9), but never retroactively alters historical attributions (an activated_by or flagged_by reference to a since-removed User remains a permanent historical fact, consistent with how Phase 0 already treats such fields).
 
**Roles:** BrandAdministrator, MarketingManager, ContentCreator, ExecutiveViewer (Phase 0 §3.3), **OrganizationAdministrator (new, §0)**, and InternalOperator (Phase 0 §3.4, structurally separate from all tenant roles).
 
**Permissions:** Deliberately not a separate entity. A Role implies a fixed permission set; RoleAssignment's scope tier (organization/workspace/brand, per the pre-Phase-5 addendum) determines *where* that permission set applies. Introducing an independent Permission entity on top of this would be exactly the kind of unnecessary abstraction the architecture has avoided throughout.
 
**Principle of least privilege:** Directly enabled by the RoleAssignment scope addendum — always assign the narrowest tier (`brand` over `workspace`, `workspace` over `organization`) that satisfies the actual need.
 
**Administrative delegation:** Achieved entirely through RoleAssignment — granting the same Role to an additional User at the same or narrower scope. No separate delegation mechanism is needed; a second RoleAssignment *is* a delegation.
 
**Separation of duties:** Two independent mechanisms, operating at different layers:
- **Structural:** InternalOperator's exclusion from all tenant-scoped data (Phase 0 §3.4) — no RoleAssignment, of any scope tier, can ever grant an InternalOperator tenant content access. This is a boundary between platform staff and customer data, not a configurable policy.
- **Procedural (optional, enterprise-configurable):** a maker-checker rule for Genome/Policy activation, defined in §4 — implemented entirely with fields Phase 0/1 already define, requiring no schema change.
 
---
 
## 3. Workspace and Collaboration
 
**Brand workspaces:** Workspace remains the RBAC/administrative container (Phase 0 §3.2); the default-workspace-per-Organization behavior for single-brand tenants is unchanged.
 
**Team collaboration:** Multiple Users may hold roles scoped to the same Brand or Workspace concurrently. This is safe by construction: Genome and Policy edits always produce a new draft version rather than mutating shared state (Phase 0 §3.6/§3.7), so concurrent editing never risks one person's change silently overwriting another's — it produces two candidate drafts, and Consolidation (Phase 1 §5) or human review resolves any resulting conflict explicitly, exactly as it already does for conflicting source material.
 
**Review workflows:** The Marketing Manager persona reviews Reports (PRD §11.4); a flagged Report feeds the existing Mediated Path (Phase 2 §9) rather than any automatic mechanism.
 
**Human approval responsibilities — two distinct authorities, never conflated:**
- **Brand Administrator** approves Genome/Policy activation (governs what the platform believes about the brand and how it scores).
- **Marketing Manager** approves publication (governs what actually goes out the door).
One role's approval is never substitutable for the other's.
 
**Shared ownership:** A Brand's Genome and Policy are owned by the Brand itself, not by an individual User — any User holding an appropriately-scoped BrandAdministrator RoleAssignment may act on it. Accountability is tracked through `activated_by` and equivalent authored-by fields (already present, Phase 0 §3.6/§3.7), not through an exclusive-ownership field, which would be redundant with what those fields already establish.
 
**Concurrent work:** AssetVersion's append-only nature (Phase 0 §3.10) means concurrent uploads to the same Asset never conflict at all — each simply becomes its own version, with no merge or locking concept required.
 
---
 
## 4. Governance Architecture
 
**Policy ownership / Genome ownership:** Both remain Brand-scoped (Phase 0 §3.6/§3.7); unchanged.
 
**Version publishing:** "Publishing" is simply activation, in both cases — no new concept, no new terminology.
 
**Approval workflows:**
- Genome activation retains its mandatory human sign-off (DR-006) — non-negotiable, unchanged.
- Policy activation's review requirement was left open by Phase 2 §11 (flagged, not resolved). Phase 5 resolves it as an **enterprise-configurable option**, not a universal requirement: a tenant may enable a maker-checker rule requiring that the User who activates a Policy (or, optionally, a Genome) differ from the User who last edited its draft. This is checkable using fields that already exist (`activated_by`, and the draft's most recent editor) — no new field, no schema change, purely a workflow rule some tenants may opt into and others may not.
 
**Draft vs. active configurations:** Unchanged from Phase 0/1 — restated here only because Phase 5's audience needs the enterprise framing, not because anything about it changes.
 
**Administrative responsibilities:** Brand Administrator owns this category end to end, at whatever scope (organization-wide-by-convention-only, workspace, or brand) their RoleAssignment grants.
 
**Enterprise governance boundaries:** A RoleAssignment scoped to one Brand must never permit activating a Genome or Policy for a different Brand — this is the direct, concrete payoff of the pre-Phase-5 RoleAssignment addendum, and is stated here as a governance boundary rather than merely an access-control detail, because a Genome/Policy activation is a governance act, not just a data write.
 
---
 
## 5. Workflow Architecture
 
None of the following redefines AnalysisRun (Phase 0/3/4) — it describes what surrounds it.
 
- **Asset submission:** A User holding ContentCreator (or broader) scope uploads an AssetVersion; this triggers the existing Phase 3/4 pipeline unchanged.
- **Analysis lifecycle:** Referenced, not redefined — `queued → running → {complete, failed}` exactly as frozen.
- **Human review lifecycle:** A completed AnalysisRun's Report is reviewed by a Marketing Manager–scoped User, who approves for publication or returns it for revision (PRD §11.4), optionally flagging it (Phase 2 §9) for future governance attention.
- **Recommendation lifecycle:** A Recommendation (Phase 2 §6) is acted on by a ContentCreator-scoped User, producing a new AssetVersion, which enters a new AnalysisRun (PRD §11.3) — the same campaign-improvement loop already specified, now named as an enterprise workflow.
- **Genome evolution:** Typically initiated by a Brand Administrator, sometimes prompted by a pattern of flagged Reports (Phase 2 §9.2's Mediated Path) — a new draft enters compilation/validation (Phase 1 §5/§10) and then activation (DR-006, optionally with the §4 maker-checker rule).
- **Policy evolution:** Same shape, same actor, same optional maker-checker overlay.
- **Organization administration:** A User holding OrganizationAdministrator scope manages Membership (inviting, suspending, removing Users) and Organization-level status — and, critically, has no implied access to any Brand's Genome, Evidence, or Report content unless separately granted a content-facing role at Workspace or Brand scope. Administrative scope and content scope are always distinct grants.
 
---
 
## 6. Security Architecture (Conceptual)
 
**Tenant isolation:** Restated per §1 — the platform's supreme invariant, checked at every layer.
 
**Authorization boundaries:** Every tenant-scoped action must be checked against the acting User's RoleAssignment at its actual scope tier — a Workspace-scoped grant does not imply Organization-scope, and a Brand-scoped grant does not imply access to sibling Brands in the same Workspace. This is the enforcement mechanism the pre-Phase-5 addendum exists to make possible.
 
**Audit responsibilities:** Every RoleAssignment grant or revoke, every Membership lifecycle transition, every Genome/Policy activation, every Report flag, and every Organization lifecycle transition produces an AuditLogEntry (Phase 0 §3.15) — no exceptions.
 
**Administrative accountability:** InternalOperator actions (e.g., suspending an Organization for a platform-level reason) are audited identically to tenant-side actions, but distinctly tagged by actor type — so platform-staff actions remain separately reviewable from tenant self-service actions, without special-casing the audit mechanism itself.
 
**Data ownership:** The tenant owns all Brand-scoped knowledge and content, without exception. BrandGuard the platform owns only the AI Slop Knowledge Base and the Genome taxonomy scaffolding (§1) — never a tenant's Assertions, Evidence, Decisions, or Reports.
 
**Secure default behavior:** The default RoleAssignment scope tier for any new grant should always be the narrowest tier that satisfies the request (§2) — narrow-by-default is a stated design principle here, not an incidental convenience.
 
---
 
## 7. Enterprise Administration
 
| Responsibility | Role | Belongs to |
|---|---|---|
| Manage Membership (invite/suspend/remove Users) | **OrganizationAdministrator** | Customer |
| Own Genome/Policy for scoped Brand(s) | **BrandAdministrator** | Customer |
| Review Reports, approve publication, flag for governance attention | **MarketingManager** (Reviewer) | Customer |
| Upload/revise Assets, view campaign trend data | **ContentCreator / ExecutiveViewer** (Analyst) | Customer |
| Tenant onboarding, platform health, Organization lifecycle transitions at the platform's own discretion | **InternalOperator** (Platform Operator) | BrandGuard |
 
**The customer/platform split, stated plainly:** everything under an Organization — its Members, Brands, Genomes, Policies, content, and Reports — is customer-owned and customer-managed. BrandGuard's own operators act only on cross-tenant platform health and Organization-level lifecycle transitions (never Brand content), and are structurally barred from the rest by Phase 0 §3.4, not merely instructed to stay out.
 
---
 
## 8. Compliance and Audit Architecture
 
**Immutable audit philosophy:** Unchanged from NFR-003 and Phase 0 §3.15 — now explicitly extended to cover RoleAssignment and Membership lifecycle events, since those didn't exist as concepts when Phase 0 first specified AuditLogEntry's scope.
 
**Administrative traceability:** Every privilege grant, revoke, and scope change is traceable to a specific actor and timestamp — no exceptions, no privileged path around this for OrganizationAdministrator or InternalOperator actors.
 
**Configuration history:** Genome and Policy version chains (draft → active → superseded, Phase 0 §3.6/§3.7) already constitute a complete, append-only configuration history. No additional mechanism is introduced — this is a case where Phase 5's requirement is already satisfied by Phase 0's existing design.
 
**Review accountability:** Report's `review_flag`/`flagged_by` (Phase 0/2) already provides this; restated here as satisfying the enterprise compliance requirement, not extended.
 
**Decision accountability:** The Decision entity's `decision_function_version` plus its pinned `genome_version_id`/`policy_version_id` (Phase 0 §3.14, DR-005) already gives a complete, reconstructable accountability chain — again, already satisfied, not extended.
 
**Governance transparency:** Any tenant User holding an appropriately-scoped role may view the full audit trail for their own Organization. InternalOperator's visibility is limited to the fact that an audited event occurred (for platform-health purposes) — never its substantive content — consistent with the same content/administration boundary drawn in §7.
 
---
 
## 9. Lifecycle Architecture
 
| Entity | Lifecycle | Interaction Notes |
|---|---|---|
| **Organization** | `provisioned → active → suspended → offboarded` | Suspension halts new Memberships, AnalysisRuns, and Genome/Policy activations; never hides history |
| **User** | (governed by Membership, below — User itself has no independent lifecycle beyond existing) | |
| **Membership** | `invited → active → suspended → removed` | Removal cascades to revoke every RoleAssignment that User held at that Organization, immediately; never alters historical attributions already recorded elsewhere |
| **Brand Genome** | `draft → pending_review → active → superseded` (unchanged) | Optional maker-checker overlay per §4 |
| **Brand Policy** | `draft → active → superseded` (unchanged) | Optional maker-checker overlay per §4 |
| **Asset / AssetVersion** | No lifecycle on Asset; AssetVersion append-only (unchanged) | Concurrent uploads never conflict (§3) |
| **AnalysisRun** | `queued → running → {complete, failed}` (unchanged, Phase 0/4) | Referenced only, never redefined here |
| **Report** | Generated (immutable) → optionally `flagged` (unchanged, Phase 0/2) | Only lifecycle Report has; it is a read model, not a stateful process |
 
**Cross-entity interaction, stated once, generally:** every lifecycle above shares one rule — a transition may halt *future* activity, but never retroactively erases or reinterprets a historical fact already recorded elsewhere (a superseded Genome remains exactly what it was; a removed Member's past `activated_by` reference remains exactly what it was; a suspended Organization's past Decisions remain exactly what they were). This single rule is why none of these lifecycles need bespoke interaction logic with one another — they're all instances of the same principle already established by DR-005's version-pinning philosophy.
 
---
 
## 10. Platform Invariants
 
1. **Tenant isolation:** no tenant-scoped operation, at any layer (domain, execution, access), may ever resolve using another tenant's identifier.
2. **Authorization correctness:** a RoleAssignment is always evaluated at its actual scope tier; no implicit escalation from Brand → Workspace → Organization ever occurs.
3. **Version consistency:** DR-005 pinning and `decision_function_version` (Phase 2 §8) hold across every Organization, without exception, unaffected by anything in this document.
4. **Governance integrity:** no Genome or Policy reaches `active` without satisfying its required validation and review gate (Phase 1 §10, DR-006, plus any enterprise-configured maker-checker overlay from §4).
5. **Audit completeness:** every privilege change, membership transition, and governance action is logged immutably, without exception, for every Organization.
6. **Reproducibility preservation:** nothing in this multi-tenant, collaborative layer may introduce non-determinism into Decision computation (Phase 2 §8.2) — concurrent collaboration always produces new draft versions, never mutates a pinned one.
7. **Workflow integrity:** a Report's review lifecycle and a Genome/Policy's governance lifecycle are always mediated by an explicit human action, never an automatic one (Phase 2 §9.1, restated at enterprise scale).
 
---
 
## 11. Out of Scope
 
Databases, APIs, programming languages, frameworks, cloud providers, networking, authentication protocols, containers, orchestration platforms, message queues, storage technologies, monitoring tools, and deployment architecture. These are Phase 6/7 and later engineering decisions, to be made in service of the guarantees this document defines — not decided by it.
 
---
 
## 12. Consistency Check Against Frozen Phase 0–4
 
- No AnalysisRun, Genome, or Policy lifecycle state is altered.
- Membership and OrganizationAdministrator are additive, not replacements for anything frozen.
- The Organization lifecycle elaboration widens the meaning of an existing field; it does not repurpose it.
- Every "compliance" requirement in §8 that Phase 0 already satisfies is stated as satisfied, not re-implemented — avoiding the redundant-mechanism trap this architecture has avoided at every prior phase.
 
**No contradiction requiring Phase 0–4 to reopen was found beyond the one addendum applied before this document began.**
 
---
 
*End of Phase 5 — Enterprise SaaS Architecture Specification, v1.0. Awaiting your review before this becomes the frozen baseline Phase 6 (Security & Governance) builds against.*