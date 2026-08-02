"""Brand History ingestion endpoint (Phase 1 §5 step 1, FR-001)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Form, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import CurrentActor, get_current_actor, get_object_storage
from src.brand_governance.brand_history_service import BrandHistoryService
from src.brand_governance.domain.models import BrandHistoryAuthorityLevel, BrandHistoryModality, BrandHistorySourceType
from src.brand_governance.repository import BrandHistoryRepository
from src.shared_kernel.db import get_session
from src.shared_kernel.object_storage import ObjectStorageClient

router = APIRouter(prefix="/brands/{brand_id}/history", tags=["brand-history"])


class BrandHistoryOut(BaseModel):
    id: uuid.UUID
    brand_id: uuid.UUID
    source_type: BrandHistorySourceType
    modality: BrandHistoryModality
    authority_level: BrandHistoryAuthorityLevel
    era_tag: str | None
    storage_ref: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[BrandHistoryOut])
async def list_brand_history(
    brand_id: uuid.UUID, actor: CurrentActor = Depends(get_current_actor), session: AsyncSession = Depends(get_session)
):
    """Backs the Explainability drill-down's last step (Assertion ->
    Brand History, Phase 1 §7 provenance) and the Genome Explorer's
    History tab — lists what has already been ingested for this Brand."""
    items = await BrandHistoryRepository(session).list_for_brand(brand_id)
    return items


@router.post("", response_model=BrandHistoryOut, status_code=201)
async def ingest_brand_history(
    brand_id: uuid.UUID,
    file: UploadFile,
    source_type: BrandHistorySourceType = Form(...),
    modality: BrandHistoryModality = Form(...),
    authority_level: BrandHistoryAuthorityLevel = Form(...),
    era_tag: str | None = Form(None),
    actor: CurrentActor = Depends(get_current_actor),
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorageClient = Depends(get_object_storage),
):
    content = await file.read()
    service = BrandHistoryService(BrandHistoryRepository(session), storage)
    item = await service.ingest(
        org_id=actor.org_id,
        brand_id=brand_id,
        source_type=source_type,
        modality=modality,
        authority_level=authority_level,
        era_tag=era_tag,
        filename=file.filename or "upload",
        content=content,
        content_type=file.content_type or "application/octet-stream",
    )
    await session.commit()
    return item
