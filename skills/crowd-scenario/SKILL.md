---
name: stackfund-crowd-scenario
description: Rehearse (not predict) how Taiwan retail ETF investor archetypes might react to an already-computed market event, producing a second-order reaction-chain narrative plus a categorical, NON-AUTHORITATIVE crowd_consensus (bearish / neutral / bullish — no numeric scalar). Scenario stress-test, not sentiment forecast. Use for the Pro crowd-scenario report. It never decides any number, never influences any action, and never writes back to the decision layer.
license: MIT
version: 1.0.0
metadata:
  hermes:
    tags: [scenario, crowd, consensus, ETF, Taiwan, narrative, non-authoritative]
    firewall: non-authoritative
---

# StackFund — Crowd Scenario Engine (FACE / non-authoritative)

> **Tier A disclaimer (load banner):** 情境推演·合成人格·非真實民意·不是預測·未經回測;此層只產敘事與一個非權威標註,**不決定任何數字、不回寫決策層、不下任何證券單**。

This is the **headline FACE**, deliberately firewalled from the decision path.
It reads a frozen `ScenarioSeed` (bucketed ordinal context only — never raw
numbers) and emits a `CrowdNarrative` (narrative + persona reactions + a
**categorical `crowd_consensus ∈ {bearish, neutral, bullish}`**,
`non_authoritative = true`). There is **no numeric / decision-shaped scalar**;
the model only writes persona reaction *text*.

## When to use
- Generate the Pro report's second-order reaction-chain narrative for one event.

## How to run
```bash
# dry-run = zero LLM, zero spend (CI + demo fallback safe)
python ${HERMES_SKILL_DIR}/scripts/run_scenario.py --symbol 0056 --scenario 0056_cut
```

## Hard rules (see references/firewall.md)
- **G1** output whitelist: narrative / persona samples / stance counts / chain /
  a categorical `crowd_consensus` label (no numeric scalar). Any price/NAV/NTD
  pattern is a schema violation → abort.
- **G2** `non_authoritative` is hard-wired `true`.
- **G3** L4/L5 never import this skill's artifact (import-graph CI).
- **G4** the model computes no number; numeric tokens in persona text are stripped.
- **G5** determinism: `references/seed.lock.json` is the single source of truth.

## References
- `references/personas.md` — closed-set archetype taxonomy + behavioural priors.
- `references/seed.lock.json` — rng_seed / model_id / temperature=0.
- `references/firewall.md` — the executable firewall contract.
- `references/output-schema.md` — `schemas/crowd_narrative.schema.json`.
- `references/clean-room.md` — AGPL boundary (honest provenance).
