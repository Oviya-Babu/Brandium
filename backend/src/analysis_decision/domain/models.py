"""Bounded Context 4 — Analysis & Decision (Phase 0 §3.11-3.15).

Owns: AnalysisRun, Observation, Evidence, Decision, Recommendation.
Schema only — Applicability Resolution, Planning, Workers, Evidence
Fusion (Phase 3), and the Decision Engine's aggregation math (Phase 2)
are later milestones (CLAUDE.md §14 Milestones 3-4). This module defines
only the entities' shape and reproducibility contract (INV-02), never
the scoring formula itself.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.shared_kernel.db import Base, TenantScopedMixin
from src.shared_kernel.mixins import UUIDPrimaryKeyMixin


class AnalysisRunStatus(str, enum.Enum):
    """`complete` and `failed` are both terminal states — no outgoing
    transitions from either (Phase 0 §3.11, INV-25). A retry creates a
    new AnalysisRun row; it never reopens this one."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class AnalysisRun(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.11 — pins Genome + Policy version at creation (DR-005).
    `genome_version_id`/`policy_version_id` are set once and never updated."""

    __tablename__ = "analysis_runs"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    asset_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("asset_versions.id"), nullable=False, index=True)
    genome_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brand_genomes.id"), nullable=False)
    policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policies.id"), nullable=False)
    status: Mapped[AnalysisRunStatus] = mapped_column(
        Enum(AnalysisRunStatus, name="analysis_run_status"), nullable=False, default=AnalysisRunStatus.QUEUED
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Observation(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.12 — raw, internal worker output. Immutable once
    recorded (INV-12)."""

    __tablename__ = "observations"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), nullable=False, index=True)
    worker_type: Mapped[str] = mapped_column(String, nullable=False)
    raw_output: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class Evidence(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.13 — normalized, user-facing. Immutable once recorded
    (INV-12); confidence is calibrated (DR-002)."""

    __tablename__ = "evidence"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), nullable=False, index=True)
    evidence_type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source_observation_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class Decision(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.14 — deterministic, versioned scoring output, 1:1 with
    AnalysisRun. Isolated from LLM-narrated content (Recommendation) so
    reproducibility (INV-02) applies to a clean entity.

    `decision_function_version` covers, as one atomic unit, every
    mechanism listed in CLAUDE.md INV-11 — the actual aggregation
    formula is a Phase 2 Known Gap, not defined by this schema.
    """

    __tablename__ = "decisions"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_runs.id"), nullable=False, unique=True, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[str] = mapped_column(String, nullable=False)
    decision_function_version: Mapped[int] = mapped_column(Integer, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Recommendation(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.15 — LLM-narrated, evidence-grounded; 1:N with
    AnalysisRun. No Recommendation may exist without at least one
    `related_evidence_id` (INV-06)."""

    __tablename__ = "recommendations"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), nullable=False, index=True)
    related_evidence_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
