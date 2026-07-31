"""Cross-context value objects only — no business logic (CLAUDE.md §6)."""
from __future__ import annotations

import uuid


def new_id() -> uuid.UUID:
    """Generate a new entity identifier. Centralized so the ID strategy
    (currently UUIDv4) is a one-place change if it ever needs to differ."""
    return uuid.uuid4()
