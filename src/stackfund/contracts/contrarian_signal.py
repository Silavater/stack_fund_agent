"""Write-side firewall contract: the ONLY thing L3 (crowd) is allowed to emit.

By type this object cannot carry price / nav / discount_premium / yield /
weight / cap fields — so it can never return an authoritative number. It is
hard-wired non-authoritative and is consumed only by the Pro report and the L6
audit log; the L4 decision path never imports it (enforced by import-linter).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class PersonaReaction:
    archetype_id: str
    stance: int  # -1 (contra) | 0 (neutral) | +1 (pro)
    register: str
    excerpt: str
    is_synthetic: bool = True


@dataclass(frozen=True)
class ContrarianSignal:
    seed_id: str
    rng_seed: int
    n_personas: int  # 0 (dry stub) or 20..50
    contrarian_modifier: float  # in [-1, +1]
    narrative_md: str
    persona_samples: tuple[PersonaReaction, ...] = field(default_factory=tuple)
    formula_id: str = "contrarian-agg/1.0.0"
    is_authoritative: bool = False  # HARD-WIRED False

    def __post_init__(self) -> None:
        assert -1.0 <= self.contrarian_modifier <= 1.0, "modifier out of [-1, +1]"
        assert self.n_personas == 0 or 20 <= self.n_personas <= 50, "n_personas must be 0 or 20..50"
        # The wheel is never locked to the facade.
        assert self.is_authoritative is False, "ContrarianSignal must never be authoritative"
