"""Pre-Phase-C session bootstrap (placeholder, not authentication).

There is no password/credential storage yet (Phase C, explicitly
deferred) — every request today is trusted via the `X-User-Id`/
`X-Organization-Id` headers `api/dependencies.py` reads verbatim. This
endpoint exists only so the Login page has something real to call
instead of faking a password check: given an email, it looks up the
real `User`/`Organization` row so the frontend can populate those same
headers for a *returning* user, exactly as Signup already does for a
*new* one. It is not a security boundary and must not be treated as one
once real authentication lands.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.identity_access.domain.models import Organization, User
from src.shared_kernel.db import get_session

router = APIRouter(prefix="/session", tags=["session"])


class SessionLookupOut(BaseModel):
    user_id: uuid.UUID
    org_id: uuid.UUID
    org_name: str
    email: str


@router.get("/lookup", response_model=SessionLookupOut)
async def lookup_by_email(email: str, session: AsyncSession = Depends(get_session)):
    """No tenant context is set before this query, deliberately —
    mirrors `organizations.py`'s `create_organization`/`users.py`'s
    `create_user`: resolving *which* organization an actor belongs to
    necessarily precedes having that context to scope by."""
    user = (await session.execute(select(User).where(User.email == email))).scalars().first()
    if user is None:
        raise HTTPException(status_code=404, detail="No account found for this email.")
    org = await session.get(Organization, user.org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="No account found for this email.")
    return SessionLookupOut(user_id=user.id, org_id=org.id, org_name=org.name, email=user.email)
