"""Authoritative portfolio state — part of the L4 input (AuthoritativeState).

Weights are fractions in [0, 1]; ``holdings`` + ``cash_weight`` ~= 1.0.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PortfolioState:
    holdings: dict[str, float] = field(default_factory=dict)  # symbol -> current weight
    cash_weight: float = 1.0
    as_of: str = ""

    def weight_of(self, symbol: str) -> float:
        return self.holdings.get(symbol, 0.0)
