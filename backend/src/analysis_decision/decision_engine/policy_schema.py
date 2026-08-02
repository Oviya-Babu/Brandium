"""Policy validation rules (Phase 2 §10) — checked at Policy activation
time, against the Brand's currently-active BrandGenome. A Policy failing
any of these cannot be activated (§10: "A Policy failing this cannot be
activated")."""
from __future__ import annotations

import math
import uuid

from src.analysis_decision.decision_engine.schemas import (
    CriticalRule,
    CriticalRuleTargetType,
    GenomeTree,
    PolicyRules,
    VerdictThreshold,
)

_WEIGHT_SUM_TOLERANCE = 1e-6


def policy_rules_from_json(rules: dict) -> PolicyRules:
    """Converts a Policy's persisted `rules` JSON (Phase 0 §3.7) into the
    Decision Engine's pure dataclass shape. The one place this JSON
    structure's contract is defined — API request validation for Policy
    authoring should build against the same shape."""
    return PolicyRules(
        category_weights=rules.get("category_weights", {}),
        component_weights={uuid.UUID(k): v for k, v in rules.get("component_weights", {}).items()},
        assertion_weights={uuid.UUID(k): v for k, v in rules.get("assertion_weights", {}).items()},
        critical_rules=[
            CriticalRule(
                id=uuid.UUID(r["id"]),
                target_type=CriticalRuleTargetType(r["target_type"]),
                target_id=uuid.UUID(r["target_id"]),
                critical_threshold=r["critical_threshold"],
                override_verdict=r["override_verdict"],
                severity=r["severity"],
            )
            for r in rules.get("critical_rules", [])
        ],
        verdict_thresholds=[
            VerdictThreshold(min_score=t["min_score"], max_score=t["max_score"], verdict=t["verdict"])
            for t in rules.get("verdict_thresholds", [])
        ],
        improvement_threshold=rules.get("improvement_threshold", 0.8),
    )


def validate_policy_rules(rules: PolicyRules, genome_tree: GenomeTree) -> list[str]:
    """Returns a list of human-readable validation errors; empty means valid."""
    errors: list[str] = []

    # Rule 1: weight normalization at every level.
    category_names = {c.name for c in genome_tree.categories}
    weighted_categories = set(rules.category_weights.keys())
    if weighted_categories - category_names:
        errors.append(f"category_weights references unknown categories: {weighted_categories - category_names}")
    if not math.isclose(sum(rules.category_weights.get(n, 0.0) for n in category_names), 1.0, abs_tol=_WEIGHT_SUM_TOLERANCE):
        errors.append("category_weights must sum to 1.0 across all Genome categories.")

    for category in genome_tree.categories:
        component_ids = {c.id for c in category.components}
        weights = [rules.component_weights.get(cid, 0.0) for cid in component_ids]
        if component_ids and not math.isclose(sum(weights), 1.0, abs_tol=_WEIGHT_SUM_TOLERANCE):
            errors.append(f"component_weights within category '{category.name}' must sum to 1.0.")

        for component in category.components:
            explicit = {a.id: rules.assertion_weights[a.id] for a in component.assertions if a.id in rules.assertion_weights}
            if explicit and len(explicit) == len(component.assertions):
                if not math.isclose(sum(explicit.values()), 1.0, abs_tol=_WEIGHT_SUM_TOLERANCE):
                    errors.append(f"assertion_weights within component '{component.id}' must sum to 1.0 when fully specified.")

    # Rule 2: Critical Rule referential integrity.
    assertion_ids = {a.id for c in genome_tree.categories for comp in c.components for a in comp.assertions}
    component_ids_all = {comp.id for c in genome_tree.categories for comp in c.components}
    category_ids_all = {c.id for c in genome_tree.categories}
    for rule in rules.critical_rules:
        valid_set = {
            CriticalRuleTargetType.CATEGORY: category_ids_all,
            CriticalRuleTargetType.COMPONENT: component_ids_all,
            CriticalRuleTargetType.ASSERTION: assertion_ids,
        }[rule.target_type]
        if rule.target_id not in valid_set:
            errors.append(f"Critical Rule {rule.id} references a {rule.target_type.value} not present in this Genome version.")

    # Rule 3: Verdict Threshold completeness — monotonic, no gaps, covers 0-100.
    thresholds = sorted(rules.verdict_thresholds, key=lambda t: t.min_score)
    if not thresholds:
        errors.append("verdict_thresholds must not be empty.")
    else:
        if thresholds[0].min_score > 0.0:
            errors.append("verdict_thresholds must cover the score range starting at 0.")
        if thresholds[-1].max_score < 100.0:
            errors.append("verdict_thresholds must cover the score range up to 100.")
        for prev, curr in zip(thresholds, thresholds[1:]):
            if not math.isclose(prev.max_score, curr.min_score, abs_tol=_WEIGHT_SUM_TOLERANCE):
                errors.append(f"verdict_thresholds has a gap or overlap between {prev.verdict} and {curr.verdict}.")

    return errors
