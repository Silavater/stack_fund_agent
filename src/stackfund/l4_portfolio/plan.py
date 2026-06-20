"""L4: the portfolio manager (the steering wheel) — pure hard data.

This module imports ONLY the ScoreCard and RebalancePlan contracts. It does not
import the crowd side-rail (L3) or its signal type, by construction. There is no
crowd-signal parameter on ``build_rebalance_plan`` — by signature, the facade
cannot enter this decision. (Enforced by import-linter + the firewall tests.)
"""

from __future__ import annotations

from stackfund.contracts.rebalance_plan import (
    NO_ACTION,
    REBALANCE,
    RebalancePlan,
    WeightDelta,
)
from stackfund.contracts.scorecard import ScoreCard

TOLERANCE_PP = 1.0
SCALE_PP = 6.0  # maps composite score in [-1, +1] to a target delta in pp


def _hard_delta_pp(scorecard: ScoreCard) -> float:
    return round(scorecard.composite() * SCALE_PP, 2)


def _hard_reasons(scorecard: ScoreCard) -> tuple[str, ...]:
    reasons: list[str] = []
    if scorecard.valuation_score >= 0.1:
        reasons.append(f"valuation {scorecard.valuation_score:+.2f}")
    elif scorecard.valuation_score <= -0.1:
        reasons.append(f"valuation {scorecard.valuation_score:+.2f}")
    if scorecard.fundamental_score >= 0.1:
        reasons.append(f"yield/fundamental {scorecard.fundamental_score:+.2f}")
    if scorecard.trend_score >= 0.1 or scorecard.trend_score <= -0.1:
        reasons.append(f"trend {scorecard.trend_score:+.2f}")
    if scorecard.risk_score >= 0.5:
        reasons.append(f"risk {scorecard.risk_score:+.2f}")
    return tuple(reasons)


def build_rebalance_plan(scorecard: ScoreCard) -> RebalancePlan:
    """Build a hard-only plan from a ScoreCard. NO_ACTION is a first-class output."""
    hard_delta = _hard_delta_pp(scorecard)
    plan_id = f"plan_{scorecard.scorecard_id}"
    if abs(hard_delta) < TOLERANCE_PP:
        return RebalancePlan(
            plan_id=plan_id,
            scorecard_id=scorecard.scorecard_id,
            action=NO_ACTION,
            no_action_reason=f"hard_delta {hard_delta:+.2f}pp within tolerance {TOLERANCE_PP}pp",
        )
    delta = WeightDelta(
        etf_symbol=scorecard.etf_symbol,
        hard_delta_pp=hard_delta,
        hard_reasons=_hard_reasons(scorecard),
    )
    return RebalancePlan(
        plan_id=plan_id,
        scorecard_id=scorecard.scorecard_id,
        action=REBALANCE,
        deltas=(delta,),
    )
