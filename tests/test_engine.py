"""Engine behaviour: eligibility gate, deterministic scorecard, AuthoritativeState
-driven L4 (within-tolerance / cost>benefit / rebalance), seed firewall."""

from __future__ import annotations

import json
import pathlib

from stackfund.contracts.authoritative_state import AuthoritativeState
from stackfund.contracts.costs import CostModel
from stackfund.contracts.market import MarketState
from stackfund.contracts.policy import PolicySet
from stackfund.contracts.portfolio import PortfolioState
from stackfund.contracts.rebalance_plan import (
    EXPECTED_BENEFIT_BELOW_TRANSACTION_COST,
    INELIGIBLE,
    NO_ACTION,
    REBALANCE,
    WITHIN_TOLERANCE,
)
from stackfund.l1_databook import build_databook, load_databook_from_fixture, make_seed
from stackfund.l2_scorecard import build_scorecard, eligibility_gate
from stackfund.l4_portfolio import build_rebalance_plan

FIXTURES = pathlib.Path(__file__).resolve().parents[1] / "fixtures"


def _book(**metric_overrides):
    metrics = {
        "discount_premium": -0.6,
        "yield": 8.5,
        "price_5d_return": -0.5,
        "tracking_error": 0.4,
        "catalyst_strength": 0.3,
    }
    metrics.update(metric_overrides)
    return build_databook("0056", metrics, "2026-06-19")


def _portfolio():
    data = json.loads((FIXTURES / "portfolio.json").read_text(encoding="utf-8"))
    return PortfolioState(holdings=data["holdings"], cash_weight=data["cash_weight"])


def _full_state(symbol: str) -> AuthoritativeState:
    sc = build_scorecard(load_databook_from_fixture(FIXTURES / f"etf_{symbol}.json"))
    return AuthoritativeState(sc, _portfolio(), PolicySet(), CostModel(), MarketState())


def test_scorecard_is_deterministic_and_derived():
    a = build_scorecard(_book())
    b = build_scorecard(_book())
    assert a == b
    assert a.valuation_score == 0.3
    assert a.fundamental_score == 1.0
    assert a.eligible is True


def test_eligibility_gate_blocks_leveraged():
    book = build_databook("00631L", {"leveraged_or_inverse": 1.0}, "2026-06-19")
    eligible, reasons = eligibility_gate(book)
    assert not eligible
    assert "LEVERAGED_OR_INVERSE" in reasons
    state = AuthoritativeState(
        build_scorecard(book),
        PortfolioState(holdings={"00631L": 0.0}, cash_weight=1.0),
        PolicySet(),
        CostModel(),
        MarketState(),
    )
    plan = build_rebalance_plan(state)
    assert plan.action == NO_ACTION
    assert INELIGIBLE in plan.reason_codes


def test_eligibility_accepts_live_freshness():
    # Regression: "live" is the *freshest* state but was missing from the gate's
    # accept-list, so every ETF under --live failed as STALE_OR_MISSING. Live + frozen
    # (complete data) must pass; "partial"/unknown stays stale.
    eligible, reasons = eligibility_gate(
        build_databook("0056", {"yield": 8.5}, "2026-06-25", freshness="live")
    )
    assert "STALE_OR_MISSING" not in reasons
    assert eligible is True
    _, partial = eligibility_gate(
        build_databook("0056", {"yield": 8.5}, "2026-06-25", freshness="partial")
    )
    assert "STALE_OR_MISSING" in partial


def test_0050_blocked_by_cost_gate():
    # weak conviction but far underweight -> expected benefit below transaction cost
    plan = build_rebalance_plan(_full_state("0050"))
    assert plan.action == NO_ACTION
    assert EXPECTED_BENEFIT_BELOW_TRANSACTION_COST in plan.reason_codes


def test_0056_rebalances_with_hard_reasons():
    plan = build_rebalance_plan(_full_state("0056"))
    assert plan.action == REBALANCE
    assert plan.deltas
    assert plan.deltas[0].hard_delta_pp > 0
    assert len(plan.deltas[0].hard_reasons) >= 2
    assert plan.deltas[0].benefit_bps > plan.deltas[0].cost_bps


def test_00878_within_tolerance():
    plan = build_rebalance_plan(_full_state("00878"))
    assert plan.action == NO_ACTION
    assert WITHIN_TOLERANCE in plan.reason_codes


def test_authoritative_input_hash_recorded():
    plan = build_rebalance_plan(_full_state("0056"))
    assert plan.authoritative_input_hash.startswith("sha256:")


def test_make_seed_strips_raw_numbers():
    seed = make_seed(_book(), "升息", 42)
    assert seed.ordinal_context["yield"] == "high"
    assert seed.ordinal_context["discount_premium"] == "discount"
    assert all(isinstance(v, str) for v in seed.ordinal_context.values())
