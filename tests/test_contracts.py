"""Contract invariants — ContrarianSignal is always non-authoritative & bounded."""

from __future__ import annotations

import pytest

from stackfund.contracts.contrarian_signal import ContrarianSignal


def _make(**overrides):
    base = dict(
        seed_id="seed_x",
        rng_seed=42,
        n_personas=30,
        contrarian_modifier=0.4,
        narrative_md="情境推演,非預測。",
    )
    base.update(overrides)
    return ContrarianSignal(**base)


def test_default_is_non_authoritative():
    assert _make().is_authoritative is False


def test_rejects_authoritative_true():
    with pytest.raises(AssertionError):
        _make(is_authoritative=True)


def test_rejects_modifier_out_of_range():
    with pytest.raises(AssertionError):
        _make(contrarian_modifier=1.5)


def test_rejects_bad_persona_count():
    with pytest.raises(AssertionError):
        _make(n_personas=5)
