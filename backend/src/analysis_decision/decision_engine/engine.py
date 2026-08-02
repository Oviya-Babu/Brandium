"""Decision Engine orchestration (Phase 2, all sections).

Single entry point: `compute_decision`. Pure function of its inputs —
this is the literal, checkable form of NFR-004/INV-02: identical inputs
always produce an identical `DecisionResult`. No I/O, no LLM call, no
wall-clock dependency, no unordered-set iteration affecting output
(CLAUDE.md §5.5) — verified by the Hypothesis property test in
`backend/tests/property/test_decision_engine_reproducibility.py`.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from src.analysis_decision.decision_engine.aggregation import AggregateResult, aggregate_assertion, aggregate_level
from src.analysis_decision.decision_engine.recommendation import TriggeredRecommendation, trigger_recommendations
from src.analysis_decision.decision_engine.schemas import ComponentNode, EvidenceItem, GenomeTree, PolicyRules
from src.analysis_decision.decision_engine.verdict import VerdictResult, resolve_verdict

DECISION_FUNCTION_VERSION = 1
"""Phase 2 §8.1/§8.3 — monotonically increasing integer. Bump this, and
only this, the moment any of the five covered mechanisms changes."""


@dataclass(frozen=True)
class ExplainabilityTree:
    """Every level's AggregateResult, keyed by id — the on-demand-
    reconstructable reasoning chain Phase 2 §7 requires. Never persisted
    (Phase 2 §5.3); the Explainability Engine calls `compute_decision`
    fresh and reads this off the result each time."""

    assertion_results: dict[uuid.UUID, AggregateResult] = field(default_factory=dict)
    component_results: dict[uuid.UUID, AggregateResult] = field(default_factory=dict)
    category_results: dict[uuid.UUID, AggregateResult] = field(default_factory=dict)
    overall: AggregateResult = field(
        default_factory=lambda: AggregateResult(value=None, coverage=0.0, raw_confidence=None, reported_confidence=0.0)
    )


@dataclass(frozen=True)
class DecisionResult:
    score: float
    reported_confidence: float
    verdict: VerdictResult
    recommendations: list[TriggeredRecommendation]
    explainability: ExplainabilityTree
    decision_function_version: int


def compute_decision(
    genome_tree: GenomeTree,
    evidence_by_assertion: dict[uuid.UUID, list[EvidenceItem]],
    policy: PolicyRules,
) -> DecisionResult:
    assertion_results: dict[uuid.UUID, AggregateResult] = {}
    component_results: dict[uuid.UUID, AggregateResult] = {}
    category_results: dict[uuid.UUID, AggregateResult] = {}
    all_components: list[tuple[float, ComponentNode]] = []

    category_children: list[tuple[float, AggregateResult]] = []

    for category in genome_tree.categories:
        component_children: list[tuple[float, AggregateResult]] = []

        for component in category.components:
            assertion_children: list[tuple[float, AggregateResult]] = []

            for assertion in component.assertions:
                result = aggregate_assertion(evidence_by_assertion.get(assertion.id, []))
                assertion_results[assertion.id] = result
                weight = policy.assertion_weights.get(assertion.id, 1.0)
                assertion_children.append((weight, result))

            component_result = aggregate_level(assertion_children)
            component_results[component.id] = component_result
            comp_weight = policy.component_weights.get(component.id, 1.0)
            component_children.append((comp_weight, component_result))
            all_components.append((comp_weight, component))

        category_result = aggregate_level(component_children)
        category_results[category.id] = category_result
        cat_weight = policy.category_weights.get(category.name, 1.0)
        category_children.append((cat_weight, category_result))

    overall = aggregate_level(category_children)

    # Explicit, flagged interpretation for an edge case Phase 2 does not
    # resolve: a legitimately-`complete` run where every applicable
    # Assertion resolved to attempted-no-signal (no Evidence anywhere).
    # Score floors to 0.0 with 0.0 confidence rather than raising, so a
    # Decision can still be recorded (never silently invented as a
    # positive/neutral score) — see decision_engine/README-equivalent
    # docstring in engine.py's module header for the "why."
    score = (overall.value if overall.value is not None else 0.0) * 100.0
    reported_confidence = overall.reported_confidence

    target_results: dict[uuid.UUID, AggregateResult] = {
        **assertion_results,
        **component_results,
        **category_results,
    }
    verdict = resolve_verdict(score, policy.verdict_thresholds, policy.critical_rules, target_results)

    recommendations = trigger_recommendations(
        components=all_components,
        component_results=component_results,
        evidence_by_assertion=evidence_by_assertion,
        improvement_threshold=policy.improvement_threshold,
    )

    return DecisionResult(
        score=score,
        reported_confidence=reported_confidence,
        verdict=verdict,
        recommendations=recommendations,
        explainability=ExplainabilityTree(
            assertion_results=assertion_results,
            component_results=component_results,
            category_results=category_results,
            overall=overall,
        ),
        decision_function_version=DECISION_FUNCTION_VERSION,
    )
