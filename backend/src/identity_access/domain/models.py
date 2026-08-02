"""Bounded Context 1 — Identity & Access.

Owns: Organization, Workspace, User, Membership, RoleAssignment,
InternalOperator. Schema + scope-tier authorization data model. RBAC
*enforcement* logic lives in `identity_access/authorization.py`.

Membership and RoleAssignment's `scope_tier`/`scope_id` were introduced
by Phase 5 §2/§0 and Phase 0's pre-Phase-5 RoleAssignment addendum —
referenced by Phase 5/6 and CLAUDE.md's INV-22 as already-applied, but
not spelled out in the literal Phase 0 v0.2 document text available in
this repo. Added here additively, per CLAUDE.md §9.4 (flagged to the
human architect rather than invented silently — see IMPLEMENTATION_STATUS.md).
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from src.identity_access.domain.enums import MembershipStatus, OrganizationStatus, Role, ScopeTier
from src.shared_kernel.db import Base, TenantScopedMixin
from src.shared_kernel.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin

__all__ = [
    "MembershipStatus",
    "OrganizationStatus",
    "Role",
    "ScopeTier",
    "Organization",
    "Workspace",
    "User",
    "Membership",
    "RoleAssignment",
    "InternalOperator",
]


class Organization(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """The tenant. Sole unit of billing, provisioning, isolation (Phase 0 §3.1)."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[OrganizationStatus] = mapped_column(
        Enum(OrganizationStatus, name="organization_status", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=OrganizationStatus.PROVISIONED,
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


class Membership(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 5 §2/§9 — a User's relationship to an Organization, separate
    from RoleAssignment. Removing a Membership cascades to revoke every
    RoleAssignment that User held at that Organization (enforced in
    `identity_access/authorization.py`, not by a DB trigger, so the
    cascade is itself an auditable service-layer action)."""

    __tablename__ = "memberships"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True, unique=True)
    status: Mapped[MembershipStatus] = mapped_column(
        Enum(MembershipStatus, name="membership_status", values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=MembershipStatus.INVITED
    )


class RoleAssignment(TenantScopedMixin, UUIDPrimaryKeyMixin, Base):
    """Phase 0 §3.3 + Phase 5 §2 scope-tier addendum.

    `scope_id` is polymorphic on `scope_tier`: it holds an Organization id
    when `scope_tier = organization`, a Workspace id when `workspace`, or
    a Brand id when `brand`. No single FK constraint can express this
    (three possible referent tables), so referential integrity across the
    polymorphic reference is enforced at the service layer, not the DB —
    documented here rather than silently assumed.
    """

    __tablename__ = "role_assignments"

    org_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role: Mapped[Role] = mapped_column(Enum(Role, name="role", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    scope_tier: Mapped[ScopeTier] = mapped_column(Enum(ScopeTier, name="scope_tier", values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    scope_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    granted_by: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        comment="Phase 6 §3: the distinct actor who granted this — enforced != user_id at self-escalating grants.",
    )
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class InternalOperator(UUIDPrimaryKeyMixin, Base):
    """BrandGuard's own staff. Phase 0 §3.4 — deliberately carries no
    `org_id` and no relationship into any tenant-scoped table (INV-21)."""

    __tablename__ = "internal_operators"

    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
