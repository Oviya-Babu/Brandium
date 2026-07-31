"""Common ORM mixins shared across Bounded Contexts — structural only, no business logic."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from src.shared_kernel.types import new_id


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    """UUIDv4 primary key, per Phase 0 §3's `id` field on every entity."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_id)


class CreatedAtMixin:
    """`created_at` timestamp, present on every append-only/immutable entity."""

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
