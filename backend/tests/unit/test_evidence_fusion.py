"""Evidence Fusion tests (Phase 3 §5, INV-27) — dependency-free, run
directly like the Decision Engine and Authorization tests."""
import uuid

from src.analysis_decision.evidence_fusion import RawObservation, fuse


def test_single_observation_passes_through() -> None:
    assertion_id = uuid.uuid4()
    obs = RawObservation(id=uuid.uuid4(), assertion_id=assertion_id, alignment_indicator="aligned", confidence=0.9, observed_characteristic="Uses confident tone throughout.")
    fused = fuse([obs])
    assert len(fused) == 1
    assert fused[0].assertion_id == assertion_id
    assert fused[0].source_observation_ids == [obs.id]


def test_near_identical_observations_do_not_double_count() -> None:
    """INV-27: near-identical redundant Observations must collapse into
    one Evidence item, not be counted as independent corroborating evidence."""
    assertion_id = uuid.uuid4()
    obs1 = RawObservation(id=uuid.uuid4(), assertion_id=assertion_id, alignment_indicator="aligned", confidence=0.8, observed_characteristic="The copy uses a confident, energetic tone.")
    obs2 = RawObservation(id=uuid.uuid4(), assertion_id=assertion_id, alignment_indicator="aligned", confidence=0.95, observed_characteristic="The copy uses a confident, energetic tone")
    fused = fuse([obs1, obs2])
    assert len(fused) == 1
    assert set(fused[0].source_observation_ids) == {obs1.id, obs2.id}
    assert fused[0].confidence == 0.95  # highest-confidence member represents the cluster


def test_genuinely_distinct_observations_both_survive() -> None:
    assertion_id = uuid.uuid4()
    obs1 = RawObservation(id=uuid.uuid4(), assertion_id=assertion_id, alignment_indicator="aligned", confidence=0.8, observed_characteristic="Uses the approved primary color palette.")
    obs2 = RawObservation(id=uuid.uuid4(), assertion_id=assertion_id, alignment_indicator="misaligned", confidence=0.7, observed_characteristic="Logo is stretched out of its correct aspect ratio.")
    fused = fuse([obs1, obs2])
    assert len(fused) == 2


def test_different_assertions_never_merge() -> None:
    obs1 = RawObservation(id=uuid.uuid4(), assertion_id=uuid.uuid4(), alignment_indicator="aligned", confidence=0.9, observed_characteristic="Same text, different assertion.")
    obs2 = RawObservation(id=uuid.uuid4(), assertion_id=uuid.uuid4(), alignment_indicator="aligned", confidence=0.9, observed_characteristic="Same text, different assertion.")
    fused = fuse([obs1, obs2])
    assert len(fused) == 2
