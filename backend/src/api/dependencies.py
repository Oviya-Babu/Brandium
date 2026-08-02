"""FastAPI dependency providers — DI foundation (Technology Stack §3/§4).

**Explicitly not real authentication.** No Auth0/JWT integration exists
in this pass (out of scope per the original kickoff instruction, never
revisited since). `get_current_actor` below is a clearly-labeled,
header-based stand-in — `X-User-Id`/`X-Organization-Id` — so the RBAC
and tenant-isolation *mechanisms* (which are in scope) can be built and
exercised against something. Swapping this for real JWT validation is a
contained change to this one function, not an architectural one.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.identity_access.authorization import AuthorizationContext, RoleAssignmentView
from src.identity_access.domain.enums import MembershipStatus
from src.identity_access.domain.models import Membership, RoleAssignment, User
from src.shared_kernel.db import get_session
from src.shared_kernel.llm.client import LLMClient
from src.shared_kernel.object_storage import ObjectStorageClient
from src.shared_kernel.tenant_context import set_tenant_context


@dataclass(frozen=True)
class CurrentActor:
    user_id: uuid.UUID
    org_id: uuid.UUID
    authorization: AuthorizationContext


async def get_current_actor(
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_organization_id: str = Header(..., alias="X-Organization-Id"),
    session: AsyncSession = Depends(get_session),
) -> CurrentActor:
    try:
        user_id = uuid.UUID(x_user_id)
        org_id = uuid.UUID(x_organization_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid actor identity headers.") from exc

    await set_tenant_context(session, org_id)

    user = await session.get(User, user_id)
    if user is None or user.org_id != org_id:
        # Fail-safe (INV-31): an unresolvable identity denies, never permits.
        raise HTTPException(status_code=401, detail="Unknown actor for this organization.")

    membership = (
        await session.execute(select(Membership).where(Membership.user_id == user_id))
    ).scalar_one_or_none()
    membership_status = membership.status if membership else MembershipStatus.REMOVED

    assignments_result = await session.execute(
        select(RoleAssignment).where(RoleAssignment.user_id == user_id, RoleAssignment.revoked_at.is_(None))
    )
    assignments = tuple(
        RoleAssignmentView(role=a.role, scope_tier=a.scope_tier, scope_id=a.scope_id, revoked_at=a.revoked_at)
        for a in assignments_result.scalars().all()
    )

    return CurrentActor(
        user_id=user_id,
        org_id=org_id,
        authorization=AuthorizationContext(membership_status=membership_status, assignments=assignments),
    )


def get_llm_client() -> LLMClient:
    return LLMClient()


def get_object_storage() -> ObjectStorageClient:
    return ObjectStorageClient()
