---
name: stackfund-etf-analysis
description: Produce deterministic Taiwan ETF research — fetch official TWSE price/volume (live or frozen), compute a transparent scorecard, and a hard-only rebalance plan with NO_ACTION support — by calling the StackFund engine. Use when researching 0050/0056/00878 or building an ETF scorecard or rebalance plan. All numbers are computed in Python; the model only interprets and writes prose. Research/education only — not individualised investment advice, and it never places any securities order.
license: MIT
version: 0.2.0
metadata:
  hermes:
    tags: [ETF, Taiwan, TWSE, Yahoo, research, scorecard, deterministic, non-advisory]
    attribution: "design adapted from AZNitro/tw-stock-agent (MIT); see NOTICE"
---

# StackFund — ETF Analysis (deterministic ENGINE)

> **Tier A disclaimer (load banner):** 研究/教育·非預測·非個別化投資建議·**全程不下任何證券委託單**;所有金額與權重由 deterministic 程式計算。
>
> Design & reference docs adapted from **AZNitro/tw-stock-agent** (MIT) — see [`NOTICE`](NOTICE). Its placeholder fetchers are **completed** here as real TWSE/Yahoo connectors.

This skill is a thin wrapper over the StackFund deterministic engine. The model
**does not compute any number** — it calls the CLI and interprets the output.

## Core principles (adapted from tw-stock-agent)
1. **Official data is the anchor** — prefer TWSE for price/volume/structure.
2. **Yahoo is a narrative/expectation layer** — a quote cross-check, not truth.
3. **News is catalyst context, not truth by default.**
4. **Contrarian sentiment is auxiliary** — in StackFund it is the L3 crowd
   side-rail, *non-authoritative* and firewalled out of the decision (see the
   `stackfund-crowd-scenario` skill). It must never override hard data.
5. **Separate observation from interpretation** — report what was observed first.

## Workflow
1. **Normalize** the request: ticker(s) (e.g. `0050`, `0056`, `00878`), horizon, output type.
2. **Collect official data first** (live or frozen):
   ```bash
   python ${HERMES_SKILL_DIR}/scripts/fetch.py --symbol 0050 --live   # TWSE STOCK_DAY_ALL
   ```
   This builds an immutable `DataBook` (price/volume from TWSE; ETF fundamentals
   — yield/NAV/tracking error — carried from the fundamentals source, see
   `references/data-sources.md`). Omit `--live` for the frozen fixture.
3. **Score + decide** (deterministic):
   ```bash
   python ${HERMES_SKILL_DIR}/scripts/research.py --symbols 0050 0056 00878
   ```
   Runs L1 → L2 (eligibility gate + scorecard) → L4 (hard-only plan on
   `AuthoritativeState`; `NO_ACTION` is first-class with `reason_codes`, incl.
   `EXPECTED_BENEFIT_BELOW_TRANSACTION_COST`) → L5/L6 (earn/spend + P&L).
4. **Deep value mode (optional)** — for "long-term value / moat" requests, follow
   `references/value-analysis.md` (Porter / moat / TOWS) and the **[A]–[E]** rating.

## Contract & firewall
- Output validates against `schemas/rebalance_plan.schema.json` /
  `schemas/etf_research_report.schema.json`.
- The crowd-scenario layer is **not** part of this skill's decision path (L4/L5
  never import it — enforced by `import-linter` + tests).

## References
- `references/data-sources.md` — real connectors + source priority + ETF caveats.
- `references/scoring-rules.md` — transparent scorecard formulas.
- `references/output-schema.md` — report shapes.
- `references/value-analysis.md` — value-investing / moat framework + [A]–[E] rating.

## Output expectations
Facts first, interpretation second. Cite sources, label freshness, state missing
data explicitly. Use cautious, decision-support wording (e.g. 「偏多,但估值偏高,
追價風險上升」); avoid absolute buy/sell language; never imply an order was placed.
