"""Knowledge Validation Rules (Phase 1 §10) — checked before a draft may
enter `pending_review` (Phase 1 §3's activation gate), independent of and
prior to the DR-006 human sign-off gate itself."""
from __future__ import annotations

from src.brand_governance.domain.models import (
    REQUIRED_GENOME_CATEGORIES,
    Assertion,
    AssertionStatus,
    GenomeCategory,
    GenomeComponent,
)


def validate_for_review(
    categories: list[GenomeCategory],
    components: list[GenomeComponent],
    assertions: list[Assertion],
) -> list[str]:
    errors: list[str] = []

    components_by_category: dict = {}
    for component in components:
        components_by_category.setdefault(component.category_id, []).append(component)

    assertions_by_component: dict = {}
    for assertion in assertions:
        assertions_by_component.setdefault(assertion.component_id, []).append(assertion)

    # Rule 1: Required category coverage — at least one populated
    # Component (>=1 active/non-empty Assertion) per Required category.
    for category in categories:
        if category.name not in REQUIRED_GENOME_CATEGORIES:
            continue
        populated = any(
            assertions_by_component.get(component.id)
            for component in components_by_category.get(category.id, [])
        )
        if not populated:
            errors.append(f"Required category '{category.name.value}' has no populated Component.")

    # Rule 3: No unresolved conflicts.
    conflicted = [a for a in assertions if a.status == AssertionStatus.CONFLICTED]
    if conflicted:
        errors.append(f"{len(conflicted)} Assertion(s) remain in 'conflicted' status — requires human resolution.")

    # Rule 4: Confidence validity.
    invalid_confidence = [a for a in assertions if not (0.0 <= a.confidence <= 1.0)]
    if invalid_confidence:
        errors.append(f"{len(invalid_confidence)} Assertion(s) have an out-of-range confidence value.")

    return errors
