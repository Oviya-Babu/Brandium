"""Liveness/readiness endpoint. Deliberately the only route in Phase 0 —
no business endpoints exist yet (CLAUDE.md: "Do NOT implement business
logic yet" for this milestone). Thin router, per CLAUDE.md §3.1."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
