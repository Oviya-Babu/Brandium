"""Completeness Verification (Phase 3 §6, INV-24/INV-25). Decides whether
an AnalysisRun may transition to `complete` or must route to `failed`."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum

from src.analysis_decision.applicability import ApplicableSet
from src.brand_governance.domain.models import REQUIRED_GENOME_CATEGORIES


class OutcomeType(str, Enum):
    EVIDENCE = "evidence"
    ATTEMPTED_NO_SIGNAL = "attempted_no_signal"
    WORKER_FAILURE = "worker_failure"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True)
class CompletenessResult:
    can_complete: bool
    failure_reason: str | None
    outcomes: dict[uuid.UUID, OutcomeType]


def verify_completeness(
    applicable_set: ApplicableSet,
    evidence_assertion_ids: set[uuid.UUID],
    no_signal_assertion_ids: set[uuid.UUID],
    failed_assertion_ids: set[uuid.UUID],
) -> CompletenessResult:
    """Phase 3 §6: every in-scope Assertion must reach exactly one of the
    three terminal outcomes; a Required category with an in-scope
    worker-failure Assertion routes the run to `failed`.
    """
    outcomes: dict[uuid.UUID, OutcomeType] = {}
    required_category_has_failure: dict[str, bool] = {}

    for category in applicable_set.categories:
        category_assertion_ids: list[uuid.UUID] = []
        for component in applicable_set.components_by_category.get(category.id, []):
            for assertion in applicable_set.assertions_by_component.get(component.id, []):
                category_assertion_ids.append(assertion.id)

                if assertion.id in evidence_assertion_ids:
                    outcomes[assertion.id] = OutcomeType.EVIDENCE
                elif assertion.id in no_signal_assertion_ids:
                    outcomes[assertion.id] = OutcomeType.ATTEMPTED_NO_SIGNAL
                elif assertion.id in failed_assertion_ids:
                    outcomes[assertion.id] = OutcomeType.WORKER_FAILURE
                else:
                    # In-scope but no record at all — invariant 1 violation;
                    # treated conservatively as a worker failure (fail-safe,
                    # INV-31: an inconclusive state never defaults to permissive).
                    outcomes[assertion.id] = OutcomeType.WORKER_FAILURE

        if category.name in REQUIRED_GENOME_CATEGORIES and category_assertion_ids:
            has_failure = any(outcomes[aid] == OutcomeType.WORKER_FAILURE for aid in category_assertion_ids)
            required_category_has_failure[category.name.value] = has_failure

    failed_categories = [name for name, has_failure in required_category_has_failure.items() if has_failure]
    if failed_categories:
        return CompletenessResult(
            can_complete=False,
            failure_reason=f"Required categor{'y' if len(failed_categories) == 1 else 'ies'} "
            f"{', '.join(failed_categories)} had an in-scope worker-failure outcome.",
            outcomes=outcomes,
        )

    return CompletenessResult(can_complete=True, failure_reason=None, outcomes=outcomes)
