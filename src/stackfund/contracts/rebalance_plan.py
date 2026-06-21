"""L4 output contract: the hard-only rebalance plan (pure hard data).

Every non-zero ``hard_delta_pp`` is justified only by authoritative inputs
(ScoreCard + PortfolioState + PolicySet + CostModel); the crowd side never
enters. ``NO_ACTION`` is a first-class output carrying machine-readable
``reason_codes``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

NO_ACTION = "NO_ACTION"
REBALANCE = "REBALANCE"

# NO_ACTION reason codes (closed vocabulary).
WITHIN_TOLERANCE = "WITHIN_TOLERANCE"
EXPECTED_BENEFIT_BELOW_TRANSACTION_COST = "EXPECTED_BENEFIT_BELOW_TRANSACTION_COST"
DATA_CONFIDENCE_TOO_LOW = "DATA_CONFIDENCE_TOO_LOW"
INELIGIBLE = "INELIGIBLE"
MARKET_CLOSED = "MARKET_CLOSED"


@dataclass(frozen=True)
class WeightDelta:
    etf_symbol: str
    hard_delta_pp: float
    target_weight_pct: float = 0.0
    hard_reasons: tuple[str, ...] = ()
    benefit_bps: float = 0.0
    cost_bps: float = 0.0


@dataclass(frozen=True)
class RebalancePlan:
    plan_id: str
    scorecard_id: str
    action: str  # NO_ACTION | REBALANCE
    deltas: tuple[WeightDelta, ...] = field(default_factory=tuple)
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    no_action_reason: str | None = None
    authoritative_input_hash: str = ""
