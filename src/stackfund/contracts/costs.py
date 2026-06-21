"""Authoritative cost model — part of the L4 input (AuthoritativeState).

Round-trip transaction cost in basis points (broker fee + transaction tax +
slippage). Used by L4 to gate trades on expected-benefit vs cost.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CostModel:
    fee_bps: float = 4.0  # broker commission (round trip)
    tax_bps: float = 10.0  # securities transaction tax
    slippage_bps: float = 5.0  # expected slippage

    @property
    def round_trip_bps(self) -> float:
        return round(self.fee_bps + self.tax_bps + self.slippage_bps, 2)
