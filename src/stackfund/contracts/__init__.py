"""Typed data contracts — the firewall expressed as types.

IMPORTANT (firewall): this package facade deliberately does NOT re-export the
FACE artifacts (``CrowdNarrative`` / ``NarrativeDivergence`` / ``PersonaReaction``).
They live only in ``stackfund.contracts.crowd_narrative`` /
``stackfund.contracts.narrative_divergence`` and must be imported from there
directly, so importing the contracts facade (or any trunk submodule) can never
pull a FACE artifact in transitively — the L4/L5 firewall holds even through
``__init__``.
"""

from __future__ import annotations

from stackfund.contracts.authoritative_state import AuthoritativeState
from stackfund.contracts.costs import CostModel
from stackfund.contracts.databook import DataBook
from stackfund.contracts.finops import (
    BLOCKED,
    EARN,
    MANUAL_REVIEW,
    REFUSED_SPEND,
    SPEND,
    OperationalPnL,
    OperationalReceipt,
)
from stackfund.contracts.market import MarketState
from stackfund.contracts.policy import PolicySet
from stackfund.contracts.portfolio import PortfolioState
from stackfund.contracts.provenance import CrowdReportProvenance, DecisionProvenance
from stackfund.contracts.rebalance_plan import (
    DATA_CONFIDENCE_TOO_LOW,
    EXPECTED_BENEFIT_BELOW_TRANSACTION_COST,
    INELIGIBLE,
    MARKET_CLOSED,
    NO_ACTION,
    REBALANCE,
    WITHIN_TOLERANCE,
    RebalancePlan,
    WeightDelta,
)
from stackfund.contracts.scenario_seed import ScenarioSeed
from stackfund.contracts.scorecard import ScoreCard

__all__ = [
    "BLOCKED",
    "DATA_CONFIDENCE_TOO_LOW",
    "EARN",
    "EXPECTED_BENEFIT_BELOW_TRANSACTION_COST",
    "INELIGIBLE",
    "MANUAL_REVIEW",
    "MARKET_CLOSED",
    "NO_ACTION",
    "REBALANCE",
    "REFUSED_SPEND",
    "SPEND",
    "WITHIN_TOLERANCE",
    "AuthoritativeState",
    "CostModel",
    "CrowdReportProvenance",
    "DataBook",
    "DecisionProvenance",
    "MarketState",
    "OperationalPnL",
    "OperationalReceipt",
    "PolicySet",
    "PortfolioState",
    "RebalancePlan",
    "ScenarioSeed",
    "ScoreCard",
    "WeightDelta",
]
