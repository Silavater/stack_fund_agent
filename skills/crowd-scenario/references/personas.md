# Taiwan retail persona taxonomy (closed set, N=20..50)

**Status: all 10 archetypes are implemented in the engine** (`_ARCHETYPES` in
`src/stackfund/l3_crowd/engine.py`, one-to-one with this table; hash pinned in
`seed.lock.json`). Each archetype carries stance / conviction / time_horizon /
herding / polarity / `base_weight` (crowd-influence weight, NOT investment
weight; Σ=1).

| archetype | 中文 | herding | polarity | base_weight | behavioural-prior source (verify numbers before citing) |
|---|---|---|---|---|---|
| long_term_holder | 存股族 | 0.15 | contra | 0.16 | TDCC (集保結算所) beneficial-owner counts for 0050/0056 — long-hold + dividend-reinvest structure |
| day_trader | 當沖客 | 0.85 | pro | 0.12 | TWSE day-trading statistics (當沖交易統計) — day-trade share of turnover; stop-loss cascades |
| yield_seeker | 殖利率派 | 0.40 | pro | 0.14 | TWSE ex-dividend calendar + fund-flow around distribution announcements |
| leveraged_etf_player | 槓桿 ETF 玩家 | 0.70 | pro | 0.08 | Daily-reset decay + volume spikes in 00631L-type products under volatility (issuer prospectus + TWSE volume) |
| foreign_institutional_lens | 外資視角 | 0.10 | contra | 0.12 | TWSE three-institutional-investors daily net buy/sell (三大法人); MSCI/FTSE index-review flows |
| panic_retail | 恐慌散戶 | 0.90 | pro | 0.10 | Margin-balance swings (TWSE MI_MARGN) as a chase-high/sell-low contrarian proxy |
| ptt_dcard_trendwatch | PTT/Dcard 風向 | 0.95 | pro | 0.08 | Post-volume/keyword spikes on PTT Stock board & Dcard around ETF events (narrative amplification) |
| mom_savings_group | 媽媽存股社團 | 0.35 | contra | 0.08 | TDCC regular-savings-plan (定期定額) account growth — sticky on drawdowns |
| main_force_lens | 主力/中實戶 | 0.20 | contra | 0.06 | TWSE margin/short balances + large-holder concentration (TDCC share-dispersion table) |
| dca_newbie | 定期定額新手 | 0.75 | pro | 0.06 | Broker + TDCC new-account and DCA-plan growth post-2023; recency bias |

Deliberately balanced: pro-cyclical amplifiers ≈ 0.56 vs contra-cyclical
stabilisers ≈ 0.44. `is_synthetic: true` is enforced; `base_weight` is isolated
from investment weight. In the engine, `polarity` is what runs today: `contra`
archetypes fade the seed-driven consensus, `pro` archetypes amplify it
(`_CONTRA` in `engine.py`); the finer attributes are authoring guidance for the
LLM persona-text layer.

> **Credibility note:** the source column names *where* each prior is verifiable
> (TDCC / TWSE / issuer disclosures) — pull the current numbers from those
> sources before citing any figure in a published report. Synthetic personas
> remain **scenario rehearsal, not survey data**: reproducible ≠ validated.

## Extending to another market (roadmap — e.g. US equities)

The roster is **market-scoped**. To add a market, ship a *sibling closed set*
(e.g. `personas.us.md` + a new `_ARCHETYPES_US` tuple + its own
`seed.lock` entry) — do **not** mix markets in one roster. A US set would swap
the archetypes (e.g. 401(k) DCA flows, index-fund passive share, options/0DTE
crowd, r/wallstreetbets-style narrative amplification, buyback/institutional
lens) while keeping everything else identical: the same closed-vocab stance
tokens, the same frozen-`ScenarioSeed` input, the same `CrowdNarrative` schema,
and the same firewall (non-authoritative, zero write-back). **The firewall
contract is market-independent — new market, same cage.**
