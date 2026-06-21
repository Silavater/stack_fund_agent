"""Compute crowd-vs-engine divergence at report time (no write-back)."""

from __future__ import annotations

from stackfund.contracts.crowd_narrative import CrowdNarrative
from stackfund.contracts.narrative_divergence import NarrativeDivergence
from stackfund.contracts.scorecard import ScoreCard

_ORDER = {"bearish": -1, "neutral": 0, "bullish": 1}
_BUCKETS = ("LOW", "MEDIUM", "HIGH")


def engine_posture(scorecard: ScoreCard) -> str:
    c = scorecard.composite()
    if c > 0.1:
        return "bullish"
    if c < -0.1:
        return "bearish"
    return "neutral"


def compose_divergence(narrative: CrowdNarrative, scorecard: ScoreCard) -> NarrativeDivergence:
    engine = engine_posture(scorecard)
    gap = abs(_ORDER[narrative.crowd_consensus] - _ORDER[engine])  # 0 | 1 | 2
    return NarrativeDivergence(
        seed_id=narrative.seed_id,
        crowd_consensus=narrative.crowd_consensus,
        engine_posture=engine,
        divergence_bucket=_BUCKETS[gap],
        narrative_intensity=gap + 1,
    )
