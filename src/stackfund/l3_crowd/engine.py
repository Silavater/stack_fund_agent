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

# The full closed-set Taiwan-retail roster — one-to-one with the taxonomy in
# skills/crowd-scenario/references/personas.md (10 archetypes; the consensus label
# itself is seed-driven, so roster size never moves a decision or a demo number).
_ARCHETYPES = (
    "long_term_holder",
    "day_trader",
    "yield_seeker",
    "leveraged_etf_player",
    "foreign_institutional_lens",
    "panic_retail",
    "ptt_dcard_trendwatch",
    "mom_savings_group",
    "main_force_lens",
    "dca_newbie",
)
# Contra-cyclical stabilisers (fade the consensus); the rest are pro-cyclical amplifiers.
_CONTRA = (
    "long_term_holder",
    "foreign_institutional_lens",
    "mom_savings_group",
    "main_force_lens",
)

# Per-archetype herding speed (0..1) — how fast this cohort reacts to a move.
# Mirrors the `herding` column in skills/crowd-scenario/references/personas.md.
# Used only to ORDER the narrative reaction chain (who moves first → who follows
# → who sits still). It is NOT a numeric modifier on any decision or on the
# categorical stance; the CrowdNarrative it feeds carries no scalar.
_HERDING = {
    "long_term_holder": 0.15,
    "day_trader": 0.85,
    "yield_seeker": 0.40,
    "leveraged_etf_player": 0.70,
    "foreign_institutional_lens": 0.10,
    "panic_retail": 0.90,
    "ptt_dcard_trendwatch": 0.95,
    "mom_savings_group": 0.35,
    "main_force_lens": 0.20,
    "dca_newbie": 0.75,
}

# Each archetype speaks in its own register. The template is chosen by the
# persona's own stance (pro / neutral / contra) so the same cohort says
# different things in a bullish vs bearish scenario — but it stays deterministic
# and reads ONLY the frozen ordinal context, never a raw number.
_ARCHETYPE_VOICE = {
    "long_term_holder": {
        1: "續抱不動,反而想趁機加碼撿便宜,股息照領。",
        0: "無所謂短線,部位不動,繼續存。",
        -1: "帳面回檔但不賣,長期持有本來就要耐震。",
    },
    "day_trader": {
        1: "順勢做多、跟動能,但停損設很緊,隔日沖不留倉。",
        0: "區間震盪不好做,先觀望減少進出。",
        -1: "轉空單或空手,破前低就跑,絕不凹單。",
    },
    "yield_seeker": {
        1: "殖利率誘人,除息前想卡位領息、賭填息。",
        0: "配息看得順眼才動,現在再等等看。",
        -1: "擔心貼息與配息縮水,先減碼避風頭。",
    },
    "leveraged_etf_player": {
        1: "波動就是機會,加槓桿做多、放大部位。",
        0: "盤整最傷槓桿(每日重設耗損),暫時退場。",
        -1: "怕連續下跌被複利吃掉,快速停損出場。",
    },
    "foreign_institutional_lens": {
        1: "看基本面與指數權重,逢低分批布局。",
        0: "等法說會與數據,按兵不動。",
        -1: "調節部位、對沖風險,不追殺也不接刀。",
    },
    "panic_retail": {
        1: "看到大家在買、怕錯過,追高進場。",
        0: "看不懂方向,先抱著不動。",
        -1: "看到黑K就恐慌,殺在最低點。",
    },
    "ptt_dcard_trendwatch": {
        1: "看板風向轉多,發文喊進、氣氛熱絡。",
        0: "討論度冷清,沒什麼人在推。",
        -1: "看板一片哀嚎,風向轉空、互相勸退。",
    },
    "mom_savings_group": {
        1: "群組互相打氣,續扣定期定額還加碼。",
        0: "照計畫定期定額,不看盤不改單。",
        -1: "越跌越買、當作打折,扣款照舊不停扣。",
    },
    "main_force_lens": {
        1: "低調吸籌、分批進場,不驚動散戶。",
        0: "量能不足,按兵不動觀察籌碼。",
        -1: "趁人氣高出貨、調節持股,先落袋。",
    },
    "dca_newbie": {
        1: "剛開始扣款、興奮加碼,近因偏誤明顯。",
        0: "小額試單,還在學怎麼看。",
        -1: "第一次遇到回檔就緊張,考慮暫停扣款。",
    },
}


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


# How strongly each archetype's own read of the ordinal context can override the
# baseline consensus lean. Ordinal buckets map to a small ordinal tilt in [-1, +1];
# each archetype weights the two context axes (discount_premium, yield) differently,
# so within ONE scenario they no longer all flip together. This is a categorical
# stance driver only — the emitted stance stays -1|0|1 (no numeric scalar leaves L3).
_DISCOUNT_TILT = {
    "deep_discount": 1.0,
    "discount": 0.5,
    "fair": 0.0,
    "premium": -0.5,
    "rich": -1.0,
}
_YIELD_TILT = {"low": -1.0, "normal": 0.0, "high": 1.0}

# Per-archetype sensitivity to (discount_premium, yield). A value-driven cohort
# leans on cheapness; a yield cohort leans on distribution; momentum/herd cohorts
# barely read fundamentals at all and mostly ride the consensus.
_ARCHETYPE_SENSITIVITY = {
    "long_term_holder": (0.8, 0.4),  # buys value, likes yield
    "day_trader": (0.0, 0.0),  # pure momentum — rides consensus
    "yield_seeker": (0.2, 1.0),  # distribution-driven
    "leveraged_etf_player": (0.0, 0.0),  # volatility/momentum
    "foreign_institutional_lens": (0.7, 0.2),  # valuation lens
    "panic_retail": (0.0, 0.0),  # emotion — rides consensus
    "ptt_dcard_trendwatch": (0.0, 0.0),  # narrative amplifier
    "mom_savings_group": (0.6, 0.5),  # cheap + income, sticky
    "main_force_lens": (0.9, 0.1),  # accumulates on weakness
    "dca_newbie": (0.1, 0.1),  # recency bias, weak fundamentals read
}


def _stance_for(archetype: str, consensus: str, ordinal: dict[str, str] | None = None) -> int:
    """This archetype's categorical stance (-1|0|1).

    Baseline lean comes from the seed-derived consensus (a contra archetype fades it,
    a pro archetype amplifies it). Each archetype then applies its OWN reading of the
    frozen ordinal context (cheapness + yield) weighted by its sensitivity, so within
    one scenario cohorts diverge instead of flipping in lockstep. Deterministic and
    scalar-free: the internal lean is thresholded back to -1|0|1 before it leaves L3.
    """
    base = 0.0 if consensus == "neutral" else (1.0 if consensus == "bullish" else -1.0)
    if archetype not in _CONTRA:
        lean = base
    else:
        lean = -base

    if ordinal:
        w_disc, w_yield = _ARCHETYPE_SENSITIVITY.get(archetype, (0.0, 0.0))
        tilt = w_disc * _DISCOUNT_TILT.get(ordinal.get("discount_premium", "fair"), 0.0)
        tilt += w_yield * _YIELD_TILT.get(ordinal.get("yield", "normal"), 0.0)
        # A fundamentals-driven cohort can resist (even reverse) a mild consensus;
        # a momentum/herd cohort (sensitivity 0) is unmoved and rides the consensus.
        lean += 0.9 * tilt

    if lean > 0.15:
        return 1
    if lean < -0.15:
        return -1
    return 0


# Display names for the reaction chain (one-to-one with personas.md 中文欄).
_ZH_NAME = {
    "long_term_holder": "存股族",
    "day_trader": "當沖客",
    "yield_seeker": "殖利率派",
    "leveraged_etf_player": "槓桿 ETF 玩家",
    "foreign_institutional_lens": "外資視角",
    "panic_retail": "恐慌散戶",
    "ptt_dcard_trendwatch": "PTT/Dcard 風向",
    "mom_savings_group": "媽媽存股社團",
    "main_force_lens": "主力/中實戶",
    "dca_newbie": "定期定額新手",
}


def _excerpt_for(archetype: str, stance: int, label: str) -> str:
    """This archetype's own line for its stance under the scenario `label`."""
    voice = _ARCHETYPE_VOICE.get(archetype, {}).get(stance, "條件式情境反應。")
    return f"[synthetic|{archetype}] 對「{label}」:{voice}(非預測)"


# Horizon shifts WHO leads the chain: an intraday shock is dominated by the fastest
# herders; a long-horizon rehearsal foregrounds the slow fundamentals cohorts. We
# express this as a herding-speed bias applied to the ordering (categorical framing,
# no numeric scalar leaves L3).
_HORIZON_LEAD = {
    "intraday": 1.0,  # fastest cohorts lead hardest
    "swing": 0.0,  # neutral: pure herding order
    "long": -1.0,  # slow / fundamentals cohorts lead
}
_HORIZON_FRAME = {
    "intraday": "當日盤中",
    "swing": "波段",
    "long": "長線",
}


def _reaction_chain(samples: tuple[PersonaReaction, ...], seed: ScenarioSeed) -> str:
    """A 2-3 step who-moves-first storyline, ordered by herding speed and horizon.

    Horizon re-weights the ordering (intraday → fastest herders lead; long → slow
    fundamentals cohorts lead). Intensity widens the framing (severe → note the tail
    also capitulates). Pure narrative — no number is produced or consumed.
    """
    movers = [s for s in samples if s.stance != 0]
    frame = _HORIZON_FRAME.get(seed.horizon, "波段")
    if not movers:
        return f"- 在{frame}情境下各型態普遍無感,無明顯二階反應鏈(情境偏中性)。"
    bias = _HORIZON_LEAD.get(seed.horizon, 0.0)
    # bias > 0: fast cohorts lead (descending herding). bias < 0: slow cohorts lead.
    movers.sort(key=lambda s: _HERDING.get(s.archetype_id, 0.5), reverse=bias >= 0)
    anchors = [s for s in samples if s.stance == 0]
    severe = seed.intensity == "severe"

    def _line(n: int, s: PersonaReaction, verb: str) -> str:
        name = _ZH_NAME.get(s.archetype_id, s.archetype_id)
        return f"{n}. **{name}** {verb} —— {_ARCHETYPE_VOICE[s.archetype_id][s.stance]}"

    steps = [_line(1, movers[0], f"在{frame}情境最先動作")]
    if len(movers) > 1:
        steps.append(_line(2, movers[1], "跟進"))
    tail = anchors[0] if anchors else movers[-1]
    tail_verb = (
        "最終也跟隨"
        if (severe and tail.stance != 0)
        else ("不為所動" if tail.stance == 0 else "最後才反應")
    )
    steps.append(_line(3, tail, tail_verb))
    return "\n".join(steps)


def run_scenario(seed: ScenarioSeed, n_personas: int = 30, dry_run: bool = True) -> CrowdNarrative:
    consensus = _consensus(_internal_view(seed))
    label = seed.market_scenario_label
    ordinal = seed.ordinal_context
    samples = tuple(
        PersonaReaction(
            archetype_id=a,
            stance=_stance_for(a, consensus, ordinal),
            register="zh-TW",
            excerpt=_excerpt_for(a, _stance_for(a, consensus, ordinal), label),
        )
        for a in _ARCHETYPES
    )
    chain = _reaction_chain(samples, seed)
    frame = _HORIZON_FRAME.get(seed.horizon, "波段")
    intensity_zh = "劇烈" if seed.intensity == "severe" else "溫和"
    narrative = (
        f"## 群眾情境推演:{label}(時間尺度:{frame}·強度:{intensity_zh})\n\n"
        "*合成人格情境分布,不代表真實市場調查;非預測;未經回測。*\n\n"
        f"合成群眾傾向:**{consensus}**。以下為各型態散戶的二階反應鏈(依{frame}情境的跟風順序,條件式):\n\n"
        f"{chain}\n\n"
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
