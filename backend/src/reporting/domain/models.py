"""Bounded Context 5 — Reporting (Phase 0 §3.16).

Owns: Report. Deliberately separate from Analysis & Decision — "compute
a verdict" and "manage human review of that verdict" are distinct
responsibilities. Schema only in this milestone.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared_kernel.db import Base, TenantScopedMixin
from src.shared_kernel.mixins import UUIDPrimaryKeyMixin


class ReportReviewStatus(str, enum.Enum):
    UNREVIEWED = "unreviewed"
    APPROVED = "approved"
    FLAGGED = "flagged"


class Report(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.16 — persisted read-model projection of exactly one
    Decision plus its Evidence and Recommendations, reachable via
    `analysis_run_id`. The projected content is immutable once generated;
    the four review-overlay fields below are the one deliberate,
    narrow exception (a mutable workflow overlay, not a re-computation
    of the underlying Decision)."""

    __tablename__ = "reports"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analysis_runs.id"), nullable=False, unique=True, index=True
    )
    decision_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("decisions.id"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Mutable review-overlay fields (Phase 0 §3.16 exception; lifecycle: unreviewed -> {approved, flagged})
    review_status: Mapped[ReportReviewStatus] = mapped_column(
        Enum(ReportReviewStatus, name="report_review_status", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=ReportReviewStatus.UNREVIEWED,
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    flag_reason: Mapped[str | None] = mapped_column(String, nullable=True)
