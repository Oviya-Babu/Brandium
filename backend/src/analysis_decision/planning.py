"""Planning (Phase 3 §3) — assigns workers to in-scope Assertions.

**Flagged simplification for this Text+Image pass:** Phase 3 §4 names
five conceptual worker roles (Visual, Verbal, Compliance & Accessibility,
Distinctiveness, Values & Mission). This implementation collapses the
four text-classifiable roles (Verbal, Compliance & Accessibility, Values
& Mission, and Distinctiveness's non-KB-consulting half) into one
`TextWorker` code module, and keeps Visual as `ImageWorker` — because
all four text roles use the identical mechanism (an LLM call over
extracted/asset text, judged against a Genome Assertion) and differ only
in *which* Assertions they're assigned, which Planning already keeps
unambiguous per-Assertion (Phase 3 §3: "no single Assertion is ever
assigned to more than one worker" — preserved here). The Distinctiveness
Worker's AI Slop Knowledge Base consultation (Phase 3 §4, DR-004) is
explicitly NOT implemented in this pass — there is no seeded Slop KB
corpus yet — so distinctiveness-flavored Assertions are evaluated by
`TextWorker` without that reference corpus, a real capability gap, not a
silent one. See IMPLEMENTATION_STATUS.md.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import Enum

from src.analysis_decision.applicability import ApplicableSet
from src.brand_governance.domain.models import GenomeCategoryName
from src.campaign_asset.domain.models import AssetModality

IMAGE_WORKER_CATEGORIES = {GenomeCategoryName.VISUAL_IDENTITY}
TEXT_WORKER_CATEGORIES = {
    GenomeCategoryName.VERBAL_IDENTITY,
    GenomeCategoryName.MESSAGING_POSITIONING,
    GenomeCategoryName.VALUES_MISSION,
    GenomeCategoryName.COMPLIANCE_LEGAL,
    GenomeCategoryName.ACCESSIBILITY,
}


class WorkerType(str, Enum):
    TEXT_WORKER = "text_worker"
    IMAGE_WORKER = "image_worker"


@dataclass(frozen=True)
class WorkUnit:
    """Phase 4 §2 — execution-layer concept, not a persisted entity."""

    worker_type: WorkerType
    assertion_ids: list[uuid.UUID]


_MAX_ASSERTIONS_PER_WORK_UNIT = 6
"""One Work Unit is one LLM call judging every one of its Assertions in a
single structured-output response (`workers/text_worker.py`,
`workers/image_worker.py`). Against the CPU-only small model this stack
runs, a single call covering every applicable Assertion for a category
doesn't just get slow — confirmed live: a real 30-Assertion Visual
Identity batch (Red Bull's compiled Genome) ran to completion without
erroring or timing out, but its structured output only actually covered
23 of the 30 Assertions it was asked to judge. The 7 it silently
dropped had no judgment, no `no_signal` entry, and no failure — nothing
at all — which Completeness Verification's fail-safe conservative
default (Phase 3 §6, INV-31) then correctly treated as a
`worker_failure`, blocking the Required category and the whole run.
Chunking each worker type's Assertions into batches this size (matching
a batch that has completed cleanly) trades one large unreliable call for
several smaller reliable ones — the same total judging work, just sized
to what this model can actually track in one response."""


def _chunk_into_work_units(worker_type: WorkerType, assertion_ids: list[uuid.UUID]) -> list[WorkUnit]:
    return [
        WorkUnit(worker_type=worker_type, assertion_ids=assertion_ids[i : i + _MAX_ASSERTIONS_PER_WORK_UNIT])
        for i in range(0, len(assertion_ids), _MAX_ASSERTIONS_PER_WORK_UNIT)
    ]


def build_execution_plan(applicable_set: ApplicableSet, modality: AssetModality) -> list[WorkUnit]:
    """Phase 3 §3: never run every worker against every asset — a
    text-only asset needs no ImageWorker; an image asset (without OCR in
    this pass) needs no TextWorker."""
    text_assertions: list[uuid.UUID] = []
    image_assertions: list[uuid.UUID] = []

    for category in applicable_set.categories:
        for component in applicable_set.components_by_category.get(category.id, []):
            for assertion in applicable_set.assertions_by_component.get(component.id, []):
                if category.name in IMAGE_WORKER_CATEGORIES:
                    image_assertions.append(assertion.id)
                elif category.name in TEXT_WORKER_CATEGORIES:
                    text_assertions.append(assertion.id)

    plan: list[WorkUnit] = []
    if modality == AssetModality.TEXT and text_assertions:
        plan.extend(_chunk_into_work_units(WorkerType.TEXT_WORKER, text_assertions))
    if modality == AssetModality.IMAGE and image_assertions:
        plan.extend(_chunk_into_work_units(WorkerType.IMAGE_WORKER, image_assertions))

    return plan
