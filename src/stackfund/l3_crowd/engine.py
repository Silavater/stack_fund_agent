"""L3: the Crowd Scenario Engine (FACE / headline) — narrative side-rail.

Reads ONLY a frozen ScenarioSeed; emits ONLY a ``CrowdNarrative`` (a categorical
crowd stance + narrative — NO numeric modifier). It must never import
L1/L2/L4/L5 compute. The crowd-vs-engine *divergence* is computed later by the
Report Composer, because L3 is firewalled from the engine's ScoreCard.
"""

from __future__ import annotations

import hashlib

from stackfund.contracts.crowd_narrative import CrowdNarrative, PersonaReaction
from stackfund.contracts.scenario_seed import ScenarioSeed

_ARCHETYPES = (
    "long_term_holder",
    "day_trader",
    "yield_seeker",
    "panic_retail",
    "foreign_institutional_lens",
)
_CONTRA = ("long_term_holder", "foreign_institutional_lens")


def _internal_view(seed: ScenarioSeed) -> float:
    """Deterministic, reproducible crowd lean in [-1, +1] (internal only)."""
    digest = hashlib.sha256(seed.seed_hash.encode("utf-8")).hexdigest()
    return round((int(digest[:8], 16) / 0xFFFFFFFF) * 2 - 1, 4)


def _consensus(view: float) -> str:
    if view > 0.15:
        return "bullish"
    if view < -0.15:
        return "bearish"
    return "neutral"


def _stance_for(archetype: str, consensus: str) -> int:
    if consensus == "neutral":
        return 0
    pro = 1 if consensus == "bullish" else -1
    return -pro if archetype in _CONTRA else pro


def run_scenario(seed: ScenarioSeed, n_personas: int = 30, dry_run: bool = True) -> CrowdNarrative:
    consensus = _consensus(_internal_view(seed))
    samples = tuple(
        PersonaReaction(
            archetype_id=a,
            stance=_stance_for(a, consensus),
            register="zh-TW",
            excerpt=f"[synthetic|{a}] 對「{seed.market_scenario_label}」的條件式情境反應(非預測)。",
        )
        for a in _ARCHETYPES
    )
    narrative = (
        f"## 群眾情境推演:{seed.market_scenario_label}\n\n"
        "*合成人格情境分布,不代表真實市場調查;非預測;未經回測。*\n\n"
        f"合成群眾傾向:**{consensus}**。各型態散戶**可能**形成二階反應鏈(條件式)。\n\n"
        "> 本側軌只產敘事,不決定任何數字、不回寫決策層。"
    )
    if not dry_run:
        # A live run substitutes LLM-written persona text here; the categorical
        # consensus above is unchanged. (Not wired in the MVP.)
        narrative += "\n\n<!-- live persona text substituted here -->"
    return CrowdNarrative(
        seed_id=seed.seed_id,
        rng_seed=seed.rng_seed,
        n_personas=n_personas,
        crowd_consensus=consensus,
        narrative_md=narrative,
        persona_samples=samples,
    )
