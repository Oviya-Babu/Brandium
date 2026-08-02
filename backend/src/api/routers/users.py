"""User & RoleAssignment endpoints (Phase 0 §3.3, Phase 5 §2, Phase 6 §3).

**Bootstrap exception, flagged explicitly:** self-escalation prevention
(Phase 6 §3) requires a RoleAssignment grant come from "a second, distinct
actor" — but the very first User in a brand-new Organization has no other
actor to grant them anything. Neither Phase 5 nor Phase 6 addresses this
org-bootstrap case. This module resolves it the same way most real RBAC
systems do (an AWS/GCP-style root-account bootstrap): a User created for
an Organization that provably has zero existing Users is auto-granted
OrganizationAdministrator, `granted_by` set to their own id — a narrow,
audited, one-time exception, never available once the Organization has
any User at all. Every subsequent grant goes through the ordinary
`authorization.authorize_role_grant` path with its unconditional
self-grant rejection.

**A second consequence of the same bootstrap gap, resolved the same way:**
Phase 5 §5/§7 deliberately keep OrganizationAdministrator (membership/access)
and BrandAdministrator (Genome/Policy content) as distinct grants — "has
no implied access to any Brand's Genome... unless separately granted."
For a brand-new, single-person Organization this is a real deadlock: the
bootstrap user cannot self-grant BrandAdministrator either (same
unconditional self-grant rejection), and no second actor exists yet to
grant it for them. Rather than silently working around this, the
bootstrap exception is widened to grant BOTH roles, organization-tier, to
this same first User — this mirrors how virtually every real SaaS
product treats its first signup as a full tenant administrator, and
remains a one-time, audited, zero-existing-Users-only exception.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.identity_access.authorization import AuthorizationContext, RoleAssignmentView, authorize_role_grant
from src.identity_access.domain.enums import MembershipStatus, Role, ScopeTier
from src.identity_access.domain.models import Membership, RoleAssignment, User
from src.platform_governance.audit_service import AuditService
from src.platform_governance.domain.models import AuditActorType
from src.platform_governance.repository import AuditLogRepository
from src.shared_kernel.db import get_session

router = APIRouter(prefix="/organizations/{org_id}/users", tags=["users"])


class UserCreate(BaseModel):
    email: str


class UserOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    email: str

    class Config:
        from_attributes = True


@router.post("", response_model=UserOut, status_code=201)
async def create_user(org_id: uuid.UUID, body: UserCreate, session: AsyncSession = Depends(get_session)) -> User:
    # `User.email` is globally unique by design (one email is one real
    # person's identity across the whole system, not per-Organization —
    # see the domain model). Without this check, a second signup with an
    # already-registered email (e.g. retrying Signup after an earlier
    # attempt actually succeeded, confirmed live as a real user's actual
    # sequence of events) fell through to Postgres's unique-constraint
    # violation, an uncaught `IntegrityError` that surfaced to the
    # browser as a bare "500 Internal Server Error" with no indication
    # of what actually went wrong or what to do about it.
    existing_email_user = (await session.execute(select(User).where(User.email == body.email))).scalars().first()
    if existing_email_user is not None:
        raise HTTPException(
            status_code=409,
            detail=f"An account with email '{body.email}' already exists — log in instead of creating a new organization.",
        )

    existing_count = (
        await session.execute(select(User).where(User.org_id == org_id))
    ).scalars().first()

    user = User(org_id=org_id, email=body.email, auth_identity_ref=f"placeholder:{body.email}")
    session.add(user)
    await session.flush()

    membership = Membership(org_id=org_id, user_id=user.id, status=MembershipStatus.ACTIVE)
    session.add(membership)

    audit = AuditService(AuditLogRepository(session))

    if existing_count is None:
        # Bootstrap exception — see module docstring. Both roles granted
        # so the first user can administer membership AND author/activate
        # Genome/Policy content for the organization they just created.
        for role in (Role.ORGANIZATION_ADMINISTRATOR, Role.BRAND_ADMINISTRATOR):
            session.add(
                RoleAssignment(
                    org_id=org_id,
                    user_id=user.id,
                    role=role,
                    scope_tier=ScopeTier.ORGANIZATION,
                    scope_id=org_id,
                    granted_by=user.id,
                    granted_at=datetime.now(timezone.utc),
                )
            )
        await audit.record(
            org_id=org_id, actor_id=user.id, actor_type=AuditActorType.USER,
            action_type="role_assignment.bootstrap_granted", target_entity="User", target_id=user.id,
        )

    await session.commit()
    return user


class RoleGrantRequest(BaseModel):
    recipient_user_id: uuid.UUID
    role: Role
    scope_tier: ScopeTier
    scope_id: uuid.UUID


@router.post("/{granting_user_id}/grants", status_code=201)
async def grant_role(
    org_id: uuid.UUID,
    granting_user_id: uuid.UUID,
    body: RoleGrantRequest,
    session: AsyncSession = Depends(get_session),
):
    """Phase 6 §3 self-escalation prevention enforced here, not only in
    the UI (CLAUDE.md §4.2)."""
    assignments = (
        await session.execute(
            select(RoleAssignment).where(RoleAssignment.user_id == granting_user_id, RoleAssignment.revoked_at.is_(None))
        )
    ).scalars().all()
    granter_ctx = AuthorizationContext(
        membership_status=MembershipStatus.ACTIVE,
        assignments=tuple(
            RoleAssignmentView(role=a.role, scope_tier=a.scope_tier, scope_id=a.scope_id, revoked_at=a.revoked_at)
            for a in assignments
        ),
    )

    try:
        authorize_role_grant(
            granting_user_id=granting_user_id,
            recipient_user_id=body.recipient_user_id,
            granter_ctx=granter_ctx,
            org_id=org_id,
            new_grant_tier=body.scope_tier,
            new_grant_scope_id=body.scope_id,
        )
    except (PermissionError,) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:  # SelfEscalationError
        await AuditService(AuditLogRepository(session)).record(
            org_id=org_id, actor_id=granting_user_id, actor_type=AuditActorType.USER,
            action_type="role_assignment.denied_self_escalation", target_entity="User", target_id=body.recipient_user_id,
        )
        await session.commit()
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    grant = RoleAssignment(
        org_id=org_id,
        user_id=body.recipient_user_id,
        role=body.role,
        scope_tier=body.scope_tier,
        scope_id=body.scope_id,
        granted_by=granting_user_id,
        granted_at=datetime.now(timezone.utc),
    )
    session.add(grant)
    await session.flush()  # grant.id is a client-side UUID default — only populated on the object after a flush, and the audit record below needs the real value, not None.
    await AuditService(AuditLogRepository(session)).record(
        org_id=org_id, actor_id=granting_user_id, actor_type=AuditActorType.USER,
        action_type="role_assignment.granted", target_entity="RoleAssignment", target_id=grant.id,
    )
    await session.commit()
    return {"id": str(grant.id)}
