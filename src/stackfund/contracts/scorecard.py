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
    # Medium-term (full-series) momentum, complementing the short-window trend.
    # Defaulted so any caller predating slice-004 still constructs a valid card.
    momentum_slope_score: float = 0.0
    eligible: bool = True
    gate_reasons: tuple[str, ...] = field(default_factory=tuple)

    def composite(self) -> float:
        """Transparent, hand-auditable composite in roughly [-1, +1].

        Option-A weighting: the old 0.30 trend weight is split 0.20 trend +
        0.10 momentum_slope, so the medium-term trend gets a voice without
        overhauling the mix. All positive weights + catalyst still sum to 0.90,
        minus 0.10 risk (unchanged), matching the pre-slice-004 total.
        """
        return round(
            0.20 * self.trend_score
            + 0.10 * self.momentum_slope_score
            + 0.25 * self.valuation_score
            + 0.20 * self.fundamental_score
            + 0.15 * self.catalyst_score
            - 0.10 * self.risk_score,
            4,
        )
