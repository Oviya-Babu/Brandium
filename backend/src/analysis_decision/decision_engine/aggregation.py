"""Evidence Aggregation (Phase 2 §3) and Confidence Propagation (Phase 2 §4).

Both are implemented together because they share one tree-walk over the
same (weight, child) structure at every level — computing them separately
would mean walking the tree twice for no benefit. Every formula below is
transcribed directly from Phase 2; nothing here is invented.
"""
from __future__ import annotations

from dataclasses import dataclass

from src.analysis_decision.decision_engine.schemas import ALIGNMENT_VALUES, EvidenceItem


@dataclass(frozen=True)
class AggregateResult:
    """`value`/`raw_confidence` are `None` exactly when nothing at this
    level is covered — Phase 2 §3.2: "no evidence for an Assertion is not
    the same as failing it." A `None` value must never be treated as 0.0
    by a caller; it must be excluded from its own parent's aggregation,
    which `aggregate_level` already does by construction."""

    value: float | None
    coverage: float
    raw_confidence: float | None
    reported_confidence: float


_UNCOVERED = AggregateResult(value=None, coverage=0.0, raw_confidence=None, reported_confidence=0.0)


def aggregate_assertion(evidence_items: list[EvidenceItem]) -> AggregateResult:
    """Phase 2 §3.2: confidence-weighted mean of an Assertion's Evidence
    items. Phase 2 §4.3's "confidence of covered children" at this base
    level is the Evidence items' own confidences."""
    if not evidence_items:
        return _UNCOVERED

    total_confidence = sum(e.confidence for e in evidence_items)
    if total_confidence == 0.0:
        # All evidence carries zero confidence: the weighted mean is
        # undefined (0/0). Per §3.2's "absence of signal is never a
        # negative signal" spirit, this is treated as uncovered rather
        # than silently defaulting to a misleading 0.0 or 1.0 value.
        return _UNCOVERED

    value = sum(e.confidence * ALIGNMENT_VALUES[e.alignment_indicator] for e in evidence_items) / total_confidence
    raw_confidence = total_confidence / len(evidence_items)
    return AggregateResult(value=value, coverage=1.0, raw_confidence=raw_confidence, reported_confidence=raw_confidence)


def aggregate_level(children: list[tuple[float, AggregateResult]]) -> AggregateResult:
    """Phase 2 §3.3-3.5 (Component/Category/Overall — identical formula
    shape at every level) and §4.2/§4.4 (Coverage, Coverage Discount).

    `children` is `[(weight, child_AggregateResult), ...]` for every
    child at this level, covered or not — coverage is computed from the
    full set; the value/confidence aggregation only sums over the
    covered subset, exactly as Phase 2 specifies.
    """
    total_weight_all = sum(w for w, _ in children)
    covered = [(w, r) for w, r in children if r.value is not None]

    if total_weight_all == 0.0 or not covered:
        return _UNCOVERED

    total_weight_covered = sum(w for w, _ in covered)
    value = sum(w * r.value for w, r in covered) / total_weight_covered  # type: ignore[operator]
    raw_confidence = sum(r.raw_confidence for _, r in covered) / len(covered)  # type: ignore[misc]
    coverage = total_weight_covered / total_weight_all
    reported_confidence = raw_confidence * coverage

    return AggregateResult(value=value, coverage=coverage, raw_confidence=raw_confidence, reported_confidence=reported_confidence)
