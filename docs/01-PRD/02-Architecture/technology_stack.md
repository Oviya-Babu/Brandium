# BrandGuard AI — Technology Stack Selection Document

**Status:** v1.1 — Official technology selection, pre-implementation (amended)
**Prepared by:** Principal Solutions Architect
**Grounded in:** PRD v1.0 and the frozen conceptual architecture, Phases 0–7
**Guiding constraint:** every recommendation below is justified against a specific requirement the architecture already established — not against general popularity. Where a more powerful or fashionable technology was considered and rejected for v1, that reasoning is stated explicitly rather than left implicit.

### Amendment Log

| Version | Change | Rationale |
|---|---|---|
| v1.0 | Baseline: pgvector (vector store), Voyage AI (embeddings), Claude/Anthropic API (LLM) | Original v1 selection |
| v1.1 | Vector store changed pgvector → **Qdrant**. Embeddings changed Voyage AI (hosted) → **BAAI bge-m3, self-hosted locally**. LLM provider changed Claude/Anthropic API → **Ollama (Qwen 3 8B Instruct) as primary, self-hosted; Groq API as an optional secondary provider, scoped exclusively to advanced narrative generation**. | Explicit human-architect decision (see §6, §11, §14, §15): move the platform's AI/vector surface to a self-hosted-first posture, eliminating the hosted-embedding dependency and making the primary LLM path self-hosted. This is an approved deviation from the v1.0 baseline, made deliberately by the human architect — not a Claude Code judgment call. The Brand Decision Intelligence Engine's determinism guarantee (INV-02) is unaffected: this change is scoped entirely to evidence-extraction/narration LLM calls and vector storage, never to the deterministic Decision function itself, which never calls an LLM (INV-01, §5.1 of CLAUDE.md). |

---

## Summary Table

| # | Area | Selected Technology |
|---|---|---|
| 1 | Frontend | Next.js (React + TypeScript) |
| 2 | Backend | Python, modular monolith |
| 3 | API Framework | FastAPI |
| 4 | Authentication & Authorization | Auth0 (authN) + custom RBAC scope-tier service (authZ) |
| 5 | Relational Database | PostgreSQL |
| 6 | Vector Database | Qdrant (dedicated vector database, collection-per-tenant) |
| 7 | Object Storage | MinIO (local) / Amazon S3 (cloud) |
| 8 | Cache | Redis |
| 9 | Background Job Processing | Celery + Redis |
| 10 | AI Worker Execution | Celery, dedicated queues per worker type |
| 11 | AI Frameworks/Libraries | Ollama Python client + Groq SDK (optional) + Pydantic-based structured output (no agent framework) |
| 12 | Document Processing | PyMuPDF + python-docx |
| 13 | Image Processing | Pillow + OpenCV + ffmpeg |
| 14 | Embedding Models | BAAI bge-m3 (self-hosted, served locally via Ollama or a dedicated local inference service) |
| 15 | LLM Integration Layer | Ollama (Qwen 3 8B Instruct) — primary, self-hosted; Groq API — optional secondary, narrative generation only; thin provider-agnostic wrapper |
| 16 | Configuration Management | Pydantic Settings + environment variables |
| 17 | Secrets Management | AWS Secrets Manager (cloud) / `.env` (local) |
| 18 | Logging | structlog, structured JSON to stdout |
| 19 | Monitoring & Observability | OpenTelemetry + Prometheus + Grafana |
| 20 | Audit Logging | Dedicated append-only PostgreSQL table, DB-enforced immutability |
| 21 | File Storage (transient) | Container-local ephemeral disk, cleaned per Work Unit |
| 22 | Search | PostgreSQL full-text search (`tsvector`) |
| 23 | Containerization | Docker |
| 24 | Local Development Environment | Docker Compose |
| 25 | Deployment | AWS ECS Fargate |
| 26 | CI/CD | GitHub Actions |
| 27 | Testing Frameworks | pytest + Hypothesis + Playwright |
| 28 | Security Tooling | Bandit, Semgrep, gitleaks, Dependabot/pip-audit |
| 29 | Infrastructure as Code | Terraform |
| 30 | Recommended Development Tools | Poetry, Ruff, mypy, pre-commit, VS Code |

---

## 1. Frontend

**Selected:** Next.js (React + TypeScript)

**Why it fits BrandGuard:** Phase 5/7's role-appropriate views (Brand Administrator, Marketing Manager, ExecutiveViewer, OrganizationAdministrator all seeing different surfaces of the same data) map naturally onto a component-based framework with server-side data fetching close to the RoleAssignment check. Next.js's server components let authorization checks happen server-side before any Genome/Evidence content reaches the browser, rather than hiding UI elements client-side after the fact — a meaningfully more secure default for enterprise data.

**Advantages:** Mature ecosystem, large hiring pool, built-in routing/SSR/API-route conventions reduce early scaffolding, TypeScript gives the frontend the same type safety Pydantic gives the backend (Evidence/Decision shapes can be shared as types).

**Trade-offs:** Heavier than a plain SPA for what is, at v1, a moderately complex dashboard — some of Next.js's capability (SSR, edge rendering) won't be exercised immediately.

**Alternatives considered:** A Vite + React SPA is simpler to reason about for a pure client app, but loses the server-side authorization-before-render benefit; rejected for that reason, not popularity.

---

## 2. Backend

**Selected:** Python, structured as a modular monolith aligned to the six Bounded Contexts (Identity & Access, Brand Governance, Content & Campaign, Analysis & Decision, Reporting, Audit)

**Why it fits BrandGuard:** Nearly every AI-adjacent capability the architecture requires — document parsing, image/video processing, embedding calls, LLM calls — has its best-supported libraries in Python. A single language across the API, the Decision Engine, and the AI Pipeline avoids a costly serialization boundary between "the business logic" and "the AI logic," which would otherwise become its own source of drift.

**Advantages:** One language for the whole backend; the Bounded Context structure (Phase 0's review) maps directly onto Python packages/modules, so the eventual split into separate services (if ever needed) is a matter of extracting an existing module, not a rewrite.

**Trade-offs:** Python's raw throughput is lower than compiled alternatives; mitigated because the Decision Engine's computation (Phase 2) is simple arithmetic over small aggregation trees, not a performance-critical hot path — the actual heavy lifting (model inference) happens over the network via API calls regardless of backend language.

**Alternatives considered:** Node.js/TypeScript end-to-end (one language with the frontend) was considered; rejected because it would fragment the AI/document/image ecosystem across two runtimes for no architectural benefit.

---

## 3. API Framework

**Selected:** FastAPI

**Why it fits BrandGuard:** Phase 0's Architecture Readiness assumption ("API-first; UI is a client of the same API surface") and Phase 7 §2's symmetry principle both require a single, well-typed capability surface. FastAPI's native Pydantic integration means the same models used internally for Evidence, Decision, and Genome Assertion shapes double as request/response validation and auto-generated OpenAPI documentation — the API contract and the domain model are the same artifact, not two things kept in sync by hand.

**Advantages:** Async-native (useful for I/O-bound LLM/embedding calls), automatic OpenAPI docs satisfy part of Phase 7's "symmetric capability surface" requirement for free, strong typing catches schema drift early.

**Trade-offs:** Younger ecosystem than Django REST Framework for things like built-in admin panels — not needed here, since RoleAssignment-scoped views are custom by design anyway.

**Alternatives considered:** Django REST Framework offers more batteries-included tooling (admin, ORM) but its synchronous-first ORM is a worse fit for the I/O-bound AI pipeline calls; rejected for that reason.

---

## 4. Authentication & Authorization

**Selected:** Auth0 for authentication; a custom RBAC evaluation service, built directly against Phase 0/5/6's RoleAssignment model, for authorization.

**Why it fits BrandGuard:** These are deliberately two different problems. Authentication (who is this person) is a solved, security-critical problem best not reinvented — Auth0 handles password/session/MFA and gives a clean path to PRD §5.3's future Enterprise SSO without a rewrite. Authorization (what can this person do, at what scope) is *not* a generic problem here — it's the three-tier organization/workspace/brand scope model Phase 0's addendum defined, plus the Membership-status precondition and self-escalation prevention Phase 6 added. No off-the-shelf authorization product models this domain-specific shape out of the box; building it as an explicit service function directly against the frozen RoleAssignment entity keeps the enforcement logic exactly as auditable as Phase 6 §9's invariants require.

**Advantages:** Auth0 removes an entire category of security risk (credential storage, session handling) from BrandGuard's own surface area; the custom authorization layer stays small, testable, and directly traceable to the architecture document that specifies it.

**Trade-offs:** Auth0 has a recurring per-user cost that grows with the customer base — acceptable at v1 scale, worth revisiting later (see Future Evolution). The custom authorization layer means BrandGuard, not a vendor, is responsible for keeping it correct — mitigated by the fact that Phase 6 already fully specified its rules; implementation is direct translation, not new design.

**Alternatives considered:** WorkOS is a strong alternative, purpose-built for B2B SaaS SSO/SCIM and worth a second look specifically when Enterprise SSO becomes a near-term commitment (PRD §5.3). Self-hosted Keycloak is a viable option for tenants with strict data-residency requirements; deferred to Future Evolution rather than v1 to avoid the operational overhead of running an identity server before it's needed. OPA (Open Policy Agent) was considered for the authorization layer — appropriate once policy rules grow numerous enough to warrant externalizing them from application code, but overengineering for v1's comparatively small, already-fully-specified rule set.

---

## 5. Relational Database

**Selected:** PostgreSQL

**Why it fits BrandGuard:** This is the architecture's primary data store by a wide margin — Organization, Workspace, Brand, BrandGenome, Policy, BrandHistory, Campaign, Asset, AssetVersion, AnalysisRun, Observation, Evidence, Decision, Report, Membership, RoleAssignment, and AuditLogEntry are all naturally relational, versioned, and require strong consistency (DR-005's pinning guarantee depends on it). PostgreSQL's JSONB support handles the more flexible payloads (Policy's `rules`, Genome Assertion content) without needing a separate document store, and Row-Level Security policies give a native, DB-enforced mechanism for tenant isolation (DR-003) — every tenant-scoped table can carry an `org_id` column with an RLS policy that makes cross-tenant reads structurally impossible at the database layer, not just application-layer discipline.

**Advantages:** One database technology for the overwhelming majority of the schema (see §22 below — full-text search lives here too), mature tooling, strong consistency guarantees, RLS directly implements DR-003's "application-layer verification" requirement at the strongest possible layer.

**Trade-offs:** A single relational database is a scaling bottleneck at very large multi-tenant scale — acceptable at v1, addressed in Future Evolution via read replicas and eventual sharding if needed.

**Alternatives considered:** MySQL is a viable alternative but lacks Postgres's combination of mature JSONB and native full-text search — choosing Postgres avoids a second data store for either concern. Vector storage is deliberately not one of the reasons Postgres was chosen in v1.1 — see §6, where it now lives in a dedicated vector database instead.

---

## 6. Vector Database

**Selected:** Qdrant (dedicated vector database service) — **v1.1 amendment, supersedes v1.0's pgvector selection**

**Why it fits BrandGuard:** The two places a vector store is genuinely needed — semantic matching during Genome compilation (Phase 1 §5) and the Distinctiveness Worker's consultation of the AI Slop Knowledge Base (Phase 3 §4) — both sit directly on top of DR-003/INV-19's binding requirement: **collection-per-tenant isolation, not metadata-filtering alone**. Qdrant's collection is a first-class, native primitive — a Brand's Brand History vectors live in a collection scoped to that Brand/Organization, and the AI Slop Knowledge Base lives in a wholly separate collection outside the Organization tree (DR-004), with no shared index to filter across in the first place. This makes INV-19's two-layer requirement (collection isolation *plus* an application-layer tenant-id check on every result) a direct, structural fit rather than something approximated inside a single shared Postgres table with row-level filtering.

**Advantages:** Purpose-built ANN performance and indexing (HNSW) that stays fast as Brand History/Slop KB volume grows; native collection-per-tenant maps exactly onto INV-19 with no workaround; a dedicated, horizontally-scalable service independent of the relational database's load; runs as a single Docker container locally, identical topology in production.

**Trade-offs:** A second stateful service to operate, back up, and secure, where v1.0's pgvector selection would have added zero extra infrastructure. This cost is accepted deliberately (human-architect decision, not a Claude Code judgment call) in exchange for the stronger, more direct tenant-isolation fit and a clearer growth path — mitigated by Qdrant's own operational simplicity (single binary/container, no external dependencies) and by keeping the same collection-per-tenant application-layer check pattern regardless of scale.

**Alternatives considered:** pgvector (v1.0's original selection) was the simpler, zero-extra-infrastructure choice and remains architecturally valid — it was not rejected for a technical deficiency, only superseded by an explicit decision to prioritize Qdrant's native collection-per-tenant primitive over infrastructure minimalism. Weaviate is a comparable purpose-built alternative to Qdrant; not selected here primarily on operational simplicity and the strength of Qdrant's Python client for the collection-scoped access pattern this architecture needs.

---

## 7. Object Storage

**Selected:** MinIO for local development, Amazon S3 for cloud deployment (S3-compatible API throughout, so the application code never changes between environments)

**Why it fits BrandGuard:** AssetVersion's `storage_ref` (Phase 0 §3.10) and BrandHistoryItem's raw source material both need durable, versioned blob storage outside the relational database. Using an S3-compatible API from day one means local development is a faithful mirror of production, satisfying "locally runnable" and "cloud deployable" as the same code path rather than two.

**Advantages:** MinIO is a single Docker container locally; S3 in production is effectively infinitely scalable and requires no capacity planning; identical API means zero application-code branching between environments.

**Trade-offs:** S3 has a learning curve around IAM policy configuration for correct tenant-scoped access — mitigated by keeping all object access mediated through the backend (no direct tenant-to-S3 access), so IAM complexity stays on the operations side, not the tenant-facing side.

**Alternatives considered:** Google Cloud Storage or Azure Blob Storage are equally valid if the cloud provider choice (§25) shifts; the S3-compatible API pattern makes this a low-cost decision to revisit.

---

## 8. Cache

**Selected:** Redis

**Why it fits BrandGuard:** Two clear, justified uses: caching hot lookups (an Organization's currently-active Genome/Policy version pointers, per Phase 0's `active_genome_version_id` pointer field, are read far more often than they change) and serving as the Celery broker (§9) — one piece of infrastructure serving two needs is a direct application of the design philosophy's "avoid overengineering" instruction.

**Advantages:** Extremely well understood operationally, sub-millisecond latency for the active-version lookups that gate every AnalysisRun creation (Pre-Phase-7 correction 4), doubles as the job queue backend so no separate broker is needed.

**Trade-offs:** An additional stateful service to operate, though a very well-trodden one; cache invalidation on Genome/Policy activation needs explicit handling (invalidate the specific Brand's cached pointer on activation — a small, well-defined event).

**Alternatives considered:** Memcached is simpler but lacks Redis's ability to double as a job broker, which would mean introducing a second piece of infrastructure just for caching — worse, not better, for this stack.

---

## 9. Background Job Processing

**Selected:** Celery + Redis

**Why it fits BrandGuard:** Phase 4's Work Unit model — bounded, idempotent retries with backoff, dependency ordering (video frame/transcript derivation before dependent workers), and failure isolation — maps directly onto Celery's native primitives: task-level retry/backoff configuration, and `chain`/`chord`/`group` primitives express exactly the dependency graph Phase 4 §5's Execution Plan describes, without needing a bespoke orchestration layer.

**Advantages:** Mature, well-documented, Python-native, retry/backoff/dependency chaining all come for free rather than being hand-built; one broker (Redis) serves both this and general caching.

**Trade-offs:** Celery's visibility into "what state is this specific Work Unit in right now" (Phase 4 §11's observability requirement) takes some deliberate design — task state needs to be explicitly persisted (e.g., a lightweight status row per Work Unit) rather than relying on Celery's own result backend alone, since Work Unit isn't a persisted domain entity (Phase 4 §2) but its state must still be inspectable in real time.

**Alternatives considered:** Temporal (or a similar durable-execution engine) is a genuinely strong architectural fit for Phase 4's retry/interruption/recovery semantics — arguably a *better* conceptual match than Celery — but it requires running and operating an additional stateful service (the Temporal server and its own datastore), which is more operational complexity than v1 needs. This is called out explicitly in Future Evolution rather than dismissed, because it is the most likely thing to revisit as Orchestrator complexity grows (Phase 4 §14, open question 1's retry-bound tuning is exactly the kind of experience that would justify the move).

---

## 10. AI Worker Execution

**Selected:** Celery, with a dedicated queue per worker type (Visual, Verbal, Compliance & Accessibility, Distinctiveness, Values & Mission — Phase 3 §4)

**Why it fits BrandGuard:** Phase 4 §10's scalability principle — independent Work Units should be able to execute without contention — is satisfied directly by giving each worker type its own queue and its own scalable pool of Celery workers, rather than a single shared pool. A spike in image-heavy assets (Visual Worker load) never starves Verbal Worker throughput, and each worker type can be scaled independently in production by simply adjusting how many processes consume each queue.

**Advantages:** No new infrastructure beyond §9; independent scaling per worker type is a configuration change, not an architectural one; naturally enforces Phase 3 §4's rule that no worker executes outside its assigned scope, since each worker type's code only ever consumes from its own queue.

**Trade-offs:** Requires discipline in queue naming/routing configuration as more worker types are added — a process concern, not a technology limitation.

**Alternatives considered:** A dedicated ML orchestration framework (Airflow, Prefect, Dagster) was considered for the Planning→Execution Plan dependency graph; rejected for v1 as unnecessary weight given Celery's chain/chord primitives already express the one genuine ordering dependency (video derivation) the architecture defines. Worth revisiting only if the worker graph grows substantially more complex than Phase 3 currently specifies.

---

## 11. AI Frameworks/Libraries

**Selected:** Direct use of the Ollama Python client (primary) and the Groq Python SDK (optional, secondary), combined with Pydantic-based structured output validation (an `instructor`-style pattern: define the expected schema as a Pydantic model, validate the model's response against it, retry on validation failure). **v1.1 amendment** — same pattern as v1.0, different provider clients.

**Why it fits BrandGuard:** This is a case where the architecture itself dictates the technology choice, not the other way around. Phase 2 §1 and PRD §12/§13 are emphatic that LLM outputs must be schema-constrained, never free-form, and that the decision function must never be a model. Adopting a general-purpose agent framework (LangChain, LlamaIndex-style agent loops) would introduce exactly the kind of opaque, multi-step, harder-to-audit LLM behavior the architecture was deliberately designed to avoid — this reasoning is provider-independent and holds identically for Ollama/Groq as it did for the v1.0 Anthropic selection. A thin, direct client call plus strict output-schema validation is the correct-sized tool for "extract structured, confidence-scored evidence" and "narrate a fixed evidence graph" — both bounded, single-call tasks, not open-ended agentic workflows, regardless of which model serves the call.

**Advantages:** Minimal indirection between "what the architecture requires" and "what the code does"; easy to audit exactly what prompt produced what output; no framework-specific debugging layer to learn; the same schema-validation discipline applies uniformly whether a given call is served locally (Ollama) or by the optional secondary provider (Groq).

**Trade-offs:** Some conveniences general frameworks provide (built-in retrieval chains, memory management) must be built directly if ever needed — acceptable, since Phase 2/3 never call for conversational memory or multi-step agentic reasoning in the first place. Locally-served open-weight models (Qwen 3 8B Instruct via Ollama, §15) generally have weaker instruction-following/structured-output adherence than a frontier hosted model — this raises the importance of the bounded-retry-then-fail discipline already required by CLAUDE.md §5.4; schema validation failure routes to a worker-failure outcome rather than being silently accepted, exactly as already specified.

**Alternatives considered:** LangChain/LlamaIndex were explicitly considered and rejected for the reason above — this remains the clearest case in this document of avoiding a popular technology because it doesn't fit the architecture's own stated principles, not because it's a bad framework in general. The Anthropic Python SDK (v1.0's original selection) was not rejected for a technical deficiency — see §15 for the full reasoning behind moving the primary LLM path to a self-hosted provider.

---

## 12. Document Processing

**Selected:** PyMuPDF (`fitz`) for PDF, `python-docx` for Word documents

**Why it fits BrandGuard:** Genome compilation ingestion (Phase 1 §4/§5) needs to extract text and structure from brand guideline documents and design system specs. Both libraries are lightweight, well-maintained, and handle the genuine need (structured text/layout extraction) without requiring a heavier document-AI pipeline.

**Advantages:** Fast, no external service dependency, handle the overwhelming majority of real-world guideline documents correctly.

**Trade-offs:** Neither handles deeply unusual layouts (scanned, image-only PDFs) natively — would require OCR as a separate step if that becomes a common case.

**Alternatives considered:** `unstructured.io` (open-source, broader format support, some layout-AI capability) is a reasonable upgrade path if document variety in practice proves messier than PyMuPDF/python-docx handle well — flagged as Future Evolution rather than adopted upfront, since it pulls in meaningfully more dependency weight for a need not yet demonstrated.

---

## 13. Image Processing

**Selected:** Pillow for general image operations, OpenCV for more advanced computer-vision preprocessing, ffmpeg (via `ffmpeg-python`) for video frame and audio/transcript extraction

**Why it fits BrandGuard:** The Visual Worker (Phase 3 §4) needs consistent image handling (resizing, format normalization) before any model call, and video assets need their "derived representative frames and transcript" (Phase 3 §3) extracted before Visual/Verbal workers can process them. This is exactly ffmpeg's purpose, and Pillow/OpenCV are the standard, well-supported Python tools for the image side.

**Advantages:** All three are mature, widely used, well-documented; ffmpeg specifically is the de facto standard for video frame/audio extraction, with no serious competing alternative.

**Trade-offs:** ffmpeg is a native binary dependency, not pure Python — requires it to be present in the container image (a Dockerfile concern, not an architectural one).

**Alternatives considered:** None seriously compete with ffmpeg for this purpose; for image processing, OpenCV vs. Pillow isn't an either/or — Pillow handles simple operations with less overhead, OpenCV is used only where its computer-vision-specific capability (e.g., color palette extraction) is actually needed.

---

## 14. Embedding Models

**Selected:** BAAI bge-m3, self-hosted, served locally (via Ollama or a dedicated local inference service such as `sentence-transformers`/`text-embeddings-inference`). **v1.1 amendment, supersedes v1.0's Voyage AI selection.**

**Why it fits BrandGuard:** Genome compilation's semantic matching and the Distinctiveness Worker's Slop KB comparisons (§6) both need embeddings. The v1.1 decision is to make the embedding pipeline fully self-hosted, consistent with the same decision made for the primary LLM path (§15) — no hosted embedding API is part of the production architecture. bge-m3 is a strong, well-regarded open-weight multilingual/multi-granularity embedding model whose vector output is what Qdrant (§6) indexes.

**Advantages:** No external API dependency or per-call cost for embeddings; consistent, fully self-hosted AI surface (embeddings + primary LLM both run locally); no network round-trip for the embedding step; embedding calls stay data-local during Genome compilation and Distinctiveness Worker consultation.

**Trade-offs:** Self-hosting shifts embedding compute from "someone else's infrastructure, billed per call" to infrastructure this platform must provision, run, and scale — a real operational cost accepted deliberately as part of the same decision covered in §15. Embedding quality is strong but not guaranteed to exceed a top hosted-API model on every benchmark; acceptable given embedding calls happen during Genome compilation (an infrequent, human-reviewed workflow, Phase 1 §5) and bounded Distinctiveness Worker consultation (Phase 3 §3), not a high-frequency hot path, and given the architecture's overriding v1.1 goal of a self-hosted-first AI surface.

**Alternatives considered:** Voyage AI and OpenAI's embedding models (v1.0's original selection and its stated alternative) remain valid hosted options and were not rejected for a quality deficiency — they were superseded by the explicit human-architect decision to eliminate hosted-API dependency from the embedding pipeline. Other self-hosted open-weight embedding models (e.g., `nomic-embed-text`, `gte-large`) are reasonable substitutes for bge-m3 behind the same local-inference interface if evaluation later favors a different model.

---

## 15. LLM Integration Layer

**Selected:** Ollama serving **Qwen 3 8B Instruct** as the primary LLM, self-hosted; Groq API as an **optional secondary provider, scoped exclusively to advanced narrative generation** (Recommendation/Report text narration — never evidence extraction, and never anything decision-adjacent beyond narration); both accessed through the same thin, provider-agnostic internal wrapper. **v1.1 amendment, supersedes v1.0's Claude/Anthropic API selection — the Anthropic API is not part of the production runtime.**

**Why it fits BrandGuard:** The architecture's two LLM-touching responsibilities — structured evidence extraction (tone, voice, distinctiveness) and schema-constrained narration of an already-computed evidence graph (Phase 2 §6.3) — are unchanged by this amendment; only the provider serving them changes. Qwen 3 8B Instruct via Ollama gives the platform a fully self-hosted default path for both responsibilities, with Groq available as a secondary provider specifically where narrative quality benefits from a larger/faster-served model — deliberately scoped to narration only, so that the platform's evidence-extraction path (the one closer to INV-01's "no model originates a judgment" boundary) stays on the self-hosted default rather than being split unpredictably across providers. The thin wrapper design from v1.0 is exactly what makes this change tractable: swapping (and adding) providers is a wrapper-level change, not a rewrite of every worker.

**Advantages:** No per-call API cost or external dependency for the primary path (evidence extraction and default narration); data — including OCR/transcript/document text that must never leave the trust boundary as anything but data (§5.2's prompt-injection defense in CLAUDE.md) — stays on infrastructure this platform controls for the primary path; Groq's optional role is narrow and auditable (narration only), keeping the INV-01/INV-03 boundary between "evidence extraction" and "narration" visible in the provider routing itself, not just in code comments.

**Trade-offs:** Qwen 3 8B Instruct is a materially smaller, weaker model than a frontier hosted model (including the v1.0 Claude selection) on raw instruction-following and structured-output reliability — this is accepted as a deliberate trade-off (self-hosted-first over peak per-call quality) and is mitigated, not eliminated, by §5.4's existing bounded-retry-then-fail discipline and by keeping Groq available for narration where quality matters most to the end user. Serving an 8B model with acceptable latency requires GPU-backed compute; this is a non-trivial change to the v1.0 deployment assumption (§25) — AWS ECS Fargate does not support GPU tasks, so production hosting for the Ollama service specifically will need a GPU-capable compute path (e.g., ECS on EC2 with GPU instances, or a dedicated inference host) rather than Fargate. This is flagged here as a known, deferred consequence for Phase 4 (Platform Engineering) to resolve when execution/infrastructure is actually designed — not resolved in this document, consistent with this document's own scope (v1 technology selection, not deployment topology design). Locally, Docker Compose runs Ollama as an ordinary container (CPU inference works for development; GPU passthrough is a Compose-level configuration, not an architectural blocker).

**Alternatives considered:** Claude/Anthropic API (v1.0's original selection) was not rejected for an instruction-following deficiency — quite the opposite, per v1.0's original rationale, preserved in the Amendment Log — it was superseded by an explicit human-architect decision to make the primary LLM path self-hosted. OpenAI's GPT models remain a viable alternative behind the same wrapper interface if a different secondary/tertiary provider is ever warranted. Larger self-hosted models (e.g., Qwen 3 32B+, Llama-family models) are a reasonable Future Evolution path if Qwen 3 8B's quality proves insufficient in practice and the additional GPU capacity is justified.

---

## 16. Configuration Management

**Selected:** Pydantic Settings, backed by environment variables

**Why it fits BrandGuard:** Application configuration (as distinct from secrets, §17) needs to be identical in shape between local Docker Compose and cloud deployment — environment variables are the one mechanism every deployment target supports natively, and Pydantic Settings gives that configuration the same type-validated treatment as every other domain model in the FastAPI stack.

**Advantages:** No additional service to run; configuration errors are caught at startup (type validation) rather than as runtime surprises; identical mechanism locally and in the cloud.

**Trade-offs:** Not suited to configuration that needs to change without a redeploy — not a need this architecture currently has (Genome/Policy versioning, the actual "configuration" that changes frequently, is already a first-class versioned domain concept, not infrastructure config).

**Alternatives considered:** A dedicated configuration service (Consul, etc.) would be genuine overengineering for a need fully met by environment variables at this scale.

---

## 17. Secrets Management

**Selected:** AWS Secrets Manager in cloud deployment; `.env` files (git-ignored) for local development

**Why it fits BrandGuard:** Secrets (the optional Groq API key, database credentials, Auth0 credentials) need tighter handling than general config — access-controlled, auditable retrieval, and rotation capability. Ollama and the local embedding service (§14/§15) run self-hosted and require no external API key at all, which narrows this category's scope relative to v1.0 without eliminating it. AWS Secrets Manager provides this natively if AWS is the chosen cloud (§25), with no separate secrets infrastructure to run.

**Advantages:** Native IAM-based access control means secrets access itself is auditable, satisfying the same "administrative traceability" spirit as Phase 6 §5, applied to infrastructure credentials rather than domain data.

**Trade-offs:** Adds a small amount of AWS-specific coupling — acceptable, since the application never talks to Secrets Manager directly in business logic, only at startup/config-load time, keeping the coupling isolated.

**Alternatives considered:** HashiCorp Vault is a more powerful, cloud-agnostic alternative, explicitly deferred to Future Evolution — it requires running and securing an additional service, which is unjustified weight while a single cloud provider's native secrets manager already meets the need.

---

## 18. Logging

**Selected:** `structlog`, emitting structured JSON to stdout

**Why it fits BrandGuard:** Every log line should be able to carry structured context — `analysis_run_id`, `organization_id`, `work_unit_id` — so that a single AnalysisRun's execution can be traced across every stage of Phase 3's pipeline without regex-parsing free-text log lines. Writing to stdout (rather than to files or a specific log-shipping agent directly) keeps the application decoupled from whatever log collection mechanism the deployment environment provides.

**Advantages:** Structured logs are directly queryable once collected; stdout-based logging is the simplest possible integration with any container platform's native log collection, requiring zero additional application-level configuration for where logs go.

**Trade-offs:** Structured logging has a small performance/verbosity cost versus plain text — negligible at this scale, and outweighed by the debugging value given how many distinct entities (Work Unit, AnalysisRun, Evidence, Decision) a single request can touch.

**Alternatives considered:** Plain Python `logging` with string formatting is simpler but loses the structured-context benefit that makes tracing a single AnalysisRun through Phase 3/4's multi-stage pipeline tractable.

---

## 19. Monitoring & Observability

**Selected:** OpenTelemetry for instrumentation; Prometheus for metrics storage; Grafana for dashboards — all self-hosted via Docker Compose at v1

**Why it fits BrandGuard:** Phase 4 §11's observability requirement (Work Unit and AnalysisRun state must be inspectable in real time, not only reconstructable after the fact) and Phase 7 §3's tenant-facing status visibility both need real metrics, not just logs. OpenTelemetry is the vendor-neutral instrumentation standard specifically so that the choice of backend (Prometheus/Grafana now, a hosted APM tool later) is a configuration change, not a re-instrumentation effort.

**Advantages:** No vendor lock-in at the instrumentation layer; Prometheus/Grafana are free, well-documented, and run as two more containers in the same Docker Compose file already used for local development, keeping "locally runnable" true even for the observability stack itself.

**Trade-offs:** Self-hosted Prometheus/Grafana requires some operational attention (retention, alerting rules) that a managed APM product would handle automatically — acceptable at v1's team size and scale.

**Alternatives considered:** Datadog or Grafana Cloud are strong managed alternatives, explicitly deferred to Future Evolution — OpenTelemetry instrumentation means switching to either later requires no code change, only a different exporter configuration.

---

## 20. Audit Logging

**Selected:** A dedicated, append-only PostgreSQL table for AuditLogEntry, with the application's normal database role explicitly denied `UPDATE` and `DELETE` privileges on that table at the database level.

**Why it fits BrandGuard:** NFR-003 and Phase 6 §9's invariant ("audit history is never rewritten, truncated, or deleted") are strong enough guarantees that they deserve database-level enforcement, not just application-level discipline. Revoking `UPDATE`/`DELETE` grants on this one table for the application's service role means even a bug in application code — not just a malicious actor — cannot violate the invariant; the database itself refuses the operation.

**Advantages:** The strongest, simplest possible enforcement mechanism for an already-simple requirement (this table only ever receives `INSERT`s); no separate audit-logging technology or service needed, since Postgres already provides everything required.

**Trade-offs:** Table size grows indefinitely — an accepted trade-off for an immutable audit trail; partitioning by time is a natural, low-risk future optimization, not an architectural change.

**Alternatives considered:** A dedicated audit-logging service or event-sourcing store was considered and rejected as overengineering — the requirement is "never mutated," which a permissions grant satisfies directly, without needing a new class of infrastructure.

---

## 21. File Storage (Transient/Local)

**Selected:** Container-local ephemeral disk, explicitly cleaned up after each Work Unit completes

**Why it fits BrandGuard:** This is distinct from §7's durable object storage — it covers the temporary working files a Worker needs mid-processing (an extracted video frame, a decoded document's intermediate text) that should never persist beyond that Work Unit's execution (Phase 4 §2/§7's isolation principle: one Work Unit's execution must never affect another's). Using the container's own ephemeral filesystem, cleaned deterministically at the end of each Work Unit's execution, keeps this transient data from ever becoming a second, informal storage system that needs its own lifecycle management.

**Advantages:** Zero additional infrastructure; cleanup is automatic when a container/task ends, reinforcing rather than working against Work Unit isolation.

**Trade-offs:** None material — this data was never meant to be durable or shared.

**Alternatives considered:** A shared temporary storage volume across workers was considered and explicitly rejected — it would violate Phase 4 §7's Work Unit isolation principle by creating a path for one Work Unit's data to accidentally affect another's.

---

## 22. Search

**Selected:** PostgreSQL full-text search (`tsvector`/`tsquery`)

**Why it fits BrandGuard:** Operational search needs at v1 — finding a Campaign, Asset, or Report by name or content keyword (distinct from the semantic vector search in §6) — are well within what Postgres's native full-text search handles, without introducing a fourth data store alongside the relational database, vector extension, and object store.

**Advantages:** No additional infrastructure; search indexes live in the same transactional database as the data they index, so there's no separate synchronization process to keep search results consistent with the source of truth.

**Trade-offs:** Postgres full-text search has less sophisticated relevance ranking and faceting than a dedicated search engine.

**Alternatives considered:** OpenSearch/Elasticsearch are the clear Future Evolution path once search sophistication (faceted filtering across large report/campaign volumes, fuzzy matching at scale) genuinely outgrows what Postgres provides.

---

## 23. Containerization

**Selected:** Docker

**Why it fits BrandGuard:** The industry-standard, uncontroversial choice for "locally runnable and cloud deployable" — every other technology in this document (Postgres, Redis, MinIO, the backend, Celery workers, the frontend) runs identically as a container locally and in production, which is precisely the property the design philosophy asks for.

**Advantages:** Universal tooling support; identical artifact from a developer's laptop through to production deployment.

**Trade-offs:** None material at this stage — Docker is close to a default choice for this requirement.

**Alternatives considered:** Podman is a viable, more security-hardened alternative with a largely Docker-compatible CLI; not selected for v1 simply because Docker's tooling and documentation ecosystem remains broader, easing onboarding.

---

## 24. Local Development Environment

**Selected:** Docker Compose, defining every service in this stack (Postgres, Qdrant, Redis, MinIO, Ollama, backend API, Celery workers, Prometheus, Grafana, frontend) as one composable local environment

**Why it fits BrandGuard:** "Locally runnable" is a first-class design requirement, not an afterthought — a single `docker compose up` should bring up a fully functional, representative instance of the entire architecture, including observability, for any engineer working on any part of the system.

**Advantages:** New developer onboarding is a single command; local environment closely mirrors production topology, reducing "works on my machine" drift.

**Trade-offs:** Running the full stack (including Grafana/Prometheus) locally has some resource overhead on a laptop — mitigated by making the observability containers optional via Compose profiles for engineers who don't need them for a given task.

**Alternatives considered:** Devcontainers (VS Code) are a reasonable complementary addition rather than a replacement — noted under §30, not a competing choice here.

---

## 25. Deployment

**Selected:** AWS ECS Fargate (managed container hosting, no cluster to operate)

**Why it fits BrandGuard:** This is the document's central answer to "horizontally scalable later without Kubernetes now." Fargate runs the exact same Docker images used locally, scales horizontally by adjusting task count (directly satisfying Phase 4 §10's scalability principle — independent Work Units/AnalysisRuns need only more execution capacity, not a redesigned deployment model), and requires no cluster management, node patching, or control-plane operations. Critically, because the deployable unit is already a standard container image, a future move to Kubernetes (if genuinely justified — see Future Evolution) is a matter of pointing existing images at a new orchestrator, not re-architecting the application.

**Advantages:** No Kubernetes control plane to run or secure at v1; horizontal scaling is a configuration change (desired task count); integrates natively with the rest of an AWS-based stack (§7, §17, §29).

**Trade-offs:** Somewhat more AWS-specific than a Kubernetes deployment would be — accepted, since the actual application artifact (container images) remains portable regardless. **v1.1 note:** Fargate does not support GPU-backed tasks, and the v1.1 move to a self-hosted primary LLM (Ollama serving Qwen 3 8B Instruct, §15) requires GPU compute to serve at acceptable latency — the Ollama service specifically will need a GPU-capable hosting path (e.g., ECS on EC2 with GPU instances) distinct from the Fargate path used for the rest of the stack. This is flagged as a Phase 4 (Platform Engineering) deployment-design item, not resolved here.

**Alternatives considered:** Google Cloud Run and Azure Container Apps are directly comparable if a different cloud provider is preferred — the underlying reasoning (managed containers, no cluster ops, horizontal scale via task/instance count) is identical across all three. Kubernetes itself is explicitly deferred to Future Evolution.

---

## 26. CI/CD

**Selected:** GitHub Actions

**Why it fits BrandGuard:** Assuming source control on GitHub, Actions requires no additional service to run, integrates directly with pull requests (running tests, linting, and security scans, §27–28, before merge), and can deploy directly to ECS Fargate (§25) on merge to the main branch.

**Advantages:** Zero additional infrastructure; tight integration with the same platform hosting the code; large ecosystem of pre-built actions for common steps (Docker build/push, Terraform plan/apply).

**Trade-offs:** Vendor-tied to GitHub — acceptable, since migrating CI/CD platforms later is a well-understood, bounded effort if source control ever moves.

**Alternatives considered:** GitLab CI is directly comparable if GitLab is the chosen source host; the underlying pipeline design (test → lint → scan → build → deploy) is unaffected by which is chosen.

---

## 27. Testing Frameworks

**Selected:** pytest for backend unit/integration tests, Hypothesis for property-based testing of the Decision Engine specifically, Playwright for frontend/end-to-end tests

**Why it fits BrandGuard:** pytest is the standard, unopinionated choice for the Python backend. Hypothesis deserves specific, deliberate inclusion — not as generic "good practice," but because Phase 2 §8.2's reproducibility guarantee ("identical inputs always produce an identical Decision") is precisely the kind of property Hypothesis is designed to verify: generate many varied Evidence sets and confirm the Decision Engine's determinism holds across all of them, rather than only the handful of example cases a hand-written unit test would cover. Playwright is a strong, modern choice for testing the role-appropriate frontend views (§1) across the different personas.

**Advantages:** Hypothesis directly tests an explicit, named architectural guarantee rather than incidental behavior; Playwright's multi-browser, TypeScript-native support fits the Next.js frontend well.

**Trade-offs:** Property-based tests take more upfront thought to write well than example-based tests — a worthwhile cost given what specifically is being verified (a guarantee the entire Decision Architecture depends on).

**Alternatives considered:** Cypress is a comparable end-to-end alternative to Playwright; either is defensible, Playwright's slight edge here being native multi-browser support out of the box.

---

## 28. Security Tooling

**Selected:** Bandit (Python static security analysis), Semgrep (broader static analysis), gitleaks (secrets-in-commit scanning), Dependabot or `pip-audit` (dependency vulnerability scanning)

**Why it fits BrandGuard:** These four cover the concrete, near-term risks (insecure code patterns, accidentally committed secrets, vulnerable dependencies) with free or low-cost tools that integrate directly into the GitHub Actions pipeline (§26) — appropriate weight for a pre-launch product, without committing to an enterprise security platform before there's a team or budget to operate one.

**Advantages:** All four run automatically in CI with no dedicated security engineering headcount required; catch the highest-frequency real-world issues (leaked keys, known-vulnerable packages) with minimal false-positive noise.

**Trade-offs:** Not a substitute for the formal STRIDE threat model and deeper security tooling PRD §18 already flags as a later, dedicated phase (Phase 6 explicitly deferred formal threat modeling to actual security engineering work, not this document) — these tools are a baseline, not the complete security program.

**Alternatives considered:** Snyk and dedicated SAST/DAST platforms are the clear Future Evolution path once NFR-010's SOC 2 readiness work becomes an active initiative rather than a stated future intent.

---

## 29. Infrastructure as Code

**Selected:** Terraform

**Why it fits BrandGuard:** Defining the ECS Fargate services, RDS Postgres instance, Redis (ElastiCache), S3 buckets, and IAM roles declaratively means the entire cloud environment is reproducible, reviewable in pull requests, and never configured by hand through a console — directly supporting "cloud deployable" as a repeatable process rather than a one-time manual setup.

**Advantages:** Mature, cloud-agnostic-enough tooling with the largest ecosystem of provider support; infrastructure changes go through the same review process as application code changes.

**Trade-offs:** HCL (Terraform's configuration language) is a small additional syntax to learn beyond Python/TypeScript — a reasonable, industry-standard cost.

**Alternatives considered:** Pulumi allows writing infrastructure definitions in Python directly, which some teams prefer for consistency with the application language; a defensible alternative, not selected here only because Terraform's broader adoption means more available documentation and hiring familiarity.

---

## 30. Recommended Development Tools

**Selected:** Poetry (Python dependency management), Ruff (linting and formatting), mypy (static type checking), pre-commit (automated check enforcement), VS Code (with Python, Docker, and Terraform extensions) as the suggested IDE

**Why it fits BrandGuard:** This combination keeps the Python codebase's type discipline consistent with its heavy reliance on Pydantic models throughout (API schemas, domain models, Genome Assertion structures) — mypy catches schema mismatches before runtime, exactly where a mismatch would otherwise surface as a confusing production bug in something as consequential as Evidence or Decision construction. Ruff replaces what would otherwise be three separate tools (flake8, black, isort) with one fast tool, keeping the developer feedback loop quick. FastAPI's built-in Swagger UI already provides interactive API exploration for free, so no additional API client tool is recommended as a required part of the stack.

**Advantages:** Fast feedback loop (Ruff is significantly faster than the tools it replaces); pre-commit ensures these checks run before code ever reaches CI, catching issues earlier and cheaper.

**Trade-offs:** None material — this is a low-risk, high-leverage set of choices.

**Alternatives considered:** `uv` is a newer, faster alternative to Poetry worth adopting once its ecosystem maturity is fully established; flagged as a likely near-term upgrade rather than excluded outright.

---

# Future Evolution

The principle throughout this document has been: choose the simplest technology that genuinely satisfies today's requirement, and ensure the upgrade path exists without an architectural rewrite. This section makes that path explicit, area by area.

| Area | Current (v1) | Future Evolution | Trigger for the change |
|---|---|---|---|
| Background jobs / AI orchestration | Celery + Redis | Temporal (or similar durable-execution engine) | Orchestrator complexity (Phase 4) grows — many more worker types, more complex conditional dependency graphs, or a genuine need for long-running human-in-the-loop steps |
| Vector store | Qdrant (v1.1) | Sharded/clustered Qdrant deployment | Brand History / AI Slop KB volume or query throughput outgrows a single Qdrant instance |
| Deployment | AWS ECS Fargate | Kubernetes (EKS or equivalent) | Operational complexity (many independently-scaled services, need for custom scheduling/operators) genuinely exceeds what managed containers provide — not before |
| Search | PostgreSQL full-text search | OpenSearch / Elasticsearch | Faceted search, fuzzy matching, or report/campaign volume genuinely outgrows native Postgres search |
| Object storage | MinIO (local) / Amazon S3 (cloud) | No change expected — S3-compatible API already is the long-term answer; only the provider (S3 vs. GCS vs. Azure Blob) might shift with a cloud-provider change |
| Secrets management | AWS Secrets Manager | HashiCorp Vault | Multi-cloud requirements or advanced secret-rotation/dynamic-credential needs emerge |
| Authentication | Auth0 | WorkOS, or self-hosted Keycloak | Enterprise SSO/SCIM (PRD §5.3) becomes an active, near-term commitment, or specific tenants require data-residency guarantees a self-hosted identity provider satisfies |
| Authorization | Custom RBAC service | OPA (Open Policy Agent) | The RoleAssignment rule set (Phase 5/6) grows numerous or complex enough that externalizing policy from application code becomes clearly worth the added operational piece |
| Monitoring | Self-hosted OpenTelemetry + Prometheus + Grafana | Datadog or Grafana Cloud | Team size or operational maturity makes managing the observability stack itself a distraction from product work |
| Document processing | PyMuPDF + python-docx | `unstructured.io` | Real-world guideline document variety proves messier (scanned documents, complex layouts) than the lightweight parsers handle well |
| Embeddings | BAAI bge-m3, self-hosted (v1.1) | Larger/domain-tuned self-hosted embedding model, or a GPU-scaled serving layer | Embedding quality or throughput demands genuinely outgrow bge-m3 served on current infrastructure |
| LLM provider | Ollama (Qwen 3 8B Instruct, self-hosted, v1.1) + Groq (optional, narration only) | Larger self-hosted model (e.g., Qwen 3 32B+) and/or additional hosted providers behind the same wrapper | Evidence-extraction or narration quality genuinely requires more capacity than Qwen 3 8B provides, and the added GPU capacity or provider cost is justified |
| Relational database scaling | Single PostgreSQL instance | Read replicas, then partitioning/sharding by Organization | Query load or data volume at large multi-tenant scale genuinely exceeds a single instance's capacity |
| Security tooling | Bandit / Semgrep / gitleaks / Dependabot | Snyk or a dedicated SAST/DAST platform | NFR-010's SOC 2 readiness becomes an active initiative requiring formal, continuous security tooling |

**Why this evolution path is low-risk by construction:** every "future" entry above swaps out one piece of infrastructure behind an interface the v1 stack already established — the S3-compatible object storage API, the OpenTelemetry instrumentation layer, the provider-agnostic LLM wrapper, the container image as the unit of deployment. None of these changes require touching the conceptual architecture in Phases 0–7; they are implementation substitutions the architecture was explicitly designed to tolerate.

---

*End of Technology Stack Selection Document, v1.1 (amended). This document, together with the frozen Phases 0–7, forms the complete pre-implementation baseline for BrandGuard AI.*