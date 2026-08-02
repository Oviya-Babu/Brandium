"""Campaign & Asset endpoints (Phase 0 §3.9/§3.10, FR-004)."""
from __future__ import annotations

import mimetypes
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CurrentActor, get_current_actor, get_object_storage
from src.campaign_asset.domain.models import Asset, AssetModality, AssetVersion, Campaign, CampaignStatus
from src.campaign_asset.repository import AssetRepository, AssetVersionRepository
from src.shared_kernel.db import get_session
from src.shared_kernel.object_storage import ObjectStorageClient

router = APIRouter(tags=["campaigns", "assets"])


class CampaignCreate(BaseModel):
    brand_id: uuid.UUID
    name: str


class CampaignOut(BaseModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    name: str
    status: CampaignStatus

    class Config:
        from_attributes = True


class AssetOut(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    name: str
    modality: AssetModality

    class Config:
        from_attributes = True


class AssetVersionOut(BaseModel):
    id: uuid.UUID
    asset_id: uuid.UUID
    version_number: int
    storage_ref: str
    content_hash: str

    class Config:
        from_attributes = True


@router.post("/campaigns", response_model=CampaignOut, status_code=201)
async def create_campaign(
    body: CampaignCreate,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> Campaign:
    campaign = Campaign(org_id=actor.org_id, brand_id=body.brand_id, name=body.name, status=CampaignStatus.ACTIVE)
    session.add(campaign)
    await session.flush()
    await session.commit()
    return campaign


@router.post("/campaigns/{campaign_id}/assets", response_model=AssetOut, status_code=201)
async def create_asset(
    campaign_id: uuid.UUID,
    name: str,
    modality: AssetModality,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
) -> Asset:
    asset = Asset(org_id=actor.org_id, campaign_id=campaign_id, name=name, modality=modality)
    session.add(asset)
    await session.flush()
    await session.commit()
    return asset


@router.post("/assets/{asset_id}/versions", response_model=AssetVersionOut, status_code=201)
async def upload_asset_version(
    asset_id: uuid.UUID,
    file: UploadFile,
    context_tags: str = "",
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorageClient = Depends(get_object_storage),
) -> AssetVersion:
    """FR-004: content upload, subject to Pre-Phase-7 correction 4's
    precondition (the Brand must have an active Genome+Policy) — enforced
    at the analysis-trigger endpoint, not here, since upload itself is
    always legal (a Report just can't be produced from it yet)."""
    import hashlib

    content = await file.read()
    content_hash = hashlib.sha256(content).hexdigest()

    version_repo = AssetVersionRepository(session)
    asset_repo = AssetRepository(session)
    asset = await asset_repo.get_by_id(asset_id)
    if asset is None or asset.org_id != actor.org_id:
        raise HTTPException(status_code=404, detail="Asset not found.")

    storage_ref = storage.put_object(
        org_id=actor.org_id, key_prefix=f"assets/{asset_id}", filename=file.filename or "upload", content=content
    )
    version_number = await version_repo.next_version_number(asset_id)

    version = AssetVersion(
        org_id=actor.org_id,
        asset_id=asset_id,
        version_number=version_number,
        uploaded_by=actor.user_id,
        uploaded_at=datetime.now(timezone.utc),
        storage_ref=storage_ref,
        content_hash=content_hash,
        context_tags=[t.strip() for t in context_tags.split(",") if t.strip()],
    )
    await version_repo.add(version)
    await session.commit()
    return version


@router.get("/asset-versions/{version_id}/content")
async def get_asset_version_content(
    version_id: uuid.UUID,
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorageClient = Depends(get_object_storage),
):
    """Streams the raw uploaded bytes back through the backend — object
    access is always mediated here, never a direct-to-storage URL (see
    `ObjectStorageClient.put_object`'s docstring). Backs the Analysis
    page's asset preview; content type is guessed from the original
    filename embedded in `storage_ref` since uploads don't persist one."""
    version = await AssetVersionRepository(session).get_by_id(version_id)
    if version is None or version.org_id != actor.org_id:
        raise HTTPException(status_code=404, detail="AssetVersion not found.")
    content = storage.get_object(version.storage_ref)
    media_type = mimetypes.guess_type(version.storage_ref)[0] or "application/octet-stream"
    return Response(content=content, media_type=media_type)
