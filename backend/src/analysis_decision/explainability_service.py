"""Explainability Engine (Phase 2 §7, Phase 1 §8's traceability chain).
Reconstructs the full reasoning chain on demand — nothing here is read
from a persisted copy (Phase 2 §5.3); it recomputes the Decision Engine
fresh from Evidence + pinned Genome/Policy and reads the resulting
`ExplainabilityTree` straight off the result, exactly as CLAUDE.md §1.7
requires.
"""
from __future__ import annotations

import uuid

from src.analysis_decision.decision_engine.engine import compute_decision
from src.analysis_decision.decision_engine.policy_schema import policy_rules_from_json
from src.analysis_decision.decision_engine.schemas import AlignmentIndicator as EngineAlignment
from src.analysis_decision.decision_engine.schemas import EvidenceItem
from src.analysis_decision.applicability import EvaluationContext, resolve_applicability
from src.analysis_decision.genome_tree_builder import build_genome_tree
from src.analysis_decision.repository import AnalysisRunRepository, EvidenceRepository
from src.brand_governance.repository import BrandGenomeRepository, PolicyRepository
from src.campaign_asset.repository import AssetRepository, AssetVersionRepository, CampaignRepository


class ExplainabilityService:
    def __init__(
        self,
        run_repo: AnalysisRunRepository,
        evidence_repo: EvidenceRepository,
        genome_repo: BrandGenomeRepository,
        policy_repo: PolicyRepository,
        asset_repo: AssetRepository,
        asset_version_repo: AssetVersionRepository,
        campaign_repo: CampaignRepository,
    ) -> None:
        self._run_repo = run_repo
        self._evidence_repo = evidence_repo
        self._genome_repo = genome_repo
        self._policy_repo = policy_repo
        self._asset_repo = asset_repo
        self._asset_version_repo = asset_version_repo
        self._campaign_repo = campaign_repo

    async def reconstruct(self, analysis_run_id: uuid.UUID) -> dict:
        run = await self._run_repo.get_by_id(analysis_run_id)
        if run is None:
            raise ValueError(f"AnalysisRun {analysis_run_id} not found.")

        asset_version = await self._asset_version_repo.get_by_id(run.asset_version_id)
        asset = await self._asset_repo.get_by_id(asset_version.asset_id)

        categories = await self._genome_repo.get_categories(run.genome_version_id)
        components_by_category: dict = {}
        assertions_by_component: dict = {}
        for category in categories:
            components = await self._genome_repo.get_components(category.id)
            components_by_category[category.id] = components
            for component in components:
                assertions_by_component[component.id] = await self._genome_repo.get_assertions(component.id)

        context = EvaluationContext(modality=asset.modality.value, context_tags=asset_version.context_tags or [])
        applicable_set = resolve_applicability(categories, components_by_category, assertions_by_component, context)
        genome_tree = build_genome_tree(applicable_set)

        policy = await self._policy_repo.get_by_id(run.policy_version_id)
        policy_rules = policy_rules_from_json(policy.rules or {})

        evidence_rows = await self._evidence_repo.list_for_run(analysis_run_id)
        evidence_by_assertion: dict[uuid.UUID, list[EvidenceItem]] = {}
        evidence_detail_by_id = {}
        for ev in evidence_rows:
            evidence_by_assertion.setdefault(ev.assertion_id, []).append(
                EvidenceItem(id=ev.id, alignment_indicator=EngineAlignment(ev.alignment_indicator.value), confidence=ev.confidence)
            )
            evidence_detail_by_id[ev.id] = ev

        result = compute_decision(genome_tree, evidence_by_assertion, policy_rules)

        def _serialize_result(r):
            return None if r is None else {
                "value": r.value, "coverage": r.coverage,
                "raw_confidence": r.raw_confidence, "reported_confidence": r.reported_confidence,
            }

        campaign = await self._campaign_repo.get_by_id(asset.campaign_id)

        chain = {
            "overall": _serialize_result(result.explainability.overall),
            "score": result.score,
            "verdict": result.verdict.verdict,
            "verdict_source": result.verdict.source,
            # Phase 1 §8's traceability chain terminates at the original
            # uploaded asset — surfaced here (rather than a raw storage
            # URL, since object access is always mediated through the
            # backend, never direct-to-storage) so the Explainability
            # Viewer's last drill-down step has something to point at.
            "brand_id": str(campaign.brand_id),
            "asset": {"id": str(asset.id), "name": asset.name, "modality": asset.modality.value},
            "categories": [],
        }

        for category in applicable_set.categories:
            category_node = {
                "id": str(category.id),
                "name": category.name.value,
                "result": _serialize_result(result.explainability.category_results.get(category.id)),
                "components": [],
            }
            for component in applicable_set.components_by_category.get(category.id, []):
                component_node = {
                    "id": str(component.id),
                    "name": component.name,
                    "result": _serialize_result(result.explainability.component_results.get(component.id)),
                    "assertions": [],
                }
                for assertion in applicable_set.assertions_by_component.get(component.id, []):
                    assertion_evidence = [
                        {
                            "evidence_id": str(ev.id),
                            "alignment_indicator": ev.alignment_indicator.value,
                            "confidence": ev.confidence,
                            "observed_characteristic": ev.observed_characteristic,
                            "source_observation_ids": ev.source_observation_ids,
                        }
                        for ev in evidence_rows
                        if ev.assertion_id == assertion.id
                    ]
                    component_node["assertions"].append(
                        {
                            "id": str(assertion.id),
                            "content": assertion.content,
                            "result": _serialize_result(result.explainability.assertion_results.get(assertion.id)),
                            "source_reference_ids": assertion.source_reference_ids,
                            "evidence": assertion_evidence,
                        }
                    )
                category_node["components"].append(component_node)
            chain["categories"].append(category_node)

        return chain
