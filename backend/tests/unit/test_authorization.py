import uuid
from datetime import datetime, timezone

import pytest

from src.identity_access.authorization import (
    AuthorizationContext,
    RoleAssignmentView,
    SelfEscalationError,
    authorize_role_grant,
    effective_roles,
    has_role,
)
from src.identity_access.domain.enums import MembershipStatus, Role, ScopeTier

ORG = uuid.uuid4()
WORKSPACE = uuid.uuid4()
BRAND = uuid.uuid4()
OTHER_BRAND = uuid.uuid4()


def _assignment(role: Role, tier: ScopeTier, scope_id: uuid.UUID, revoked: bool = False) -> RoleAssignmentView:
    return RoleAssignmentView(
        role=role,
        scope_tier=tier,
        scope_id=scope_id,
        revoked_at=datetime.now(timezone.utc) if revoked else None,
    )


def test_organization_scoped_grant_covers_every_brand() -> None:
    ctx = AuthorizationContext(
        membership_status=MembershipStatus.ACTIVE,
        assignments=(_assignment(Role.BRAND_ADMINISTRATOR, ScopeTier.ORGANIZATION, ORG),),
    )
    assert has_role(ctx, ORG, ScopeTier.BRAND, BRAND, Role.BRAND_ADMINISTRATOR)
    assert has_role(ctx, ORG, ScopeTier.BRAND, OTHER_BRAND, Role.BRAND_ADMINISTRATOR)


def test_brand_scoped_grant_never_covers_sibling_brand() -> None:
    """INV-22: privilege inheritance never flows sideways."""
    ctx = AuthorizationContext(
        membership_status=MembershipStatus.ACTIVE,
        assignments=(_assignment(Role.BRAND_ADMINISTRATOR, ScopeTier.BRAND, BRAND),),
    )
    assert has_role(ctx, ORG, ScopeTier.BRAND, BRAND, Role.BRAND_ADMINISTRATOR)
    assert not has_role(ctx, ORG, ScopeTier.BRAND, OTHER_BRAND, Role.BRAND_ADMINISTRATOR)


def test_workspace_scoped_grant_covers_contained_brand_only_when_told_which_workspace() -> None:
    ctx = AuthorizationContext(
        membership_status=MembershipStatus.ACTIVE,
        assignments=(_assignment(Role.BRAND_ADMINISTRATOR, ScopeTier.WORKSPACE, WORKSPACE),),
    )
    assert has_role(
        ctx, ORG, ScopeTier.BRAND, BRAND, Role.BRAND_ADMINISTRATOR, containing_workspace_id=WORKSPACE
    )
    assert not has_role(ctx, ORG, ScopeTier.BRAND, BRAND, Role.BRAND_ADMINISTRATOR, containing_workspace_id=None)


def test_revoked_assignment_grants_nothing() -> None:
    ctx = AuthorizationContext(
        membership_status=MembershipStatus.ACTIVE,
        assignments=(_assignment(Role.BRAND_ADMINISTRATOR, ScopeTier.BRAND, BRAND, revoked=True),),
    )
    assert effective_roles(ctx, ORG, ScopeTier.BRAND, BRAND) == frozenset()


def test_inactive_membership_denies_regardless_of_assignments() -> None:
    """Phase 6 §3's Membership-status precondition."""
    ctx = AuthorizationContext(
        membership_status=MembershipStatus.SUSPENDED,
        assignments=(_assignment(Role.BRAND_ADMINISTRATOR, ScopeTier.ORGANIZATION, ORG),),
    )
    assert effective_roles(ctx, ORG, ScopeTier.BRAND, BRAND) == frozenset()


def test_no_applicable_assignment_denies_by_default() -> None:
    """INV-32: default state for any actor with no applicable RoleAssignment is total denial."""
    ctx = AuthorizationContext(membership_status=MembershipStatus.ACTIVE, assignments=())
    assert effective_roles(ctx, ORG, ScopeTier.BRAND, BRAND) == frozenset()


def test_self_grant_is_always_rejected() -> None:
    user_id = uuid.uuid4()
    granter_ctx = AuthorizationContext(
        membership_status=MembershipStatus.ACTIVE,
        assignments=(_assignment(Role.ORGANIZATION_ADMINISTRATOR, ScopeTier.ORGANIZATION, ORG),),
    )
    with pytest.raises(SelfEscalationError):
        authorize_role_grant(
            granting_user_id=user_id,
            recipient_user_id=user_id,
            granter_ctx=granter_ctx,
            org_id=ORG,
            new_grant_tier=ScopeTier.BRAND,
            new_grant_scope_id=BRAND,
        )


def test_grant_by_unauthorized_actor_is_rejected() -> None:
    granter_ctx = AuthorizationContext(
        membership_status=MembershipStatus.ACTIVE,
        assignments=(_assignment(Role.CONTENT_CREATOR, ScopeTier.BRAND, BRAND),),
    )
    with pytest.raises(PermissionError):
        authorize_role_grant(
            granting_user_id=uuid.uuid4(),
            recipient_user_id=uuid.uuid4(),
            granter_ctx=granter_ctx,
            org_id=ORG,
            new_grant_tier=ScopeTier.BRAND,
            new_grant_scope_id=BRAND,
        )


def test_grant_by_authorized_distinct_actor_succeeds() -> None:
    granter_ctx = AuthorizationContext(
        membership_status=MembershipStatus.ACTIVE,
        assignments=(_assignment(Role.ORGANIZATION_ADMINISTRATOR, ScopeTier.ORGANIZATION, ORG),),
    )
    authorize_role_grant(
        granting_user_id=uuid.uuid4(),
        recipient_user_id=uuid.uuid4(),
        granter_ctx=granter_ctx,
        org_id=ORG,
        new_grant_tier=ScopeTier.BRAND,
        new_grant_scope_id=BRAND,
    )
