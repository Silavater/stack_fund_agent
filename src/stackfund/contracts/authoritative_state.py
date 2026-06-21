"""AuthoritativeState — the complete, deterministic input to L4.

This replaces "L4 only eats ScoreCard". A ScoreCard says whether an ETF is good;
it cannot alone answer "how much should I hold right now" — that needs current
positions, policy limits, costs and market state. AuthoritativeState bundles all
of them. It is pure ENGINE data: by construction it contains NO FACE artifact
(no crowd narrative / divergence). The firewall invariant becomes
"L4 reads only AuthoritativeState; never a FACE artifact."
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from stackfund.contracts.costs import CostModel
from stackfund.contracts.market import MarketState
from stackfund.contracts.policy import PolicySet
from stackfund.contracts.portfolio import PortfolioState
from stackfund.contracts.scorecard import ScoreCard


@dataclass(frozen=True)
class AuthoritativeState:
    scorecard: ScoreCard
    portfolio: PortfolioState
    policy: PolicySet
    costs: CostModel
    market: MarketState

    def input_hash(self) -> str:
        payload = {
            "scorecard_id": self.scorecard.scorecard_id,
            "composite": self.scorecard.composite(),
            "holdings": dict(sorted(self.portfolio.holdings.items())),
            "cash": self.portfolio.cash_weight,
            "policy": self.policy.__dict__,
            "costs": self.costs.__dict__,
            "market": self.market.__dict__,
        }
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return f"sha256:{digest[:16]}"
