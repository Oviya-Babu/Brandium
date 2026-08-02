"""Initial domain foundation — Phase 0-6 entity model, RLS, audit immutability

Revision ID: 0001
Revises:
Create Date: 2026-07-31

Creates every entity from Phase 0-6, across all six Bounded Contexts
(CLAUDE.md §1.5), including the additive elaborations later phases
require (all flagged, none silently invented — see IMPLEMENTATION_STATUS.md):

  - Phase 1 §1: BrandGenome's internal Category/Component/Assertion
    structure, as tables scoped to `genome_id` (not new aggregate roots).
  - Phase 1 §0/§4: BrandHistory.source_type extension + modality/era_tag/
    authority_level fields.
  - Phase 3 addenda: `applicability_scope` on Genome elements,
    `context_tags` on AssetVersion, the AssertionOutcome four-state
    taxonomy table.
  - Phase 5 §0/§2: Membership entity, RoleAssignment `scope_tier`/
    `scope_id`, OrganizationAdministrator role, Organization's widened
    `provisioned|active|suspended|offboarded` lifecycle.
  - `org_id` denormalized on every tenant-scoped table (Phase 0 §6,
    DR-003), with Postgres RLS scoped to `current_setting('app.current_org_id')`
    (CLAUDE.md §4.3). The per-request `SET LOCAL` middleware is
    application-layer (see `src/shared_kernel/tenant_context.py`).
  - No UPDATE/DELETE grants on `audit_log_entries` for the application
    role (INV-33, Technology Stack §20).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_SCOPED_TABLES = [
    "workspaces",
    "users",
    "memberships",
    "role_assignments",
    "brands",
    "brand_genomes",
    "genome_categories",
    "genome_components",
    "assertions",
    "policies",
    "brand_history_items",
    "campaigns",
    "assets",
    "asset_versions",
    "analysis_runs",
    "observations",
    "assertion_outcomes",
    "evidence",
    "reports",
    "decisions",
    "recommendations",
]

APP_ROLE = "brandium"


def upgrade() -> None:
    # --- Bounded Context 1: Identity & Access -----------------------------
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("provisioned", "active", "suspended", "offboarded", name="organization_status"),
            nullable=False,
        ),
    )

    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        sa.Column("auth_identity_ref", sa.String(), nullable=False),
    )

    op.create_table(
        "internal_operators",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(), nullable=False, unique=True),
        comment="INV-21: deliberately no org_id, no relationship into any tenant-scoped table.",
    )

    op.create_table(
        "memberships",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True, unique=True),
        sa.Column(
            "status", sa.Enum("invited", "active", "suspended", "removed", name="membership_status"), nullable=False
        ),
    )

    # --- Bounded Context 2: Brand Governance -------------------------------
    op.create_table(
        "brands",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.Enum("active", "archived", name="brand_status"), nullable=False),
        sa.Column("active_genome_version_id", sa.Uuid(), nullable=True),
        sa.Column("active_policy_version_id", sa.Uuid(), nullable=True),
    )

    op.create_table(
        "brand_genomes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("brand_id", sa.Uuid(), sa.ForeignKey("brands.id"), nullable=False, index=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "pending_review", "rejected", "superseded", name="genome_status"),
            nullable=False,
        ),
        sa.Column("compiled_from", sa.JSON(), nullable=True),
        sa.Column("activated_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("activated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "policies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("brand_id", sa.Uuid(), sa.ForeignKey("brands.id"), nullable=False, index=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.Enum("draft", "rejected", "superseded", name="policy_status"), nullable=False),
        sa.Column("rules", sa.JSON(), nullable=True),
    )

    op.create_foreign_key(
        "fk_brand_active_genome_version", "brands", "brand_genomes", ["active_genome_version_id"], ["id"]
    )
    op.create_foreign_key(
        "fk_brand_active_policy_version", "brands", "policies", ["active_policy_version_id"], ["id"]
    )

    op.create_table(
        "genome_categories",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("genome_id", sa.Uuid(), sa.ForeignKey("brand_genomes.id"), nullable=False, index=True),
        sa.Column(
            "name",
            sa.Enum(
                "visual_identity",
                "verbal_identity",
                "messaging_positioning",
                "values_mission",
                "compliance_legal",
                "accessibility",
                name="genome_category_name",
            ),
            nullable=False,
        ),
        sa.Column("applicability_scope", sa.JSON(), nullable=True),
    )

    op.create_table(
        "genome_components",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("category_id", sa.Uuid(), sa.ForeignKey("genome_categories.id"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("applicability_scope", sa.JSON(), nullable=True),
    )

    op.create_table(
        "assertions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("component_id", sa.Uuid(), sa.ForeignKey("genome_components.id"), nullable=False, index=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.Enum("active", "conflicted", name="assertion_status"), nullable=False),
        sa.Column(
            "origin_type",
            sa.Enum("explicit_source", "exemplar_source", "human_override", name="assertion_origin_type"),
            nullable=False,
        ),
        sa.Column("source_reference_ids", sa.JSON(), nullable=False),
        sa.Column("applicability_scope", sa.JSON(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "role_assignments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column(
            "role",
            sa.Enum(
                "OrganizationAdministrator",
                "BrandAdministrator",
                "MarketingManager",
                "ContentCreator",
                "ExecutiveViewer",
                name="role",
            ),
            nullable=False,
        ),
        sa.Column("scope_tier", sa.Enum("organization", "workspace", "brand", name="scope_tier"), nullable=False),
        sa.Column("scope_id", sa.Uuid(), nullable=False, index=True),
        sa.Column("granted_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "brand_history_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("brand_id", sa.Uuid(), sa.ForeignKey("brands.id"), nullable=False, index=True),
        sa.Column(
            "source_type",
            sa.Enum(
                "guideline_document",
                "design_system_spec",
                "campaign",
                "ad",
                "social",
                "video",
                name="brand_history_source_type",
            ),
            nullable=False,
        ),
        sa.Column("modality", sa.Enum("text", "image", "video", name="brand_history_modality"), nullable=False),
        sa.Column("era_tag", sa.String(), nullable=True),
        sa.Column(
            "authority_level", sa.Enum("explicit", "exemplar", name="brand_history_authority_level"), nullable=False
        ),
        sa.Column("storage_ref", sa.String(), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- Bounded Context 3: Campaign & Asset Management --------------------
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("brand_id", sa.Uuid(), sa.ForeignKey("brands.id"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("status", sa.Enum("active", "archived", name="campaign_status"), nullable=False),
    )

    op.create_table(
        "assets",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("campaign_id", sa.Uuid(), sa.ForeignKey("campaigns.id"), nullable=False, index=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("modality", sa.Enum("text", "image", "video", name="asset_modality"), nullable=False),
    )

    op.create_table(
        "asset_versions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("asset_id", sa.Uuid(), sa.ForeignKey("assets.id"), nullable=False, index=True),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("storage_ref", sa.String(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=False),
        sa.Column("context_tags", sa.JSON(), nullable=False),
        comment="Append-only (INV-13) — enforced at the application/service layer, not by DDL alone.",
    )

    # --- Bounded Context 4: Analysis & Decision -----------------------------
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("asset_version_id", sa.Uuid(), sa.ForeignKey("asset_versions.id"), nullable=False, index=True),
        sa.Column("genome_version_id", sa.Uuid(), sa.ForeignKey("brand_genomes.id"), nullable=False),
        sa.Column("policy_version_id", sa.Uuid(), sa.ForeignKey("policies.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("queued", "running", "complete", "failed", name="analysis_run_status"),
            nullable=False,
        ),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "observations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_runs.id"), nullable=False, index=True),
        sa.Column("assertion_id", sa.Uuid(), sa.ForeignKey("assertions.id"), nullable=False, index=True),
        sa.Column("worker_type", sa.String(), nullable=False),
        sa.Column("raw_output", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
    )

    op.create_table(
        "assertion_outcomes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_runs.id"), nullable=False, index=True),
        sa.Column("assertion_id", sa.Uuid(), sa.ForeignKey("assertions.id"), nullable=False, index=True),
        sa.Column(
            "outcome_type",
            sa.Enum(
                "evidence", "attempted_no_signal", "worker_failure", "not_applicable", name="assertion_outcome_type"
            ),
            nullable=False,
        ),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_runs.id"), nullable=False, index=True),
        sa.Column("assertion_id", sa.Uuid(), sa.ForeignKey("assertions.id"), nullable=False, index=True),
        sa.Column("observed_characteristic", sa.JSON(), nullable=False),
        sa.Column(
            "alignment_indicator",
            sa.Enum("aligned", "partially_aligned", "misaligned", name="alignment_indicator"),
            nullable=False,
        ),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_observation_ids", sa.JSON(), nullable=False),
    )

    op.create_table(
        "decisions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column(
            "analysis_run_id",
            sa.Uuid(),
            sa.ForeignKey("analysis_runs.id"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("verdict", sa.String(), nullable=False),
        sa.Column("verdict_source", sa.String(), nullable=False),
        sa.Column("decision_function_version", sa.Integer(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_runs.id"), nullable=False, index=True),
        sa.Column("component_id", sa.Uuid(), sa.ForeignKey("genome_components.id"), nullable=False),
        sa.Column("related_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("priority", sa.Float(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # --- Bounded Context 5: Reporting --------------------------------------
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column(
            "analysis_run_id",
            sa.Uuid(),
            sa.ForeignKey("analysis_runs.id"),
            nullable=False,
            unique=True,
            index=True,
        ),
        sa.Column("decision_id", sa.Uuid(), sa.ForeignKey("decisions.id"), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "review_status",
            sa.Enum("unreviewed", "approved", "flagged", name="report_review_status"),
            nullable=False,
        ),
        sa.Column("reviewed_by", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("flag_reason", sa.String(), nullable=True),
    )

    # --- Bounded Context 6: Platform Governance -----------------------------
    op.create_table(
        "audit_log_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), nullable=True, index=True),
        sa.Column("actor_id", sa.Uuid(), nullable=False),
        sa.Column("actor_type", sa.Enum("user", "internal_operator", name="audit_actor_type"), nullable=False),
        sa.Column("action_type", sa.String(), nullable=False),
        sa.Column("target_entity", sa.String(), nullable=False),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        comment="Global, append-only. No TenantScopedMixin — org_id is visibility scoping only (Phase 0 §6).",
    )

    op.create_table(
        "ai_slop_knowledge_base",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_type", sa.Enum("public", "synthetic", name="ai_slop_source_type"), nullable=False),
        sa.Column("content_ref", sa.String(), nullable=False),
    )

    # --- Row-Level Security (Phase 0 §6, CLAUDE.md §4.3, INV-18) ----------
    for table in TENANT_SCOPED_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")
        op.execute(
            f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (org_id = current_setting('app.current_org_id', true)::uuid)
            WITH CHECK (org_id = current_setting('app.current_org_id', true)::uuid)
            """
        )

    # --- Audit log immutability (INV-33, Technology Stack §20) -------------
    op.execute(f"REVOKE UPDATE, DELETE ON audit_log_entries FROM {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON audit_log_entries TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"GRANT UPDATE, DELETE ON audit_log_entries TO {APP_ROLE}")

    for table in reversed(TENANT_SCOPED_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    for table in [
        "ai_slop_knowledge_base",
        "audit_log_entries",
        "reports",
        "recommendations",
        "decisions",
        "evidence",
        "assertion_outcomes",
        "observations",
        "analysis_runs",
        "asset_versions",
        "assets",
        "campaigns",
        "brand_history_items",
        "role_assignments",
        "assertions",
        "genome_components",
        "genome_categories",
    ]:
        op.drop_table(table)

    op.drop_constraint("fk_brand_active_policy_version", "brands", type_="foreignkey")
    op.drop_constraint("fk_brand_active_genome_version", "brands", type_="foreignkey")

    for table in ["policies", "brand_genomes", "brands", "memberships", "internal_operators", "users", "workspaces",
                  "organizations"]:
        op.drop_table(table)

    for enum_name in [
        "ai_slop_source_type",
        "audit_actor_type",
        "report_review_status",
        "assertion_outcome_type",
        "alignment_indicator",
        "analysis_run_status",
        "asset_modality",
        "campaign_status",
        "brand_history_authority_level",
        "brand_history_modality",
        "brand_history_source_type",
        "scope_tier",
        "role",
        "assertion_origin_type",
        "assertion_status",
        "genome_category_name",
        "policy_status",
        "genome_status",
        "brand_status",
        "membership_status",
        "organization_status",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
