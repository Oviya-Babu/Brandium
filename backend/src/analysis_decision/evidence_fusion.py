"""Evidence Normalization & Fusion (Phase 3 §5). Converts raw Observations
into Evidence, one per Assertion, merging near-identical redundant
Observations rather than double-counting them as independent
corroborating evidence (Phase 3 §5, INV-27)."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from difflib import SequenceMatcher

_NEAR_DUPLICATE_THRESHOLD = 0.9
"""Same deterministic-similarity approach as genome_compiler.py's
Consolidation step, applied here to avoid double-counting near-identical
Observations of the same underlying finding (Phase 3 §5) — a higher
threshold than Consolidation's, since here both Observations already
target the exact same Assertion (a stronger prior that near-identical
text really is a duplicate, not two distinct sub-claims)."""


@dataclass(frozen=True)
class RawObservation:
    id: uuid.UUID
    assertion_id: uuid.UUID
    alignment_indicator: str
    confidence: float
    observed_characteristic: str


@dataclass(frozen=True)
class FusedEvidence:
    assertion_id: uuid.UUID
    alignment_indicator: str
    confidence: float
    observed_characteristic: str
    source_observation_ids: list[uuid.UUID]


def fuse(observations: list[RawObservation]) -> list[FusedEvidence]:
    by_assertion: dict[uuid.UUID, list[RawObservation]] = {}
    for obs in observations:
        by_assertion.setdefault(obs.assertion_id, []).append(obs)

    fused: list[FusedEvidence] = []
    for assertion_id, obs_list in by_assertion.items():
        clusters: list[list[RawObservation]] = []
        for obs in obs_list:
            placed = False
            for cluster in clusters:
                if SequenceMatcher(None, cluster[0].observed_characteristic.lower(), obs.observed_characteristic.lower()).ratio() >= _NEAR_DUPLICATE_THRESHOLD:
                    cluster.append(obs)
                    placed = True
                    break
            if not placed:
                clusters.append([obs])

        for cluster in clusters:
            # Near-identical Observations collapse into one Evidence item
            # (INV-27) — represented by the highest-confidence member,
            # citing every Observation that contributed to it.
            best = max(cluster, key=lambda o: o.confidence)
            fused.append(
                FusedEvidence(
                    assertion_id=assertion_id,
                    alignment_indicator=best.alignment_indicator,
                    confidence=best.confidence,
                    observed_characteristic=best.observed_characteristic,
                    source_observation_ids=[o.id for o in cluster],
                )
            )

    return fused
