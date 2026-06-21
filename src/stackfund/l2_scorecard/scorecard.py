"""L2: eligibility gate THEN transparent scorecard.

Gate first (stale / insufficient history / leveraged-inverse / NAV-incomparable /
low volume), score second — so ineligible ETFs never receive a misleading score.
Formulas are derived from observable DataBook metrics (R5: computed, not fed).
"""

from __future__ import annotations

from stackfund.contracts.databook import DataBook
from stackfund.contracts.scorecard import ScoreCard

MIN_HISTORY_DAYS = 60
MIN_AVG_VOLUME_LOTS = 1000


def eligibility_gate(book: DataBook) -> tuple[bool, tuple[str, ...]]:
    """Return (eligible, reason_codes). Reasons are empty when eligible."""
    reasons: list[str] = []
    m = book.metrics
    if book.freshness not in ("fresh", "frozen"):
        reasons.append("STALE_OR_MISSING")
    if m.get("leveraged_or_inverse", 0.0) >= 1.0:
        reasons.append("LEVERAGED_OR_INVERSE")
    if m.get("history_days", MIN_HISTORY_DAYS) < MIN_HISTORY_DAYS:
        reasons.append("INSUFFICIENT_HISTORY")
    if m.get("avg_volume_lots", MIN_AVG_VOLUME_LOTS) < MIN_AVG_VOLUME_LOTS:
        reasons.append("VOLUME_TOO_LOW")
    if m.get("nav_comparable", 1.0) < 1.0:
        reasons.append("NAV_NOT_COMPARABLE")
    return (len(reasons) == 0, tuple(reasons))


def _clip(x: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def build_scorecard(book: DataBook) -> ScoreCard:
    eligible, gate_reasons = eligibility_gate(book)
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
        eligible=eligible,
        gate_reasons=gate_reasons,
    )
