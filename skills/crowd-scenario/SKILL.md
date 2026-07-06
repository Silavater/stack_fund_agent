---
name: stackfund-crowd-scenario
description: Rehearse (not predict) how 10 Taiwan retail investor archetypes react to a market event, producing a per-archetype reaction chain plus a categorical, NON-AUTHORITATIVE crowd_consensus (bearish/neutral/bullish). Use for the Pro crowd-scenario report. It decides no number, influences no action, and never writes back to the decision layer.
license: MIT
version: 1.2.0
metadata:
  hermes:
    tags: [scenario, crowd, consensus, ETF, Taiwan, narrative, non-authoritative]
    firewall: non-authoritative
---

# StackFund — Crowd Scenario Engine (FACE / non-authoritative)

> **Tier A disclaimer (load banner):** 情境推演·合成人格·非真實民意·不是預測·未經回測;此層只產敘事與一個非權威標註,**不決定任何數字、不回寫決策層、不下任何證券單**。

The **headline FACE**, deliberately firewalled from the decision path. It reads a
frozen `ScenarioSeed` (bucketed ordinal context — never raw numbers) and emits a
`CrowdNarrative`: a per-archetype reaction chain + a categorical
`crowd_consensus`. There is **no numeric scalar** anywhere. The real decision
lives in the `stackfund-etf-analysis` engine; when the two disagree, the engine wins.

## Quick start
```bash
# dry-run = zero LLM, zero spend (CI + demo safe). Deterministic per seed+label.
python ${HERMES_SKILL_DIR}/scripts/run_scenario.py --symbol 0056 --scenario 0056_cut
```
Output (excerpt): `crowd_consensus` + a `narrative_md` reaction chain where each of
the 10 archetypes speaks in its own voice, ordered by how fast that cohort herds.

## Commands
| command | what it does |
|---|---|
| `run_scenario.py --symbol S --scenario LABEL` | Emit a `CrowdNarrative` for symbol `S` under context tag `LABEL`. Dry-run by default. |
| `--seed N` | Change the deterministic seed (same seed+label → identical output). |
| `--n N` | Persona count (0, or 20..50). Does **not** move the consensus — the label is seed-derived. |

**Scenario labels** (`--scenario`, free-form context tag, bucketed to ordinal —
never raw numbers): `升息` / `降息` / `0056_cut`(配息調整)/ `電子權值回檔` /
`高股息追捧`. Same seed + label → deterministic consensus.

## What the output contains
1. **`crowd_consensus`** — one of `bearish / neutral / bullish` (categorical, non-authoritative).
2. **Per-archetype reactions** — each of the 10 archetypes (存股族 / 當沖客 / 殖利率派 /
   槓桿玩家 / 外資視角 / 恐慌散戶 / PTT風向 / 媽媽存股社團 / 主力 / 定期定額新手) has
   its **own line** for its stance under the scenario — the day-trader talks stop-losses,
   the yield-seeker talks 填息, the savings group keeps DCA-ing. Contra archetypes fade
   the consensus; pro archetypes amplify it.
3. **A reaction chain** — a 2-3 step *who-moves-first* storyline ordered by herding
   speed: the fastest cohort (PTT/當沖) moves first, the slowest (外資/存股) anchors the
   tail. Pure narrative — no number is produced.

## How to present it
> 〔情境推演 · 合成人格 · 非權威 · 已與決策層隔離〕在這個**降息假想情境**下,合成散戶
> 整體偏多(crowd_consensus = bullish)。反應鏈:PTT 風向先轉多 → 恐慌散戶追高 →
> 外資最後才逢低布局。這是反應鏈推演,**不是預測,也不回寫任何權重或委託**。
> 真正的決策看 `stackfund-etf-analysis` 的確定性引擎;兩者分歧時,**以引擎為準**。

## Guardrails (summary — full contract in references/firewall.md)
The crowd layer is a pure narrative side-rail, enforced on 5 layers: **type**
(`CrowdNarrative` carries no numeric scalar), **import** (L3 imports no engine
module), **input** (reads only a frozen bucketed `ScenarioSeed`), **flag**
(`non_authoritative` hard-wired `true`), **wiring** (L4/L5 never receive any crowd
artifact). Schema-encoded + CI-tested. Even under prompt-injection the worst L3 can
do is tell a vivid but wrong *story* — it moves zero numbers and zero actions.

## Extending to another market
The roster is **market-scoped**. To add a market (e.g. US equities), ship a sibling
closed set (`personas.us.md` + its own `_ARCHETYPES` tuple + seed.lock entry) with
the same stance vocabulary, the same `CrowdNarrative` schema, and the same firewall.
Never mix markets in one roster. New market, same cage.

## References
- `references/personas.md` — the 10-archetype taxonomy + behavioural priors + herding table.
- `references/firewall.md` — the executable 5-layer firewall contract.
- `references/output-schema.md` — the committed `crowd_narrative` schema.
- `references/seed.lock.json` — rng_seed / model_id / temperature=0 (determinism source).
- `references/clean-room.md` — AGPL boundary (honest provenance).
