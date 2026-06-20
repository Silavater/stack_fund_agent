"""L4 output contract: the hard-only rebalance plan (pure hard data).

Every non-zero ``final_delta`` is, by construction, equal to ``hard_delta`` —
the crowd modifier never enters this object.
"""

from __future__ import annotations

from dataclasses import dataclass, field

NO_ACTION = "NO_ACTION"
REBALANCE = "REBALANCE"


@dataclass(frozen=True)
class WeightDelta:
    etf_symbol: str
    hard_delta_pp: float
    # Each non-zero move carries >= 2 independent hard-data reasons.
    hard_reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class RebalancePlan:
    plan_id: str
    scorecard_id: str
    action: str  # NO_ACTION | REBALANCE
    deltas: tuple[WeightDelta, ...] = field(default_factory=tuple)
    no_action_reason: str | None = None
