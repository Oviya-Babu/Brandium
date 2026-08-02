"""Bounded Context 3 — Campaign & Asset Management (Phase 0 §3.9-3.10).

Owns: Campaign, Asset, AssetVersion. Schema only — upload endpoints and
campaign-versioning/trend logic (FR-010) are later milestones.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared_kernel.db import Base, TenantScopedMixin
from src.shared_kernel.mixins import UUIDPrimaryKeyMixin


class CampaignStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class AssetModality(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class Campaign(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.9."""

    __tablename__ = "campaigns"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus, name="campaign_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=CampaignStatus.ACTIVE
    )


class Asset(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.10."""

    __tablename__ = "assets"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    campaign_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campaigns.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    modality: Mapped[AssetModality] = mapped_column(Enum(AssetModality, name="asset_modality", values_callable=lambda obj: [e.value for e in obj]), nullable=False)


class AssetVersion(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.10 — append-only (INV-13); concurrent uploads never
    conflict, each is simply its own version."""

    __tablename__ = "asset_versions"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assets.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    storage_ref: Mapped[str] = mapped_column(String, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    context_tags: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        comment="Phase 3 addendum: part of the Evaluation Context (with modality) "
        "that Applicability Determination consumes (Phase 3 §2).",
    )
