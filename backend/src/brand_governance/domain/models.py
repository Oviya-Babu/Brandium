"""Bounded Context 2 — Brand Governance (Phase 0 §3.5-3.8, Phase 1 §1-§7).

Owns: Brand, BrandGenome, Policy, BrandHistory, and BrandGenome's internal
structure (GenomeCategory/GenomeComponent/Assertion — Phase 1 §1, elaborating
BrandGenome's aggregate content per Phase 1 §0, not new aggregate roots).
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text
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
    """Phase 1 §0 additive extension: `guideline_document`/`design_system_spec`
    alongside Phase 0's original four values (FR-001 onboarding inputs)."""

    GUIDELINE_DOCUMENT = "guideline_document"
    DESIGN_SYSTEM_SPEC = "design_system_spec"
    CAMPAIGN = "campaign"
    AD = "ad"
    SOCIAL = "social"
    VIDEO = "video"


class BrandHistoryModality(str, enum.Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class BrandHistoryAuthorityLevel(str, enum.Enum):
    """Phase 1 §4 — Explicit outranks Exemplar during Consolidation (§5)."""

    EXPLICIT = "explicit"
    EXEMPLAR = "exemplar"


class GenomeCategoryName(str, enum.Enum):
    """Phase 1 §2 — fixed, closed taxonomy for v1. Required-ness (Phase 1
    §3) is a function of this name, not an independently stored flag."""

    VISUAL_IDENTITY = "visual_identity"
    VERBAL_IDENTITY = "verbal_identity"
    MESSAGING_POSITIONING = "messaging_positioning"
    VALUES_MISSION = "values_mission"
    COMPLIANCE_LEGAL = "compliance_legal"
    ACCESSIBILITY = "accessibility"


REQUIRED_GENOME_CATEGORIES = frozenset(
    {
        GenomeCategoryName.VISUAL_IDENTITY,
        GenomeCategoryName.VERBAL_IDENTITY,
        GenomeCategoryName.MESSAGING_POSITIONING,
    }
)
"""Phase 1 §3 — Visual Identity, Verbal Identity, Messaging & Positioning
are Required; Values & Mission, Compliance & Legal, Accessibility are
Optional. Fixed platform behavior, not tenant-configurable."""


class AssertionStatus(str, enum.Enum):
    """Phase 1 §5 step 3(c) — a Component may hold a `conflicted`
    Assertion pending human resolution; Phase 1 §10 rule 3 blocks
    `pending_review` while any remain conflicted."""

    ACTIVE = "active"
    CONFLICTED = "conflicted"


class AssertionOriginType(str, enum.Enum):
    """Phase 1 §7 Provenance Model, Assertion column."""

    EXPLICIT_SOURCE = "explicit_source"
    EXEMPLAR_SOURCE = "exemplar_source"
    HUMAN_OVERRIDE = "human_override"


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
        Enum(BrandStatus, name="brand_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=BrandStatus.ACTIVE
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
    `Brand.active_genome_version_id`. Internal Category/Component/Assertion
    structure lives in the three tables below, all scoped to `genome_id`."""

    __tablename__ = "brand_genomes"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[GenomeStatus] = mapped_column(
        Enum(GenomeStatus, name="genome_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=GenomeStatus.DRAFT
    )
    compiled_from: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    activated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        comment="Required, non-null the moment this version is pointed-to (DR-006, INV-15).",
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class GenomeCategory(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 1 §1 — top-level dimension of brand identity within one
    BrandGenome version. `applicability_scope` is the Phase 3 addendum
    (null = universally applicable, the default)."""

    __tablename__ = "genome_categories"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    genome_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brand_genomes.id"), nullable=False, index=True)
    name: Mapped[GenomeCategoryName] = mapped_column(
        Enum(GenomeCategoryName, name="genome_category_name", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    applicability_scope: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class GenomeComponent(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 1 §1 — named unit of knowledge within a Category. Platform-
    defined per Category so every Genome has a predictable shape; the
    specific component names in use are seeded per Category, not
    hardcoded here (see scripts/seed_data)."""

    __tablename__ = "genome_components"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    category_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("genome_categories.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    applicability_scope: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class Assertion(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 1 §1/§7 — the atomic, evaluable knowledge claim Evidence is
    compared against. Immutable once its parent BrandGenome version is
    pointed-to (INV-08 applies transitively to Genome's full content)."""

    __tablename__ = "assertions"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    component_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("genome_components.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[AssertionStatus] = mapped_column(
        Enum(AssertionStatus, name="assertion_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=AssertionStatus.ACTIVE
    )
    origin_type: Mapped[AssertionOriginType] = mapped_column(
        Enum(AssertionOriginType, name="assertion_origin_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    source_reference_ids: Mapped[list] = mapped_column(
        JSON, nullable=False, comment="BrandHistoryItem ids (Phase 1 §7); provenance, not FK-enforced (many-to-many)."
    )
    applicability_scope: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Policy(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.7 — same versioned pattern as BrandGenome. `rules`
    payload shape defined by Phase 2 §2.1: category_weights,
    component_weights, assertion_weights, critical_rules, verdict_thresholds
    (validated by `analysis_decision.decision_engine.policy_schema`)."""

    __tablename__ = "policies"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus, name="policy_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=PolicyStatus.DRAFT
    )
    rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class BrandHistory(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.8 (DR-008 rename from "Brand Evidence") + Phase 1 §4's
    conceptual field elaboration (modality, era_tag, authority_level).
    Repository of historical marketing assets; query scope is Genome-
    compilation-input only, never used at analysis time (Phase 0 §9.4)."""

    __tablename__ = "brand_history_items"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    brand_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    source_type: Mapped[BrandHistorySourceType] = mapped_column(
        Enum(BrandHistorySourceType, name="brand_history_source_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    modality: Mapped[BrandHistoryModality] = mapped_column(
        Enum(BrandHistoryModality, name="brand_history_modality", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    era_tag: Mapped[str | None] = mapped_column(String, nullable=True)
    authority_level: Mapped[BrandHistoryAuthorityLevel] = mapped_column(
        Enum(BrandHistoryAuthorityLevel, name="brand_history_authority_level", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    storage_ref: Mapped[str] = mapped_column(String, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Compilation-time text cache (document/OCR extraction) so recompilation never "
        "re-parses the raw asset. Implementation detail, not a Phase 1 §4 conceptual field.",
    )
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
