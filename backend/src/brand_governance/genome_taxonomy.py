"""Platform-defined GenomeComponent taxonomy (Phase 1 §1: "GenomeComponent
— platform-defined per category, so every Genome has a predictable
shape"). Phase 1 fixes the six Categories (§2) but explicitly leaves the
Component-level detail to "a companion schema reference" (§12 open
question 2) — this is that reference. Identical for every tenant; only
the Assertions filling these Components are tenant-owned content
(Phase 5 §1's "shared shape, never shared substance").

Extended per docs/01-PRD/02-Architecture/Red_Bull_Brand_Intelligence_Blueprint.md
("Genome Taxonomy Extension") with 5 Components (Motion & Energy;
Packaging & Product Form; Brand Personality; Storytelling & Narrative
Style; Sponsorship & Cultural Platforms) this taxonomy didn't previously
have a home for. Additive and forward-only (Phase 1 §9): existing,
already-compiled Genome versions (e.g. Apple's) are untouched — this
only changes what a *future* `compile_draft()` call produces.
"""
from __future__ import annotations

from src.brand_governance.domain.models import GenomeCategoryName

GENOME_TAXONOMY: dict[GenomeCategoryName, list[str]] = {
    GenomeCategoryName.VISUAL_IDENTITY: [
        "Logo Usage",
        "Color Palette",
        "Typography",
        "Imagery & Photography Style",
        "Layout & Composition",
        "Motion & Energy",
        "Packaging & Product Form",
    ],
    GenomeCategoryName.VERBAL_IDENTITY: [
        "Tone Attributes",
        "Vocabulary Preferences",
        "Prohibited or Discouraged Language",
        "Sentence-Level Style Conventions",
        "Brand Personality",
    ],
    GenomeCategoryName.MESSAGING_POSITIONING: [
        "Core Value Propositions",
        "Approved Taglines & Key Messages",
        "Positioning Statements",
        "Storytelling & Narrative Style",
        "Sponsorship & Cultural Platforms",
    ],
    GenomeCategoryName.VALUES_MISSION: [
        "Mission Statement",
        "Organizational Values",
        "Cause & Purpose Alignment",
    ],
    GenomeCategoryName.COMPLIANCE_LEGAL: [
        "Regulatory Constraints",
        "Mandatory Disclaimers",
        "Trademark & Attribution Usage",
    ],
    GenomeCategoryName.ACCESSIBILITY: [
        "Content Accessibility Requirements",
    ],
}
