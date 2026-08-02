"""Pure data shapes the Decision Engine computes over (Phase 2).

Deliberately plain stdlib `dataclasses`, not Pydantic — unlike API
request/response shapes (CLAUDE.md §3.2's "every domain shape that
crosses a boundary"), these never cross a process/serialization boundary
directly: the service layer parses/validates the Policy.rules JSON
through a separate Pydantic schema (`policy_rules_json_schema.py`) and
*then* builds these dataclasses from already-validated data. Keeping the
engine's core types dependency-free is also what makes this module (and
`aggregation.py`/`verdict.py`/`recommendation.py`/`engine.py`, all of
which depend on nothing but this file and the stdlib) independently
runnable and testable with zero third-party packages installed —
deliberate, not incidental, given how load-bearing this module is.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum


class AlignmentIndicator(str, Enum):
    ALIGNED = "aligned"
    PARTIALLY_ALIGNED = "partially_aligned"
    MISALIGNED = "misaligned"


ALIGNMENT_VALUES: dict[AlignmentIndicator, float] = {
    AlignmentIndicator.ALIGNED: 1.0,
    AlignmentIndicator.PARTIALLY_ALIGNED: 0.5,
    AlignmentIndicator.MISALIGNED: 0.0,
}
"""Phase 2 §3.1 — fixed platform behavior. A change to this table is a
`decision_function_version` bump (Phase 2 §8.1 item 1), never a silent edit."""


@dataclass(frozen=True)
class EvidenceItem:
    id: uuid.UUID
    alignment_indicator: AlignmentIndicator
    confidence: float


@dataclass(frozen=True)
class AssertionNode:
    """No `weight` field here by design (Phase 2 §2.2: "Why Weighting
    Lives in Policy, Not in the Genome") — the Genome asserts what is
    true about the brand; weighting is Policy's job, sourced by the
    engine from `PolicyRules.*_weights`, keyed by id/name. Two Brands
    could share an identical Genome shape and legitimately want
    different scoring emphasis; a weight field here would make that
    impossible without duplicating brand-identity content."""

    id: uuid.UUID


@dataclass(frozen=True)
class ComponentNode:
    id: uuid.UUID
    assertions: list[AssertionNode]


@dataclass(frozen=True)
class CategoryNode:
    id: uuid.UUID
    name: str
    is_required: bool
    components: list[ComponentNode]


@dataclass(frozen=True)
class GenomeTree:
    categories: list[CategoryNode]


class CriticalRuleTargetType(str, Enum):
    CATEGORY = "category"
    COMPONENT = "component"
    ASSERTION = "assertion"


@dataclass(frozen=True)
class CriticalRule:
    id: uuid.UUID
    target_type: CriticalRuleTargetType
    target_id: uuid.UUID
    critical_threshold: float
    override_verdict: str
    severity: int
    """Higher fires over lower when multiple rules fire simultaneously (Phase 2 §2.3)."""


@dataclass(frozen=True)
class VerdictThreshold:
    min_score: float
    max_score: float
    verdict: str


@dataclass(frozen=True)
class PolicyRules:
    """Phase 2 §2.1's four Policy components, plus the improvement
    threshold Recommendation triggering needs (§6.1) — Policy-defined,
    not named as a separate top-level entity anywhere in Phase 0-2, so it
    lives inside this same `rules` payload rather than inventing a field
    on the frozen Policy entity."""

    category_weights: dict[str, float]
    component_weights: dict[uuid.UUID, float]
    verdict_thresholds: list[VerdictThreshold]
    improvement_threshold: float
    assertion_weights: dict[uuid.UUID, float] = field(default_factory=dict)
    critical_rules: list[CriticalRule] = field(default_factory=list)
