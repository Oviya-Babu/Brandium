"""Policy Service — authoring and activation (Phase 0 §3.7, Phase 2 §2.1/§10).

Phase 5 §4 resolves Phase 2 §11's open question: Policy activation's
review requirement is an *enterprise-configurable* maker-checker overlay,
not a universal requirement. This service implements the required base
case (author-and-activate, same as Genome's mechanism minus the mandatory
DR-006 gate — Policy has no `activated_by`-required invariant, INV-15 is
specific to Genome); the opt-in maker-checker overlay is a documented,
not-yet-built enhancement (see IMPLEMENTATION_STATUS.md), since Phase 5
itself specifies it as optional, not blocking for a working core loop.
"""
from __future__ import annotations

import uuid

from src.analysis_decision.decision_engine.policy_schema import policy_rules_from_json, validate_policy_rules
from src.analysis_decision.decision_engine.schemas import GenomeTree
from src.brand_governance.domain.models import Policy, PolicyStatus
from src.brand_governance.repository import BrandGenomeRepository, BrandRepository, PolicyRepository
from src.platform_governance.audit_service import AuditService
from src.platform_governance.domain.models import AuditActorType


class PolicyValidationError(Exception):
    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


class PolicyActivationError(Exception):
    pass


class PolicyService:
    def __init__(
        self,
        policy_repo: PolicyRepository,
        brand_repo: BrandRepository,
        genome_repo: BrandGenomeRepository,
        audit: AuditService,
    ) -> None:
        self._policy_repo = policy_repo
        self._brand_repo = brand_repo
        self._genome_repo = genome_repo
        self._audit = audit

    async def create_draft(
        self, *, org_id: uuid.UUID, brand_id: uuid.UUID, rules: dict, actor_id: uuid.UUID
    ) -> Policy:
        version_number = await self._policy_repo.next_version_number(brand_id)
        policy = Policy(
            org_id=org_id, brand_id=brand_id, version_number=version_number, status=PolicyStatus.DRAFT, rules=rules
        )
        await self._policy_repo.add(policy)
        await self._audit.record(
            org_id=org_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            action_type="policy.draft_created",
            target_entity="Policy",
            target_id=policy.id,
        )
        return policy

    async def validate_against_active_genome(self, policy: Policy, genome_tree: GenomeTree) -> None:
        """Phase 2 §10 rules 1-3, checked against the Brand's Genome
        version active at validation time."""
        rules = policy.rules or {}
        policy_rules = policy_rules_from_json(rules)
        errors = validate_policy_rules(policy_rules, genome_tree)
        if errors:
            raise PolicyValidationError(errors)

    async def activate(self, *, policy: Policy, actor_id: uuid.UUID) -> Policy:
        """Base case activation (no maker-checker overlay in this pass —
        see module docstring). `Brand.active_policy_version_id` pointer
        mechanics mirror Genome's (Phase 0 §3.5/§3.7)."""
        if policy.status != PolicyStatus.DRAFT:
            raise PolicyActivationError(f"Policy {policy.id} is '{policy.status.value}', not 'draft'.")

        brand = await self._brand_repo.get_by_id(policy.brand_id)
        if brand is None:
            raise PolicyActivationError(f"Brand {policy.brand_id} not found.")

        previous_active_id = brand.active_policy_version_id
        brand.active_policy_version_id = policy.id
        # Guard mirrors GenomeService.activate(): don't supersede the
        # version being activated if it was already the active one.
        if previous_active_id is not None and previous_active_id != policy.id:
            previous = await self._policy_repo.get_by_id(previous_active_id)
            if previous is not None:
                previous.status = PolicyStatus.SUPERSEDED

        await self._audit.record(
            org_id=policy.org_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            action_type="policy.activated",
            target_entity="Policy",
            target_id=policy.id,
        )
        return policy
