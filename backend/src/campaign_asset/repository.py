from __future__ import annotations

import uuid

from sqlalchemy import select

from src.campaign_asset.domain.models import Asset, AssetVersion, Campaign
from src.shared_kernel.repository import BaseRepository


class CampaignRepository(BaseRepository[Campaign]):
    model = Campaign


class AssetRepository(BaseRepository[Asset]):
    model = Asset


class AssetVersionRepository(BaseRepository[AssetVersion]):
    model = AssetVersion

    async def next_version_number(self, asset_id: uuid.UUID) -> int:
        stmt = select(AssetVersion).where(AssetVersion.asset_id == asset_id)
        result = await self._session.execute(stmt)
        existing = list(result.scalars().all())
        return (max((v.version_number for v in existing), default=0)) + 1
