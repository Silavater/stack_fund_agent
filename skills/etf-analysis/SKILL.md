---
name: stackfund-etf-analysis
description: Produce deterministic Taiwan ETF research (price, NAV, discount/premium, tracking error, yield) and a hard-only rebalance plan with NO_ACTION support by calling the StackFund engine. Use when researching 0050/0056/00878 or building an ETF scorecard or rebalance plan. All numbers are computed in Python; the model only interprets and writes prose. Research/education only — not individualised investment advice, and it never places any securities order.
license: MIT
version: 0.1.0
metadata:
  hermes:
    tags: [ETF, Taiwan, TWSE, research, scorecard, deterministic, non-advisory]
---

# StackFund — ETF Analysis (deterministic ENGINE)

> **Tier A disclaimer (load banner):** 情境推演/研究·非預測·非個別化投資建議·不下任何證券委託單;所有金額與權重由 deterministic 程式計算。

This skill is a thin wrapper over the StackFund deterministic engine. The LLM
**does not compute any number** — it calls the CLI and interprets the output.

## When to use
- Build a daily number card or scorecard for 0050 / 0056 / 00878.
- Produce a hard-only `RebalancePlan` (or a justified `NO_ACTION`).

## How to run
```bash
python ${HERMES_SKILL_DIR}/scripts/research.py --symbols 0050 0056 00878
```
This runs L1 (data book) → L2 (scorecard) → L4 (hard-only plan) → L5/L6
(earn/spend + P&L). Every non-zero weight delta carries ≥ 2 independent
hard-data reasons; `NO_ACTION` is a first-class output.

## Contract
- Output validates against `schemas/rebalance_plan.schema.json` and
  `schemas/etf_research_report.schema.json`.
- The crowd-scenario layer is **not** part of this skill's decision path.

## References
- `references/data-sources.md` — source priority (TWSE → TPEX/MOPS → Yahoo → news).
- `references/scoring-rules.md` — transparent scorecard formulas.
- `references/output-schema.md` — report shapes.
