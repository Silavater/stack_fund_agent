# Taiwan retail persona taxonomy (closed set, N=20..50)

Each archetype carries stance / conviction / time_horizon / herding / polarity /
`base_weight` (crowd-influence weight, NOT investment weight; Σ=1) and **must**
ship with 3–5 citable behavioural priors before this layer is defensible as a
headline.

| archetype | 中文 | herding | polarity | base_weight | behavioural prior (cite before ship) |
|---|---|---|---|---|---|
| long_term_holder | 存股族 | 0.15 | contra | 0.16 | 0050/0056 long-hold + dividend reinvest |
| day_trader | 當沖客 | 0.85 | pro | 0.12 | TW day-trade share, stop-loss cascade |
| yield_seeker | 殖利率派 | 0.40 | pro | 0.14 | ex-dividend rotation sensitivity |
| leveraged_etf_player | 槓桿 ETF 玩家 | 0.70 | pro | 0.08 | 00631L-type forced unwind |
| foreign_institutional_lens | 外資視角 | 0.10 | contra | 0.12 | net foreign flow, index rebal |
| panic_retail | 恐慌散戶 | 0.90 | pro | 0.10 | chase-high / sell-low contrarian |
| ptt_dcard_trendwatch | PTT/Dcard 風向 | 0.95 | pro | 0.08 | narrative amplification, meme speed |
| mom_savings_group | 媽媽存股社團 | 0.35 | contra | 0.08 | DCA growth, sticky on drawdowns |
| main_force_lens | 主力/中實戶 | 0.20 | contra | 0.06 | margin balance, large-holder fade |
| dca_newbie | 定期定額新手 | 0.75 | pro | 0.06 | post-2023 accounts, recency bias |

Deliberately balanced: pro-cyclical amplifiers ≈ 0.56 vs contra-cyclical
stabilisers ≈ 0.44. `is_synthetic: true` is enforced; `base_weight` is isolated
from investment weight.

> **CREDIBILITY fix (must do before ship):** the "prior" column is currently
> placeholder description. Replace each with 3–5 real citations (TWSE retail
> structure stats, DCA account growth, etc.) or this non-backtestable layer
> cannot be defended as the headline.
