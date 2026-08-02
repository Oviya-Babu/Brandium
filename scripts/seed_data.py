"""Demonstration seed data — Apple (unchanged, full pipeline) and Red Bull
(PRD §2.6/Assumptions: "Public brand assets... usable for internal
validation/demo purposes without licensing brand content for
redistribution to end customers").

**This script ingests brand-history text and runs it through the real
Genome Compilation Workflow (Phase 1 §5) via GenomeService/BrandHistoryService
— it does not construct BrandGenome/Assertion rows directly.** All text
is original, written from general public knowledge of these brands'
publicly-stated positioning, tone, and visual identity (the kind of thing
found in their own public marketing and press materials) — not a copy of
any specific proprietary or copyrighted guideline document. Suitable for
internal demonstration only, never for redistribution as if it were the
brands' own official guidelines.

Red Bull is being built as a deliberately richer "Brand Brain" per
docs/01-PRD/02-Architecture/Red_Bull_Brand_Intelligence_Blueprint.md,
implemented one Knowledge Domain cluster at a time
(`seed_red_bull_brand_intelligence` / `RED_BULL_KNOWLEDGE_DOMAINS` below)
— ingestion only for now, Genome compilation and Policy authoring are
deferred until every planned cluster is implemented and reviewed. Apple's
seeding (`DEMO_BRANDS` / `seed_brand`) is untouched and still runs the
full ingest -> compile -> activate -> policy pipeline as before.

Run with the backend's Python environment active and the full
docker-compose stack up (Postgres, Ollama, MinIO all reachable) — this
script was NOT executed in the sandbox that wrote it (no DB/LLM access
there); it has been reviewed for correctness against the service-layer
APIs it calls, not run.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from src.brand_governance.brand_history_service import BrandHistoryService  # noqa: E402
from src.brand_governance.domain.models import BrandHistoryAuthorityLevel, BrandHistoryModality, BrandHistorySourceType  # noqa: E402
from src.brand_governance.genome_service import GenomeService  # noqa: E402
from src.brand_governance.policy_service import PolicyService  # noqa: E402
from src.brand_governance.repository import BrandGenomeRepository, BrandHistoryRepository, BrandRepository, PolicyRepository  # noqa: E402
from src.identity_access.domain.models import Membership, MembershipStatus, Organization, OrganizationStatus, Role, RoleAssignment, ScopeTier, User, Workspace  # noqa: E402
from src.platform_governance.audit_service import AuditService  # noqa: E402
from src.platform_governance.repository import AuditLogRepository  # noqa: E402
from src.shared_kernel.db import get_session_factory  # noqa: E402
from src.shared_kernel.llm.client import LLMClient  # noqa: E402
from src.shared_kernel.object_storage import ObjectStorageClient  # noqa: E402
from src.brand_governance.domain.models import Brand, BrandStatus  # noqa: E402
from datetime import datetime, timezone  # noqa: E402


RED_BULL_KNOWLEDGE_DOMAINS: list[dict] = [
    # Visual Identity System (Blueprint § II) + Packaging & Product System
    # (Blueprint § III) — first Knowledge Domain cluster of the Red Bull
    # Brand Brain build (see
    # docs/01-PRD/02-Architecture/Red_Bull_Brand_Intelligence_Blueprint.md).
    # One document per GenomeComponent (or tightly related pair) so each
    # stays focused for genome_compiler.py's per-item LLM extraction;
    # every line is written as an already atomic, evaluable claim rather
    # than narrative prose, per the Blueprint's writing directive.
    {
        "component": "Logo Usage",
        "filename": "redbull_visual_identity_logo.txt",
        "text": (
            "Visual Identity — Logo Usage\n"
            "- Primary logo mark depicts two red bulls in profile, facing and charging toward each other.\n"
            "- The two bulls are set in front of a yellow sun disc as part of the same mark.\n"
            "- The bulls-and-sun mark is used as a standalone icon and is never split into its individual "
            "elements (bulls alone, or sun alone) in primary brand usage.\n"
            "- The wordmark \"Red Bull\" is set in a bold, heavyweight, all-uppercase sans-serif typeface.\n"
            "- Primary lockups always pair the bulls-and-sun mark with the wordmark.\n"
            "- The logo has been refined incrementally over time rather than redesigned or replaced outright.\n"
            "- No italic, script, or decorative variant of the logo exists in primary brand usage."
        ),
    },
    {
        "component": "Color Palette",
        "filename": "redbull_visual_identity_color.txt",
        "text": (
            "Visual Identity — Color Palette\n"
            "- Primary brand color is Red Bull Red, approximating Pantone 186 C (hex #CC1E4A).\n"
            "- Secondary brand color is a deep navy blue, used in the wordmark and on packaging.\n"
            "- Accent color is a gold-yellow, approximating hex #FFC906, used in the sun-disc logo element "
            "and as a packaging accent.\n"
            "- Product can livery is built on a silver/gunmetal base with the red-blue-gold system applied over it.\n"
            "- The same red-blue-gold-silver palette is applied consistently across product packaging, "
            "motorsport livery, and marketing materials."
        ),
    },
    {
        "component": "Typography",
        "filename": "redbull_visual_identity_typography.txt",
        "text": (
            "Visual Identity — Typography\n"
            "- The primary wordmark is set in a bold, heavyweight typeface, entirely in uppercase.\n"
            "- The wordmark typeface is a strong sans-serif, chosen for legibility and visibility at small "
            "sizes such as on a can.\n"
            "- No italic or script typography is used in the primary wordmark treatment.\n"
            "- Supporting marketing copy typography favors clean, high-legibility sans-serif faces "
            "consistent with the wordmark's boldness."
        ),
    },
    {
        "component": "Imagery & Photography Style",
        "filename": "redbull_visual_identity_photography.txt",
        "text": (
            "Visual Identity — Imagery & Photography Style\n"
            "- Photography style favors dynamic, high-energy action photography over static or posed shots.\n"
            "- Subjects are frequently captured mid-motion — mid-air, mid-jump, mid-maneuver — frozen at the "
            "peak moment of action.\n"
            "- Lighting favors natural or dramatic backlighting and high contrast over flat, even studio lighting.\n"
            "- Product-only studio shots are used sparingly; the hero image in marketing content is typically "
            "an athlete, event, or moment of action rather than the can alone.\n"
            "- Photography is set in real environments — mountains, race tracks, urban skylines, open air — "
            "rather than isolated studio backdrops."
        ),
    },
    {
        "component": "Layout & Composition",
        "filename": "redbull_visual_identity_layout.txt",
        "text": (
            "Visual Identity — Layout & Composition\n"
            "- Compositions favor dynamic diagonal framing over static, centered symmetry.\n"
            "- Action subjects are typically cropped tightly to emphasize motion and immediacy rather than "
            "framed with generous negative space.\n"
            "- Layouts avoid perfectly mirrored or evenly balanced symmetrical arrangements as a default choice."
        ),
    },
    {
        "component": "Motion & Energy",
        "filename": "redbull_visual_identity_motion.txt",
        "text": (
            "Visual Identity — Motion & Energy\n"
            "- Visual content is expected to convey a strong sense of kinetic energy and momentum, not stillness.\n"
            "- Motion is typically conveyed through subject pose — mid-air, mid-stride, banking through a "
            "turn — rather than through motion-blur effects alone.\n"
            "- A technically well-composed but visually static image, showing a posed and still subject with "
            "no implied movement, is considered off-brand regardless of correct color or logo usage."
        ),
    },
    {
        "component": "Packaging & Product Form",
        "filename": "redbull_packaging_product_form.txt",
        "text": (
            "Visual Identity — Packaging & Product Form\n"
            "- The standard product package is a tall, slim aluminum can, not a bottle or wide-body can format.\n"
            "- Can livery follows the established silver/blue/red/gold color system consistently across "
            "product variants, including Original, Sugarfree, Zero, and flavor editions.\n"
            "- Different product variants are visually distinguished primarily through livery color-blocking "
            "rather than through a change in can shape or logo treatment.\n"
            "- The can silhouette itself functions as a recognizable brand asset independent of the logo."
        ),
    },
]
"""First implemented cluster of the Red Bull Brand Brain (Blueprint § II-III).
Genome compilation is deliberately NOT run yet — remaining clusters
(Compliance & Legal, Verbal Identity, Messaging & Positioning, Company
Identity, Sponsorship & Cultural Positioning) are still pending, per the
Blueprint's one-domain-at-a-time implementation sequencing."""


async def seed_red_bull_brand_intelligence(session, storage: ObjectStorageClient) -> None:
    """Ingests the Red Bull Brand History documents implemented so far.
    Intentionally stops at ingestion — no `GenomeService.create_draft()`,
    no Policy authoring — until every planned Knowledge Domain cluster has
    been implemented and reviewed (Blueprint "Implementation sequencing")."""
    org = Organization(name="Red Bull", status=OrganizationStatus.ACTIVE)
    session.add(org)
    await session.flush()

    admin = User(org_id=org.id, email="admin@redbull.demo", auth_identity_ref="seed")
    session.add(admin)
    await session.flush()
    session.add(Membership(org_id=org.id, user_id=admin.id, status=MembershipStatus.ACTIVE))
    for role in (Role.ORGANIZATION_ADMINISTRATOR, Role.BRAND_ADMINISTRATOR):
        session.add(
            RoleAssignment(
                org_id=org.id, user_id=admin.id, role=role, scope_tier=ScopeTier.ORGANIZATION, scope_id=org.id,
                granted_by=admin.id, granted_at=datetime.now(timezone.utc),
            )
        )

    workspace = Workspace(org_id=org.id, name="Default Workspace")
    session.add(workspace)
    await session.flush()

    brand = Brand(org_id=org.id, workspace_id=workspace.id, name="Red Bull", status=BrandStatus.ACTIVE)
    session.add(brand)
    await session.flush()
    await session.commit()

    history_service = BrandHistoryService(BrandHistoryRepository(session), storage)
    for doc in RED_BULL_KNOWLEDGE_DOMAINS:
        await history_service.ingest(
            org_id=org.id,
            brand_id=brand.id,
            source_type=BrandHistorySourceType.GUIDELINE_DOCUMENT,
            modality=BrandHistoryModality.TEXT,
            authority_level=BrandHistoryAuthorityLevel.EXPLICIT,
            era_tag="2025",
            filename=doc["filename"],
            content=doc["text"].encode("utf-8"),
            content_type="text/plain",
        )
    await session.commit()

    print(
        f"Ingested {len(RED_BULL_KNOWLEDGE_DOMAINS)} Red Bull Brand History document(s) "
        f"(org={org.id} brand={brand.id}). Genome compilation deliberately deferred — "
        "remaining Knowledge Domain clusters are still pending."
    )


DEMO_BRANDS = {
    "Apple": {
        "guideline_text": (
            "Apple's brand voice is simple, confident, and human — it favors short, direct sentences over "
            "technical jargon, and explains products in terms of what people can do with them, not "
            "internal specifications. Core positioning emphasizes design simplicity, seamless integration "
            "across devices, and privacy as a fundamental value, not an add-on feature. Visual identity is "
            "minimal: generous white space, clean sans-serif typography, product photography on neutral "
            "backgrounds, and a restrained color palette that lets the product itself be the visual focus. "
            "Marketing language avoids superlative-heavy hype and competitor comparisons, preferring "
            "understated confidence. Accessibility is treated as a core design value across products, "
            "referenced directly in marketing materials, not only in technical documentation."
        ),
        "authority": BrandHistoryAuthorityLevel.EXPLICIT,
        "era_tag": "2024",
    },
}


async def seed_brand(session, storage: ObjectStorageClient, llm: LLMClient, brand_name: str, data: dict) -> None:
    org = Organization(name=brand_name, status=OrganizationStatus.ACTIVE)
    session.add(org)
    await session.flush()

    admin = User(org_id=org.id, email=f"admin@{brand_name.lower().replace(' ', '')}.demo", auth_identity_ref="seed")
    session.add(admin)
    await session.flush()
    session.add(Membership(org_id=org.id, user_id=admin.id, status=MembershipStatus.ACTIVE))
    for role in (Role.ORGANIZATION_ADMINISTRATOR, Role.BRAND_ADMINISTRATOR):
        session.add(
            RoleAssignment(
                org_id=org.id, user_id=admin.id, role=role, scope_tier=ScopeTier.ORGANIZATION, scope_id=org.id,
                granted_by=admin.id, granted_at=datetime.now(timezone.utc),
            )
        )

    workspace = Workspace(org_id=org.id, name="Default Workspace")
    session.add(workspace)
    await session.flush()

    brand = Brand(org_id=org.id, workspace_id=workspace.id, name=brand_name, status=BrandStatus.ACTIVE)
    session.add(brand)
    await session.flush()
    await session.commit()

    history_service = BrandHistoryService(BrandHistoryRepository(session), storage)
    await history_service.ingest(
        org_id=org.id,
        brand_id=brand.id,
        source_type=BrandHistorySourceType.GUIDELINE_DOCUMENT,
        modality=BrandHistoryModality.TEXT,
        authority_level=data["authority"],
        era_tag=data["era_tag"],
        filename=f"{brand_name.lower()}_guidelines.txt",
        content=data["guideline_text"].encode("utf-8"),
        content_type="text/plain",
    )
    await session.commit()

    genome_service = GenomeService(
        BrandGenomeRepository(session), BrandRepository(session), BrandHistoryRepository(session),
        AuditService(AuditLogRepository(session)), llm, session,
    )
    genome, categories, components, assertions = await genome_service.create_draft(
        org_id=org.id, brand_id=brand.id, actor_id=admin.id
    )
    await session.commit()

    await genome_service.submit_for_review(
        genome=genome, categories=categories, components=components, assertions=assertions, actor_id=admin.id
    )
    await genome_service.activate(genome=genome, actor_id=admin.id)
    await session.commit()

    policy_service = PolicyService(
        PolicyRepository(session), BrandRepository(session), BrandGenomeRepository(session),
        AuditService(AuditLogRepository(session)),
    )
    default_rules = {
        "category_weights": {
            "visual_identity": 0.2, "verbal_identity": 0.2, "messaging_positioning": 0.2,
            "values_mission": 0.15, "compliance_legal": 0.15, "accessibility": 0.1,
        },
        "component_weights": {}, "assertion_weights": {}, "critical_rules": [],
        "verdict_thresholds": [
            {"min_score": 0, "max_score": 59.999999, "verdict": "Non-Compliant"},
            {"min_score": 59.999999, "max_score": 100, "verdict": "Compliant"},
        ],
        "improvement_threshold": 0.8,
    }
    policy = await policy_service.create_draft(org_id=org.id, brand_id=brand.id, rules=default_rules, actor_id=admin.id)
    await policy_service.activate(policy=policy, actor_id=admin.id)
    await session.commit()

    print(f"Seeded {brand_name}: org={org.id} brand={brand.id} genome={genome.id} policy={policy.id}")


async def main() -> None:
    session_factory = get_session_factory()
    storage = ObjectStorageClient()
    llm = LLMClient()
    async with session_factory() as session:
        for brand_name, data in DEMO_BRANDS.items():
            await seed_brand(session, storage, llm, brand_name, data)
        await seed_red_bull_brand_intelligence(session, storage)


if __name__ == "__main__":
    asyncio.run(main())
