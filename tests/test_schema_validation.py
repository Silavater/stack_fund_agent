"""Every L1->L6 intermediate object validates against its JSON Schema."""

from __future__ import annotations

import json
import pathlib

from stackfund.contracts.authoritative_state import AuthoritativeState
from stackfund.contracts.costs import CostModel
from stackfund.contracts.market import MarketState
from stackfund.contracts.policy import PolicySet
from stackfund.contracts.portfolio import PortfolioState
from stackfund.l1_databook import build_databook, make_seed
from stackfund.l2_scorecard import build_scorecard
from stackfund.l3_crowd import run_scenario
from stackfund.l4_portfolio import build_rebalance_plan
from stackfund.l5_finops import attempt_spend, record_earn
from stackfund.report import compose_divergence
from stackfund.validation import as_jsonable, is_valid, validate

ROOT = pathlib.Path(__file__).resolve().parents[1]


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


def _state():
    sc = build_scorecard(_book())
    portfolio = PortfolioState(holdings={"0056": 0.25}, cash_weight=0.75)
    return AuthoritativeState(sc, portfolio, PolicySet(), CostModel(), MarketState())


def test_scenario_seed_schema():
    validate(as_jsonable(make_seed(_book(), "升息", 42)), "scenario_seed.schema.json")


def test_crowd_narrative_schema():
    narrative = run_scenario(make_seed(_book(), "升息", 42))
    validate(as_jsonable(narrative), "crowd_narrative.schema.json")


def test_narrative_divergence_schema():
    narrative = run_scenario(make_seed(_book(), "升息", 42))
    divergence = compose_divergence(narrative, build_scorecard(_book()))
    validate(as_jsonable(divergence), "narrative_divergence.schema.json")


def test_rebalance_plan_schema():
    validate(as_jsonable(build_rebalance_plan(_state())), "rebalance_plan.schema.json")


def test_operational_receipt_schemas():
    validate(as_jsonable(record_earn("e1", 299.0)), "operational_receipt.schema.json")
    validate(as_jsonable(attempt_spend("s1", 999.0, 100.0)), "operational_receipt.schema.json")


def test_baked_replay_scenario_matches_schema():
    data = json.loads((ROOT / "fixtures" / "scenario_0056_cut.json").read_text(encoding="utf-8"))
    validate(data, "crowd_scenario_report.schema.json")


def test_planted_market_field_is_rejected():
    bad = as_jsonable(run_scenario(make_seed(_book(), "升息", 42)))
    bad["price"] = 36.8  # an authoritative number must never validate
    assert not is_valid(bad, "crowd_narrative.schema.json")
