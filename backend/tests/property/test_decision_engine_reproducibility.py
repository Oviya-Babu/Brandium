"""Hypothesis is wired up here in Phase 0 so the harness exists before it's
needed. The real, load-bearing test this file will eventually hold is the
Decision Engine's reproducibility guarantee (INV-02/NFR-004): given an
identical Evidence set + genome_version_id + policy_version_id +
decision_function_version, recomputing a Decision always yields an
identical score/verdict. The Decision Engine itself doesn't exist yet
(CLAUDE.md §14 Milestone 4) — this placeholder only proves the property-
testing harness is correctly configured, per Technology Stack §27.
"""
from hypothesis import given
from hypothesis import strategies as st


@given(st.integers(), st.integers())
def test_hypothesis_harness_is_wired_up(a: int, b: int) -> None:
    assert a + b == b + a
