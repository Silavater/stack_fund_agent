"""L2 output contract: the authoritative deterministic scorecard.

This is the ONLY input L4 (the portfolio manager / steering wheel) consumes.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreCard:
    scorecard_id: str
    databook_id: str
    etf_symbol: str
    trend_score: float
    fundamental_score: float
    valuation_score: float
    catalyst_score: float
    risk_score: float

    def composite(self) -> float:
        """Transparent, hand-auditable composite in roughly [-1, +1]."""
        return round(
            0.30 * self.trend_score
            + 0.25 * self.valuation_score
            + 0.20 * self.fundamental_score
            + 0.15 * self.catalyst_score
            - 0.10 * self.risk_score,
            4,
        )
