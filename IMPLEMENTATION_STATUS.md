# Brandium — Implementation Status

**Last updated:** 2026-08-01
**Current phase:** Demonstration build — the full journey (create org → Brand Genome → upload → watch the Celery-backed runtime execute → BDI score → evidence-grounded recommendations → explainability drill-down → report) is implemented end-to-end and wired into an enterprise-styled frontend. Not "exhaustively tested": see "What remains."

---

## Local execution fixes (this pass — no product functionality changed)

A DevOps audit for local runnability found and fixed four real defects, none of which had been exercised by any prior pass because none of them were runtime-verifiable in this sandbox (no Docker access here either — see "Runtime verification" below):

1. **CORS was entirely unconfigured.** `backend/src/main.py` had no `CORSMiddleware` — every frontend fetch from `http://localhost:3000` to the API at `http://localhost:8000` would have been blocked by the browser. Added `cors_allowed_origins` to `config.py` (defaults to `localhost:3000`/`127.0.0.1:3000`) and wired `CORSMiddleware` into `main.py`. This was the single most severe defect: without it, the frontend would load but every API call would silently fail in the browser console.
2. **MinIO bucket was never created.** `ObjectStorageClient` assumes `brandium-assets` already exists and never creates it — a fresh MinIO volume has no buckets, so the first Brand History or Asset upload would fail with `NoSuchBucket`. Added a one-shot `minio-init` service (official `minio/mc` image) to `docker-compose.yml` that creates the bucket; `backend`/`worker` now wait on it via `service_completed_successfully`.
3. **No Ollama model was ever pulled.** The `ollama/ollama` image ships with zero models; every LLM/embedding call would fail against a fresh volume. Added a one-shot `ollama-init` service that runs `ollama pull` for both `OLLAMA_LLM_MODEL` and `OLLAMA_EMBEDDING_MODEL` against the running `ollama` service (via `OLLAMA_HOST`), gated on a new healthcheck on `ollama` itself; `backend`/`worker` wait on it too. First run downloads several GB — expected, not a bug.
4. **`worker` service's volume mount was broken** (carried over from the previous pass, already fixed then): `./workers:/workers` sat outside the image's `/app` WORKDIR, so `-A workers.celery_app` could never resolve. Now mounted at `/app/workers` on both `backend` and `worker`.

**Not fixed, documented only:** no `alembic upgrade head` is run automatically on container startup — this is a required manual step after first `docker compose up` (see the execution guide provided alongside this update). No `poetry.lock` exists, so `poetry install` re-resolves dependencies on every image build rather than using a pinned, reproducible set — not fixable without running `poetry lock`, which needs network/pip access this sandbox doesn't have.

**Root cause of "the project cannot start" as reported:** not a repository defect at all — Docker Desktop's WSL integration is not enabled for the `Ubuntu` WSL distro this repo runs in (confirmed: `/usr/bin/docker` does not exist in this distro; the `docker` command found on `PATH` is Docker Desktop's own wrapper script, which prints exactly the "could not be found in this WSL 2 distro" message observed). This requires a one-time Docker Desktop settings change on the Windows host — an action outside this repository and outside what this environment can perform on its own. Full fix in the execution guide.

## Ollama model tag correction (follow-up — WSL integration now enabled, stack starts, this was the next blocker)

`OLLAMA_LLM_MODEL` was set to `qwen3:8b-instruct` in three places (`docker-compose.yml`'s shared env block and the `ollama-init` entrypoint's fallback, `.env.example`, `backend/src/config.py`'s default) — **not a real Ollama tag**, confirmed against `ollama.com/library/qwen3`'s tag list: Qwen3's dense models are instruct-capable by default and published under just their size (`qwen3:8b`, `qwen3:4b`, `qwen3:30b`, …); the `-instruct` suffix exists only for the separate 4B/30B/235B "2507" refreshes, none of which is the 8B size this architecture selected. This is why `ollama pull qwen3:8b-instruct` failed with "pull model manifest: file does not exist," which in turn made `ollama-init` exit non-zero and block `backend`/`worker` from ever starting (`depends_on: ollama-init: condition: service_completed_successfully`).

**Fix:** corrected the tag to `qwen3:8b` in all three locations. Same model, same architectural decision (Qwen 3 8B, self-hosted via Ollama) — only the tag string was wrong. `bge-m3` (the embedding model) was checked against `ollama.com/library/bge-m3` and is a valid, real tag — no change needed there. Verified live: `docker exec brandium-ollama-1 ollama pull qwen3:8b` was run directly against the already-running `ollama` container and began downloading immediately (no manifest error), confirming the corrected tag resolves.

## Full runtime verification session (this pass) — real bugs found via live execution, all fixed and re-verified

With Docker Desktop's WSL integration enabled on the host, `docker compose up` was run for real and driven end-to-end through the actual API (the same calls the frontend makes) to force every code path to execute for the first time ever in this project's history. This surfaced six genuine defects — none catchable by `ast.parse` or reasoning alone, all confirmed via real tracebacks and fixed via empirical reproduction before re-verifying live:

1. **`worker` never subscribed to its own queues.** `celery_app.py`'s `task_routes` sends tasks to `orchestration`/`worker.text_image`, but the `worker` service's command never passed `-Q` — a Celery worker only consumes the default `celery` queue otherwise. Every dispatched task would have sat in Redis forever. Fixed: added `-Q orchestration,worker.text_image` to the worker's command in `docker-compose.yml`.
2. **Every SQLAlchemy `Enum` column sent the wrong casing.** `Enum(SomeEnum, name="...")` defaults to binding a Python enum member's `.name` ("PROVISIONED") — but the Alembic migration created every Postgres enum type using the lowercase `.value` strings ("provisioned"), matching the API/frontend contract. Every INSERT touching any enum column failed. Fixed: added `values_callable=lambda obj: [e.value for e in obj]` to all 21 `Enum(...)` declarations across every bounded context's domain models.
3. **`SET LOCAL app.current_org_id = $1` is invalid SQL.** Postgres's `SET` statement doesn't accept a bind parameter for its value over asyncpg's extended query protocol — this is the RLS tenant-context call, invoked on literally every authenticated request, and had never executed successfully before this session. Fixed `tenant_context.py` to use `SELECT set_config('app.current_org_id', :org_id, true)` instead, which is a normal parameterized function call with identical `SET LOCAL` semantics.
4. **Genome compilation read `.id` off unflushed ORM objects.** `genome_compiler.py` built `GenomeCategory`/`GenomeComponent`/`Assertion` rows referencing their parent's `.id` before any of them had been flushed — SQLAlchemy's `default=` callables for primary keys only fire at flush time, so every FK column was `None`. Fixed by assigning `id=new_id()` explicitly at construction (IDs are client-generated UUIDs, not DB sequences, so there's no reason to wait on a flush round-trip). A related second bug in `genome_service.py`'s `create_draft()` — a single `add_all([*categories, *components, *assertions])` + one `flush()` did not reliably order the per-table INSERTs to satisfy FK constraints (observed: `assertions` attempted before every `genome_components` row existed, tripping a FK violation even with valid, consistent ids) — fixed by flushing in explicit dependency order (categories, then components, then assertions). The same unflushed-`.id` pattern was also found and fixed in `api/routers/users.py`'s role-grant endpoint (audit record was reading `grant.id` before a flush).
5. **The Celery worker process never registered every domain model.** `workers/tasks.py` only imported the specific repository/model modules it needed directly, never `identity_access.domain.models` (where `organizations` is mapped) — the API process gets this for free because `uvicorn src.main:app` transitively imports every router. The first flush of any tenant-scoped row inside a Celery task raised `NoReferencedTableError` for `organizations`. Fixed by importing `src.main` (for its registration side effect only) at the top of `workers/tasks.py`.
6. **The Phase 1 §10 validation gate correctly rejected an under-specified test Genome** ("Required category 'messaging_positioning' has no populated Component") — not a bug, confirmed by inspection; a richer Brand History document was ingested and recompiled instead.

**Genuinely verified live and working, end-to-end, through real HTTP calls against a real browser-reachable stack:** organization/user/workspace/brand creation, Brand History ingestion (including the MinIO upload path), Genome compilation via two real Ollama LLM calls (candidate extraction correctly categorized content into the right Genome Category/Component every time it was inspected directly), Phase 1 §10 validation correctly blocking an incomplete draft, three-step Genome activation (`Brand.active_genome_version_id` correctly set, `GenomeStatus` correctly staying non-`active` by the documented INV-09 design), Policy creation/activation, Campaign/Asset/AssetVersion creation, and the full Phase 4 Celery execution runtime dispatching a real AnalysisRun (`dispatch_analysis_run` → Applicability → Planning → a real Work Unit released to `execute_work_unit_task`, all visible in real time via `GET /analysis-runs/{id}/progress`).

**Not yet verified: a Text AnalysisRun's `text_worker` LLM call completing through to Decision/Recommendation/Report.** Two attempts both failed for the same reason — a real, reproducible hardware/resource-provisioning constraint of this specific host, not a code defect:

**Finding: this host's WSL2 memory budget (7.664GB total) is insufficient to run the full 8-container stack plus Ollama serving `qwen3:8b` under sustained load.** The resident model alone consumes ~5.4GB (70% of the entire budget) whenever loaded; combined with Postgres/Redis/MinIO/Qdrant/backend/worker/frontend, the system has almost no headroom left. Both attempted AnalysisRuns drove available memory to under 100MB free with swap fully exhausted, at which point: Docker's internal DNS resolution started failing intermittently (`Temporary failure in name resolution` — observed on both the Celery worker's and the FastAPI backend's Redis connections), and the Linux OOM killer killed a Celery `ForkPoolWorker` process outright (`signal 9 (SIGKILL)`) mid-task, permanently stranding that AnalysisRun in `running` with no automatic recovery (Celery's `task_acks_late` redelivery did not occur — most likely because the broker connection itself was one of the casualties of the DNS failures during the same window). Restarting the `ollama` container to force it to release its resident memory recovered the stack to healthy both times, but the underlying ceiling is unchanged and will recur on the next real AnalysisRun attempt under the current memory allocation.

**Recommended fix (host-level, outside this repository):** increase the WSL2 VM's memory allocation via `%UserProfile%\.wslconfig` (e.g. `[wsl2]\nmemory=16GB`) if the Windows host has more RAM to spare, then restart WSL (`wsl --shutdown` from PowerShell, then reopen). Docker Desktop's default WSL2 memory cap is commonly 50% of host RAM — if the host has 16GB total, that's exactly this 7.664GB ceiling. This is a host configuration change, not something fixable from inside the repository or this session.

---

## What this pass covered

Built on top of the previous passes' Domain Model, Authorization Service, Decision Engine, Brand Genome workflow, and Text+Image AI Pipeline **without rewriting any of them**. This pass's job was narrower and specific: replace the synchronous in-request analysis execution with the real Phase 4 execution runtime, and turn the frontend into the demonstration artifact itself.

### 1. Execution Runtime (Phase 4, in full)

Previously, `POST /analysis-runs` ran the entire pipeline synchronously inside the HTTP request. That's gone. Now:

- `POST /analysis-runs` only creates the AnalysisRun (`queued`) and calls `dispatch_analysis_run.delay(run_id, org_id)` — the request returns immediately.
- `workers/celery_app.py` — the Celery app (Redis broker + result backend), with routing for the two queues this build's worker roles actually use (`orchestration`, `worker.text_image`). Fixed a real defect in the Phase 0 scaffold here: the `worker` service's `docker-compose.yml` mount (`./workers:/workers`) put the package outside the image's `/app` WORKDIR, so `-A workers.celery_app` could never have resolved. Both `backend` and `worker` services now mount it at `/app/workers`, and `celery_app.py`'s path setup handles both the in-container layout and running locally from the repo root.
- `workers/tasks.py` — three tasks implementing Phase 4 §3's Orchestrator responsibilities:
  - `dispatch_analysis_run` — Stage 1 (Applicability) + Stage 2 (Planning), then releases every Work Unit as a Celery `chord` (parallel by construction, since Text/Image Work Units have no ordering dependency — Phase 4 §5's video-only dependency doesn't apply here).
  - `execute_work_unit_task` — one Work Unit's Invocation → Attempt → Resolution → Handoff (Phase 4 §4). Bounded retry (`max_retries=2`, exponential backoff) on transient failures; a Celery `soft_time_limit` maps to Phase 4 §2's `timed_out` state distinctly from `failed`. A Work Unit reaching a terminal failure state is returned normally, never raised through the chord — Completeness Verification, not Celery, is what's entitled to decide whether that fails the run.
  - `finalize_analysis_run` — the chord callback, guaranteed to run only once every Work Unit has reached a terminal state. Stage 4 (Evidence Fusion) → Stage 5 (Completeness Verification) → Decision Engine handoff → Recommendation generation → Report generation.
- `analysis_decision/analysis_orchestrator.py` was split into three stage functions (`plan_run`, `execute_work_unit`, `finalize_run`) so the business logic stays framework-agnostic — `workers/tasks.py` owns session/retry/progress plumbing only, never `src.*`.
- `analysis_decision/execution_progress.py` (new) — Redis-backed Work Unit + pipeline-stage tracking (Phase 4 §11's real-time visibility requirement). Work Units are explicitly not a persisted domain entity (Phase 4 §2), so Redis — already the Celery broker — is the right store, with a bounded TTL; Postgres remains the durable record of what actually happened.
- `GET /analysis-runs/{run_id}/progress` (new) — the endpoint the frontend polls.
- Every Celery task opens its own DB session and sets `SET LOCAL app.current_org_id` exactly like the API request path does (RLS is enforced identically regardless of which process issued the query); `org_id` is passed into every task explicitly by the API caller rather than derived from the (RLS-protected) AnalysisRun row itself.

### 2. Frontend — the demonstration artifact

Rebuilt from plain fetch+useState pages into an enterprise-styled app:
- Dependencies added: TanStack Query, React Hook Form + Zod, Framer Motion, class-variance-authority, clsx/tailwind-merge, lucide-react.
- `components/ui/*` — hand-written shadcn-style primitives (Button, Card, Badge, Progress, Tabs, Input, Select) — no Radix, to keep everything verifiable by inspection given this sandbox cannot run `tsc`.
- `components/nav-shell.tsx` — persistent top navigation across every authenticated screen.
- `components/pipeline-track.tsx` — the live 9-stage pipeline visualization (Applicability → Planning → Worker Execution → Evidence Fusion → Completeness → Decision Engine → Recommendations → Report), with per-Work-Unit state shown underneath, polling `/analysis-runs/{id}/progress` via TanStack Query (`refetchInterval`, stops once `complete`/`failed`).
- `analysis/[runId]/page.tsx` — rebuilt around that live view; once the run completes, five tabs appear (Overview/BDI score, Evidence, Recommendations, Explainability drill-down, Report with approve/flag).
- Explainability drill-down now goes one step further than before: `explainability_service.py` returns `asset` (the original uploaded content's name/modality) and `brand_id`; a new `GET /brands/{brand_id}/history` endpoint lets the frontend resolve each Assertion's `source_reference_ids` back to the Brand History document it came from — completing the BDI → Category → Component → Assertion → Evidence → Brand History → Original Asset chain.
- Dashboard, Brand Genome Explorer (now tabbed: History/Genome/Policy), and Upload Workspace were all restyled on the same design system; Upload now redirects straight to the Live Analysis Progress view instead of waiting on a synchronous response.

### 3. Everything from prior passes, unchanged

Brand Genome workflow, Text+Image AI Pipeline, Decision Engine, Recommendation narration, RBAC/RLS, and seed data (`scripts/seed_data.py`, Red Bull + Apple via the real ingestion pipeline) are untouched by this pass except where the execution runtime now calls into them via Celery tasks instead of directly from the API.

---

## Runtime verification performed / not performed

**Performed:** the Decision Engine, Authorization Service, and Evidence Fusion module (all dependency-free) were re-verified to still execute correctly after this pass's changes — nothing in this pass touched their logic, only how they're invoked.

**Not performed, same constraint as every prior pass:** no `pip`/`docker` access in this sandbox — Celery, Redis, Postgres, and a real frontend build/typecheck are all unavailable here. Everything new in this pass is **static-checked only**: all 91 backend `.py` files under `backend/src`, `workers/`, and `scripts/` parse cleanly via `ast.parse` (zero syntax errors); all 18 frontend `.ts`/`.tsx` files pass a bracket-balance sanity check (not a real `tsc` compile). The Celery task graph (chord composition, retry/timeout handling, RLS-scoped sessions inside worker processes) has been reasoned through carefully but **has not been executed once**. Please run `docker compose up`, apply the migration, and drive the dashboard → brand → upload → live progress → results flow in a browser — that is the verification this sandbox cannot perform, and nothing here should be taken as a substitute for it.

---

## What remains

1. **Tests** — unit/integration/API/Playwright E2E and the tenant-isolation suite are still not written for the Genome/Pipeline/API/Celery code from this and the prior pass.
2. **Video** — untouched, as instructed.
3. **Observability, Grafana/Loki/Prometheus wiring, enterprise administration, ops dashboards** — untouched, as instructed.
4. **Maker-checker Policy overlay** (Phase 5 §4's enterprise-configurable option) — base activation path only.
5. **Retry bound tuning, concurrency limits** — Phase 4 §14 explicitly leaves these as tuning decisions; `max_retries=2` and a 120s soft time limit are reasonable defaults, not measured ones.
6. **First real end-to-end run** — see "Runtime verification" above.

## Next steps

Bring the stack up and run one real AnalysisRun through it (this surfaces any session/import-path mistakes static analysis can't catch), then tests, in the order: dependency-free unit tests first, then integration/API tests once the stack is confirmed running.
