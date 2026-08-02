"""Per-request tenant context: the application-layer half of RLS (Phase 0
§6, CLAUDE.md §4.3). Migration 0001 enables RLS policies keyed on
`current_setting('app.current_org_id')`; this module is what actually
sets that session variable for the duration of one request/transaction,
scoped with `SET LOCAL` so it never leaks across pooled connections.
"""
from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_tenant_context(session: AsyncSession, org_id: uuid.UUID) -> None:
    """Must be called inside an open transaction on `session` before any
    tenant-scoped query — `SET LOCAL` only takes effect within the
    current transaction and is automatically cleared at commit/rollback,
    so there is no cross-request leakage risk even under connection pooling.

    Uses `set_config(..., true)` rather than a literal `SET LOCAL` string:
    Postgres's `SET` statement does not accept a bind parameter for its
    value over the extended query protocol asyncpg uses (`SET LOCAL
    app.current_org_id = $1` is a syntax error) — `set_config()` is a
    regular function call and accepts one normally. `is_local=true` is
    exactly equivalent to `SET LOCAL`'s transaction-scoped behavior.
    """
    await session.execute(
        text("SELECT set_config('app.current_org_id', :org_id, true)"), {"org_id": str(org_id)}
    )
