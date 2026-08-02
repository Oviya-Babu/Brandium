"""Recommendation narration — the generative half of Recommendation
(Phase 2 §6.3). Receives only the triggering Component's name, the
specific covered Assertions/Evidence that pulled it down, and the
already-computed priority; it cannot alter whether the recommendation
exists or its priority (CLAUDE.md §5.1) — those are already decided by
`decision_engine/recommendation.py` before this module is ever called.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from src.shared_kernel.llm.client import LLMClient, LLMValidationFailure


class NarrationResult(BaseModel):
    text: str = Field(description="A specific, actionable recommendation grounded only in the evidence given.")


def _build_prompt(component_name: str, evidence_descriptions: list[str]) -> str:
    evidence_text = "\n".join(f"- {d}" for d in evidence_descriptions)
    return (
        "Write one specific, actionable recommendation for a content creator, addressing the "
        f"brand identity component '{component_name}'. Base it exclusively on the evidence "
        "below — do not introduce any claim, fact, or suggestion not directly grounded in it. "
        "Do not mention scores, numbers, or priority. Two to three sentences, plain language.\n\n"
        f"Evidence:\n{evidence_text}"
    )


async def narrate_recommendation(*, component_name: str, evidence_descriptions: list[str], llm: LLMClient) -> str:
    try:
        result: NarrationResult = await llm.generate_structured(
            system_prompt=_build_prompt(component_name, evidence_descriptions),
            untrusted_content="\n".join(evidence_descriptions),
            response_schema=NarrationResult,
        )
        return result.text
    except LLMValidationFailure:
        # Narration failure must never block Recommendation persistence —
        # the deterministic trigger/priority/grounding already computed
        # (Phase 2 §6.3) is the load-bearing part; a generic fallback
        # phrasing still leaves the recommendation fully evidence-grounded.
        return (
            f"Review the '{component_name}' aspect of this content against the evidence flagged "
            "for it — automated wording generation was unavailable for this recommendation."
        )
