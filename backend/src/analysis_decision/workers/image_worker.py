"""Image Worker — Visual Identity category, image-modality assets.

See `image_features.py`'s module docstring for the text-only-LLM
limitation this pass works within.
"""
from __future__ import annotations

from src.analysis_decision.workers.base import WorkerResult
from src.analysis_decision.workers.image_features import describe_features, extract_image_features
from src.analysis_decision.workers.judgment_schemas import WorkerJudgmentResult
from src.analysis_decision.workers.prompting import build_judgment_system_prompt, safe_uuid
from src.brand_governance.domain.models import Assertion
from src.logging import get_logger
from src.shared_kernel.llm.client import LLMClient, LLMValidationFailure

logger = get_logger(__name__)


async def run_image_worker(*, image_bytes: bytes, assertions: list[Assertion], llm: LLMClient) -> WorkerResult:
    if not assertions:
        return WorkerResult(succeeded=True)

    try:
        features = extract_image_features(image_bytes)
    except Exception:
        logger.warning("image_worker.feature_extraction_failed")
        return WorkerResult(succeeded=False)

    description = describe_features(features)

    try:
        result: WorkerJudgmentResult = await llm.generate_structured(
            system_prompt=build_judgment_system_prompt(assertions),
            untrusted_content=description,
            response_schema=WorkerJudgmentResult,
        )
    except LLMValidationFailure:
        logger.warning("image_worker.judgment_failed", assertion_count=len(assertions))
        return WorkerResult(succeeded=False)

    valid_ids = {a.id for a in assertions}
    judgments = [j for j in result.judgments if safe_uuid(j.assertion_id) in valid_ids]
    no_signal = [uid for aid in result.no_signal_assertion_ids if (uid := safe_uuid(aid)) in valid_ids]

    return WorkerResult(succeeded=True, judgments=judgments, no_signal_assertion_ids=no_signal)
