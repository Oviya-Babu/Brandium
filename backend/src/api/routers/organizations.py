"""Organization & Workspace endpoints (Phase 0 §3.1/§3.2, Phase 5 §1)."""
from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CurrentActor, get_current_actor
from src.brand_governance.domain.models import Brand, BrandStatus
from src.identity_access.domain.models import Organization, OrganizationStatus, Workspace
from src.shared_kernel.db import get_session

router = APIRouter(prefix="/organizations", tags=["organizations"])


class OrganizationCreate(BaseModel):
    name: str


class OrganizationOut(BaseModel):
    id: uuid.UUID
    name: str
    status: OrganizationStatus
    created_at: datetime

    class Config:
        from_attributes = True


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    name: str

    class Config:
        from_attributes = True


@router.post("", response_model=OrganizationOut, status_code=201)
async def create_organization(body: OrganizationCreate, session: AsyncSession = Depends(get_session)) -> Organization:
    """Organization onboarding (PRD §11.1 step 1) — no auth/RBAC gate
    here by design: creating the very first Organization necessarily
    precedes any actor having a RoleAssignment within it."""
    org = Organization(name=body.name, status=OrganizationStatus.PROVISIONED)
    session.add(org)
    await session.flush()
    await session.commit()
    return org


@router.get("/{org_id}", response_model=OrganizationOut)
async def get_organization(org_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Organization:
    org = await session.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found.")
    return org


@router.post("/{org_id}/workspaces", response_model=WorkspaceOut, status_code=201)
async def create_workspace(
    org_id: uuid.UUID, body: WorkspaceCreate, session: AsyncSession = Depends(get_session)
) -> Workspace:
    workspace = Workspace(org_id=org_id, name=body.name)
    session.add(workspace)
    await session.flush()
    await session.commit()
    return workspace


class BrandSummaryOut(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    status: BrandStatus
    active_genome_version_id: uuid.UUID | None
    active_policy_version_id: uuid.UUID | None

    class Config:
        from_attributes = True


@router.get("/{org_id}/brands", response_model=list[BrandSummaryOut])
async def list_brands(
    org_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
):
    """Dashboard's real brand list (PRD §11.1) — previously the frontend
    only had `localStorage`'s own creation history to show, which is
    empty on a new browser/device even though the brands themselves are
    real, persisted rows."""
    result = await session.execute(select(Brand).where(Brand.org_id == org_id).order_by(Brand.name))
    return list(result.scalars().all())
