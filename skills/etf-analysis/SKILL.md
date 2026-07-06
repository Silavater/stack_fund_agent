---
name: stackfund-etf-analysis
description: Research a Taiwan ETF (0050/0056/006208/00878/00919/00713/00929/00850) or build a rebalance plan. Computes a transparent scorecard + a hard-only plan with first-class NO_ACTION (and a worth-acting ranking) via the StackFund engine — the model interprets, never computes. Research/education only; places no securities order.
license: MIT
version: 0.4.0
metadata:
  hermes:
    tags: [ETF, Taiwan, TWSE, Yahoo, research, scorecard, deterministic, non-advisory]
    attribution: "design adapted from AZNitro/tw-stock-agent (MIT); see NOTICE"
---

# StackFund — ETF Analysis (deterministic ENGINE)

> **Tier A disclaimer (load banner):** 研究/教育·非預測·非個別化投資建議·**全程不下任何證券委託單**;所有金額與權重由 deterministic 程式計算。

A thin wrapper over the StackFund deterministic engine. The model **computes no
number** — it calls the CLI and interprets the output. Design docs adapted from
**AZNitro/tw-stock-agent** (MIT) — see [`NOTICE`](NOTICE).

## Quick start
```bash
# The full desk in one call: L1→L2 (eligibility + scorecard) → L4 (plan / NO_ACTION)
# → a worth-acting ranking → L5 ledgers. Omit --live for the frozen fixture.
python ${HERMES_SKILL_DIR}/scripts/research.py --symbols 0050 0056 00878
```
Each ETF returns `REBALANCE ±Xpp` **or** `NO_ACTION` with a reason code; the run
ends with a ranking of which ETFs are most worth acting on this cycle.

## Commands
| command | what it does |
|---|---|
| `research.py --symbols 0050 0056 …` | Run the full pipeline (score → plan → rank → ledgers). Add `--live` for real TWSE price/volume; `--json` for structured output. |
| `fetch.py --symbol 0050 [--live]` | Build/refresh one ETF's immutable `DataBook`. |
| `signals.py --symbol 0050` | Live market **context only** — institutional net-buy (T86), margin (MI_MARGN), news. Never a decision input; graceful on failure. |

## Reading the output
The engine gives you numbers; you turn them into plain language. **Invent no number.**

- **REBALANCE** — e.g. `0056 +5.00pp, target 37.4%, benefit 81bps vs cost 19bps`.
  Say: 引擎建議小幅加碼到約 37%,因為預期效益(81bps)明顯蓋過交易成本(19bps),不是追價。
- **NO_ACTION [EXPECTED_BENEFIT_BELOW_TRANSACTION_COST]** — the output now shows the
  gap, e.g. `15.8bps short of the 19.0bps cost threshold`. Say: 這週不動 0050 ——
  預期效益離手續費/稅的門檻還差 15.8bps,動了反而虧。**Lead with how close it was.**
- **NO_ACTION [WITHIN_TOLERANCE]** — the target barely moved; holding is correct.
- **NO_ACTION [INELIGIBLE, …]** — failed the L2 gate (e.g. `00631L` 2× leveraged →
  `LEVERAGED_OR_INVERSE`). Rejected before scoring, by design.
- **The ranking** — `net edge = benefit - cost`, sorted. One glance at "what's most
  worth acting on this run"; below-cost and ineligible rows sort last. It re-uses the
  engine's own numbers — it is a **view, never a new decision**.

## Worked example
**User:** 研究 0056,給再平衡決策
```bash
python ${HERMES_SKILL_DIR}/scripts/research.py --symbols 0050 0056 00878
```
The 0056 decision (excerpt): `REBALANCE +5.00pp, target 37.4%, benefit 81.0bps,
cost 19.0bps, reasons [valuation +0.30, yield +1.00, trend −0.10]`.
> 【結論】0056 偏正向,引擎建議**小幅加碼**到約 37% 權重。
> 【為什麼】估值與配息面偏好,且**預期效益明顯大於買賣成本**(不是追價)。
> 〔細節〕benefit 81bps vs cost 19bps;valuation +0.30 / yield +1.00 / trend −0.10。
> 群眾情境見 `stackfund-crowd-scenario`;**群眾僅供參考,不影響決策**。
> *研究/教育 · 非個別化建議 · 不下任何證券委託單。*

## Data & freshness rules
- **Official data is the anchor** — TWSE for price/volume; ETF yield/NAV/tracking-error
  are **reference/fixture** (the free TWSE feed excludes ETFs) — label them as such.
- **Always surface freshness** — state `as_of` and live-vs-frozen every reply. Live
  fetch fails/partial → fall back to the frozen `DataBook`, labelled `frozen`/`partial`.
  Never present stale data as live; never fabricate a missing fundamental.
- **Context ≠ decision** — chips/news from `signals.py` are colour only; the scorecard
  reads the `DataBook`, not those signals. Present them in a clearly separated block.

## Guardrails (summary)
The crowd-scenario layer is **not** in this skill's decision path — L4/L5 never
import it (import-linter + `tests/test_firewall_no_imports.py`). Engine artifacts
validate against committed JSON Schemas (`schemas/`), asserted in CI. `L4` consumes
only an `AuthoritativeState`, never a crowd input.

## Extending the universe
Adding an ETF is a **data change, not code**: create `fixtures/etf_<symbol>.json`
(copy an existing one) and add the symbol to `DEFAULT_SYMBOLS` in `cli.py` (or pass
`--symbols`). The eligibility gate decides — a leveraged/thin product is *supposed*
to return `INELIGIBLE`. Individual TW/US equities are a roadmap item behind the same
`DataBook → ScoreCard → plan` contracts (the L4 math is already instrument-agnostic).

## References
- `references/data-sources.md` — real connectors, source priority, ETF caveats.
- `references/scoring-rules.md` — transparent scorecard + decision formulas.
- `references/value-analysis.md` — value/moat framework + [A]–[E] durability rating.
- `references/output-schema.md` — report shapes.
