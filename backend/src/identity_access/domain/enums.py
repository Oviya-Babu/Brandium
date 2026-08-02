"""Plain enums for Bounded Context 1, deliberately dependency-free (no
SQLAlchemy import) so `identity_access/authorization.py` — and its tests
— can run without a database driver installed, exactly like the Decision
Engine (`analysis_decision/decision_engine/schemas.py`). `domain/models.py`
imports these rather than redefining them."""
from __future__ import annotations

import enum


class OrganizationStatus(str, enum.Enum):
    """Phase 5 §1/§9 — additive widening of Phase 0's `active|suspended`."""

    PROVISIONED = "provisioned"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    OFFBOARDED = "offboarded"


class Role(str, enum.Enum):
    """Phase 0 §3.3 + Phase 5 §0/§2's OrganizationAdministrator addition."""

    ORGANIZATION_ADMINISTRATOR = "OrganizationAdministrator"
    BRAND_ADMINISTRATOR = "BrandAdministrator"
    MARKETING_MANAGER = "MarketingManager"
    CONTENT_CREATOR = "ContentCreator"
    EXECUTIVE_VIEWER = "ExecutiveViewer"


class ScopeTier(str, enum.Enum):
    """Phase 5 §2 / CLAUDE.md INV-22 — a RoleAssignment is always
    evaluated at its actual tier; inheritance flows broad -> narrow only."""

    ORGANIZATION = "organization"
    WORKSPACE = "workspace"
    BRAND = "brand"


class MembershipStatus(str, enum.Enum):
    """Phase 5 §2/§9 — distinct from RoleAssignment: "is this person part
    of this Organization at all" vs. "what can they do, and where"."""

    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REMOVED = "removed"
