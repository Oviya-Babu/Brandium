"""Genome Service — orchestrates the compilation/review/activation
workflow (Phase 0 §3.6, Phase 1 §5/§10, DR-006/INV-15). The only layer
allowed to compose the repository + compiler + validation + audit calls
into one business transaction (CLAUDE.md §3.1's service-layer principle).
"""
from __future__ import annotations

import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.brand_governance.domain.models import Assertion, BrandGenome, GenomeCategory, GenomeComponent, GenomeStatus
from src.brand_governance.genome_compiler import compile_draft
from src.brand_governance.genome_validation import validate_for_review
from src.brand_governance.repository import BrandGenomeRepository, BrandHistoryRepository, BrandRepository
from src.platform_governance.audit_service import AuditService
from src.platform_governance.domain.models import AuditActorType
from src.shared_kernel.llm.client import LLMClient


class GenomeActivationError(Exception):
    """Raised when activation is attempted on a version that hasn't
    passed the pending_review gate, or without a valid human actor."""


class GenomeValidationError(Exception):
    """Raised when a draft fails Phase 1 §10's validation rules and
    therefore cannot enter `pending_review`."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


class GenomeService:
    def __init__(
        self,
        genome_repo: BrandGenomeRepository,
        brand_repo: BrandRepository,
        history_repo: BrandHistoryRepository,
        audit: AuditService,
        llm: LLMClient,
        session: AsyncSession,
    ) -> None:
        self._genome_repo = genome_repo
        self._brand_repo = brand_repo
        self._history_repo = history_repo
        self._audit = audit
        self._llm = llm
        self._session = session
        """A BrandGenome's Category/Component/Assertion rows (Phase 1 §0:
        internal structure of one aggregate, not separate aggregate roots)
        are inserted together in one transaction — the one legitimate use
        of the raw session in this service, per CLAUDE.md §3.1's "service
        layer composes multiple repository calls into one business
        transaction" allowance."""

    async def create_draft(
        self,
        *,
        org_id: uuid.UUID,
        brand_id: uuid.UUID,
        actor_id: uuid.UUID,
        on_stage: Callable[[str], None] | None = None,
    ) -> tuple[BrandGenome, list[GenomeCategory], list[GenomeComponent], list[Assertion]]:
        """Phase 1 §5 steps 1-4. Ingestion (step 1) already happened via
        BrandHistoryService; this compiles everything ingested so far for
        the Brand into a new draft version. `on_stage` is passed straight
        through to `compile_draft` — see its docstring."""
        history_items = await self._history_repo.list_for_brand(brand_id)
        current_item_ids = sorted(str(item.id) for item in history_items)

        existing_versions = await self._genome_repo.list_for_brand(brand_id)
        if existing_versions:
            latest = existing_versions[-1]
            previous_item_ids = sorted((latest.compiled_from or {}).get("brand_history_item_ids", []))
            if previous_item_ids == current_item_ids:
                # Same BrandHistory set as the last compile — the LLM
                # would re-derive the same output from the same source
                # documents, so skip the sequential per-item extraction
                # pass (the actual cost driver) entirely and hand back
                # what's already compiled. A changed `current_item_ids`
                # set (new documents ingested) is the only thing that
                # invalidates this.
                categories, components, assertions = await self.load_full_tree(latest.id)
                return latest, categories, components, assertions

        version_number = await self._genome_repo.next_version_number(brand_id)

        genome, categories, components, assertions = await compile_draft(
            org_id=org_id,
            brand_id=brand_id,
            version_number=version_number,
            brand_history_items=history_items,
            llm=self._llm,
            on_stage=on_stage,
        )

        # Flushed in FK-dependency order (genome -> categories ->
        # components -> assertions), not one combined add_all()+flush().
        # IDs are already assigned client-side (genome_compiler.py's
        # `new_id()`), so this isn't about generating them — it's that
        # Postgres validates each FK constraint at INSERT time, and a
        # single flush covering four mapped classes linked only by plain
        # `ForeignKey` columns (no ORM `relationship()` between them) does
        # not reliably order its per-table INSERTs to satisfy that: it
        # was observed to attempt the `assertions` INSERT before every
        # `genome_components` row existed, tripping a FK violation even
        # though every id involved was valid and consistent.
        await self._genome_repo.add(genome)
        self._session.add_all(categories)
        await self._session.flush()
        self._session.add_all(components)
        await self._session.flush()
        self._session.add_all(assertions)
        await self._session.flush()

        await self._audit.record(
            org_id=org_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            action_type="genome.draft_created",
            target_entity="BrandGenome",
            target_id=genome.id,
        )
        return genome, categories, components, assertions

    async def get_genome(self, genome_id: uuid.UUID) -> BrandGenome | None:
        return await self._genome_repo.get_by_id(genome_id)

    async def load_full_tree(
        self, genome_id: uuid.UUID
    ) -> tuple[list[GenomeCategory], list[GenomeComponent], list[Assertion]]:
        """Flat (non-nested) load of a genome's full Category/Component/
        Assertion set — what `submit_for_review`'s validation needs."""
        categories = await self._genome_repo.get_categories(genome_id)
        components: list[GenomeComponent] = []
        assertions: list[Assertion] = []
        for category in categories:
            category_components = await self._genome_repo.get_components(category.id)
            components.extend(category_components)
            for component in category_components:
                assertions.extend(await self._genome_repo.get_assertions(component.id))
        return categories, components, assertions

    async def submit_for_review(
        self,
        *,
        genome: BrandGenome,
        categories: list[GenomeCategory],
        components: list[GenomeComponent],
        assertions: list[Assertion],
        actor_id: uuid.UUID,
    ) -> BrandGenome:
        """Phase 1 §3's activation gate: a draft may enter `pending_review`
        only if it passes §10's validation rules. Raises GenomeValidationError
        otherwise — never silently allowed through."""
        errors = validate_for_review(categories, components, assertions)
        if errors:
            raise GenomeValidationError(errors)

        genome.status = GenomeStatus.PENDING_REVIEW
        await self._audit.record(
            org_id=genome.org_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            action_type="genome.submitted_for_review",
            target_entity="BrandGenome",
            target_id=genome.id,
        )
        return genome

    async def activate(self, *, genome: BrandGenome, actor_id: uuid.UUID) -> BrandGenome:
        """Phase 0 §3.6's atomic three-step activation operation
        (DR-006/INV-15: `activated_by` becomes non-null exactly here).
        The caller (API layer) is responsible for the RBAC check that
        `actor_id` holds BrandAdministrator at this Brand's scope —
        this service enforces only the state-machine/atomicity invariant,
        not authorization, per CLAUDE.md §3.1's layering."""
        if genome.status != GenomeStatus.PENDING_REVIEW:
            raise GenomeActivationError(
                f"BrandGenome {genome.id} is '{genome.status.value}', not 'pending_review' — cannot activate."
            )

        brand = await self._brand_repo.get_by_id(genome.brand_id)
        if brand is None:
            raise GenomeActivationError(f"Brand {genome.brand_id} not found.")

        previous_active_id = brand.active_genome_version_id

        # Step 1: mark this version activated.
        genome.activated_by = actor_id
        genome.activated_at = datetime.now(timezone.utc)

        # Step 2: point Brand at it.
        brand.active_genome_version_id = genome.id

        # Step 3: supersede the previously-active version, if any — but
        # not itself. Without this guard, re-activating the version
        # that's already `Brand.active_genome_version_id` (a harmless,
        # idempotent-looking retry) would fetch itself as "previous" and
        # mark the currently-active genome SUPERSEDED, corrupting the
        # only version the Brand points to.
        if previous_active_id is not None and previous_active_id != genome.id:
            previous = await self._genome_repo.get_by_id(previous_active_id)
            if previous is not None:
                previous.status = GenomeStatus.SUPERSEDED

        await self._audit.record(
            org_id=genome.org_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            action_type="genome.activated",
            target_entity="BrandGenome",
            target_id=genome.id,
        )
        return genome

    async def get_tree(self, genome_id: uuid.UUID) -> dict:
        """Genome browsing: nested Category -> Component -> Assertion tree."""
        categories = await self._genome_repo.get_categories(genome_id)
        tree = {"genome_id": str(genome_id), "categories": []}
        for category in categories:
            components = await self._genome_repo.get_components(category.id)
            component_nodes = []
            for component in components:
                assertions = await self._genome_repo.get_assertions(component.id)
                component_nodes.append(
                    {
                        "id": str(component.id),
                        "name": component.name,
                        "assertions": [
                            {
                                "id": str(a.id),
                                "content": a.content,
                                "confidence": a.confidence,
                                "status": a.status.value,
                                "origin_type": a.origin_type.value,
                            }
                            for a in assertions
                        ],
                    }
                )
            tree["categories"].append(
                {"id": str(category.id), "name": category.name.value, "components": component_nodes}
            )
        return tree

    async def compare(self, genome_id_a: uuid.UUID, genome_id_b: uuid.UUID) -> dict:
        """Phase 1 §9: a diff between two Genome versions is a derived
        view, never a stored entity."""
        tree_a = await self.get_tree(genome_id_a)
        tree_b = await self.get_tree(genome_id_b)

        assertions_a = {
            (cat["name"], comp["name"]): {a["content"] for a in comp["assertions"]}
            for cat in tree_a["categories"]
            for comp in cat["components"]
        }
        assertions_b = {
            (cat["name"], comp["name"]): {a["content"] for a in comp["assertions"]}
            for cat in tree_b["categories"]
            for comp in cat["components"]
        }

        diff: dict[str, list] = {"added": [], "removed": [], "unchanged_components": []}
        for key in set(assertions_a) | set(assertions_b):
            before = assertions_a.get(key, set())
            after = assertions_b.get(key, set())
            added = after - before
            removed = before - after
            if added or removed:
                diff["added"].extend({"component": key, "content": c} for c in added)
                diff["removed"].extend({"component": key, "content": c} for c in removed)
            else:
                diff["unchanged_components"].append({"component": key})

        return diff
