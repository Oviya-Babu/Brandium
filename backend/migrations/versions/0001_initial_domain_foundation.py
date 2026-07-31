"""Initial domain foundation — Phase 0 entity model, RLS, audit immutability

Revision ID: 0001
Revises:
Create Date: 2026-07-31

Creates every entity from Phase 0 Business Domain Specification v0.2 §3,
across all six Bounded Contexts (CLAUDE.md §1.5), with:
  - `org_id` denormalized on every tenant-scoped table (Phase 0 §6, DR-003)
  - Postgres Row-Level Security enabled on every tenant-scoped table,
    scoped to `current_setting('app.current_org_id')` (CLAUDE.md §4.3).
    NOTE: the per-request `SET app.current_org_id` wiring is an
    application-layer concern deferred to the next milestone (Milestone 1
    in CLAUDE.md's roadmap) — this migration establishes the DB-enforced
    mechanism, not the request middleware that populates it.
  - `Brand.active_genome_version_id` / `active_policy_version_id` as
    deferred (use_alter) foreign keys, resolving the circular reference
    between Brand <-> BrandGenome/Policy (Phase 0 §3.5, INV-09).
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

# Tables that carry a tenant-scoping `org_id` and must have RLS enabled
# (Phase 0 §6 — everything except InternalOperator, AuditLogEntry, AISlopKnowledgeBase).
TENANT_SCOPED_TABLES = [
    "workspaces",
    "users",
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
    "reports",
    "decisions",
    "recommendations",
]

# The role the application connects as (matches docker-compose's default
# `POSTGRES_USER`/`DATABASE_URL` credential, src/config.py). If the
# connecting role ever changes, this migration's REVOKE/RLS `TO` targets
# must be updated to match — flagged explicitly rather than assumed silently.
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
            sa.Enum("active", "suspended", name="organization_status"),
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

    # --- Bounded Context 2: Brand Governance -------------------------------
    # `brands` created first without FKs on active_genome_version_id /
    # active_policy_version_id (deferred below via ALTER) to break the
    # Brand <-> BrandGenome/Policy circular reference (Phase 0 §3.5).
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
        sa.Column(
            "activated_by",
            sa.Uuid(),
            sa.ForeignKey("users.id"),
            nullable=True,
            comment="Required non-null at activation time — DR-006/INV-15; app-layer enforced.",
        ),
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

    # Deferred FKs completing Brand's version pointers (INV-09).
    op.create_foreign_key(
        "fk_brand_active_genome_version",
        "brands",
        "brand_genomes",
        ["active_genome_version_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_brand_active_policy_version",
        "brands",
        "policies",
        ["active_policy_version_id"],
        ["id"],
    )

    op.create_table(
        "brand_history_items",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("brand_id", sa.Uuid(), sa.ForeignKey("brands.id"), nullable=False, index=True),
        sa.Column(
            "source_type",
            sa.Enum("campaign", "ad", "social", "video", name="brand_history_source_type"),
            nullable=False,
        ),
        sa.Column("storage_ref", sa.String(), nullable=False),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "role_assignments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False, index=True),
        sa.Column(
            "role",
            sa.Enum(
                "BrandAdministrator",
                "MarketingManager",
                "ContentCreator",
                "ExecutiveViewer",
                name="role",
            ),
            nullable=False,
        ),
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
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        comment="genome_version_id/policy_version_id set once at creation, never updated (DR-005).",
    )

    op.create_table(
        "observations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_runs.id"), nullable=False, index=True),
        sa.Column("worker_type", sa.String(), nullable=False),
        sa.Column("raw_output", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
    )

    op.create_table(
        "evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_runs.id"), nullable=False, index=True),
        sa.Column("evidence_type", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
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
        sa.Column("decision_function_version", sa.Integer(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("org_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False, index=True),
        sa.Column("analysis_run_id", sa.Uuid(), sa.ForeignKey("analysis_runs.id"), nullable=False, index=True),
        sa.Column("related_evidence_ids", sa.JSON(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        comment="INV-06: application layer must reject empty related_evidence_ids.",
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
        comment="DR-004: global, structurally outside the Organization tree.",
    )

    # --- Row-Level Security (Phase 0 §6, CLAUDE.md §4.3, INV-18) ----------
    # Structural mechanism only in this migration: enables RLS and defines
    # the policy shape. The per-request `SET LOCAL app.current_org_id`
    # middleware that populates this session variable is an application-
    # layer concern for the next milestone, not this one.
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
    # The application role receives INSERT/SELECT only; UPDATE/DELETE are
    # revoked at the database level so even a buggy application cannot
    # violate "audit history is never rewritten, truncated, or deleted."
    op.execute(f"REVOKE UPDATE, DELETE ON audit_log_entries FROM {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON audit_log_entries TO {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"GRANT UPDATE, DELETE ON audit_log_entries TO {APP_ROLE}")

    for table in reversed(TENANT_SCOPED_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.drop_table("ai_slop_knowledge_base")
    op.drop_table("audit_log_entries")
    op.drop_table("reports")
    op.drop_table("recommendations")
    op.drop_table("decisions")
    op.drop_table("evidence")
    op.drop_table("observations")
    op.drop_table("analysis_runs")
    op.drop_table("asset_versions")
    op.drop_table("assets")
    op.drop_table("campaigns")
    op.drop_table("role_assignments")
    op.drop_table("brand_history_items")
    op.drop_constraint("fk_brand_active_policy_version", "brands", type_="foreignkey")
    op.drop_constraint("fk_brand_active_genome_version", "brands", type_="foreignkey")
    op.drop_table("policies")
    op.drop_table("brand_genomes")
    op.drop_table("brands")
    op.drop_table("internal_operators")
    op.drop_table("users")
    op.drop_table("workspaces")
    op.drop_table("organizations")

    for enum_name in [
        "ai_slop_source_type",
        "report_review_status",
        "analysis_run_status",
        "asset_modality",
        "campaign_status",
        "role",
        "brand_history_source_type",
        "policy_status",
        "genome_status",
        "brand_status",
        "organization_status",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
