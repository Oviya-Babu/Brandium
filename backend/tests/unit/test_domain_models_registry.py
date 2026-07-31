"""Verifies every Bounded Context's models are wired into models_registry
and that Phase 0 §4's cardinality-defining tables all exist — a schema-
drift guard, not a business-logic test."""
from src.models_registry import Base

EXPECTED_TABLES = {
    "organizations",
    "workspaces",
    "users",
    "internal_operators",
    "brands",
    "brand_genomes",
    "policies",
    "brand_history_items",
    "role_assignments",
    "campaigns",
    "assets",
    "asset_versions",
    "analysis_runs",
    "observations",
    "evidence",
    "decisions",
    "recommendations",
    "reports",
    "audit_log_entries",
    "ai_slop_knowledge_base",
}


def test_all_phase_0_entities_are_registered() -> None:
    assert EXPECTED_TABLES.issubset(set(Base.metadata.tables.keys()))


def test_brand_active_version_pointers_are_nullable() -> None:
    """INV-09: exactly-one-active is enforced by a single nullable FK,
    never a stored `active` status value."""
    brands = Base.metadata.tables["brands"]
    assert brands.c.active_genome_version_id.nullable
    assert brands.c.active_policy_version_id.nullable


def test_genome_and_policy_status_never_include_active() -> None:
    """INV-09: a version is "active" solely by being pointed-to; the
    status enum itself must never carry an "active" value (Phase 0 §3.5/§3.6)."""
    from src.brand_governance.domain.models import GenomeStatus, PolicyStatus

    assert "active" not in {s.value for s in GenomeStatus}
    assert "active" not in {s.value for s in PolicyStatus}
