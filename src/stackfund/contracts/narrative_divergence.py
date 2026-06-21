"""Report-time FACE artifact: crowd-vs-engine divergence (categorical, bounded).

Deliberately replaces ``contrarian_modifier ∈ [-1,+1]``. There is **no additive
scalar** anything could silently wire into a sort — only a bucket and two
categorical postures. Produced by the Report Composer (which reads the L6
authoritative snapshot + the crowd narrative); never produced inside the engine,
never consumed by L4/L5.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DIVERGENCE_BUCKETS = ("LOW", "MEDIUM", "HIGH")
POSTURES = ("bearish", "neutral", "bullish")


@dataclass(frozen=True)
class NarrativeDivergence:
    seed_id: str
    crowd_consensus: str  # bearish | neutral | bullish
    engine_posture: str  # bearish | neutral | bullish
    divergence_bucket: str  # LOW | MEDIUM | HIGH
    narrative_intensity: int  # 1 | 2 | 3
    non_authoritative: bool = True
    synthetic_population: bool = True
    artifact_type: str = "NarrativeDivergence"
    storylines: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        assert self.crowd_consensus in POSTURES, "crowd_consensus out of vocabulary"
        assert self.engine_posture in POSTURES, "engine_posture out of vocabulary"
        assert self.divergence_bucket in DIVERGENCE_BUCKETS, "bad divergence_bucket"
        assert self.narrative_intensity in (1, 2, 3), "narrative_intensity 1|2|3"
        assert self.non_authoritative is True, "divergence artifact must be non-authoritative"
