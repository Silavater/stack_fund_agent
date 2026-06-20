"""L3: the Crowd Scenario Engine (FACE / headline) — narrative side-rail.

It reads ONLY a frozen ScenarioSeed and emits ONLY a ContrarianSignal. It must
never import L1/L2/L4/L5 compute (enforced by import-linter). In the MVP the
aggregation is a deterministic Python stub; a live run would call the LLM once
per sampled persona to write reaction *text* only — the modifier is always
computed in Python, never by the model.
"""

from __future__ import annotations

import hashlib

from stackfund.contracts.contrarian_signal import ContrarianSignal, PersonaReaction
from stackfund.contracts.scenario_seed import ScenarioSeed

# Closed-set archetype sample (full taxonomy lives in the skill's personas.md).
_ARCHETYPES = (
    "long_term_holder",
    "day_trader",
    "yield_seeker",
    "panic_retail",
    "foreign_institutional_lens",
)
_CONTRA = ("long_term_holder", "foreign_institutional_lens")


def _deterministic_modifier(seed: ScenarioSeed) -> float:
    """Map the seed hash to a bounded, fully reproducible modifier in [-1, +1]."""
    digest = hashlib.sha256(seed.seed_hash.encode("utf-8")).hexdigest()
    return round((int(digest[:8], 16) / 0xFFFFFFFF) * 2 - 1, 4)


def _stance_for(archetype: str, modifier: float) -> int:
    if modifier > 0.15:
        return -1 if archetype in _CONTRA else 1
    if modifier < -0.15:
        return 1 if archetype in _CONTRA else -1
    return 0


def run_scenario(
    seed: ScenarioSeed, n_personas: int = 30, dry_run: bool = True
) -> ContrarianSignal:
    modifier = _deterministic_modifier(seed)
    samples = tuple(
        PersonaReaction(
            archetype_id=a,
            stance=_stance_for(a, modifier),
            register="zh-TW",
            excerpt=(
                f"[synthetic|{a}] 對「{seed.market_scenario_label}」的條件式情境反應(非預測)。"
            ),
        )
        for a in _ARCHETYPES
    )
    interp = (
        "fade_overbought" if modifier > 0.15 else "fade_oversold" if modifier < -0.15 else "no_tilt"
    )
    narrative = (
        f"## 群眾情境推演:{seed.market_scenario_label}\n\n"
        "*情境推演,非預測;合成人格,非真實民意;未經回測。*\n\n"
        "在此情境下,各型態散戶**可能**形成二階反應鏈(條件式)。"
        f"非權威 contrarian_modifier = {modifier:+.2f} ({interp})。\n\n"
        "> 此標註不影響本報告之 deterministic 配置結論。"
    )
    if not dry_run:
        # A live run substitutes LLM-written persona reaction text here; the
        # deterministic modifier above is unchanged. (Not wired in the MVP.)
        narrative += "\n\n<!-- live narrative substituted here -->"
    return ContrarianSignal(
        seed_id=seed.seed_id,
        rng_seed=seed.rng_seed,
        n_personas=n_personas,
        contrarian_modifier=modifier,
        narrative_md=narrative,
        persona_samples=samples,
    )
