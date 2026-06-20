"""Typed data contracts — the firewall expressed as types.

IMPORTANT (firewall): this package facade deliberately does NOT re-export
``ContrarianSignal`` / ``PersonaReaction``. They live only in
``stackfund.contracts.contrarian_signal`` and must be imported from there
directly. This guarantees that importing ``stackfund.contracts`` (or any of its
trunk submodules) can never pull the crowd signal in transitively — so the L4
firewall holds even through the package ``__init__``.
"""

from __future__ import annotations

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
from stackfund.contracts.provenance import CrowdReportProvenance, DecisionProvenance
from stackfund.contracts.rebalance_plan import NO_ACTION, REBALANCE, RebalancePlan, WeightDelta
from stackfund.contracts.scenario_seed import ScenarioSeed
from stackfund.contracts.scorecard import ScoreCard

__all__ = [
    "BLOCKED",
    "EARN",
    "MANUAL_REVIEW",
    "NO_ACTION",
    "REBALANCE",
    "REFUSED_SPEND",
    "SPEND",
    "CrowdReportProvenance",
    "DataBook",
    "DecisionProvenance",
    "OperationalPnL",
    "OperationalReceipt",
    "RebalancePlan",
    "ScenarioSeed",
    "ScoreCard",
    "WeightDelta",
]
