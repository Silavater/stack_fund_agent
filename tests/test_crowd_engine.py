"""L3 crowd engine: per-archetype voices, ordinal-driven stance, reaction chain.

These lock slice-002 behaviour: archetypes read the frozen ordinal context by
their own sensitivity (they no longer flip in lockstep), while the emitted stance
stays categorical (-1|0|1) and the whole narrative stays deterministic per seed.
"""

from __future__ import annotations

from stackfund.l1_databook import build_databook, make_seed
from stackfund.l3_crowd.engine import _ARCHETYPES, _stance_for, run_scenario

_CHEAP = {"discount_premium": "deep_discount", "yield": "high"}
_RICH = {"discount_premium": "rich", "yield": "low"}


def _book(discount_premium: float, yield_pct: float):
    return build_databook(
        "0056",
        {
            "discount_premium": discount_premium,
            "yield": yield_pct,
            "price_5d_return": -0.5,
            "tracking_error": 0.4,
            "catalyst_strength": 0.3,
        },
        "2026-06-19",
    )


def test_stance_is_always_categorical():
    for s in run_scenario(make_seed(_book(-0.6, 8.5), "0056_cut", 42)).persona_samples:
        assert s.stance in (-1, 0, 1)


def test_all_ten_archetypes_present_and_distinct_excerpts():
    samples = run_scenario(make_seed(_book(-0.6, 8.5), "0056_cut", 42)).persona_samples
    assert {s.archetype_id for s in samples} == set(_ARCHETYPES)
    # each archetype speaks in its own voice — excerpts are not all identical
    assert len({s.excerpt for s in samples}) > 1


def test_ordinal_context_shifts_stance_at_fixed_consensus():
    """Holding consensus constant, a fundamentals-driven cohort must read cheap+high-yield
    differently from rich+low-yield — proving cohorts diverge on their own ordinal read,
    not a single lockstep flip. (Called directly so the consensus can't co-vary.)"""
    # long_term_holder is contra + fundamentals-sensitive. Under a bearish consensus its
    # baseline lean is bullish; rich/low-yield fundamentals must pull it back down.
    assert _stance_for("long_term_holder", "bearish", _CHEAP) != _stance_for(
        "long_term_holder", "bearish", _RICH
    )


def test_momentum_cohort_ignores_fundamentals_at_fixed_consensus():
    """Sensitivity-(0,0) archetypes ride the consensus only — with consensus held fixed,
    the ordinal context must not move their stance."""
    for a in ("day_trader", "leveraged_etf_player", "panic_retail", "ptt_dcard_trendwatch"):
        assert _stance_for(a, "bullish", _CHEAP) == _stance_for(a, "bullish", _RICH)
        assert _stance_for(a, "bearish", _CHEAP) == _stance_for(a, "bearish", _RICH)


def test_reaction_chain_present_in_narrative():
    md = run_scenario(make_seed(_book(-0.6, 8.5), "0056_cut", 42)).narrative_md
    assert "反應鏈" in md
    assert "1. " in md  # at least a first chain step


def test_determinism_full_narrative():
    a = run_scenario(make_seed(_book(-0.6, 8.5), "0056_cut", 42))
    b = run_scenario(make_seed(_book(-0.6, 8.5), "0056_cut", 42))
    assert a.crowd_consensus == b.crowd_consensus
    assert a.narrative_md == b.narrative_md
    assert a.persona_samples == b.persona_samples


def test_horizon_changes_reaction_chain_lead():
    """slice-003: horizon re-weights who leads the chain — intraday is led by the
    fastest herder, long by a slow fundamentals cohort. The two narratives differ."""
    book = _book(-0.6, 8.5)
    intraday = run_scenario(make_seed(book, "0056_cut", 42, horizon="intraday")).narrative_md
    long = run_scenario(make_seed(book, "0056_cut", 42, horizon="long")).narrative_md
    assert intraday != long
    # the first chain step names a different cohort
    assert intraday.split("1. ")[1].split("\n")[0] != long.split("1. ")[1].split("\n")[0]


def test_intensity_changes_tail_framing():
    book = _book(-0.6, 8.5)
    mild = run_scenario(make_seed(book, "0056_cut", 42, intensity="mild")).narrative_md
    severe = run_scenario(make_seed(book, "0056_cut", 42, intensity="severe")).narrative_md
    assert mild != severe


def test_horizon_intensity_deterministic():
    book = _book(-0.6, 8.5)
    a = run_scenario(make_seed(book, "0056_cut", 42, horizon="long", intensity="severe"))
    b = run_scenario(make_seed(book, "0056_cut", 42, horizon="long", intensity="severe"))
    assert a.narrative_md == b.narrative_md
    assert a.persona_samples == b.persona_samples


def test_scenario_seed_rejects_bad_horizon_intensity():
    import pytest

    from stackfund.contracts.scenario_seed import ScenarioSeed

    with pytest.raises(AssertionError):
        ScenarioSeed("s", "d", 42, "L", horizon="weekly")
    with pytest.raises(AssertionError):
        ScenarioSeed("s", "d", 42, "L", intensity="nuclear")
