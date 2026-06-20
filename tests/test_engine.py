"""Engine behaviour: deterministic scorecard, hard-only plan, seed firewall."""

from __future__ import annotations

import pathlib

from stackfund.contracts.rebalance_plan import REBALANCE
from stackfund.l1_databook import build_databook, load_databook_from_fixture, make_seed
from stackfund.l2_scorecard import build_scorecard
from stackfund.l4_portfolio import build_rebalance_plan

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures"


def _book():
    return build_databook(
        "0056",
        {
            "discount_premium": -0.6,
            "yield": 8.5,
            "price_5d_return": -0.5,
            "tracking_error": 0.4,
            "catalyst_strength": 0.3,
        },
        "2026-06-19",
    )


def test_scorecard_is_deterministic_and_derived():
    a = build_scorecard(_book())
    b = build_scorecard(_book())
    assert a == b
    assert a.valuation_score == 0.3  # -(-0.6)/2
    assert a.fundamental_score == 1.0  # (8.5-4)/4 clipped


def test_0056_fixture_triggers_rebalance_with_multiple_hard_reasons():
    book = load_databook_from_fixture(FIXTURES / "etf_0056.json")
    plan = build_rebalance_plan(build_scorecard(book))
    assert plan.action == REBALANCE
    assert plan.deltas
    assert len(plan.deltas[0].hard_reasons) >= 2


def test_make_seed_strips_raw_numbers():
    seed = make_seed(_book(), "升息", 42)
    assert seed.ordinal_context["yield"] == "high"
    assert seed.ordinal_context["discount_premium"] == "discount"
    assert all(isinstance(v, str) for v in seed.ordinal_context.values())
