"""Bounded Context 1 — Identity & Access (Phase 0 §3.1-3.4, CLAUDE.md §1.5).

Owns: Organization, Workspace, User, RoleAssignment, InternalOperator.
Schema only in this milestone — no authentication, no authorization
evaluation service, no RBAC enforcement logic (those are later
milestones, see CLAUDE.md §14 Milestone 10).

Note: CLAUDE.md §1.5 lists "Membership" alongside RoleAssignment in this
context's ownership, but Phase 0 v0.2 §3 does not define Membership's
fields — it is introduced by the Phase 5 RoleAssignment scope-tier
addendum (CLAUDE.md Milestone 10). Not modeled here to avoid inventing
fields for an entity the frozen Phase 0 spec doesn't yet define; tracked
as an open item in IMPLEMENTATION_STATUS.md.
"""
from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.shared_kernel.db import Base, TenantScopedMixin
from src.shared_kernel.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class OrganizationStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class Role(str, enum.Enum):
    """v1 roles (Phase 0 §3.3). Scope-tier evaluation (organization |
    workspace | brand, INV-22) is a Phase 5 addendum, not yet modeled."""

    BRAND_ADMINISTRATOR = "BrandAdministrator"
    MARKETING_MANAGER = "MarketingManager"
    CONTENT_CREATOR = "ContentCreator"
    EXECUTIVE_VIEWER = "ExecutiveViewer"


class Organization(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """The tenant. Sole unit of billing, provisioning, isolation (Phase 0 §3.1)."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus, name="organization_status"),
        nullable=False,
        default=OrganizationStatus.ACTIVE,
    )


class Workspace(UUIDPrimaryKeyMixin, CreatedAtMixin, TenantScopedMixin, Base):
    """Phase 0 §3.2."""

    __tablename__ = "workspaces"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)


class User(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.3."""

    __tablename__ = "users"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    auth_identity_ref: Mapped[str] = mapped_column(String, nullable=False)


class RoleAssignment(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.3."""

    __tablename__ = "role_assignments"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role"), nullable=False)


class InternalOperator(UUIDPrimaryKeyMixin, Base):
    """BrandGuard's own staff. Phase 0 §3.4 — deliberately carries no
    `org_id` and no relationship into any tenant-scoped table (INV-21)."""

    __tablename__ = "internal_operators"

    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
