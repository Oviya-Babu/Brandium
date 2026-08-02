"""Policy endpoints (Phase 0 §3.7, Phase 2 §2.1/§10)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.dependencies import CurrentActor, get_current_actor
from src.brand_governance.domain.models import PolicyStatus
from src.brand_governance.policy_service import PolicyActivationError, PolicyService
from src.brand_governance.repository import BrandGenomeRepository, BrandRepository, PolicyRepository
from src.identity_access.authorization import has_role
from src.identity_access.domain.enums import Role, ScopeTier
from src.platform_governance.audit_service import AuditService
from src.platform_governance.repository import AuditLogRepository
from src.shared_kernel.db import get_session

router = APIRouter(prefix="/brands/{brand_id}/policies", tags=["policies"])


class PolicyCreate(BaseModel):
    rules: dict


class PolicyOut(BaseModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    version_number: int
    status: PolicyStatus
    rules: dict | None

    class Config:
        from_attributes = True


def _service(session) -> PolicyService:
    return PolicyService(
        PolicyRepository(session), BrandRepository(session), BrandGenomeRepository(session),
        AuditService(AuditLogRepository(session)),
    )


@router.post("", response_model=PolicyOut, status_code=201)
async def create_policy_draft(
    brand_id: uuid.UUID,
    body: PolicyCreate,
    actor: CurrentActor = Depends(get_current_actor),
    session=Depends(get_session),
):
    if not has_role(actor.authorization, actor.org_id, ScopeTier.BRAND, brand_id, Role.BRAND_ADMINISTRATOR):
        raise HTTPException(status_code=403, detail="Requires BrandAdministrator at this Brand's scope.")
    service = _service(session)
    policy = await service.create_draft(org_id=actor.org_id, brand_id=brand_id, rules=body.rules, actor_id=actor.user_id)
    await session.commit()
    return policy


@router.get("/{policy_id}", response_model=PolicyOut)
async def get_policy(
    brand_id: uuid.UUID,
    policy_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session=Depends(get_session),
):
    policy = await PolicyRepository(session).get_by_id(policy_id)
    if policy is None or policy.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Policy not found.")
    return policy


@router.post("/{policy_id}/activate", response_model=PolicyOut)
async def activate_policy(
    brand_id: uuid.UUID,
    policy_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session=Depends(get_session),
):
    if not has_role(actor.authorization, actor.org_id, ScopeTier.BRAND, brand_id, Role.BRAND_ADMINISTRATOR):
        raise HTTPException(status_code=403, detail="Requires BrandAdministrator at this Brand's scope.")
    repo = PolicyRepository(session)
    policy = await repo.get_by_id(policy_id)
    if policy is None or policy.brand_id != brand_id:
        raise HTTPException(status_code=404, detail="Policy not found.")
    service = _service(session)
    try:
        await service.activate(policy=policy, actor_id=actor.user_id)
    except PolicyActivationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    await session.commit()
    return policy
