"""Bounded Context 2 — Brand Governance (Phase 0 §3.5-3.8, CLAUDE.md §1.5).

Owns: Brand, BrandGenome, Policy, BrandHistory. Schema only — Genome
compilation, the activation workflow (Phase 0 §3.6's atomic three-step
operation, INV-15), and Policy authoring are later milestones
(CLAUDE.md §14 Milestone 2), not implemented here.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared_kernel.db import Base, TenantScopedMixin
from src.shared_kernel.mixins import UUIDPrimaryKeyMixin


class BrandStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class GenomeStatus(str, enum.Enum):
    """No `active` value by design (Phase 0 §3.6/§3.5) — a version is
    "active" solely by being the target of `Brand.active_genome_version_id`
    (INV-09), never by a stored status flag."""

    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class PolicyStatus(str, enum.Enum):
    """Same pointer-based activation pattern as Genome (Phase 0 §3.7)."""

    DRAFT = "draft"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class BrandHistorySourceType(str, enum.Enum):
    CAMPAIGN = "campaign"
    AD = "ad"
    SOCIAL = "social"
    VIDEO = "video"


class Brand(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.5 — carries the version pointers.

    Invariant (INV-09, enforced by construction): exactly one active
    Genome version and exactly one active Policy version can exist per
    Brand at any time, because each is a single nullable FK that can
    point to at most one row — never a `status = active` convention.
    """

    __tablename__ = "brands"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[BrandStatus] = mapped_column(
        Enum(BrandStatus, name="brand_status"), nullable=False, default=BrandStatus.ACTIVE
    )
    active_genome_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("brand_genomes.id", use_alter=True, name="fk_brand_active_genome_version"),
        nullable=True,
    )
    active_policy_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("policies.id", use_alter=True, name="fk_brand_active_policy_version"),
        nullable=True,
    )


class BrandGenome(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.6 — versioned, immutable once pointed-to by
    `Brand.active_genome_version_id`."""

    __tablename__ = "brand_genomes"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[GenomeStatus] = mapped_column(
        Enum(GenomeStatus, name="genome_status"), nullable=False, default=GenomeStatus.DRAFT
    )
    compiled_from: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    activated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="Required, non-null the moment this version is pointed-to (DR-006, INV-15).",
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Policy(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.7 — same versioned pattern as BrandGenome. `rules`
    payload shape is deferred to Phase 2 (Decision Architecture)."""

    __tablename__ = "policies"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus, name="policy_status"), nullable=False, default=PolicyStatus.DRAFT
    )
    rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class BrandHistory(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.8 (DR-008 rename from "Brand Evidence"). Repository of
    historical marketing assets; query scope is Genome-compilation-input
    only, never used at analysis time (Phase 0 §9.4)."""

    __tablename__ = "brand_history_items"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    source_type: Mapped[BrandHistorySourceType] = mapped_column(
        Enum(BrandHistorySourceType, name="brand_history_source_type"), nullable=False
    )
    storage_ref: Mapped[str] = mapped_column(String, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
