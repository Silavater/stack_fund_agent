"""L4: the portfolio manager (the steering wheel) — pure hard data.

Consumes ONLY ``AuthoritativeState`` (ScoreCard + PortfolioState + PolicySet +
CostModel + MarketState). It never imports the crowd side-rail or any FACE
artifact — by signature, the facade cannot enter this decision. ``NO_ACTION`` is
a first-class output with machine-readable ``reason_codes``, including the
key "rebalance not worth the transaction cost" case.
"""

from __future__ import annotations

from stackfund.contracts.authoritative_state import AuthoritativeState
from stackfund.contracts.rebalance_plan import (
    EXPECTED_BENEFIT_BELOW_TRANSACTION_COST,
    INELIGIBLE,
    NO_ACTION,
    REBALANCE,
    WITHIN_TOLERANCE,
    RebalancePlan,
    WeightDelta,
)
from stackfund.contracts.scorecard import ScoreCard

ALPHA_BPS = 300.0  # per-unit-conviction annual edge scale (composite -> benefit)


def _target_weight(composite: float, n_symbols: int, max_weight: float, tilt_pp: float) -> float:
    base = 1.0 / max(n_symbols, 1)
    target = base + composite * (tilt_pp / 100.0)
    return max(0.0, min(max_weight, target))


def _hard_reasons(sc: ScoreCard) -> tuple[str, ...]:
    reasons: list[str] = []
    if abs(sc.valuation_score) >= 0.1:
        reasons.append(f"valuation {sc.valuation_score:+.2f}")
    if sc.fundamental_score >= 0.1:
        reasons.append(f"yield/fundamental {sc.fundamental_score:+.2f}")
    if abs(sc.trend_score) >= 0.1:
        reasons.append(f"trend {sc.trend_score:+.2f}")
    if sc.risk_score >= 0.5:
        reasons.append(f"risk {sc.risk_score:+.2f}")
    return tuple(reasons)


def build_rebalance_plan(state: AuthoritativeState) -> RebalancePlan:
    sc = state.scorecard
    plan_id = f"plan_{sc.scorecard_id}"
    ih = state.input_hash()

    if not sc.eligible:
        return RebalancePlan(
            plan_id=plan_id,
            scorecard_id=sc.scorecard_id,
            action=NO_ACTION,
            reason_codes=(INELIGIBLE, *sc.gate_reasons),
            no_action_reason="ETF failed the L2 eligibility gate",
            authoritative_input_hash=ih,
        )

    composite = sc.composite()
    n_symbols = max(1, len(state.portfolio.holdings))
    target = _target_weight(
        composite, n_symbols, state.policy.max_weight_per_etf, state.policy.base_weight_tilt_pp
    )
    current = state.portfolio.weight_of(sc.etf_symbol)
    raw_delta_pp = round((target - current) * 100.0, 2)
    benefit_bps = round(abs(composite) * ALPHA_BPS, 1)
    cost_bps = state.costs.round_trip_bps

    if abs(raw_delta_pp) < state.policy.tolerance_pp:
        return RebalancePlan(
            plan_id=plan_id,
            scorecard_id=sc.scorecard_id,
            action=NO_ACTION,
            reason_codes=(WITHIN_TOLERANCE,),
            no_action_reason=(
                f"delta {raw_delta_pp:+.2f}pp within tolerance {state.policy.tolerance_pp}pp"
            ),
            authoritative_input_hash=ih,
        )

    if benefit_bps < cost_bps:
        return RebalancePlan(
            plan_id=plan_id,
            scorecard_id=sc.scorecard_id,
            action=NO_ACTION,
            reason_codes=(EXPECTED_BENEFIT_BELOW_TRANSACTION_COST,),
            no_action_reason=(
                f"expected benefit {benefit_bps}bps < round-trip cost {cost_bps}bps "
                f"on a {raw_delta_pp:+.2f}pp move"
            ),
            authoritative_input_hash=ih,
        )

    cap = state.policy.max_delta_pp_per_run
    clamped = max(-cap, min(cap, raw_delta_pp))
    delta = WeightDelta(
        etf_symbol=sc.etf_symbol,
        hard_delta_pp=round(clamped, 2),
        target_weight_pct=round(target * 100.0, 2),
        hard_reasons=_hard_reasons(sc),
        benefit_bps=benefit_bps,
        cost_bps=cost_bps,
    )
    return RebalancePlan(
        plan_id=plan_id,
        scorecard_id=sc.scorecard_id,
        action=REBALANCE,
        deltas=(delta,),
        authoritative_input_hash=ih,
    )
