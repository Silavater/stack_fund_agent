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
- The engine's artifacts validate against committed JSON Schemas in `schemas/`
  (`rebalance_plan`, `etf_research_report`, …); `tests/test_schema_validation.py`
  asserts conformance, and `STACKFUND_SCHEMA_DIR` locates them at runtime.
- The crowd-scenario layer is **not** part of this skill's decision path (L4/L5
  never import it — enforced by `import-linter` + tests).

## Worked example
**User:** 研究 0056,給再平衡決策

1. `python ${HERMES_SKILL_DIR}/scripts/fetch.py --symbol 0056 --live` → immutable `DataBook`.
2. `python ${HERMES_SKILL_DIR}/scripts/research.py --symbols 0050 0056 00878` → the engine
   computes every number (its artifacts are schema-checked in CI). The 0056 decision (excerpt):
   ```json
   {"symbol": "0056", "action": "REBALANCE", "delta_pp": 5.0, "target_weight_pct": 37.4,
    "benefit_bps": 81.0, "cost_bps": 19.0,
    "reasons": ["valuation +0.30", "yield/fundamental +1.00", "trend -0.10"],
    "crowd_consensus": "neutral", "engine_posture": "bullish", "divergence_bucket": "MEDIUM"}
   ```
3. **Interpret — invent no number; plain language first, jargon in a separate detail block:**
   > 【結論】0056 偏正向,引擎在這個研究情境下建議**小幅加碼**到約 37% 權重。
   > 【為什麼】估值與配息面偏好,而且**預期效益明顯大於買賣成本**(不是追價)。
   > 〔細節〕REBALANCE +5.00pp → 目標 37.4%;benefit 81bps(約每投入 1 萬多 ~81 元預期效益)
   > > cost 19bps;reason codes valuation +0.30 / yield +1.00 / trend −0.10。群眾 neutral、
   > 引擎 bullish、分歧 MEDIUM —— 群眾僅供參考,不影響決策。
   > *研究/教育 · 非個別化建議 · 不下任何證券委託單。*

   For a `NO_ACTION` (e.g. 0050 `EXPECTED_BENEFIT_BELOW_TRANSACTION_COST`): lead with
   「這週不動 0050 —— 預期效益還蓋不過手續費/稅,動了反而虧」, then the bps detail.

## References
- `references/data-sources.md` — real connectors + source priority + ETF caveats.
- `references/scoring-rules.md` — transparent scorecard formulas.
- `references/output-schema.md` — report shapes.
- `references/value-analysis.md` — value-investing / moat framework + [A]–[E] rating.

## Output expectations
Facts first, interpretation second. Cite sources, label freshness, state missing
data explicitly. Use cautious, decision-support wording (e.g. 「偏多,但估值偏高,
追價風險上升」); avoid absolute buy/sell language; never imply an order was placed.
