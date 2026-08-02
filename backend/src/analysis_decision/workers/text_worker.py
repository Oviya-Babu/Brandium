"""Text Worker — covers Verbal Identity, Messaging & Positioning, Values
& Mission, Compliance & Legal, and Accessibility categories for
text-modality assets (see planning.py's module docstring for the
collapsed-worker-roles simplification this pass makes).

Never receives Policy weights, Critical Rule thresholds, or another
worker's findings (CLAUDE.md §5.1, Phase 6 §2's trust-boundary table) —
its only inputs are the asset's own text and the Assertions it was
assigned.
"""
from __future__ import annotations

from src.analysis_decision.workers.base import WorkerResult
from src.analysis_decision.workers.judgment_schemas import WorkerJudgmentResult
from src.analysis_decision.workers.prompting import build_judgment_system_prompt, safe_uuid
from src.brand_governance.domain.models import Assertion
from src.logging import get_logger
from src.shared_kernel.llm.client import LLMClient, LLMValidationFailure

logger = get_logger(__name__)


async def run_text_worker(*, asset_text: str, assertions: list[Assertion], llm: LLMClient) -> WorkerResult:
    if not assertions:
        return WorkerResult(succeeded=True)

    try:
        result: WorkerJudgmentResult = await llm.generate_structured(
            system_prompt=build_judgment_system_prompt(assertions),
            untrusted_content=asset_text,
            response_schema=WorkerJudgmentResult,
        )
    except LLMValidationFailure:
        logger.warning("text_worker.failed", assertion_count=len(assertions))
        return WorkerResult(succeeded=False)

    valid_ids = {a.id for a in assertions}
    judgments = [j for j in result.judgments if safe_uuid(j.assertion_id) in valid_ids]
    no_signal = [uid for aid in result.no_signal_assertion_ids if (uid := safe_uuid(aid)) in valid_ids]

    return WorkerResult(succeeded=True, judgments=judgments, no_signal_assertion_ids=no_signal)
