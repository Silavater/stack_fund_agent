"""L2: transparent, hand-auditable scorecard from observable DataBook metrics.

Formulas are intentionally derived from observable signals (R5 mitigation: the
conclusion is computed from inputs, not fed in). Placeholder weights — replace
with the finalised scoring-rules during the Day 3 build.
"""

from __future__ import annotations

from stackfund.contracts.databook import DataBook
from stackfund.contracts.scorecard import ScoreCard


def _clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def build_scorecard(book: DataBook) -> ScoreCard:
    m = book.metrics
    trend = _clip(m.get("price_5d_return", 0.0) / 5.0)
    valuation = _clip(-m.get("discount_premium", 0.0) / 2.0)  # at a discount -> cheaper -> +
    fundamental = _clip((m.get("yield", 0.0) - 4.0) / 4.0)
    catalyst = _clip(m.get("catalyst_strength", 0.0))
    risk = _clip(m.get("tracking_error", 0.0) / 2.0, 0.0, 1.0)
    return ScoreCard(
        scorecard_id=f"sc_{book.book_id}",
        databook_id=book.book_id,
        etf_symbol=book.etf_symbol,
        trend_score=round(trend, 4),
        fundamental_score=round(fundamental, 4),
        valuation_score=round(valuation, 4),
        catalyst_score=round(catalyst, 4),
        risk_score=round(risk, 4),
    )
