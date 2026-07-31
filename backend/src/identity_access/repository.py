"""Example concrete repository wiring for this Bounded Context (CLAUDE.md
§3.1/§3.3-I). Demonstrates the pattern other contexts' repositories
follow; contains no business logic."""
from __future__ import annotations

from src.identity_access.domain.models import Organization
from src.shared_kernel.repository import BaseRepository


class OrganizationRepository(BaseRepository[Organization]):
    model = Organization
