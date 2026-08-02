"""Verdict Determination (Phase 2 §5.2) and Critical Rule resolution (§2.3)."""
from __future__ import annotations

from dataclasses import dataclass

from src.analysis_decision.decision_engine.aggregation import AggregateResult
from src.analysis_decision.decision_engine.schemas import CriticalRule, VerdictThreshold


@dataclass(frozen=True)
class FiredCriticalRule:
    rule: CriticalRule


@dataclass(frozen=True)
class VerdictResult:
    verdict: str
    source: str
    """'threshold' or 'critical_rule_override:<rule_id>' (Phase 2 §2.3:
    "must never be presented identically to one that came from the
    ordinary threshold lookup")."""
    fired_rules: list[CriticalRule]
    not_evaluated_rules: list[CriticalRule]


def lookup_threshold_verdict(score: float, thresholds: list[VerdictThreshold]) -> str:
    """Phase 2 §5.2 step 1 / §10 rule 3: thresholds are monotonically
    ordered and cover the full range with no gaps — validated at Policy
    activation time (policy_schema.py), trusted here."""
    for band in thresholds:
        if band.min_score <= score <= band.max_score:
            return band.verdict
    # Should be unreachable given §10 rule 3's completeness validation;
    # fail safe (INV-31) rather than silently guessing a verdict.
    raise ValueError(f"Score {score} matched no Verdict Threshold band — Policy failed §10 rule 3 validation.")


def resolve_verdict(
    score: float,
    thresholds: list[VerdictThreshold],
    critical_rules: list[CriticalRule],
    target_results: dict,
) -> VerdictResult:
    """`target_results` maps a Critical Rule's `target_id` to its
    `AggregateResult` (across category/component/assertion levels, all
    already computed by the caller's tree walk).
    """
    baseline = lookup_threshold_verdict(score, thresholds)

    fired: list[CriticalRule] = []
    not_evaluated: list[CriticalRule] = []

    for rule in critical_rules:
        result: AggregateResult | None = target_results.get(rule.target_id)
        if result is None or result.value is None:
            # INV-26: zero applicable/zero covered elements at the target
            # => "not evaluated", never treated as value=0.
            not_evaluated.append(rule)
            continue
        if result.value < rule.critical_threshold:
            fired.append(rule)

    if not fired:
        return VerdictResult(verdict=baseline, source="threshold", fired_rules=[], not_evaluated_rules=not_evaluated)

    # Phase 2 §2.3: most severe fired override applies.
    winning = max(fired, key=lambda r: r.severity)
    return VerdictResult(
        verdict=winning.override_verdict,
        source=f"critical_rule_override:{winning.id}",
        fired_rules=fired,
        not_evaluated_rules=not_evaluated,
    )
