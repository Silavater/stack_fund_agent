"""Every L1->L6 intermediate object validates against its JSON Schema."""

from __future__ import annotations

import json
import pathlib

from stackfund.l1_databook import build_databook, make_seed
from stackfund.l2_scorecard import build_scorecard
from stackfund.l3_crowd import run_scenario
from stackfund.l4_portfolio import build_rebalance_plan
from stackfund.l5_finops import attempt_spend, record_earn
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


def test_scenario_seed_schema():
    validate(as_jsonable(make_seed(_book(), "升息", 42)), "scenario_seed.schema.json")


def test_contrarian_signal_schema():
    sig = run_scenario(make_seed(_book(), "升息", 42))
    validate(as_jsonable(sig), "contrarian_signal.schema.json")


def test_rebalance_plan_schema():
    plan = build_rebalance_plan(build_scorecard(_book()))
    validate(as_jsonable(plan), "rebalance_plan.schema.json")


def test_operational_receipt_schemas():
    validate(as_jsonable(record_earn("e1", 299.0)), "operational_receipt.schema.json")
    validate(as_jsonable(attempt_spend("s1", 999.0, 100.0)), "operational_receipt.schema.json")


def test_baked_replay_scenario_matches_schema():
    data = json.loads((ROOT / "fixtures" / "scenario_0056_cut.json").read_text(encoding="utf-8"))
    validate(data, "crowd_scenario_report.schema.json")


def test_planted_market_field_is_rejected():
    bad = as_jsonable(run_scenario(make_seed(_book(), "升息", 42)))
    bad["price"] = 36.8  # an authoritative number must never validate
    assert not is_valid(bad, "contrarian_signal.schema.json")
