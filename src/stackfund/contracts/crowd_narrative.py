"""Write-side firewall contract: the ONLY thing L3 (crowd) may emit.

Replaces the old ``ContrarianSignal``. Crucially there is **no numeric scalar
modifier** — its very shape invited "just add 0.05" architecture rot. L3 emits a
categorical crowd stance + narrative only. The crowd-vs-engine *divergence* is
computed later, at report-composition time (see ``stackfund.report``), because
L3 is firewalled from the engine's ScoreCard and cannot know the engine posture.
"""

from __future__ import annotations

from dataclasses import dataclass, field

CONSENSUS = ("bearish", "neutral", "bullish")


@dataclass(frozen=True)
class PersonaReaction:
    archetype_id: str
    stance: int  # -1 (contra) | 0 (neutral) | +1 (pro)
    register: str
    excerpt: str
    is_synthetic: bool = True


@dataclass(frozen=True)
class CrowdNarrative:
    seed_id: str
    rng_seed: int
    n_personas: int  # 0 (dry stub) or 20..50
    crowd_consensus: str  # bearish | neutral | bullish (NO numeric modifier)
    narrative_md: str
    persona_samples: tuple[PersonaReaction, ...] = field(default_factory=tuple)
    synthetic_population: bool = True
    non_authoritative: bool = True  # HARD-WIRED True
    artifact_type: str = "CrowdNarrative"

    def __post_init__(self) -> None:
        assert self.crowd_consensus in CONSENSUS, "crowd_consensus out of vocabulary"
        assert self.n_personas == 0 or 20 <= self.n_personas <= 50, "n_personas 0 or 20..50"
        assert self.non_authoritative is True, "crowd narrative must be non-authoritative"
