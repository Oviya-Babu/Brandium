"""Bounded Context 4 — Analysis & Decision (Phase 0 §3.11-3.15, Phase 1 §6,
Phase 3 §5/§6).

Owns: AnalysisRun, Observation, Evidence, AssertionOutcome, Decision,
Recommendation. `AssertionOutcome` gives Phase 3 §5's four-state outcome
taxonomy (evidence / attempted-no-signal / worker-failure / not-applicable)
a persisted, queryable record per (AnalysisRun, Assertion) — required by
Completeness Verification (Phase 3 §6) and Coverage exclusion (Phase 2
§3.2), not a new business concept, just the taxonomy Phase 3 already
names made concrete for storage.
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


class AlignmentIndicator(str, enum.Enum):
    """Phase 1 §6 Evidence Schema; Phase 2 §3.1's Alignment Value Function
    maps these to 1.0 / 0.5 / 0.0 respectively."""

    ALIGNED = "aligned"
    PARTIALLY_ALIGNED = "partially_aligned"
    MISALIGNED = "misaligned"


class AssertionOutcomeType(str, enum.Enum):
    """Phase 3 §5 — every in-scope (Applicable) Assertion resolves to
    exactly one of these three; out-of-scope Assertions get NOT_APPLICABLE
    (Phase 3 §2 addendum). Never conflated with one another (INV-24)."""

    EVIDENCE = "evidence"
    ATTEMPTED_NO_SIGNAL = "attempted_no_signal"
    WORKER_FAILURE = "worker_failure"
    NOT_APPLICABLE = "not_applicable"


class AnalysisRun(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.11 — pins Genome + Policy version at creation (DR-005).
    `genome_version_id`/`policy_version_id` are set once and never updated."""

    __tablename__ = "analysis_runs"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    asset_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("asset_versions.id"), nullable=False, index=True)
    genome_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("brand_genomes.id"), nullable=False)
    policy_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policies.id"), nullable=False)
    status: Mapped[AnalysisRunStatus] = mapped_column(
        Enum(AnalysisRunStatus, name="analysis_run_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=AnalysisRunStatus.QUEUED
    )
    failure_reason: Mapped[str | None] = mapped_column(
        String, nullable=True, comment="Set when status=failed: which Required-category worker-failure caused it."
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Observation(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.12 — raw, internal worker output. Immutable once
    recorded (INV-12)."""

    __tablename__ = "observations"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), nullable=False, index=True)
    assertion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assertions.id"), nullable=False, index=True)
    worker_type: Mapped[str] = mapped_column(String, nullable=False)
    raw_output: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)


class AssertionOutcome(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Persisted record of Phase 3 §5's per-Assertion terminal outcome for
    one AnalysisRun. Exactly one row per (analysis_run_id, assertion_id)
    that was in the Applicability Set (plus NOT_APPLICABLE rows for
    out-of-scope Assertions, recorded for explainability per the Phase 3
    §2 addendum's "extend Explainability to report Not Applicable")."""

    __tablename__ = "assertion_outcomes"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), nullable=False, index=True)
    assertion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assertions.id"), nullable=False, index=True)
    outcome_type: Mapped[AssertionOutcomeType] = mapped_column(
        Enum(AssertionOutcomeType, name="assertion_outcome_type", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Evidence(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.13 shape, elaborated by Phase 1 §6. Immutable once
    recorded (INV-12); confidence is calibrated (DR-002)."""

    __tablename__ = "evidence"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), nullable=False, index=True)
    assertion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assertions.id"),
        nullable=False,
        index=True,
        comment="Phase 1 §6: assertion_reference — which specific Assertion this evaluates against.",
    )
    observed_characteristic: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="Structured description shaped to be directly comparable to the Assertion."
    )
    alignment_indicator: Mapped[AlignmentIndicator] = mapped_column(
        Enum(AlignmentIndicator, name="alignment_indicator", values_callable=lambda obj: [e.value for e in obj]), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    source_observation_ids: Mapped[list] = mapped_column(JSON, nullable=False, default=list)


class Decision(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.14 — deterministic, versioned scoring output, 1:1 with
    AnalysisRun. Per Phase 2 §5.3, only these four fields are persisted;
    the full aggregation tree is deliberately derived on demand, never
    stored, so there is exactly one source of truth for "why this score."
    """

    __tablename__ = "decisions"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_runs.id"), nullable=False, unique=True, index=True
    )
    score: Mapped[float] = mapped_column(Float, nullable=False)
    verdict: Mapped[str] = mapped_column(String, nullable=False)
    verdict_source: Mapped[str] = mapped_column(
        String,
        nullable=False,
        comment="'threshold' or 'critical_rule_override:<rule_id>' (Phase 2 §5.2/§2.3 — never presented identically).",
    )
    decision_function_version: Mapped[int] = mapped_column(Integer, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Recommendation(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.15, Phase 2 §6 — LLM-narrated, evidence-grounded; 1:N
    with AnalysisRun. `priority` and `component_id` are deterministic
    (Phase 2 §6.2, covered by `decision_function_version`); `text` is not
    (Phase 2 §6.3)."""

    __tablename__ = "recommendations"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_runs.id"), nullable=False, index=True)
    component_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("genome_components.id"),
        nullable=False,
        comment="Phase 2 §6.1: the Component whose aggregate fell below the improvement threshold.",
    )
    related_evidence_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Phase 2 §6.2: component_weight * max(0, improvement_threshold - value)."
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
