"""Correctness tests for the Decision Engine formulas (Phase 2 §3-§6) —
hand-computed expected values, not just reproducibility."""
import uuid

from src.analysis_decision.decision_engine.aggregation import aggregate_assertion, aggregate_level
from src.analysis_decision.decision_engine.engine import compute_decision
from src.analysis_decision.decision_engine.recommendation import trigger_recommendations
from src.analysis_decision.decision_engine.schemas import (
    AlignmentIndicator,
    AssertionNode,
    CategoryNode,
    ComponentNode,
    CriticalRule,
    CriticalRuleTargetType,
    EvidenceItem,
    GenomeTree,
    PolicyRules,
    VerdictThreshold,
)
from src.analysis_decision.decision_engine.verdict import resolve_verdict


def test_alignment_value_function_lookup() -> None:
    from src.analysis_decision.decision_engine.schemas import ALIGNMENT_VALUES

    assert ALIGNMENT_VALUES[AlignmentIndicator.ALIGNED] == 1.0
    assert ALIGNMENT_VALUES[AlignmentIndicator.PARTIALLY_ALIGNED] == 0.5
    assert ALIGNMENT_VALUES[AlignmentIndicator.MISALIGNED] == 0.0


def test_assertion_aggregation_is_confidence_weighted_mean() -> None:
    # aligned @ 0.8 confidence, misaligned @ 0.2 confidence
    # value = (0.8*1.0 + 0.2*0.0) / (0.8+0.2) = 0.8
    items = [
        EvidenceItem(id=uuid.uuid4(), alignment_indicator=AlignmentIndicator.ALIGNED, confidence=0.8),
        EvidenceItem(id=uuid.uuid4(), alignment_indicator=AlignmentIndicator.MISALIGNED, confidence=0.2),
    ]
    result = aggregate_assertion(items)
    assert result.value is not None and abs(result.value - 0.8) < 1e-9
    assert result.coverage == 1.0


def test_uncovered_assertion_excluded_not_penalized() -> None:
    result = aggregate_assertion([])
    assert result.value is None
    assert result.coverage == 0.0


def test_component_aggregation_excludes_uncovered_assertions_from_both_sums() -> None:
    from src.analysis_decision.decision_engine.aggregation import AggregateResult

    covered = AggregateResult(value=1.0, coverage=1.0, raw_confidence=0.9, reported_confidence=0.9)
    uncovered = AggregateResult(value=None, coverage=0.0, raw_confidence=None, reported_confidence=0.0)

    # Two assertions of equal weight, one covered (value=1.0) one not:
    # component value should be exactly 1.0 (uncovered excluded), not 0.5.
    result = aggregate_level([(0.5, covered), (0.5, uncovered)])
    assert result.value == 1.0
    # Coverage should be 0.5 (half the weight was covered).
    assert result.coverage == 0.5
    assert result.reported_confidence == result.raw_confidence * 0.5


def test_critical_rule_fires_and_overrides_baseline_verdict() -> None:
    from src.analysis_decision.decision_engine.aggregation import AggregateResult

    target_id = uuid.uuid4()
    rule = CriticalRule(
        id=uuid.uuid4(),
        target_type=CriticalRuleTargetType.COMPONENT,
        target_id=target_id,
        critical_threshold=0.5,
        override_verdict="Non-Compliant",
        severity=10,
    )
    thresholds = [VerdictThreshold(min_score=0.0, max_score=100.0, verdict="Compliant")]
    target_results = {target_id: AggregateResult(value=0.1, coverage=1.0, raw_confidence=1.0, reported_confidence=1.0)}

    verdict = resolve_verdict(95.0, thresholds, [rule], target_results)

    assert verdict.verdict == "Non-Compliant"
    assert verdict.source == f"critical_rule_override:{rule.id}"


def test_critical_rule_not_evaluated_when_target_uncovered() -> None:
    """INV-26: zero covered elements => not evaluated, never value=0."""
    from src.analysis_decision.decision_engine.aggregation import AggregateResult

    target_id = uuid.uuid4()
    rule = CriticalRule(
        id=uuid.uuid4(),
        target_type=CriticalRuleTargetType.COMPONENT,
        target_id=target_id,
        critical_threshold=0.5,
        override_verdict="Non-Compliant",
        severity=10,
    )
    thresholds = [VerdictThreshold(min_score=0.0, max_score=100.0, verdict="Compliant")]
    target_results = {target_id: AggregateResult(value=None, coverage=0.0, raw_confidence=None, reported_confidence=0.0)}

    verdict = resolve_verdict(95.0, thresholds, [rule], target_results)

    assert verdict.verdict == "Compliant"
    assert verdict.source == "threshold"
    assert rule in verdict.not_evaluated_rules
    assert rule not in verdict.fired_rules


def test_multiple_fired_rules_most_severe_wins() -> None:
    from src.analysis_decision.decision_engine.aggregation import AggregateResult

    t1, t2 = uuid.uuid4(), uuid.uuid4()
    low_severity = CriticalRule(
        id=uuid.uuid4(), target_type=CriticalRuleTargetType.COMPONENT, target_id=t1,
        critical_threshold=0.9, override_verdict="Needs Review", severity=1,
    )
    high_severity = CriticalRule(
        id=uuid.uuid4(), target_type=CriticalRuleTargetType.COMPONENT, target_id=t2,
        critical_threshold=0.9, override_verdict="Non-Compliant", severity=100,
    )
    thresholds = [VerdictThreshold(min_score=0.0, max_score=100.0, verdict="Compliant")]
    target_results = {
        t1: AggregateResult(value=0.1, coverage=1.0, raw_confidence=1.0, reported_confidence=1.0),
        t2: AggregateResult(value=0.1, coverage=1.0, raw_confidence=1.0, reported_confidence=1.0),
    }

    verdict = resolve_verdict(95.0, thresholds, [low_severity, high_severity], target_results)

    assert verdict.verdict == "Non-Compliant"
    assert verdict.source == f"critical_rule_override:{high_severity.id}"


def test_recommendation_grounding_never_empty_when_triggered() -> None:
    """INV-06: no Recommendation may exist without at least one related_evidence_id."""
    component_id = uuid.uuid4()
    assertion_id = uuid.uuid4()
    ev_id = uuid.uuid4()
    component = ComponentNode(id=component_id, assertions=[AssertionNode(id=assertion_id)])
    from src.analysis_decision.decision_engine.aggregation import AggregateResult

    component_results = {component_id: AggregateResult(value=0.2, coverage=1.0, raw_confidence=1.0, reported_confidence=1.0)}
    evidence_by_assertion = {
        assertion_id: [EvidenceItem(id=ev_id, alignment_indicator=AlignmentIndicator.MISALIGNED, confidence=1.0)]
    }

    recs = trigger_recommendations([(1.0, component)], component_results, evidence_by_assertion, improvement_threshold=0.9)

    assert len(recs) == 1
    assert recs[0].related_evidence_ids == [ev_id]
    assert recs[0].priority == 1.0 * (0.9 - 0.2)


def test_end_to_end_decision_matches_hand_computed_score() -> None:
    category_name = "verbal_identity"
    category_id, component_id, assertion_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    tree = GenomeTree(
        categories=[
            CategoryNode(
                id=category_id,
                name=category_name,
                is_required=True,
                components=[ComponentNode(id=component_id, assertions=[AssertionNode(id=assertion_id)])],
            )
        ]
    )
    policy = PolicyRules(
        category_weights={category_name: 1.0},
        component_weights={component_id: 1.0},
        assertion_weights={assertion_id: 1.0},
        critical_rules=[],
        verdict_thresholds=[VerdictThreshold(min_score=0.0, max_score=100.0, verdict="Compliant")],
        improvement_threshold=0.5,
    )
    evidence = {assertion_id: [EvidenceItem(id=uuid.uuid4(), alignment_indicator=AlignmentIndicator.ALIGNED, confidence=1.0)]}

    result = compute_decision(tree, evidence, policy)

    assert result.score == 100.0
    assert result.reported_confidence == 1.0
    assert result.verdict.verdict == "Compliant"
    assert result.recommendations == []
