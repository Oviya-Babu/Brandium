"""Applicability Determination (Phase 3 §2). Computes the Applicable Set
for one AssetVersion against the active Genome — derived, deterministic,
not persisted. `applicability_scope` is a small JSON condition object;
absence means universally applicable (the default)."""
from __future__ import annotations

from dataclasses import dataclass

from src.brand_governance.domain.models import Assertion, GenomeCategory, GenomeComponent


@dataclass(frozen=True)
class EvaluationContext:
    """Phase 3 §2: modality + context_tags, taken together — pinned
    alongside genome/policy/decision_function_version in the
    reproducibility contract (Phase 3 §2's addendum)."""

    modality: str
    context_tags: list[str]


def _scope_satisfied(scope: dict | None, context: EvaluationContext) -> bool:
    """A minimal, deterministic condition language: `{"modality": "image"}`
    and/or `{"context_tags_any": ["social", "paid"]}`. Phase 1/3 do not
    specify the condition grammar beyond "a condition satisfied by the
    Evaluation Context" — this is the smallest sufficient implementation,
    documented rather than silently assumed, with a clear extension point
    if richer conditions are needed later."""
    if not scope:
        return True
    if "modality" in scope and scope["modality"] != context.modality:
        return False
    if "context_tags_any" in scope:
        if not set(scope["context_tags_any"]) & set(context.context_tags):
            return False
    return True


@dataclass(frozen=True)
class ApplicableSet:
    categories: list[GenomeCategory]
    components_by_category: dict
    assertions_by_component: dict

    def is_assertion_applicable(self, assertion_id) -> bool:
        for assertions in self.assertions_by_component.values():
            if any(a.id == assertion_id for a in assertions):
                return True
        return False


def resolve_applicability(
    categories: list[GenomeCategory],
    components_by_category_id: dict,
    assertions_by_component_id: dict,
    context: EvaluationContext,
) -> ApplicableSet:
    """Phase 3 §2: scope inherited downward (Category -> Component ->
    Assertion) unless a lower level further restricts it — a Category
    excluded by its own scope excludes everything beneath it regardless
    of child-level scopes."""
    result_categories: list[GenomeCategory] = []
    components_by_category: dict = {}
    assertions_by_component: dict = {}

    for category in categories:
        if not _scope_satisfied(category.applicability_scope, context):
            continue
        result_categories.append(category)

        applicable_components = []
        for component in components_by_category_id.get(category.id, []):
            if not _scope_satisfied(component.applicability_scope, context):
                continue
            applicable_components.append(component)

            applicable_assertions = [
                a
                for a in assertions_by_component_id.get(component.id, [])
                if _scope_satisfied(a.applicability_scope, context)
            ]
            assertions_by_component[component.id] = applicable_assertions

        components_by_category[category.id] = applicable_components

    return ApplicableSet(
        categories=result_categories,
        components_by_category=components_by_category,
        assertions_by_component=assertions_by_component,
    )
