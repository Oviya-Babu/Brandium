"""Hypothesis property test for the Decision Engine's reproducibility
guarantee (INV-02/NFR-004, Phase 2 §8.2): given an identical Evidence
set + Genome + Policy, recomputing a Decision must always yield an
identical score and verdict. This is the direct test of the platform's
core defensibility claim (CLAUDE.md §7), not incidental coverage.
"""
import uuid

from hypothesis import given
from hypothesis import strategies as st

from src.analysis_decision.decision_engine.engine import compute_decision
from src.analysis_decision.decision_engine.schemas import (
    AlignmentIndicator,
    AssertionNode,
    CategoryNode,
    ComponentNode,
    EvidenceItem,
    GenomeTree,
    PolicyRules,
    VerdictThreshold,
)

ASSERTION_A = uuid.uuid4()
ASSERTION_B = uuid.uuid4()
COMPONENT_ID = uuid.uuid4()
CATEGORY_NAME = "verbal_identity"

FIXED_TREE = GenomeTree(
    categories=[
        CategoryNode(
            id=uuid.uuid4(),
            name=CATEGORY_NAME,
            is_required=True,
            components=[
                ComponentNode(
                    id=COMPONENT_ID,
                    assertions=[
                        AssertionNode(id=ASSERTION_A),
                        AssertionNode(id=ASSERTION_B),
                    ],
                )
            ],
        )
    ]
)

FIXED_POLICY = PolicyRules(
    category_weights={CATEGORY_NAME: 1.0},
    component_weights={COMPONENT_ID: 1.0},
    assertion_weights={ASSERTION_A: 0.5, ASSERTION_B: 0.5},
    critical_rules=[],
    verdict_thresholds=[
        VerdictThreshold(min_score=0.0, max_score=59.999999, verdict="Non-Compliant"),
        VerdictThreshold(min_score=59.999999, max_score=100.0, verdict="Compliant"),
    ],
    improvement_threshold=0.9,
)


def _evidence_for(alignment_a: AlignmentIndicator, conf_a: float, alignment_b: AlignmentIndicator, conf_b: float):
    return {
        ASSERTION_A: [EvidenceItem(id=uuid.uuid4(), alignment_indicator=alignment_a, confidence=conf_a)],
        ASSERTION_B: [EvidenceItem(id=uuid.uuid4(), alignment_indicator=alignment_b, confidence=conf_b)],
    }


alignment_strategy = st.sampled_from(list(AlignmentIndicator))
confidence_strategy = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


@given(alignment_strategy, confidence_strategy, alignment_strategy, confidence_strategy)
def test_identical_inputs_always_produce_identical_score_and_verdict(
    alignment_a: AlignmentIndicator, conf_a: float, alignment_b: AlignmentIndicator, conf_b: float
) -> None:
    evidence = _evidence_for(alignment_a, conf_a, alignment_b, conf_b)

    result_1 = compute_decision(FIXED_TREE, evidence, FIXED_POLICY)
    result_2 = compute_decision(FIXED_TREE, evidence, FIXED_POLICY)

    assert result_1.score == result_2.score
    assert result_1.verdict.verdict == result_2.verdict.verdict
    assert result_1.verdict.source == result_2.verdict.source
    assert result_1.reported_confidence == result_2.reported_confidence
    assert result_1.decision_function_version == result_2.decision_function_version


@given(alignment_strategy, confidence_strategy, alignment_strategy, confidence_strategy)
def test_score_is_always_within_valid_range(
    alignment_a: AlignmentIndicator, conf_a: float, alignment_b: AlignmentIndicator, conf_b: float
) -> None:
    evidence = _evidence_for(alignment_a, conf_a, alignment_b, conf_b)
    result = compute_decision(FIXED_TREE, evidence, FIXED_POLICY)
    assert 0.0 <= result.score <= 100.0
    assert 0.0 <= result.reported_confidence <= 1.0


def test_no_evidence_anywhere_yields_zero_confidence_not_a_crash() -> None:
    """Explicit, documented interpretation for the fully-uncovered edge
    case Phase 2 doesn't resolve (engine.py's docstring) — must not raise."""
    result = compute_decision(FIXED_TREE, {}, FIXED_POLICY)
    assert result.score == 0.0
    assert result.reported_confidence == 0.0
