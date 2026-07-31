"""Bounded Context 6 — Platform Governance (Phase 0 §3.17-3.18).

Owns: AuditLogEntry, AISlopKnowledgeBase. Both are cross-cutting global
concerns, structurally isolated from all tenant contexts (Phase 0 §6) —
neither uses `TenantScopedMixin`. Database-level immutability (INV-33:
no UPDATE/DELETE grants on the application role for `audit_log_entries`)
is applied in the Alembic migration, not expressible via SQLAlchemy
model metadata alone.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared_kernel.db import Base
from src.shared_kernel.mixins import UUIDPrimaryKeyMixin


class AISlopSourceType(str, enum.Enum):
    PUBLIC = "public"
    SYNTHETIC = "synthetic"


class AuditLogEntry(UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.17 — global, append-only. `org_id` is present for
    visibility scoping only, never as a tenant-isolation exemption
    mechanism, and is nullable because some audited actions (e.g.
    platform-level InternalOperator actions) are not organization-scoped.
    """

    __tablename__ = "audit_log_entries"

    org_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    actor_id: Mapped[uuid.UUID] = mapped_column(
        nullable=False, comment="References either a User or an InternalOperator; no single FK by design."
    )
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    target_entity: Mapped[str] = mapped_column(String, nullable=False)
    target_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AISlopKnowledgeBase(UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.18 (DR-004) — global, structurally outside the
    Organization tree. No field on this entity, and no field on any
    tenant entity, establishes a reference into or out of it. Populated
    exclusively from public/synthetic corpora — never from tenant-private
    data (INV-20), enforced by having no automated ingestion path from
    any tenant-scoped table, not by policy alone."""

    __tablename__ = "ai_slop_knowledge_base"

    source_type: Mapped[AISlopSourceType] = mapped_column(
        Enum(AISlopSourceType, name="ai_slop_source_type"), nullable=False
    )
    content_ref: Mapped[str] = mapped_column(String, nullable=False)
