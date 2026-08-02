"""Brand History ingestion (Phase 1 §4/§5 step 1, FR-001). Accepts brand
guideline documents, logos, design systems, and historical campaigns;
stores the raw asset durably and, for document-type sources, extracts
text for later compilation input."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from src.brand_governance.document_processing import extract_text
from src.brand_governance.domain.models import BrandHistory, BrandHistoryModality, BrandHistorySourceType
from src.brand_governance.repository import BrandHistoryRepository
from src.shared_kernel.object_storage import ObjectStorageClient

_DOCUMENT_SOURCE_TYPES = {BrandHistorySourceType.GUIDELINE_DOCUMENT, BrandHistorySourceType.DESIGN_SYSTEM_SPEC}


class BrandHistoryService:
    def __init__(self, repo: BrandHistoryRepository, storage: ObjectStorageClient) -> None:
        self._repo = repo
        self._storage = storage

    async def ingest(
        self,
        *,
        org_id: uuid.UUID,
        brand_id: uuid.UUID,
        source_type: BrandHistorySourceType,
        modality: BrandHistoryModality,
        authority_level,
        era_tag: str | None,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> BrandHistory:
        storage_ref = self._storage.put_object(
            org_id=org_id, key_prefix=f"brand_history/{brand_id}", filename=filename, content=content
        )

        extracted_text: str | None = None
        if source_type in _DOCUMENT_SOURCE_TYPES or modality == BrandHistoryModality.TEXT:
            try:
                extracted_text = extract_text(content, content_type)
            except ValueError:
                # Unsupported content type for text extraction (e.g. a raw
                # image logo tagged design_system_spec) — legitimate, not
                # an error; this item contributes to compilation without
                # text-based candidate extraction.
                extracted_text = None

        item = BrandHistory(
            org_id=org_id,
            brand_id=brand_id,
            source_type=source_type,
            modality=modality,
            authority_level=authority_level,
            era_tag=era_tag,
            storage_ref=storage_ref,
            extracted_text=extracted_text,
            ingested_at=datetime.now(timezone.utc),
        )
        return await self._repo.add(item)
