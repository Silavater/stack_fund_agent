---
name: stackfund-crowd-scenario
description: Rehearse (not predict) how Taiwan retail ETF investor archetypes might react to an already-computed market event, producing a second-order reaction-chain narrative plus a categorical, NON-AUTHORITATIVE crowd_consensus (bearish / neutral / bullish — no numeric scalar). Scenario stress-test, not sentiment forecast. Use for the Pro crowd-scenario report. It never decides any number, never influences any action, and never writes back to the decision layer.
license: MIT
version: 1.1.0
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
> `--scenario` is a free-form context tag (bucketed to ordinal context — never raw numbers).
> Useful labels: `升息` / `降息` / `0056_cut`(配息調整)/ `電子權值回檔` / `高股息追捧`.
> Same seed + label → deterministic consensus.

## Hard rules (see references/firewall.md)
- **G1** output whitelist: narrative / persona samples / stance counts / chain /
  a categorical `crowd_consensus` label (no numeric scalar). Any price/NAV/NTD
  pattern is a schema violation → abort.
- **G2** `non_authoritative` is hard-wired `true`.
- **G3** L4/L5 never import this skill's artifact (import-graph CI).
- **G4** the model computes no number; numeric tokens in persona text are stripped.
- **G5** determinism: `references/seed.lock.json` is the single source of truth.

> **G1/G2 are schema-encoded + tested.** The committed `crowd_narrative` schema pins them:
> `additionalProperties:false` is the firewall's teeth — any numeric / decision-shaped scalar
> is rejected — and `non_authoritative` is `const: true`. `tests/test_schema_validation.py`
> asserts a conforming narrative passes and a tampered one fails.

## Worked example
**User:** 推演 0056 在降息情境下散戶可能的反應

`python ${HERMES_SKILL_DIR}/scripts/run_scenario.py --symbol 0056 --scenario 0056_cut`
→ emits (the `crowd_narrative` schema pins the shape — a sneaked scalar fails it):
```json
{"artifact_type": "CrowdNarrative", "crowd_consensus": "bullish", "non_authoritative": true,
 "synthetic_population": true, "n_personas": 30, "seed_id": "seed_0056_…",
 "narrative_md": "## 群眾情境推演 …"}
```
**Present it as scenario rehearsal — never a number, never a call:**
> 〔情境推演 · 合成人格 · 非權威 · 已與決策層隔離〕在這個**降息假想情境**下,合成散戶人格
> 整體偏多(crowd_consensus = bullish)。這是反應鏈推演,**不是預測,也不回寫任何權重或委託**。
> 真正的決策請看 `stackfund-etf-analysis` 的確定性引擎;兩者分歧時,**以引擎為準**。

## Roster & extending to another market
- The full **10-archetype Taiwan-retail roster** runs in the engine
  (`_ARCHETYPES`, one-to-one with `references/personas.md`; hash pinned in
  `references/seed.lock.json`). Roster size never moves the consensus — the
  categorical label depends only on the frozen seed hash.
- The roster is **market-scoped**. Adding US equities later = a sibling closed
  set (`personas.us.md` + its own roster tuple + seed.lock entry), with the
  same stance vocabulary, the same `CrowdNarrative` schema, and the **same
  firewall — new market, same cage**. Never mix markets in one roster.

## References
- `references/personas.md` — closed-set archetype taxonomy + behavioural priors.
- `references/seed.lock.json` — rng_seed / model_id / temperature=0.
- `references/firewall.md` — the executable firewall contract.
- `references/output-schema.md` — the committed `crowd_narrative` schema in `schemas/`,
  checked by `tests/test_schema_validation.py`.
- `references/clean-room.md` — AGPL boundary (honest provenance).
