"""Cross-tenant-leakage tests (CLAUDE.md §7, §4.3) — required for every
tenant-scoped read/write path: attempt a cross-tenant read/write and
assert denial, at both the application and RLS layers.

These tests need a real PostgreSQL instance with the RLS policies from
migration 0001 applied (RLS is Postgres-specific; SQLite has no
equivalent), and they need the per-request `SET LOCAL app.current_org_id`
middleware that is explicitly deferred to the next milestone (see
migration 0001's docstring). Both are absent in this Phase 0 scaffolding
pass, so this suite is marked skipped rather than faked against SQLite —
a stub that "passes" without exercising RLS would be worse than an
honest, visible gap (CLAUDE.md §7: no TODO standing in for an
unimplemented invariant).

TODO(milestone-1): replace this skip with real tests once the
docker-compose Postgres service, the `SET LOCAL app.current_org_id`
request middleware, and a live test-database fixture exist.
"""
import pytest

pytestmark = pytest.mark.skip(
    reason="Requires a live Postgres instance with migration 0001 applied "
    "and the org-context request middleware — both land in the domain "
    "foundation milestone (CLAUDE.md Milestone 1), not this Phase 0 pass."
)


def test_cross_tenant_read_is_denied_by_rls() -> None:
    raise NotImplementedError
