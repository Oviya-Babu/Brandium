"""Recommendation Triggering and Priority (Phase 2 §6.1-6.2) — the
deterministic half only. Narration (`text`) lives in
`analysis_decision/recommendation_narration.py`, a separate module by
design (Phase 2 §6.3's deterministic/generative boundary, INV-04)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from src.analysis_decision.decision_engine.aggregation import AggregateResult
from src.analysis_decision.decision_engine.schemas import AlignmentIndicator, ComponentNode, EvidenceItem


@dataclass(frozen=True)
class TriggeredRecommendation:
    component_id: uuid.UUID
    priority: float
    related_evidence_ids: list[uuid.UUID]


def trigger_recommendations(
    components: list[tuple[float, ComponentNode]],
    component_results: dict[uuid.UUID, AggregateResult],
    evidence_by_assertion: dict[uuid.UUID, list[EvidenceItem]],
    improvement_threshold: float,
) -> list[TriggeredRecommendation]:
    """`components` is `[(weight_within_category, ComponentNode), ...]`
    for every Component in the Applicability Set (Phase 2 §6.1: "the
    chosen granularity"). Only covered Components (a value exists) are
    eligible — Phase 3 §2 addendum: Recommendation Generation only
    considers applicable (and, implicitly, evaluated) components."""
    triggered: list[TriggeredRecommendation] = []

    for weight, component in components:
        result = component_results.get(component.id)
        if result is None or result.value is None:
            continue
        if result.value >= improvement_threshold:
            continue

        priority = weight * max(0.0, improvement_threshold - result.value)

        related_evidence_ids: list[uuid.UUID] = []
        for assertion in component.assertions:
            for evidence in evidence_by_assertion.get(assertion.id, []):
                if evidence.alignment_indicator != AlignmentIndicator.ALIGNED:
                    related_evidence_ids.append(evidence.id)

        if not related_evidence_ids:
            # Component fell below threshold via partially-aligned-only
            # evidence at some sub-weighting that still nets non-perfect;
            # fall back to citing every covered assertion's evidence so
            # INV-06 ("no ungrounded recommendation") is never violated.
            for assertion in component.assertions:
                related_evidence_ids.extend(e.id for e in evidence_by_assertion.get(assertion.id, []))

        if related_evidence_ids:
            triggered.append(
                TriggeredRecommendation(
                    component_id=component.id, priority=priority, related_evidence_ids=related_evidence_ids
                )
            )

    return triggered
