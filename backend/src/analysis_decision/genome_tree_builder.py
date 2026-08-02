"""Converts the ORM Genome structure (already filtered to one run's
Applicable Set — see `applicability.py`) into the Decision Engine's pure
`GenomeTree` dataclass shape (`decision_engine/schemas.py`). The one
translation boundary between the persisted Brand Governance model and
the dependency-free Decision Engine, per CLAUDE.md §3.1's dependency-
inversion principle."""
from __future__ import annotations

from src.analysis_decision.applicability import ApplicableSet
from src.analysis_decision.decision_engine.schemas import AssertionNode, CategoryNode, ComponentNode, GenomeTree
from src.brand_governance.domain.models import REQUIRED_GENOME_CATEGORIES


def build_genome_tree(applicable_set: ApplicableSet) -> GenomeTree:
    categories: list[CategoryNode] = []
    for category in applicable_set.categories:
        components: list[ComponentNode] = []
        for component in applicable_set.components_by_category.get(category.id, []):
            assertions = [
                AssertionNode(id=a.id) for a in applicable_set.assertions_by_component.get(component.id, [])
            ]
            if not assertions:
                continue
            components.append(ComponentNode(id=component.id, assertions=assertions))
        if not components:
            continue
        categories.append(
            CategoryNode(
                id=category.id,
                name=category.name.value,
                is_required=category.name in REQUIRED_GENOME_CATEGORIES,
                components=components,
            )
        )
    return GenomeTree(categories=categories)
