# Brandium — Phase 0: Business Domain Specification
## Companion Document to PRD v1.0

**Status:** v0.2 — **FROZEN** (supersedes v0.1)
**Depends on:** PRD v1.0 (Sections 6, 8–10, 12–13, 19, 24)
**Blocks:** Phase 1 (Brand Genome schema — already aligned, see companion v0.2), Phase 2 (Decision Architecture), Phase 5 (Multi-tenancy enforcement)

---

## Changelog from v0.1

| # | Change | Rationale |
|---|---|---|
| 1 | Added **Decision** as a first-class, versioned entity, separate from Report | Reproducibility (DR-002) applies to the deterministic decision function, not to LLM narration; these must not share one entity |
| 2 | Added **Recommendation** as a first-class entity | Necessary consequence of #3 below — Report cannot be "built from Decision + Evidence + Recommendations" if Recommendations have no entity of their own |
| 3 | **Report** redefined as a persisted, immutable read-model projection (with a mutable review-overlay exception, see §3.15) | Report should not be an independently-computed domain entity; it materializes Decision + Evidence + Recommendation |
| 4 | Replaced `status = active` on Genome/Policy versions with `active_genome_version_id` / `active_policy_version_id` pointers on Brand | Enforces "exactly one active version" *by construction* instead of by convention (Design Principle 1) |
| 5 | Added denormalized `org_id` to every tenant-scoped entity | Concrete mechanism behind DR-003's tenant-isolation double-check; avoids requiring a full parent-chain join to authorize or audit any row |
| 6 | Explicitly documented the six Bounded Contexts | Were implicit in v0.1; now named and given owned responsibilities |
| 7 | Added Report review/flag lifecycle; documented `AnalysisRun.failed` as terminal | Supports PRD's reviewer feedback workflow; closes an unstated ambiguity in the AnalysisRun state machine |

No aggregate root from v0.1 was removed. No invariant was weakened. All changes are additive or structural-strengthening.

---

## 0. Purpose

Unchanged from v0.1: this is a conceptual domain model, not a database schema. Per PRD Section 24, no infrastructure or technology selection occurs before this model is finalized.

---

## 1. Design Principles Governing This Model

1. **Every PRD invariant should be enforceable by construction, not just by convention.** (This principle is what drove changes #1 and #4 above.)
2. **No entity exists without a distinct responsibility** (NFR-008).
3. **Tenant boundary is a single, unambiguous line** (NFR-001, DR-003) — now reinforced at the field level by change #5.
4. **Versioning and immutability are explicit on the entities that need them**, not implied.

---

## 2. Core Entity Hierarchy (Revised)

```
Organization (tenant root)
  └─ Workspace
       └─ Brand
            ├─ active_genome_version_id ──► BrandGenome (versioned, immutable once pointed-to)
            ├─ active_policy_version_id ──► Policy (versioned, immutable once pointed-to)
            ├─ BrandHistory (repository — DR-008 rename)
            └─ Campaign
                 └─ Asset
                      └─ AssetVersion
                           └─ AnalysisRun [pins genome_version_id + policy_version_id — DR-005]
                                ├─ Observation (raw, internal)
                                ├─ Evidence (normalized, user-facing)
                                ├─ Decision (deterministic, versioned scoring output) [NEW]
                                ├─ Recommendation (LLM-narrated, evidence-grounded) [NEW]
                                └─ Report (persisted read model; review/flag lifecycle) [REVISED]

AuditLogEntry — global-append, references any of the above by (type, id)
AISlopKnowledgeBase — global, structurally outside the Organization tree (DR-004)
```

---

## 3. Entity Definitions

### 3.1 Organization
Unchanged. The tenant. Sole unit of billing, provisioning, isolation.

| Field | Notes |
|---|---|
| id | tenant primary key |
| name | |
| status | `active` \| `suspended` |
| created_at | |

### 3.2 Workspace
| Field | Notes |
|---|---|
| id | |
| org_id | FK → Organization *(denormalized tenant key — see §6)* |
| name | |
| created_at | |

### 3.3 User / RoleAssignment
| Entity | Fields |
|---|---|
| User | id, org_id, email, auth_identity_ref |
| RoleAssignment | id, org_id, user_id, workspace_id, role |

Roles unchanged (v1): `BrandAdministrator`, `MarketingManager`, `ContentCreator`, `ExecutiveViewer`.

### 3.4 InternalOperator
Unchanged. No field on this entity references tenant-private data; no org_id-scoped relationship exists on it at all.

### 3.5 Brand — *now carries the version pointers*
| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| workspace_id | FK → Workspace |
| name | |
| status | `active` \| `archived` |
| **active_genome_version_id** | **nullable FK → BrandGenome; null until first Genome is activated** |
| **active_policy_version_id** | **nullable FK → Policy; null until first Policy is activated** |

**Invariant (structural, replaces v0.1's status-based version):** Exactly one active Genome version and exactly one active Policy version can exist per Brand at any time — enforced because each is a single FK field that can point to at most one row. "Active" is no longer a stored per-row status value; it is defined solely as *"is this the row the pointer currently references."*

### 3.6 BrandGenome — versioned, immutable once pointed-to
| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| brand_id | FK → Brand |
| version_number | monotonic per brand |
| status | `draft` → `pending_review` → `{rejected, superseded}` *(no "active" value — see §3.5)* |
| compiled_from | references to source BrandHistory assets used in compilation |
| activated_by | **required, non-null the moment this version becomes the target of `Brand.active_genome_version_id`** — the DR-006 human-review gate, now enforced structurally |
| activated_at | |

**Activation operation (atomic, three steps):**
1. Set this version's `activated_by` / `activated_at`.
2. Update `Brand.active_genome_version_id` to point to this version.
3. Update the *previously*-pointed version's `status` to `superseded`.

There is no window in which two versions are simultaneously "active." Once pointed-to, a version's Category/Component/Assertion content (Phase 1) is immutable; any edit produces a new `draft`.

### 3.7 Policy — versioned, same pattern as Genome
| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| brand_id | FK → Brand |
| version_number | |
| status | `draft` → `{rejected, superseded}` *(no "active" value; see §3.5)* |
| rules | payload — shape deferred to Phase 2 |

Same atomic activation mechanism as Genome, pointed to via `Brand.active_policy_version_id`.

**Still-open question (unchanged from v0.1, not resolved by this pass):** whether Policy activation requires human sign-off the way Genome activation does. Carried forward to §8.

### 3.8 BrandHistory *(DR-008 rename — unchanged structurally)*
| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| brand_id | FK → Brand |
| source_type | `campaign` \| `ad` \| `social` \| `video` *(Phase 1 extends this enum additively — see Phase 1 v0.2 §0)* |
| storage_ref | |
| ingested_at | |

### 3.9 Campaign
| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| brand_id | FK → Brand |
| name | |
| status | `active` \| `archived` |

### 3.10 Asset / AssetVersion
| Entity | Fields |
|---|---|
| Asset | id, org_id, campaign_id, name, modality (`text`\|`image`\|`video`) |
| AssetVersion | id, org_id, asset_id, version_number, uploaded_by, uploaded_at, storage_ref, content_hash |

**Invariant unchanged:** AssetVersion is append-only.

### 3.11 AnalysisRun — pins Genome + Policy version (DR-005 mechanism)
| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| asset_version_id | FK → AssetVersion |
| genome_version_id | set at creation, never updated |
| policy_version_id | set at creation, never updated |
| status | `queued` → `running` → `{complete, failed}` |
| started_at / completed_at | |

**State machine clarification (fix #7):** `complete` and `failed` are both **terminal states**. No transition exists out of either. A retry after failure creates a **new** AnalysisRun row referencing the same AssetVersion — it does not reopen or mutate the failed row. This preserves a full, honest audit record of every attempt, consistent with the platform's append-only pattern elsewhere (AssetVersion, AuditLogEntry).

### 3.12 Observation — raw, internal
| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| analysis_run_id | FK → AnalysisRun |
| worker_type | e.g. `tone`, `voice`, `visual_style`, `logo_usage` |
| raw_output | |
| confidence | |

### 3.13 Evidence — normalized, user-facing
| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| analysis_run_id | FK → AnalysisRun |
| evidence_type | |
| description | |
| confidence | calibrated (DR-002) |
| source_observation_ids | traceability back to raw Observations |

### 3.14 Decision — *new, deterministic, versioned* [NEW ENTITY]
The deterministic scoring/verdict output. Exists precisely so reproducibility (DR-002) applies to a clean, isolated entity rather than being entangled with LLM-narrated content.

| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| analysis_run_id | FK → AnalysisRun (1:1 — one deterministic decision per run) |
| score | |
| verdict | |
| **decision_function_version** | **which version of the BDI scoring formula (Phase 2) produced this — without this, a future formula change would silently break reproducibility even though genome/policy stay pinned** |
| computed_at | |

**Invariant:** Given the same Evidence set, the same `genome_version_id`/`policy_version_id` (inherited from AnalysisRun), and the same `decision_function_version`, recomputing a Decision must yield an identical score and verdict — this is the literal, checkable form of NFR-004.

The specific weighting/aggregation formula that consumes Evidence to produce a score remains a Known Gap owned by Phase 2 (PRD Section 18); this entity defines only its *shape and reproducibility contract*, not its math.

### 3.15 Recommendation — *new, LLM-narrated, evidence-grounded* [NEW ENTITY]
Necessary counterpart to Decision — the non-deterministic, narrated half of what a Report is built from.

| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| analysis_run_id | FK → AnalysisRun (1:N — a run may yield multiple distinct recommendations) |
| related_evidence_ids | grounding — a Recommendation must reference the specific Evidence it responds to (no ungrounded recommendations, per PRD §12) |
| text | LLM-narrated, schema-constrained (not free generation — PRD §12/13) |
| priority | |
| generated_at | |

### 3.16 Report — *redefined as a persisted read model* [REVISED]
No longer an independently-computed entity. It is a **materialized projection** built from exactly one Decision, its associated Evidence, and its associated Recommendations — all reachable via the shared `analysis_run_id`.

| Field | Notes |
|---|---|
| id | |
| org_id | denormalized |
| analysis_run_id | FK → AnalysisRun (1:1) |
| decision_id | FK → Decision — explicit reference, not re-derived each read |
| generated_at | |
| **review_status** | **`unreviewed` \| `approved` \| `flagged`** |
| **reviewed_by** | **nullable — set when a reviewer acts on the report** |
| **reviewed_at** | |
| **flag_reason** | **nullable — required when `review_status = flagged`** |

**Immutability exception, stated explicitly:** the projected content of a Report (its decision/evidence/recommendation snapshot, reachable via `analysis_run_id`) is immutable once generated — consistent with the rest of the model. The four review fields above are the **one deliberate exception**: they form a mutable *workflow overlay* on top of an otherwise-immutable record, not a re-computation of the underlying decision. This is a narrow, explicit carve-out, not a general precedent for mutability elsewhere in this model.

### 3.17 AuditLogEntry — global, append-only
Unchanged from v0.1.

| Field | Notes |
|---|---|
| id | |
| org_id | for visibility scoping (not an isolation exemption) |
| actor_id | User or InternalOperator |
| action_type | |
| target_entity / target_id | |
| timestamp | |

### 3.18 AISlopKnowledgeBase — global, structurally outside the Organization tree
Unchanged from v0.1 (DR-004). No field on this entity, and no field on any tenant entity, establishes a reference into or out of it.

| Field | Notes |
|---|---|
| id | |
| source_type | `public` \| `synthetic` |
| content_ref | |

---

## 4. Relationship & Cardinality Summary (Revised)

| Parent | Child | Cardinality |
|---|---|---|
| Organization | Workspace | 1:N |
| Workspace | Brand | 1:N |
| Brand | BrandGenome | 1:N (pointer references exactly one as active) |
| Brand | Policy | 1:N (pointer references exactly one as active) |
| Brand | BrandHistory | 1:N |
| Brand | Campaign | 1:N |
| Campaign | Asset | 1:N |
| Asset | AssetVersion | 1:N (append-only) |
| AssetVersion | AnalysisRun | 1:N (retry creates a new run, never mutates one) |
| AnalysisRun | Observation | 1:N |
| AnalysisRun | Evidence | 1:N |
| **AnalysisRun** | **Decision** | **1:1** |
| **AnalysisRun** | **Recommendation** | **1:N** |
| AnalysisRun | Report | 1:1 |

---

## 5. Lifecycle State Machines (Revised)

**BrandGenome:** `draft → pending_review → {rejected}`; pointed-to version has no separate "active" status — becoming pointed-to is the activation event itself; a formerly-pointed version transitions to `superseded` when a new version is pointed to.

**Policy:** `draft → {rejected}`; same pointer-based activation/supersession pattern as Genome.

**Campaign / Asset:** `active → archived` (unchanged).

**AnalysisRun:** `queued → running → {complete, failed}` — **`complete` and `failed` are both terminal; no outgoing transitions from either.**

**Report (new — review overlay only, does not affect the underlying Decision):** `unreviewed → {approved, flagged}`. This lifecycle governs the review-overlay fields only; it has no path back to `queued`/`running`/`complete` on the parent AnalysisRun, and does not trigger re-computation of the Decision.

---

## 6. Tenant Isolation Boundary (Reinforced)

**Tenant-scoped, now all carrying denormalized `org_id`:** Workspace, User, RoleAssignment, Brand, BrandGenome, Policy, BrandHistory, Campaign, Asset, AssetVersion, AnalysisRun, Observation, Evidence, **Decision, Recommendation**, Report.

**Invariant:** every tenant-scoped row's `org_id` must equal the `org_id` of its ultimate Organization ancestor. This is checked at write time (mechanism is a Phase 4/5 implementation concern; the invariant itself is committed here). This denormalization is the concrete, field-level mechanism behind DR-003's "application-layer verification step" — every tenant-scoped table can be authorized or audited by a direct `org_id` check, without traversing the full parent chain.

**Global (unchanged):** AISlopKnowledgeBase; the AuditLogEntry table itself (individual entries carry `org_id` for visibility scoping only).

---

## 7. Bounded Contexts (New — Explicit)

| # | Context | Owns | Responsibility |
|---|---|---|---|
| 1 | **Identity & Access** | Organization, Workspace, User, RoleAssignment, InternalOperator | Authentication, authorization scoping, tenant/workspace membership |
| 2 | **Brand Governance** | Brand, BrandGenome, Policy, BrandHistory | Brand identity definition, Genome compilation/activation, Policy authoring/activation |
| 3 | **Campaign & Asset Management** | Campaign, Asset, AssetVersion | Content lifecycle tracking, versioned uploads, campaign grouping |
| 4 | **Analysis & Decision** | AnalysisRun, Observation, Evidence, Decision, Recommendation | Executing analysis; producing evidence; computing deterministic decisions; generating evidence-grounded recommendations |
| 5 | **Reporting** | Report | Presenting a persisted, reviewable projection of Decision+Evidence+Recommendation; owns the review/flag lifecycle — deliberately separate from Analysis & Decision because "compute a verdict" and "manage human review of that verdict" are distinct responsibilities |
| 6 | **Platform Governance** | AuditLogEntry, AISlopKnowledgeBase | Cross-cutting global concerns: audit trail, shared generic-AI-pattern corpus — structurally isolated from all tenant contexts |

Each context maps to what will eventually be an independently-ownable engineering surface; no context spans a tenant-isolation boundary, and no entity appears in two contexts.

---

## 8. Traceability to PRD (Revised)

| Domain Model Element | PRD Reference |
|---|---|
| Organization as sole isolation boundary | NFR-001, DR-003 |
| Denormalized `org_id` on every tenant-scoped entity | DR-003 (concrete field-level mechanism) |
| AnalysisRun immutable version-pinning | DR-005 |
| Decision's `decision_function_version` | DR-002, NFR-004 (reproducibility of the deterministic function specifically) |
| BrandGenome/Policy pointer-based activation | DR-006, BR-007 (structural enforcement, not conventional) |
| Observation → Evidence → Decision → Recommendation → Report chain | PRD Glossary, DR-002, Section 12 |
| BrandHistory vs. Evidence naming | DR-008 |
| AISlopKnowledgeBase structural isolation | DR-004 |
| Report review/flag lifecycle | Section 12 (reviewer feedback workflow) |
| AnalysisRun terminal states | Section 11.2 workflow completeness |

---

## 9. Open Design Questions (Carried Forward, Unresolved by This Pass)

1. **Policy scope:** brand-level only vs. org-level default + brand override. Still recommend deferring org-level templates to Future Scope.
2. **Policy activation review:** still unresolved whether Policy activation needs a human sign-off gate equivalent to Genome's. Not blocking for Phase 2, since `policy_version_id` pinning on AnalysisRun already guarantees reproducibility regardless of the answer — but it remains a real governance gap worth closing before production launch.
3. **Shared brands across workspaces:** Brand↔Workspace is still 1:N. Revisit before Phase 5 RBAC is built on this assumption if a co-branded/matrixed scenario becomes real.
4. **BrandHistory query scope:** still Genome-compilation-input only, not used at analysis time. Confirmed unchanged.

---

*End of Phase 0 — Business Domain Specification, v0.2. FROZEN. This is the baseline Phase 1 (companion v0.2) and Phase 2 build against.*