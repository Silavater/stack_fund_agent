"""Authoritative policy limits — part of the L4 input (AuthoritativeState)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicySet:
    tolerance_pp: float = 1.0  # |delta| below this -> NO_ACTION (within tolerance)
    max_weight_per_etf: float = 0.40  # cap on any single ETF weight (fraction)
    min_cash_weight: float = 0.05  # keep at least this much cash
    max_delta_pp_per_run: float = 5.0  # clamp how far a single run may move a weight
    base_weight_tilt_pp: float = 15.0  # max tilt vs equal-weight base, by conviction
