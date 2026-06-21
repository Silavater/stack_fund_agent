"""Contract invariants — FACE artifacts are non-authoritative, bounded, scalar-free."""

from __future__ import annotations

import dataclasses

import pytest

from stackfund.contracts.crowd_narrative import CrowdNarrative
from stackfund.contracts.narrative_divergence import NarrativeDivergence


def _cn(**overrides):
    base = dict(
        seed_id="seed_x", rng_seed=42, n_personas=30, crowd_consensus="bearish", narrative_md="x"
    )
    base.update(overrides)
    return CrowdNarrative(**base)


def test_crowd_narrative_is_non_authoritative_by_default():
    assert _cn().non_authoritative is True
    assert _cn().synthetic_population is True


def test_crowd_narrative_rejects_bad_consensus():
    with pytest.raises(AssertionError):
        _cn(crowd_consensus="up")


def test_crowd_narrative_rejects_bad_persona_count():
    with pytest.raises(AssertionError):
        _cn(n_personas=5)


def test_crowd_narrative_has_no_numeric_modifier_field():
    names = {f.name for f in dataclasses.fields(CrowdNarrative)}
    assert "contrarian_modifier" not in names
    assert "modifier" not in names


def _nd(**overrides):
    base = dict(
        seed_id="seed_x",
        crowd_consensus="bearish",
        engine_posture="neutral",
        divergence_bucket="MEDIUM",
        narrative_intensity=2,
    )
    base.update(overrides)
    return NarrativeDivergence(**base)


def test_divergence_is_non_authoritative_by_default():
    assert _nd().non_authoritative is True


def test_divergence_rejects_bad_bucket():
    with pytest.raises(AssertionError):
        _nd(divergence_bucket="EXTREME")


def test_divergence_rejects_bad_intensity():
    with pytest.raises(AssertionError):
        _nd(narrative_intensity=5)


def test_divergence_has_no_numeric_modifier_field():
    names = {f.name for f in dataclasses.fields(NarrativeDivergence)}
    assert "contrarian_modifier" not in names
    assert "modifier" not in names
