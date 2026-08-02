"""Genome Compilation Workflow (Phase 1 §5) — steps 1-4: Ingestion is
`brand_history_service.py`'s job; this module covers Candidate Assertion
Formation, Consolidation, and Draft Assembly.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from difflib import SequenceMatcher

from src.brand_governance.domain.models import (
    Assertion,
    AssertionOriginType,
    AssertionStatus,
    BrandGenome,
    BrandHistory,
    BrandHistoryAuthorityLevel,
    GenomeCategory,
    GenomeCategoryName,
    GenomeComponent,
    GenomeStatus,
)
from src.brand_governance.genome_llm_schemas import CandidateAssertionLLM, CandidateExtractionResult
from src.brand_governance.genome_taxonomy import GENOME_TAXONOMY
from src.logging import get_logger
from src.shared_kernel.llm.client import LLMClient, LLMValidationFailure
from src.shared_kernel.types import new_id

logger = get_logger(__name__)

_TEXT_ONLY_SCOPE = {"modality": "text"}
_IMAGE_ONLY_SCOPE = {"modality": "image"}
"""Phase 3 §2's `applicability_scope` addendum, populated here at compile
time rather than left null (its "universally applicable" default).
`analysis_decision/planning.py`'s execution planner only ever dispatches
an ImageWorker for Visual Identity assertions and only for image assets,
and a TextWorker for every other category and only for text assets — it
never evaluates Visual Identity against a text asset or the reverse.
Left at the default (null = universally applicable), Applicability
Determination still considered the *other* modality's Required
categories in scope; since Planning then never produces a worker outcome
for them, Completeness Verification's fail-safe default (Phase 3 §6:
an in-scope Assertion with no outcome at all is conservatively treated
as a `worker_failure`, INV-31) marked them failed — permanently blocking
every single-modality asset from ever reaching `complete` whenever the
Genome had real content in the other modality's Required categories
(confirmed live: an image asset failed on Verbal Identity/Messaging &
Positioning this way). Scoping each category to the one modality
Planning actually evaluates it under closes that gap by making
Applicability agree with Planning about what's in scope, rather than
each layer silently assuming something different."""


def _scope_for_category(category_name: GenomeCategoryName) -> dict | None:
    return _IMAGE_ONLY_SCOPE if category_name == GenomeCategoryName.VISUAL_IDENTITY else _TEXT_ONLY_SCOPE


_NEAR_DUPLICATE_THRESHOLD = 0.75
"""Implementation-level interpretation of Phase 1 §5's "genuine conflict"
(not precisely defined by the architecture): two candidate Assertions in
the same Component are treated as addressing the same underlying claim —
and therefore subject to Consolidation's precedence rules — when their
text similarity exceeds this threshold. Below it, they are treated as
complementary claims about different aspects of the same Component and
both survive. This is a documented, deterministic simplification, not an
invented business rule about what a Component *means*."""


def _build_system_prompt() -> str:
    taxonomy_lines = []
    for category, components in GENOME_TAXONOMY.items():
        taxonomy_lines.append(f"- {category.value}: {', '.join(components)}")
    taxonomy_text = "\n".join(taxonomy_lines)

    return (
        "You extract candidate brand-identity assertions from brand history content "
        "(guideline documents, design specs, past campaigns). An assertion is a single, "
        "atomic, evaluable claim about the brand's identity (e.g. 'Primary brand color is "
        "Pantone 186 C', 'Tone is confident but never boastful'). Only extract claims that "
        "are actually supported by the content you are given — never invent claims not "
        "present in it. Assign each candidate to exactly one Category and Component from "
        "this fixed taxonomy, using the exact names given:\n\n"
        f"{taxonomy_text}\n\n"
        "Assign a confidence between 0 and 1 reflecting how clearly and unambiguously the "
        "content supports the claim. If the content supports no clear assertions, return an "
        "empty candidates list — never fabricate assertions to fill categories."
    )


async def extract_candidates(llm: LLMClient, brand_history_text: str) -> list[CandidateAssertionLLM]:
    if not brand_history_text or not brand_history_text.strip():
        return []
    try:
        result = await llm.generate_structured(
            system_prompt=_build_system_prompt(),
            untrusted_content=brand_history_text,
            response_schema=CandidateExtractionResult,
        )
    except LLMValidationFailure:
        logger.warning("genome_compiler.candidate_extraction.failed")
        return []

    valid_names = {(cat.value, comp) for cat, comps in GENOME_TAXONOMY.items() for comp in comps}
    return [c for c in result.candidates if (c.category, c.component) in valid_names]


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _authority_for(item: BrandHistory) -> BrandHistoryAuthorityLevel:
    return item.authority_level


def consolidate(
    candidates_with_source: list[tuple[CandidateAssertionLLM, BrandHistory]],
) -> list[tuple[CandidateAssertionLLM, list[BrandHistory], AssertionStatus]]:
    """Phase 1 §5 step 3: explicit outranks exemplar; among equal
    authority, more recent era_tag outranks older; genuine remaining
    conflicts are marked conflicted, never auto-resolved."""
    consolidated: list[tuple[CandidateAssertionLLM, list[BrandHistory], AssertionStatus]] = []

    for candidate, source in candidates_with_source:
        merged = False
        for i, (existing_candidate, existing_sources, _status) in enumerate(consolidated):
            if existing_candidate.component != candidate.component:
                continue
            if _similar(existing_candidate.assertion, candidate.assertion) < _NEAR_DUPLICATE_THRESHOLD:
                continue

            existing_source = existing_sources[0]
            existing_authority = _authority_for(existing_source)
            new_authority = _authority_for(source)

            if new_authority == BrandHistoryAuthorityLevel.EXPLICIT and existing_authority == BrandHistoryAuthorityLevel.EXEMPLAR:
                consolidated[i] = (candidate, [source], AssertionStatus.ACTIVE)
            elif existing_authority == BrandHistoryAuthorityLevel.EXPLICIT and new_authority == BrandHistoryAuthorityLevel.EXEMPLAR:
                pass  # existing wins, keep as-is
            elif (existing_source.era_tag or "") != (source.era_tag or ""):
                # Equal authority, differing era: more recent (lexicographically
                # greater era_tag, e.g. "2024" > "2019") wins.
                if (source.era_tag or "") > (existing_source.era_tag or ""):
                    consolidated[i] = (candidate, [source], AssertionStatus.ACTIVE)
            else:
                # Equal authority, equal (or both-unset) era, genuinely
                # differing text at/above the similarity threshold: a real
                # conflict, surfaced to human review rather than guessed at.
                consolidated[i] = (existing_candidate, existing_sources + [source], AssertionStatus.CONFLICTED)

            merged = True
            break

        if not merged:
            consolidated.append((candidate, [source], AssertionStatus.ACTIVE))

    return consolidated


async def compile_draft(
    *,
    org_id: uuid.UUID,
    brand_id: uuid.UUID,
    version_number: int,
    brand_history_items: list[BrandHistory],
    llm: LLMClient,
    on_stage: Callable[[str], None] | None = None,
) -> tuple[BrandGenome, list[GenomeCategory], list[GenomeComponent], list[Assertion]]:
    """Phase 1 §5 steps 2-4, assembled into an in-memory draft. The
    caller (GenomeService) is responsible for persisting these via the
    repository and running the §10/§3 validation gate before allowing
    `pending_review`.

    `on_stage`, if given, is called with a coarse stage name at each
    sub-stage boundary — same plain-callback convention as
    `analysis_orchestrator.finalize_run`'s `on_stage`, so this module
    stays free of any infra-layer (Celery/Redis) import; the caller
    (`workers/tasks.py::compile_genome_draft_task`) is the one that
    knows how to turn a stage name into a progress record.
    """

    def _stage(name: str) -> None:
        if on_stage is not None:
            on_stage(name)

    _stage("extracting_candidates")
    all_candidates: list[tuple[CandidateAssertionLLM, BrandHistory]] = []
    for item in brand_history_items:
        if not item.extracted_text:
            continue
        candidates = await extract_candidates(llm, item.extracted_text)
        all_candidates.extend((c, item) for c in candidates)

    _stage("consolidating")
    consolidated = consolidate(all_candidates)
    _stage("assembling_draft")

    # `id=new_id()` is assigned explicitly on every row here, rather than
    # left to the column's `default=` — that default only fires when a
    # row is actually flushed, but these parent objects' `.id` is read by
    # their children (category.id by components, component.id by
    # assertions) before any of them have been added to a session at
    # all. IDs are client-generated UUIDs, not DB sequences, so there is
    # no reason this needs a flush round-trip — assigning it up front is
    # what makes the whole in-memory tree's FKs resolvable before persistence.
    genome = BrandGenome(
        id=new_id(),
        org_id=org_id,
        brand_id=brand_id,
        version_number=version_number,
        status=GenomeStatus.DRAFT,
        compiled_from={"brand_history_item_ids": [str(i.id) for i in brand_history_items]},
    )

    categories: list[GenomeCategory] = []
    components: list[GenomeComponent] = []
    assertions: list[Assertion] = []

    component_by_name: dict[tuple[GenomeCategoryName, str], GenomeComponent] = {}
    category_by_name: dict[GenomeCategoryName, GenomeCategory] = {}

    for category_name, component_names in GENOME_TAXONOMY.items():
        category = GenomeCategory(
            id=new_id(),
            org_id=org_id,
            genome_id=genome.id,
            name=category_name,
            applicability_scope=_scope_for_category(category_name),
        )
        categories.append(category)
        category_by_name[category_name] = category
        for component_name in component_names:
            component = GenomeComponent(id=new_id(), org_id=org_id, category_id=category.id, name=component_name)
            components.append(component)
            component_by_name[(category_name, component_name)] = component

    for candidate, sources, status in consolidated:
        try:
            category_name = GenomeCategoryName(candidate.category)
        except ValueError:
            continue
        component = component_by_name.get((category_name, candidate.component))
        if component is None:
            continue

        assertions.append(
            Assertion(
                id=new_id(),
                org_id=org_id,
                component_id=component.id,
                content=candidate.assertion,
                confidence=candidate.confidence,
                status=status,
                origin_type=(
                    AssertionOriginType.EXPLICIT_SOURCE
                    if sources[0].authority_level == BrandHistoryAuthorityLevel.EXPLICIT
                    else AssertionOriginType.EXEMPLAR_SOURCE
                ),
                source_reference_ids=[str(s.id) for s in sources],
                recorded_at=datetime.now(timezone.utc),
            )
        )

    return genome, categories, components, assertions
