"""L2 output contract: the authoritative deterministic scorecard.

Part of the L4 input bundle (AuthoritativeState). Carries an eligibility flag —
only ETFs that pass the L2 gate get a usable score.
"""

from __future__ import annotations

from dataclasses import dataclass, field


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
    eligible: bool = True
    gate_reasons: tuple[str, ...] = field(default_factory=tuple)

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
