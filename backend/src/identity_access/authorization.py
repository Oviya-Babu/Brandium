"""Authorization evaluation service (Phase 5 §2, Phase 6 §3).

Deliberately plain Python over in-memory data, not a query builder: the
caller (API dependency layer) loads the actor's active RoleAssignments
and Membership status via the repository layer, maps each ORM row to the
lightweight `RoleAssignmentView` below, then hands them to this module's
pure functions. This keeps the actual authorization *logic* — the part
CLAUDE.md §7 requires dedicated tests for — testable and runnable with
zero third-party dependencies, exactly like the Decision Engine
(CLAUDE.md §3.1's dependency-inversion principle): this module never
imports the SQLAlchemy-backed `identity_access.domain.models`, only the
dependency-free `identity_access.domain.enums`.

Simplification flagged honestly: `RoleAssignment.scope_id` is polymorphic
(domain/models.py's docstring), so this module has no independent way to
know "does this Workspace contain that Brand" — that containment fact is
resolved by the caller (which already has the Brand row) and passed in
as `containing_workspace_id`. Without it, only exact-scope-match and
organization-wide grants are recognized as covering a Brand-tier target;
this is a narrower, safe-by-default outcome (a legitimate grant might be
under-recognized), never a permissive one, consistent with INV-31.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from src.identity_access.domain.enums import MembershipStatus, Role, ScopeTier


@dataclass(frozen=True)
class RoleAssignmentView:
    """Dependency-free projection of the ORM `RoleAssignment` row — only
    the fields authorization logic actually needs."""

    role: Role
    scope_tier: ScopeTier
    scope_id: uuid.UUID
    revoked_at: datetime | None = None


@dataclass(frozen=True)
class AuthorizationContext:
    membership_status: MembershipStatus
    assignments: tuple[RoleAssignmentView, ...]


def _covers(
    assignment: RoleAssignmentView,
    target_tier: ScopeTier,
    target_scope_id: uuid.UUID,
    org_id: uuid.UUID,
    containing_workspace_id: uuid.UUID | None,
) -> bool:
    """Does `assignment` grant authority over (target_tier, target_scope_id)?
    Inheritance flows broad -> narrow only (INV-22): organization-tier
    covers everything in the org; workspace-tier covers its own brands;
    brand-tier covers only itself. Never the reverse."""
    if assignment.revoked_at is not None:
        return False
    if assignment.scope_tier == ScopeTier.ORGANIZATION:
        return assignment.scope_id == org_id
    if assignment.scope_tier == ScopeTier.WORKSPACE:
        if target_tier == ScopeTier.WORKSPACE:
            return assignment.scope_id == target_scope_id
        if target_tier == ScopeTier.BRAND:
            return containing_workspace_id is not None and assignment.scope_id == containing_workspace_id
        return False
    if assignment.scope_tier == ScopeTier.BRAND:
        return target_tier == ScopeTier.BRAND and assignment.scope_id == target_scope_id
    return False


def effective_roles(
    ctx: AuthorizationContext,
    org_id: uuid.UUID,
    target_tier: ScopeTier,
    target_scope_id: uuid.UUID,
    containing_workspace_id: uuid.UUID | None = None,
) -> frozenset[Role]:
    """Phase 6 §3: union of every applicable assignment's Role, evaluated
    at the narrowest matching tier. There is no deny construct — this
    returns the complete permissive set, or an empty set (INV-32: no
    applicable assignment => total denial by construction, the caller
    simply finds nothing in the returned set)."""
    if ctx.membership_status != MembershipStatus.ACTIVE:
        # Phase 6 §3's Membership-status precondition: gates RoleAssignment's
        # effect entirely, regardless of how many assignments nominally exist.
        return frozenset()

    return frozenset(
        a.role
        for a in ctx.assignments
        if _covers(a, target_tier, target_scope_id, org_id, containing_workspace_id)
    )


def has_role(
    ctx: AuthorizationContext,
    org_id: uuid.UUID,
    target_tier: ScopeTier,
    target_scope_id: uuid.UUID,
    required: Role,
    containing_workspace_id: uuid.UUID | None = None,
) -> bool:
    return required in effective_roles(ctx, org_id, target_tier, target_scope_id, containing_workspace_id)


class SelfEscalationError(Exception):
    """Phase 6 §3: raised when a grant would expand the requesting
    actor's own effective privilege — must come from a second, distinct,
    equal-or-broader-authority actor instead."""


def authorize_role_grant(
    *,
    granting_user_id: uuid.UUID,
    recipient_user_id: uuid.UUID,
    granter_ctx: AuthorizationContext,
    org_id: uuid.UUID,
    new_grant_tier: ScopeTier,
    new_grant_scope_id: uuid.UUID,
    containing_workspace_id: uuid.UUID | None = None,
) -> None:
    """Raises SelfEscalationError or PermissionError; returns None (i.e.
    "allowed") otherwise. Two checks, per Phase 6 §3:

    1. No actor may grant themselves a RoleAssignment — full stop. This is
       a deliberately conservative reading of "may never grant themselves
       a RoleAssignment that increases their own effective privilege":
       rather than attempting to compute whether a specific self-grant
       would be privilege-increasing (a strictly harder problem, given
       Role has no partial ordering defined anywhere in Phase 0-6), this
       blocks every self-grant unconditionally. That is a strict subset
       of what the invariant requires blocked, so it can never under-block
       an actual escalation — consistent with INV-31's fail-safe principle.
    2. The granting actor must hold authority (via `effective_roles`,
       OrganizationAdministrator or BrandAdministrator, Phase 5 §7) that
       covers the new grant's scope.
    """
    if granting_user_id == recipient_user_id:
        raise SelfEscalationError(
            "An actor may never grant themselves a RoleAssignment (Phase 6 §3)."
        )

    granter_roles = effective_roles(
        granter_ctx, org_id, new_grant_tier, new_grant_scope_id, containing_workspace_id
    )
    if not (granter_roles & {Role.ORGANIZATION_ADMINISTRATOR, Role.BRAND_ADMINISTRATOR}):
        raise PermissionError(
            "Granting actor lacks administrative authority covering the target scope."
        )
