# Brandium — Implementation Status

**Last updated:** 2026-07-31
**Current phase:** Engineering Foundation ("Phase 0" per kickoff instruction) — **complete, pending human review**
**Next milestone:** CLAUDE.md §14 Milestone 1 — Domain Foundation (RLS enforcement wiring + activation-invariant/tenant-isolation tests)

---

## What this pass covered

Per the kickoff instruction, this pass is engineering-foundation scaffolding only — no business logic, no authentication, no Brand Genome compilation, no AI pipeline, no Decision Engine, no workers. It corresponds to the ground CLAUDE.md's Milestone 1 stands on, not Milestone 1 itself (Milestone 1 additionally requires the RLS request-context middleware and dedicated activation/tenant-isolation tests — explicitly deferred here, see "Open items" below).

### Repository structure
Full tree per CLAUDE.md §6: `backend/src/` organized by the six Bounded Contexts, `workers/`, `frontend/`, `shared/`, `infra/{docker,terraform}`, `scripts/`, `backend/tests/{unit,integration,property,tenant_isolation}`.

### Technology Stack amendment (v1.0 → v1.1)
Before any code was written, a conflict was raised (per CLAUDE.md §9.4) between the kickoff instruction's Phase 0 list (Qdrant, Ollama) and the frozen Technology Stack v1.0 (pgvector, Claude/Anthropic API, Voyage AI). The human architect explicitly resolved this as an amendment, documented in full in `docs/01-PRD/02-Architecture/technology_stack.md`'s Amendment Log and §6/§11/§14/§15:

- **Vector store:** pgvector → **Qdrant** (collection-per-tenant, direct fit for INV-19)
- **Embeddings:** Voyage AI (hosted) → **BAAI bge-m3**, self-hosted locally
- **LLM:** Claude/Anthropic API → **Ollama (Qwen 3 8B Instruct)** as primary, self-hosted; **Groq API** as optional secondary, scoped exclusively to narrative generation. The Anthropic API is not part of the production runtime.

This is an approved deviation, not a unilateral choice — see the Amendment Log for the full rationale, trade-offs, and the flagged consequence that AWS ECS Fargate (Technology Stack §25) does not support GPU tasks, which the self-hosted Ollama service will need in production (flagged as a Phase 4 deployment-design item, not resolved yet).

### Domain model foundation (all six Bounded Contexts, schema only)
SQLAlchemy 2.0 models for every Phase 0 §3 entity, with `org_id` denormalized on every tenant-scoped table and `Brand`'s pointer-based activation FKs (`active_genome_version_id`/`active_policy_version_id`) implemented as deferred (`use_alter`) foreign keys to resolve the Brand↔BrandGenome/Policy circular reference:

- **Identity & Access:** Organization, Workspace, User, RoleAssignment, InternalOperator
- **Brand Governance:** Brand, BrandGenome, Policy, BrandHistory
- **Campaign & Asset Management:** Campaign, Asset, AssetVersion
- **Analysis & Decision:** AnalysisRun, Observation, Evidence, Decision, Recommendation
- **Reporting:** Report (with the four-field review overlay)
- **Platform Governance:** AuditLogEntry, AISlopKnowledgeBase (neither carries `TenantScopedMixin` — both are structurally global per Phase 0 §6)

No service-layer logic, no activation workflow, no Genome compilation — schema and the reproducibility/versioning *shape* only (e.g. `Decision.decision_function_version` exists as a field; the actual aggregation formula is still Phase 2's Known Gap).

### Migrations, RLS, audit immutability
Alembic wired up (async-compatible `env.py`); a single initial migration (`0001_initial_domain_foundation.py`) creates every table, enables Postgres Row-Level Security with a `current_setting('app.current_org_id')`-scoped policy on every tenant-scoped table, and revokes `UPDATE`/`DELETE` on `audit_log_entries` from the application role (INV-33). The migration was **not** run against a live database in this sandbox (no Docker access here — see "Verification" below); it has been carefully hand-reviewed against the model definitions but not executed.

### Base repository pattern + DI
`shared_kernel/repository.py`'s generic `BaseRepository[ModelT]`, with `identity_access/repository.py`'s `OrganizationRepository` as the worked example other contexts' repositories should follow. DI foundation is FastAPI's own `Depends` (`shared_kernel/db.py:get_session`) — no separate DI framework, per Technology Stack §3/§4's stated philosophy.

### Config, logging, API skeleton
Pydantic Settings (`src/config.py`), structlog JSON logging (`src/logging.py`), FastAPI app with only `/healthz` wired up (`src/main.py`) — deliberately the only route, since no business endpoints exist yet.

### Testing framework
pytest + pytest-asyncio + Hypothesis wired up. `tests/unit`, `tests/integration` (SQLite-backed repository round-trip), `tests/property` (Hypothesis harness proven, real Decision Engine reproducibility tests land in Milestone 4), `tests/tenant_isolation` (explicitly `pytest.mark.skip`, not faked — see "Open items").

### Dev tooling, workers, frontend, infra
Ruff/mypy config in `backend/pyproject.toml`, `.pre-commit-config.yaml` (ruff, mypy, gitleaks, hygiene hooks). `workers/celery_app.py` defines the Celery app and per-worker-type queue routing (Visual/Verbal/Compliance & Accessibility/Distinctiveness/Values & Mission) with **no task implementations** (Phase 3 scope). `frontend/` is a Next.js 15 + TypeScript + Tailwind App Router scaffold with one placeholder page, a typed API client stub, and a Playwright smoke test. `infra/terraform/main.tf` is a deliberate empty placeholder (Phase 4 scope — see file for reasoning) rather than half-written cloud resources. `docker-compose.yml` wires up Postgres, Redis, MinIO, Qdrant, Ollama, backend, worker, frontend, and an optional `observability` profile (Prometheus/Grafana).

---

## Open items (explicitly deferred, not silently dropped)

1. **`Membership` entity** — CLAUDE.md §1.5 lists it under Identity & Access, but Phase 0 v0.2 §3 never defines its fields. Not modeled here to avoid inventing schema for an entity the frozen spec doesn't yet specify (Phase 0 §9's open question 2 notes Policy-activation-review is still unresolved too, in the same spirit). Lands with the Phase 5 RoleAssignment scope-tier addendum, CLAUDE.md Milestone 10.
2. **RLS request-context middleware** — migration 0001 enables and defines the RLS policies, but nothing yet issues `SET LOCAL app.current_org_id` per request. This is Milestone 1 scope.
3. **`tests/tenant_isolation/`** — currently one explicitly-skipped placeholder, not a faked pass. Needs a live Postgres fixture and the middleware above; Milestone 1 scope.
4. **Production GPU hosting for Ollama** — Technology Stack v1.1 §15/§25 flags that ECS Fargate can't run GPU tasks; resolving this is Phase 4 (Platform Engineering) scope, not resolved here.

## Verification performed / not performed

- **Performed:** every backend `.py` file parses cleanly (`ast.parse`, syntax-only). All model/migration/config files were hand-reviewed for internal consistency against Phase 0 §3's field lists.
- **Not performed, and reported honestly rather than assumed:** this sandbox has no working `pip`/`venv` (no `ensurepip`, no `sudo`) and no `docker` CLI access (Docker Desktop's WSL integration isn't enabled for this distro), so none of the following were actually run: `poetry install`, `alembic upgrade head` against a real Postgres, `pytest`, `npm install`, `docker compose up`, or `docker compose config`. **Before trusting this as a working system, please run `docker compose up` (or `scripts/dev_up.sh`) locally and report anything that fails** — that is the real verification this pass could not perform.

---

## Next milestone

CLAUDE.md §14 **Milestone 1 — Domain Foundation**: add the `SET LOCAL app.current_org_id` request middleware, write the activation-invariant tests (INV-09) and the cross-tenant RLS-denial tests currently stubbed out in `tests/tenant_isolation/`, and confirm the migration actually applies cleanly against the real `postgres` service in `docker-compose.yml`.
