# StackFund Feasibility Report (Taiwan-ETF research desk — Core-B finalised architecture)

> 中文版 / Chinese: [StackFund_可行性報告.md](StackFund_可行性報告.md)

| Item | Content |
|---|---|
| **Project name** | StackFund — Autonomous Taiwan ETF Research Desk |
| **Product positioning** | An autonomously-run Taiwan-ETF research / advisory micro-business; front-of-house is the "crowd-scenario rehearsal engine" (Agentic Crowd-Scenario Research) |
| **Document version** | v3.1 (Core-B architecture; **FACE becomes a pure-narrative side-rail: the crowd-scenario layer does not write back to L4 and plays no part in any allocation decision**) |
| **Date** | 2026-06-19 ｜ deadline 2026-06-30 |
| **Competition** | Hermes Agent Accelerated Business Hackathon (NVIDIA × Stripe × Nous Research) |
| **Theme alignment** | The agent can **earn / spend / run real operations**; scoring: usefulness / viability / presentation |
| **Design principle** | Deterministic Python computes all numbers; the LLM only interprets impact and writes narrative; NO_ACTION is a design highlight; **the crowd-scenario layer is a pure-narrative side-rail: non-authoritative, touches no number, and enters no decision path** |

> This edition consolidates the "Core-B design". The body (§1–§9) is an exec-level viability argument; the engineering contracts, schemas, persona library, demo runbook, day-by-day build plan and other deep details of the crowd-scenario engine are collected in **Appendix A**. The Core-B design has passed five adversarial stress tests (all concluding holds_with_changes); their required_fixes are folded into this text.
>
> **v3.1 change (FACE as a pure-narrative side-rail)**: FACE changes from the old "guardrail-constrained, can write back a ±2pp micro-adjustment" to a "**pure-narrative side-rail**" — the crowd layer produces only narrative and a non-authoritative annotation, **no longer writes back to L4, and plays no part in any allocation decision**; accordingly the two-key gate, bounded clamp, threshold-flip, TiltProvenance and zero-modifier re-run are **removed** and replaced by a stronger "**the decision path is not wired**" structural guarantee (L4 does not import / does not receive ContrarianSignal). Motivation: the old firewall was already so strict that the modifier had near-zero effect on the result — rather than use a complex mechanism to "safely contain" an ineffective write-back, it is better to let the front-of-house structurally never touch the steering wheel — less engineering, and a stronger firewall story.

---

## 1. Executive summary

StackFund is a **Taiwan-ETF research desk** autonomously run by a **Hermes** agent, executing inside the **NVIDIA NemoClaw / OpenShell** sandbox, doing three real things:

1. **Run real operations** — with a custom Hermes Skill (the ETF-analysis layer's design references the open-source `AZNitro/tw-stock-agent`), it pulls TWSE OpenAPI, TPEX / MOPS, Yahoo, news and contrarian sentiment, and produces structured research and rebalance recommendations for popular Taiwan ETFs (0050 / 0056 / 00878, etc.).
2. **Spend** — using **Stripe Skills for Hermes**, it provisions and pays for its own data / compute / SaaS stack, and uses a deterministic optimizer to rebalance this "tool portfolio" within a fixed budget.
3. **Earn** — using **Stripe billing**, it charges subscribers for research, producing real revenue; a before / after **Operational P&L** proves this agentic business can pay its own way.

**The product headline is the "crowd-scenario rehearsal engine"**: for an already-computed market event, it uses 20–50 Taiwan retail **synthetic personas** to rehearse a second-order reaction chain ("if rates rise → dividend holders keep their dollar-cost-averaging unchanged → day traders stop-loss the tech heavyweights first → selling pressure concentrates on 0050 → the 0056 resilience narrative → a second rotation of capital"). This is the differentiator versus "yet another TWSE dashboard". But it is strictly isolated by a **firewall**: **the front (FACE) can only change what story we tell — it is a pure-narrative side-rail that only sends the narrative and a non-authoritative annotation into the Pro report and the audit record; it never writes back to a decision layer and never participates in allocation; it can never decide a number, never affect an action, and never touch a function that computes a number. The steering wheel is permanently locked to the engine (the deterministic trunk of Stripe earn / spend), never to the front.**

**Conclusion: technically feasible, recommend Go, with five preconditions.** The most critical design judgment: **Stripe handles the "business cash flow" (paying for tools, charging customers), not "securities orders"**; Taiwan ETFs are the **subject** of the research and service, and StackFund never places a single securities order. The three sponsor platforms (Hermes orchestration, Stripe earn + spend, NemoClaw security) each play their part, fully hitting "earn + spend + real operations".

**Three honesty red lines disclosed up front (design maturity — say it, don't dodge it):** (1) **reproducible ≠ validated** — the scenario engine is a synthetic rehearsal; its value is risk-scenario coverage, not forecasting accuracy; (2) **the crowd modifier enters no decision, and makes no claim to be better than the existing contrarian score** — it is only a scenario-reference annotation in the report; the product value is pinned to the "second-order reaction-chain **narrative**", not that scalar; (3) **the real regulatory exposure is in the "priced + named + directional" RebalancePlan** (on the trunk), defended by a safe harbour of test-mode / no fee / zero orders. The main risks concentrate in Taiwan financial regulation, data-source stability and demo credibility — not "whether the technology exists". The five preconditions are detailed in §8.

---

## 2. Product definition and positioning

StackFund is a micro-business that **earns its own money, pays its own operating cost, and does its own research** — not a stock-picking bot. Product category: **Agentic Crowd-Scenario Research for Taiwan ETFs** — a deterministic research desk whose front-of-house is a **stress-test** engine for crowd reactions.

### 2.1 Two portfolios (a design highlight)

| Portfolio | Content | Who benefits |
|---|---|---|
| **ETF research portfolio** | Allocation and rebalance recommendations for Taiwan ETFs like 0050 / 0056 / 00878 | Subscribing customers |
| **Operating-cost portfolio** | Data APIs, LLM inference, databases, observability, delivery and other SaaS | The agent itself (FinOps) |

The agent simultaneously optimises "how the customer should allocate ETFs" and "how its own business should spend money", sharing a single Operational P&L.

### 2.2 Moat — pinned to narrative, not to numbers

Dashboards and `tw-stock-agent` answer the **first-order question** (what is 00878's price, NAV, discount/premium, yield) — zero-defensibility commodity facts. StackFund's moat is the **second-order reaction-chain narrative**: "who does what because of what others do" — an artifact a data source can't sell and `tw-stock-agent` can't produce.

> The moat in one line: "Dashboards sell **data**; `tw-stock-agent` already has sentiment scores; what StackFund additionally sells is a **second-order story of how the crowd pulls on each other after the data** — a narrative artifact, not stronger numbers."

### 2.3 What subscribers buy (three-tier Stripe plan, strengthening EARN)

The free numbers are the hook; the scenario **narrative report** is the paid product; the paywall is cut on the same line as the firewall (free = authoritative numbers / engine, paid = value-add narrative layer / front).

| Plan | Stripe price (demo) | Content |
|---|---|---|
| **Watch (free)** | NT$0 | Daily number card: price / NAV / discount-premium / yield / freshness. Pure deterministic facts, deliberately commoditised. |
| **Pro (headline SKU)** | ~NT$299/mo | Single-event crowd-scenario report: second-order reaction-chain narrative + 5–8 persona samples + `contrarian_modifier` (labelled "scenario-reference signal, not investment advice, **does not affect this report's deterministic allocation conclusion**") + the deterministic research conclusion beneath it. **This is the product.** |
| **Desk (roadmap, not MVP)** | ~NT$999/mo | Pro + event-triggered scheduling + cross-ETF rotation chains + raw crowding time series. |

The LLM inference the scenario engine consumes is a **real, variable, per-report** compute cost, paid by the agent via Stripe Skills ⇒ clean unit economics; on low-value events the agent can decide "this rehearsal isn't worth the cost" ⇒ a **refused spend** (the most memorable demo beat).

### 2.4 Positioning language and the regulatory boundary

- Verbs always use **simulate / rehearse / stress-test**, **never predict / forecast**. Front-of-house tagline: "A **crowd-reaction stress test** for ETF impact scenarios", deliberately distancing from MiroFish's "predict everything" language.
- StackFund provides **research / educational decision support**, is **not discretionary management on a client's behalf, not a paid individualised securities investment advisory, and places no securities order**. All output carries a four-tier disclaimer (see §7 and Appendix A.12).
- **Honesty boundary**: before 6/30 there are no real paying subscribers; the EARN story rests on "the credibility of willingness-to-pay created by differentiation" + "having demonstrated one real Stripe collection", **not** "a validated market".

---

## 3. Technical feasibility

### 3.0 Verification summary table

| Component | Assumed capability | Verification result |
|---|---|---|
| Stripe (Skills / billing) | The agent can provision / pay for SaaS (spend) and charge customers a subscription fee (earn) | **Holds.** Stripe Skills for Hermes supports agent self-service provisioning and payment; billing supports subscription collection |
| Hermes | Open-source agent, can load Agent Skills, persists across sessions | **Holds.** Nous Research's open-source self-improving agent, already integrated with the Stripe skill |
| NemoClaw / OpenShell | Agent sandbox, controls files / network / credentials / inference | **Holds.** NVIDIA's official sandbox, four policy domains, officially supports Hermes |
| Taiwan-stock data layer | TWSE / TPEX / MOPS / Yahoo for ETF price-volume, NAV, dividends, institutional/margin (chip) data, news | **Holds.** TWSE OpenAPI is official public data; `tw-stock-agent` has demonstrated the integration path |
| ETF-analysis Skill | Loadable by Hermes in the SKILL.md + scripts/ + references/ format | **Holds.** `tw-stock-agent` already uses this format (the same format as the Hermes / Stripe official skills); forkable |
| **Crowd-scenario engine Skill** | **A clean-room-distilled lightweight native skill, N=20–50 personas, no OASIS / Zep, deterministic aggregation** | **Holds.** Same Agent Skills format; contains no MiroFish code; see §3.5 |

### 3.1 Stripe (the cash-flow layer of earn + spend)

- **Spend**: via Stripe Skills for Hermes, the agent can provision / upgrade-downgrade databases, AI, observability and other services, with a **hard spend cap enforced at the API layer** (not at the prompt layer), plus a merchant allowlist, a full transaction log, and a "high-amount needs manual approval" threshold; credentials are delivered via a Shared Payment Token.
- **Earn**: use Stripe billing to create Watch / Pro / Desk subscriptions, issue invoices and collect — forming a real revenue stream (hitting the competition's "earn" core).
- **Agent-friendly**: the commands support non-interactive flags and structured output, suitable to call from a script inside a Hermes skill.

### 3.2 Hermes (the agent and orchestration layer)

Nous Research's open-source, self-improving agent carries context across sessions, suited to the workflow of "repeatedly researching the same set of ETFs and serving the same set of subscribers". The Stripe skill is already integrated; the custom StackFund Skill, ETF-analysis Skill and crowd-scenario Skill load as long as they follow the Agent Skills format.

### 3.3 NVIDIA NemoClaw / OpenShell (execution boundary and risk-control layer)

- **Four policy domains**: filesystem, network, process, inference, declarative YAML; network / inference are hot-updatable.
- **Credential isolation**: keys never land on the sandbox filesystem; injected by an L7 proxy at egress; default-deny network by default.
- **Kernel-level mechanisms**: seccomp, Landlock, network namespaces.
- **Model**: Nemotron as the default inference model (the crowd-scenario engine also uses the same stack to write persona text); the Privacy Router can route between local / cloud.
- **Agent support**: officially supports Hermes.

For an agent that simultaneously handles real cash flow and financial research output, the sandbox's hard spend cap and network policy are the most persuasive security demo selling points.

### 3.4 Taiwan-ETF data layer (the core operation)

Referencing `AZNitro/tw-stock-agent`, build a Hermes-compatible ETF-analysis Skill. Source priority: ① TWSE OpenAPI (official: price-volume, margin financing, P/E, P/B, yield, announcements) ② TPEX / MOPS (OTC and financials / dividends) ③ Yahoo (quotes, analyst targets, peer comparison, news) ④ Web / News (catalyst events) ⑤ contrarian sentiment (overheated / panic / crowded, an auxiliary layer). **ETF-specific fields** (discount/premium, tracking error, constituent overlap, ex-dividend date) are always computed by deterministic Python.

> **Open item (low risk)**: `tw-stock-agent`'s `scripts/` are placeholders (the official README states this); the fetcher must be supplied; but its `SKILL.md` / `references/` are already an adoptable design skeleton.

### 3.5 The crowd-scenario engine (why not integrate MiroFish directly, but clean-room distill instead)

The concept inspiration for the front-of-house comes from the open-source swarm-intelligence simulation engine **`666ghj/MiroFish`**. On evaluation, **directly integrating MiroFish is blocker-level**, for three reasons:

1. **Licence**: MiroFish is **AGPL-3.0** (strong copyleft). Its §13 network clause would make a "network service that charges via Stripe" instead need to disclose source to **every paying user** — conflicting with this project's commercial / brand premise.
2. **Execution form**: it is a long-running Flask + Vue (~19.5k lines), OASIS engine + paid Zep Cloud GraphRAG + high-consumption LLM stateful dual-platform simulation; it doesn't fit a 90–120-second live demo and conflicts head-on with the deterministic principle.
3. **Cost**: LLM volume = agents × rounds × 2 platforms; the project itself admits "consumes a lot".

**So we take Path B — clean-room distill the "idea" into a lightweight native skill**: take only the **concept** of "heterogeneous personas react to an event → producing a second-order reaction chain and a contrarian signal", implemented with N=20–50 personas, a fixed RNG seed and deterministic Python aggregation, **no OASIS / no Zep / no long-running server**, with the LLM only writing persona reaction text, not computing numbers. **Clean-room discipline (honest version)**: to understand the architecture we did inspect the MiroFish source, but **copied no code / prompt / schema text** — all field names, schemas and formulas are original, and the design is re-argued from first principles as "an extension of `tw-stock-agent`'s contrarian layer", not a scaled-down MiroFish (details in Appendix A.6).

### 3.6 Integration-feasibility summary

OpenShell governs "whether the agent can bypass the normal execution path"; Stripe governs "the hard amount cap + real earn / spend"; Hermes governs "cross-session orchestration"; the ETF Skill governs "the real research operation"; the crowd-scenario Skill governs "the differentiating narrative front (isolated by the firewall)". The responsibility boundaries are clear, with no overlap or gap. **Technical feasibility holds.**

---

## 4. Architectural feasibility (Core-B six layers + firewall contract)

### 4.1 The contract in one sentence

> The crowd-scenario engine can change **what story we tell**, sending the narrative and one non-authoritative annotation into the Pro report and the audit; it **can never decide a number, never affect any action, never write back to any decision layer, and never touch any function that computes a number**. It is a pure-narrative FACE; the deterministic trunk is the ENGINE, and **there is no edge whatsoever flowing from FACE to ENGINE between them**.

### 4.2 The six-layer skeleton (│ = the deterministic trunk; FACE is a pure-narrative side-rail with no write-back edge)

```
              STACKFUND — Core-B 6-LAYER ARCHITECTURE (FACE pure-narrative side-rail)
  ┌────────────────────────────────────────────────────────────────────────┐
  │  L1  ETF DATA BOOK (deterministic ingest)                              │
  │  TWSE / TPEX / MOPS / Yahoo / news. Computes all numbers: price, NAV,  │
  │  discount/premium, tracking error, yield, ex-div date.                 │
  │  Output ▶ DataBook (immutable, book_hash)                              │
  └──────────┬──────────────────────────────────┬──────────────────────────┘
             │ DataBook(full)                    │ ScenarioSeed(projection,
             │                                   │   read-only, frozen, bucketed)
             ▼                                   ▼
  ┌───────────────────────────┐    ╔════════════════════════════════════════╗
  │ L2 DETERMINISTIC SCORECARD│    ║ L3  CROWD SCENARIO ENGINE   ★CORE-B★    ║
  │   (trunk)                 │    ║     crowd-scenario engine (FACE/headline)║
  │ transparent formulas →    │    ║ distilled from the idea (not a swarm):  ║
  │ trend / fundamental /     │    ║  seed → N=20–50 deterministic-RNG       ║
  │ valuation / catalyst /    │    ║  personas → LLM writes reaction text +  ║
  │ risk sub-scores           │    ║  stance only → deterministic Python     ║
  │ Output ▶ ScoreCard        │    ║  AGGREGATION → ONE bounded scalar        ║
  └──────────┬────────────────┘    ║  (report annotation only)               ║
             │ ScoreCard           ║ NO OASIS / NO Zep / NO server / no numbers║
             │ (authoritative)     ║ Output ▶ ContrarianSignal               ║
             │                     ║  { narrative, persona_samples,          ║
             │                     ║    contrarian_modifier ∈ [-1,+1],       ║
             │                     ║    is_authoritative = FALSE }           ║
             │                     ╚═══════════════╤════════════════════════╝
             │     narrative output, NO write-back │ flows only to ↓
             │             ┌──────────────────────────────────────────────┐
             │             │ Pro report (narrative = product) + L6 audit   │
             │             │ The crowd layer ends here; ZERO edge to the   │
             │             │ L4 decision path                              │
             │             └──────────────────────────────────────────────┘
             ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  L4  PORTFOLIO MANAGER (trunk — the steering wheel)                    │
  │  Builds RebalancePlan from the ScoreCard only. Does not import / does  │
  │  not receive ContrarianSignal. No tilt / gate / clamp / threshold-flip.│
  │  NO_ACTION is a first-class output.                                    │
  │  Output ▶ RebalancePlan (final_delta = hard_delta, pure hard data)     │
  └──────────┬─────────────────────────────────────────────────────────────┘
             │ RebalancePlan
             ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  L5  FINOPS & EXECUTION (trunk)                                        │
  │  Stripe SPEND(provision, hard cap) + EARN(subscription collection).    │
  │  A Value-of-Information gate decides whether a paid report is worth    │
  │  running. The crowd layer has ZERO reach into this layer.              │
  └──────────┬─────────────────────────────────────────────────────────────┘
             ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  L6  AUDIT & OPERATIONAL P&L                                           │
  │  Records FULL PROVENANCE of every deterministic decision + the crowd   │
  │  report archive. Replayable. P&L.                                      │
  └────────────────────────────────────────────────────────────────────────┘
```

**Key structural fact**: L3 is a pure-narrative **leaf node** on the side-rail — data flows in (ScenarioSeed) and its output (CrowdScenarioReport + ContrarianSignal) flows only to the **Pro report and the L6 audit**, with **no outward edge** to L1 / L2 / **L4** / L5 (L4 doesn't even import it). Deterministic market scenarios (rate hike / tech-heavyweight pullback — legitimately driving numbers) stay in the L1 / L2 trunk; only the **crowd / persona reaction** is cut out into the L3 side-rail narrative.

### 4.3 The firewall — five enforced layers (details in Appendix A.1–A.3)

1. **Type layer**: the `ContrarianSignal` has **no** price / nav / discount-premium / yield / weight / cap field → it cannot return a number by contract.
2. **Import layer**: L3 imports no compute module; the CI guard `test_firewall_no_imports` greps the import graph; a violation fails the build.
3. **Input layer**: L3 only takes the frozen `ScenarioSeed` (bucketed ordinal context — **the personas never see raw numbers**); there is no setter to call.
4. **Flag layer**: `is_authoritative` is hard-wired False and asserted.
5. **Wiring layer (replaces the old zero-modifier CI, stronger)**: the L4 decision path **does not import / does not receive** `ContrarianSignal`; the CI guard asserts that L4's input type is only `ScoreCard` and that the import graph has no L3 / `ContrarianSignal`. There is **no connection whatsoever** between the crowd layer and the steering wheel.

Even if L3 is prompt-injected internally, the most it can produce is a vivid-but-wrong **story** — because it simply isn't wired to any decision or compute path, causing **zero** harm to any **computed number** or **any action**.

### 4.4 How the Portfolio Manager works (pure hard data, details in Appendix A.3)

L4 **consumes only the ScoreCard**: `hard_plan = build_plan_from_scorecard(scorecard)`. If hard_plan is empty / within tolerance → **NO_ACTION**; otherwise it outputs `RebalancePlan(final_delta = hard_delta)`. **L4 does not import / does not receive `ContrarianSignal`; there is no tilt / gate / clamp / threshold-flip in the flow.** The crowd modifier is shown in the Pro report and the audit but participates in no computation at this layer.

**The independent-defensibility invariant (the headline-credibility guarantee, machine-checkable)**: every non-zero weight change in a RebalancePlan has, **by construction**, only a pure-hard-data explanation — because the crowd layer never entered the decision path. **The structural CI invariant: assert that the L4 module's input type is only `ScoreCard` and that the import graph has no L3 / `ContrarianSignal`, else reject.** This is **stronger** than the old "zeroing the modifier and re-running still holds": it isn't "still holds after zeroing", it's "**was never wired in at all**".

### 4.5 Several judgments that remain correct

1. **LLM / deterministic division of labour**: price, NAV, discount/premium, yield, weight and spend are computed by deterministic Python; the LLM only interprets impact and writes narrative. The crowd engine **computes no number** — it in fact **strengthens** this principle.
2. **Two portfolios, one P&L**: the demo can simultaneously show "value to the customer" and "whether the agent itself makes money".
3. **Defence-in-depth spend control**: StackFund business rules (soft) → Stripe API-layer cap (hard) → OpenShell execution boundary (hard).
4. **Schema-first**: lock the four JSON schemas (ETFResearchReport / RebalancePlan / OperationalReceipt / CrowdScenarioReport) first. Sensitive tokens never enter JSON.
5. **NO_ACTION is a design highlight**: being able to prove "no adjustment is needed this week" or "this spend isn't worth it" is the strongest signal of "actually reasoning".

**Architecture point to strengthen**: the real hard guarantees are the Stripe API-level cap and the OpenShell policy; the business rules are only an advisory layer; and all outward research output must carry a disclaimer (§7).

---

## 5. Operational and execution feasibility

| Dimension | Assessment |
|---|---|
| Team capability | Has a CS / systems-integration background, can handle CLI, Python, JSON, sandbox config and Taiwan-stock data fetching — a good capability match |
| Development scope | The MVP converges well (3 ETFs, 1 fixed scenario, deterministic scorecard + optimizer, 1 real Stripe payment + 1 collection + 1 refused, firewall code, 1 pre-baked crowd scenario) |
| Demo form | A 90–110-second live demo (hard cap 120s); the crowd engine is the emotional peak, but earn / spend / refused-spend take the opening/closing lines and most of the seconds |
| External dependencies | Depends on Stripe account eligibility and TWSE / Yahoo data availability — must be verified on Day 1 |

**Development order (firewall + Stripe FIRST)**: Day 1 verify Stripe TW dual-flow + TWSE reachability → lock the four schemas + freeze fixtures → deterministic scorecard + optimizer → **Stripe SPEND + REFUSED SPEND** → Stripe EARN → **firewall contract + hard-only PM + P&L (CORE FROZEN at the end of Day 6 — after which we can win even if the front demo is cut)** → crowd-scenario engine scaffold + bake → replay / non-authoritative chapter / hard-cut → finally wrap in NemoClaw and record the demo. The day-by-day plan is in Appendix A.11.

---

## 6. Risk assessment and mitigation

| ID | Risk | Level | Description | Mitigation |
|---|---|---|---|---|
| R1 | Taiwan Stripe earn / spend eligibility | High | The country list for the Stripe Skills payment layer / subscription collection may not include Taiwan or may be limited | Three modes `dry_run / free_only / live_limited`; Day 1 verify whether the account can "pay to provision" and "collect against a test card"; fallback to free-tier + test-mode collection, mark the paid action blocked |
| R2 | Taiwan investment-advisory regulation (SITA §4) | High | Charging for individualised securities advice touches the Securities Investment Trust and Consulting Act | **PRIMARY defence**: the demo has no real consideration (test-mode, no mandator) + a **non-individualised** research / publication framing + removal of absolute buy/sell instructions; the RebalancePlan is rendered as "an illustrative allocation under a research scenario", not "you should reduce". **The firewall is a correctness / credibility control, not the primary advisory defence** (corrected from the old version's mis-assignment) |
| R2b | Market integrity / appearance of manipulation (Securities and Exchange Act §155) | Medium–High | §155 splits into a **trading limb** (wash / continuous trading — **fully defused by zero orders**) and an **information limb §155(1)6** (disseminating information sufficient to affect price — **only partly defused**) | Cannot claim "almost fully defused"; published narrative must be framed as a **hypothetical stress scenario** and must **never** state how a named ETF will move; forbid any external language asserting a price direction for a named ticker; demo narrative is explicitly counterfactual ("**if** … **this kind of** persona **might** …") |
| R2c | Headlining degrades the research carve-out | Medium | Marketing shifts from "numbers" to "what the crowd will **do**", more action-oriented and further from a neutral publication | Keep the tagline / Pro copy as **scenario / education** (stress test / scenario rehearsal), never outcome-promising |
| R3 | Live demo execution failure | High | The three live Stripe calls (collect / provision / refused) are the real blowup risk; auth pop-ups / latency / rate limits | Provision services in advance, the crowd sim is pure replay; mark live / replayed; **forbid a live re-bake during the demo**; `>5s → alt-tab to the recording`; the static card is a **first-class** fallback; dry_run safety net |
| R4 | Data-source stability and timeliness | Medium | TWSE rate limits; Yahoo redesigns; limited intraday real-time | Use "official daily data as a proxy for intraday" fallback (fmtqik / mi-stock20); mark freshness; mark missing as partial, don't guess |
| R5 | Credibility: reproducible ≠ validated (R5 / R6) | Medium | The headline is **LLM narrative**; deterministic aggregation only buys "reproducible", not "correct"; persona stances are authored priors, not observed; no backtest | Disclose the **modifier is weak, value pinned to narrative**; attach a **citable prior** to each archetype; give the firewall / NO_ACTION equal or greater weight in the demo, and show "deleting the crowd panel on the spot leaves the action still holding"; say in voiceover "**not backtested**"; the narrative is always conditional |
| R6 | Agency perception | Medium | When every decision is deterministic, it can be challenged as "an agent or just a calculator with subtitles" | Put agency in the **execution / adaptation loop**: really run a Stripe provision, hit a cap and fail, read the error and downgrade; really charge subscribers; the demo plays out "responding to a real failure" |
| R7 | Clean-room / licensing credibility | Medium–Low | Legal risk is low (never distributed, no MiroFish code in the repo, original field names, MIT, stateless with no §13 surface); **but** if the provenance statement is dishonest, the credibility pillar collapses when a judge diffs the two repos | `clean-room.md` uses the honest version (inspected the source but copied no code / prompt / schema); remove any reference to MiroFish module / class names from the design; NOTICE only credits the idea (Appendix A.6) |
| R8 | Minor technical points | Low | ① the custom skill format must align with Hermes; ② `tw-stock-agent` scripts are placeholders | ① fork the same format directly, verify loading on Day 1; ② supply a minimal fetcher on Day 1 (TWSE price-volume + Yahoo quotes to start) |

**The five adversarial stress tests** (firewall / demo / credibility / regulatory / clean-room) all conclude **holds_with_changes**; the required_fixes are folded into this text and the appendix; the three most honest residual risks are the three red lines in §1 (the full stress-test table is in Appendix A.13).

---

## 7. Resource needs and schedule (Core-B MVP scope)

**IN — the immovable CORE (the engine; must ship even if the front is cut)**
3 ETFs (0050 / 0056 / 00878, frozen fixtures, all Python-computed); the ETFResearchReport / RebalancePlan / OperationalReceipt / CrowdScenarioReport schemas; deterministic scorecard + cost optimizer (hard cap / reserve); **1 real Stripe EARN + 1 SPEND + 1 REFUSED SPEND**; **firewall code enforcement** (`firewall_test.py` asserts the crowd layer never writes any number field, and the L4 import graph has no L3 / ContrarianSignal); L4 reads only the ScoreCard to produce the plan (does not receive the modifier), every action carrying an independent hard-data reason; before / after P&L; executed inside NemoClaw; output carrying a four-tier disclaimer.

**IN — the front (signature beat, bolt-on, degradable)**
**Just one** pre-baked scenario `0056_cut`, N=30, seed=42, replay animation, non-authoritative chapter.

**OUT (explicitly not doing)**
Live multi-round / multi-scenario swarm; any OASIS / Zep / Flask runtime; >1 scenario; N>50; real order placement / broker API; paid individualised advisory; intraday ticks; leveraged / futures ETFs; hundreds of ETFs; ML prediction; historical backtest; per-user memory; A–E moat rating.

**CUT-LINE (if behind on 6/29)**: cut the replay animation, beat 5 becomes a static card; the firewall, hard-only PM and the other beats are untouched. **The front is never on the critical path.**

This scope and the "don't do" list show a convergence from over-design, good scope discipline, and a deliberate avoidance of the two regulatory landmines: "real order placement" and "paid individualised advisory".

---

## 8. Conclusion and recommendation

**Recommendation: Go**, with the following five preconditions and a Phase 1 go / no-go checkpoint.

**Preconditions (must complete early in development)**
1. **Day 1 verify Stripe two-way cash flow**: a Taiwan account can "pay to provision at least one SaaS" + "create a subscription against a test card and collect", deciding whether the demo runs `free_only` or `live_limited`.
2. **Day 1 verify the Taiwan-stock data layer**: run TWSE OpenAPI to fetch one ETF's price-volume + Yahoo quotes, confirm rate limits and timeliness, supply a minimal `tw-stock-agent` fetcher.
3. **Change the scorecard to formula-derived**: in the optimizer skeleton, compute scores from observable signals, eliminating "the conclusion being fed by the inputs" (R5).
4. **Land the firewall contract**: `ContrarianSignal` (is_authoritative=false) + five-layer enforcement (type / import / input / flag / **wiring**) + **L4 pure hard data, does not import or receive the modifier** + the **wiring CI invariant** (L4 import graph has no L3 / ContrarianSignal) + `firewall_test.py`, in place by Phase 1 (CORE frozen by Day 6).
5. **Land the regulatory positioning, the wording lexicon and the four-tier disclaimer**: positioned as research / education, places no securities order; conditional narrative tone; the demo runbook includes the Tier D voiceover checklist; `clean-room.md` uses the honest version.

**Go / No-Go checkpoint (Phase 1)**: if Day 1 cannot complete both "at least one real paid provision" and "at least one real / test-mode collection" on a Taiwan account, switch to `free_only` + a test-mode demo and confirm the sandbox with the organisers. **Do not let the architecture be hard-bound to the assumption that "a Taiwan account can definitely run a full earn + spend".**

Overall, StackFund's greatest strength is not "the agent can pick ETFs", but "the agent can **run its own Taiwan-ETF research business** — do real research, pay its own operating cost, charge customers, and proactively refuse a spend when it isn't worth it", differentiated by an **eye-catching but strictly isolated** crowd-scenario front. It fully hits earn / spend / run real operations, and treats "the face is eye-catching while the steering wheel is still clearly locked to the engine" as a proactively-disclosed sign of design maturity — which is exactly the best proof of viability and presentation.

---

## 9. References

- Hermes Agent Accelerated Business Hackathon (NVIDIA × Stripe × Nous Research) — theme and scoring
- Taiwan-ETF analysis skill design reference: `AZNitro/tw-stock-agent` — https://github.com/AZNitro/tw-stock-agent
- Crowd-scenario engine **concept** inspiration (**its code is not integrated**; AGPL-3.0, direct integration evaluated as a blocker, replaced by clean-room distillation, see §3.5 / Appendix A.6): `666ghj/MiroFish` — https://github.com/666ghj/MiroFish
- TWSE Taiwan Stock Exchange OpenAPI — https://openapi.twse.com.tw/
- Market Observation Post System (MOPS) — https://mops.twse.com.tw/
- Stripe (Skills for Hermes / billing) official docs — https://docs.stripe.com/
- Hermes (Nous Research) — https://nousresearch.com/
- NVIDIA NemoClaw — https://github.com/NVIDIA/NemoClaw ｜ NVIDIA OpenShell — https://github.com/NVIDIA/OpenShell
- NVIDIA Technical Blog: Run Autonomous, Self-Evolving Agents More Safely with OpenShell — https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/

> Notes: ① external-platform capabilities are presented as summaries; the actual command flags and vendor lists follow each platform's latest official documentation. ② This document is a competition feasibility assessment, **not investment advice**; StackFund's product is positioned as research / educational decision support, not discretionary management or a paid securities investment advisory, and places no securities order. ③ The crowd scenario is a **scenario rehearsal** of synthetic personas, not real public opinion or a market forecast.

---
---

# Appendix A — Crowd-scenario engine detailed design (Core-B)

> This appendix is the engineering expansion of §4, with the required_fixes of the five adversarial stress tests folded in.

## A.1 Data contracts (the firewall is the type)

**Read side `ScenarioSeed` (the only thing L3 can read, a frozen projection)**: produced by the pure function `make_seed(book)->ScenarioSeed`, carrying only **bucketed ordinal context** (discount/premium → {deep_discount…rich}, yield → {low, normal, high}) + `rng_seed` + `market_scenario_label`. **The personas never see raw numbers** — structurally preventing the LLM from regurgitating or recomputing numbers. No live handle, no setter, no optimizer / Stripe / weight / cap reference.

**Write side `ContrarianSignal` (the only thing L3 can emit)**:
```python
@dataclass(frozen=True)
class ContrarianSignal:
    seed_id: str                # must equal the ScenarioSeed.seed_id it reacts to
    rng_seed: int
    n_personas: int             # 20..50
    contrarian_modifier: float  # ∈ [-1,+1]; positive = crowd overheated → lean defensive, negative = crowd panic → lean aggressive
    is_authoritative: bool      # HARD-WIRED False (__post_init__ assert)
    narrative_md: str           # the second-order reaction-chain story (LLM writes it)
    persona_samples: tuple[PersonaReaction, ...]
    # this type "has no" price/nav/discount-premium/yield/weight/cap field
    def __post_init__(self):
        assert -1.0 <= self.contrarian_modifier <= 1.0
        assert self.is_authoritative is False
```
The aggregation from N persona stances to a single scalar is **deterministic Python**, not LLM: `modifier = clamp(mean(stance_i) * crowding_factor, -1, +1)`, where `stance_i ∈ {-1,0,+1}` is parsed from the LLM text by a rule-based, version-pinned classifier. **The LLM writes text; Python turns text into a number.**

## A.2 Hard prohibitions (five-layer enforcement)

① **Type layer**: `ContrarianSignal` has no numeric field. ② **Import layer**: L3 imports no `l1_databook.compute` / `l2_scorecard` / `l4_portfolio.optimizer` / `l5_finops.stripe`; the CI guard `test_firewall_no_imports` fails the build on a violation. ③ **Input layer**: L3 only takes the frozen `ScenarioSeed`, no setter. ④ **Flag layer**: `is_authoritative` is hard-wired False and asserted. ⑤ **Wiring layer (replaces the old zero-modifier CI)**: the L4 / L5 decision path **does not import / does not receive** `ContrarianSignal`; the CI guard asserts L4's input type is only `ScoreCard` and the decision-side import graph has no L3 module. The crowd layer and the steering wheel are **zero-wired**.

## A.3 How the Portfolio Manager works (pure hard data, no modifier consumption)

**L4 consumes only the ScoreCard**: `hard_plan = build_plan_from_scorecard(scorecard)`. If empty / within tolerance → **NO_ACTION**; otherwise it outputs `RebalancePlan(final_delta = hard_delta)`. **No two-key gate, no bounded clamp, no threshold-flip, no tilt** — these old mechanisms are **all removed** because the modifier no longer enters L4.

```python
def build_rebalance_plan(scorecard: ScoreCard) -> RebalancePlan:
    # the only input is the ScoreCard; there is no ContrarianSignal parameter in the signature
    hard_plan = build_plan_from_scorecard(scorecard)
    if hard_plan.is_empty_or_within_tolerance():
        return RebalancePlan(action="NO_ACTION", reason=hard_plan.why_flat())
    return RebalancePlan.from_hard(hard_plan)   # final_delta == hard_delta, identically
```

**The independent-defensibility invariant (structural, machine-checkable)**: every non-zero `final_delta` in a RebalancePlan equals `hard_delta` by construction — the crowd layer never entered the decision path. **CI: assert that the `build_rebalance_plan` signature accepts only `ScoreCard` and that the L4 import graph has no L3 / `ContrarianSignal`, else reject.** This replaces the old "zero the modifier and re-run still holds" — now guaranteed directly by "**structurally not wired**", stronger and easier to test.

## A.4 The SPEND firewall and provenance (L6)

Paid reports / provisioning are gated by a **deterministic value-of-information rule** (materiality + spend-cap headroom, all computed from hard inputs); `contrarian_modifier` **plays no part whatsoever in a spend decision (not even a tie-breaker)**. **CI assertion: the import graph of the spend decision path has no `ContrarianSignal` / L3 module.**

Each L4 decision writes a pure-hard-data `DecisionProvenance`: `{decision_id, scorecard_id, ticker, hard_delta_pp, hard_signals[(name,value)], final_delta_pp(= hard_delta_pp), action}`. The crowd layer **separately writes** a `CrowdReportProvenance`: `{report_id, seed_id, rng_seed, contrarian_modifier, is_authoritative(always False), narrative_digest(sha256)}`, marked **for narrative audit only, linked to no decision**. The demo dashboard line: "Hard-data action: +3.0pp 0056 (valuation+yield+trend) │ Crowd narrative (non-authoritative, not part of allocation): modifier=+0.42 fade_overbought".

## A.5 crowd-scenario-skill design (clean-room)

```
crowd-scenario-skill/
  SKILL.md
  scripts/
    seed_builder.py     # deterministic: DataBook -> EventSeed (no LLM)
    persona_sim.py      # fixed RNG picks roster/order/edges; LLM only writes text + stance
    aggregate.py        # deterministic: stance -> contrarian_modifier + reaction chain (no LLM)
  references/
    personas.md         # fixed N=20..50 persona library (each archetype with a behavioural prior + citation)
    seed.lock.json      # rng_seed / roster hash / model_id / temperature=0.0
    firewall.md         # the firewall contract (executable rules)
    output-schema.md    # EventSeed / ScenarioReport / ContrarianSignal JSON schema
    clean-room.md       # the AGPL boundary and provenance (honest version, see A.6)
```

| Step | Who does it | Content |
|---|---|---|
| `seed_builder.py` | **Python** | Reads databook.json, picks a fixed market_event, buckets continuous metrics into ordinals, emits EventSeed + seed_hash. No LLM. |
| `persona_sim.py` | **Python + LLM** | Python (RNG seeded) picks N personas, the reaction order, and a sparse who-reads-whom edge set. Round 1 each persona reacts independently; Round 2 each persona reads K neighbours' round-1 text and may change stance (second-order / contagion, in-memory, no Zep). The LLM **only** returns `{reaction_text, stance-token}`. |
| `aggregate.py` | **Python (+ 1 LLM)** | Stance token → clamped `contrarian_modifier`; walks the edges to enumerate the second-order reaction chain; computes the stance_histogram / flip_count; runs a forbidden-output scan; finally **one** LLM call consumes only the already-computed values to write the narrative (numeric-token diff verification; strip on violation). |

**The Round model (N=20–50, no OASIS/Zep)**: 2 rounds × N personas = 40–100 small LLM calls, parallelisable, within the demo budget. **Deterministic seeding**: `seed.lock.json` is the single source of truth (rng_seed, roster_hash, pinned model_id, temperature=0.0); the modifier depends only on the closed-vocab `stance` token, robust to LLM wording drift; there is also a **stance re-derivation cross-check** (re-derive the stance by a deterministic rule, compare it with the LLM stance, fall back to the deterministic stance beyond tolerance). `--dry-run` swaps the LLM for a stub, zero calls and zero spend, as a CI and R3 safety net.

**SKILL.md front-matter + Guardrails**:
```yaml
---
name: crowd-scenario-engine
description: For an "already-computed" market event, rehearse how each type of Taiwan ETF investor
  reacts, producing a second-order reaction-chain narrative and a bounded, non-authoritative
  contrarian_modifier. Scenario rehearsal, not sentiment forecasting.
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [scenario, crowd, contrarian, ETF, Taiwan, narrative, non-authoritative]
    firewall: non-authoritative
---
```
G1 output allowlist (only narrative / samples / stance counts / chain / one scalar; any price/NAV/NTD pattern is a schema violation → abort); G2 `is_authoritative:false` hard-wired; G3 the PM treats it as just one signal, dual reasons required; G4 the LLM computes no number, persona text containing numbers is stripped by aggregate; G5 determinism.

## A.6 Clean-room AGPL discipline (honest version)

**The legal risk itself is low**: never distributed, no MiroFish code in the repo, original field names and formulas, ships MIT, stateless CLI with no §13 surface; the NOTICE only credits the idea inspiration. **But the project's self-imposed clean-room standard must be honestly met**:
1. `clean-room.md` states — "to **understand** the architecture we inspected the MiroFish source; **copied no** code / prompt / schema text; all field names, schemas and the stance / contrarian formulas are original." (Does **not** claim README-only.)
2. **Remove MiroFish's expression** from the architecture: do not replicate its module decomposition or private class names; re-argue the seed→personas→rounds→aggregate pipeline from first principles (or from `tw-stock-agent`'s own scorecard structure) so the design reads as an extension of `tw-stock-agent`'s contrarian layer.
3. If a true README-only clean-room is required: a person who has **not read the source** re-implements from the concept spec.

## A.7 CrowdScenarioReport JSON Schema (Draft 2020-12, the key defence)

The root-level `is_authoritative` is `const:false`; every object is `additionalProperties:false`; **no price/NAV/discount-premium/yield/weight/spend-cap-typed field exists anywhere in the schema**; the only decision scalar emitted is `contrarian_modifier ∈ [-1,+1]` (also `is_authoritative:false`, `formula_id` pinned).
```json
{
  "is_authoritative": { "const": false },
  "engine": { "seed": "<int>", "deterministic_core": { "const": true }, "model": "nemotron" },
  "scenario": { "scenario_id", "label", "shock_description", "horizon" },
  "reaction_chain": [ { "order", "trigger_archetype", "reacting_archetype",
                        "mechanism(enum)", "narrative" } ],
  "persona_samples": [ { "archetype_id", "stance", "register", "excerpt",
                         "is_synthetic": { "const": true } } ],
  "signals": { "crowding{value,direction}", "hype{value,direction}",
               "panic_euphoria∈[-1,1]", "tone_price_divergence∈[-1,1]" },
  "contrarian_modifier": { "value∈[-1,1]", "is_authoritative":{"const":false},
                           "formula_id":{"const":"contrarian-agg/1.0.0"},
                           "interpretation": ["fade_overbought","fade_oversold","no_tilt"] },
  "confidence": { "label(low/medium/high)", "rationale" },
  "provenance": { "inputs_read[{source,field,freshness}]", "method(const)" },
  "data_completeness": ["full","partial"],
  "disclaimer": { "minLength": 40, "required": true }
}
```
`engine.seed` + `signals` + `provenance.inputs_read` make the R5 claim (the conclusion is reproducible from observable signals) **machine-checkable**.

## A.8 Taiwan-retail persona archetype taxonomy (10 classes, closed set)

Each archetype carries stance / conviction / time_horizon / leverage_appetite / yield_sensitivity / herding / polarity / register / **base_weight (crowd-influence weight, not investment weight, Σ=1)**, and **a one-line citable behavioural prior**.

| archetype | Chinese | herding | polarity | base_weight | Behavioural prior (3–5 real citations must be supplied before ship) |
|---|---|---|---|---|---|
| long_term_holder | 存股族 | 0.15 | contra | 0.16 | 0050/0056 long-hold structure, dividend reinvestment |
| day_trader | 當沖客 | 0.85 | pro | 0.12 | Taiwan day-trade share, stop-loss cascades |
| yield_seeker | 殖利率派 | 0.40 | pro | 0.14 | ex-div rotation, sensitivity to dividend changes |
| leveraged_etf_player | 槓桿 ETF 玩家 | 0.70 | pro | 0.08 | forced unwind under 00631L-type volatility |
| foreign_institutional_lens | 外資視角 | 0.10 | contra | 0.12 | foreign net flows, index rebalancing |
| panic_retail | 恐慌散戶 | 0.90 | pro | 0.10 | contrarian indicator, buy-high-sell-low |
| ptt_dcard_trendwatch | PTT/Dcard 風向 | 0.95 | pro | 0.08 | narrative amplification, meme velocity |
| mom_savings_group | 媽媽存股社團 | 0.35 | contra | 0.08 | regular DCA growth, defensive stickiness |
| main_force_lens | 主力/中實戶 | 0.20 | contra | 0.06 | margin financing, big-holder fade |
| dca_newbie | 定期定額新手 | 0.75 | pro | 0.06 | post-2023 new accounts, recency bias |

Deliberately balanced: **pro-cyclical amplifiers 0.56** vs **contra-cyclical stabilisers 0.44**. `is_synthetic:true` is enforced; `base_weight` is isolated from investment weight.
> **Stress-test CREDIBILITY fix**: the "prior" column is currently a **placeholder description**; before ship, `personas.md` **must** attach 3–5 citable real priors to each archetype (TWSE retail-structure statistics, DCA account growth, etc.), otherwise this non-backtestable layer cannot be defended as a headline.

## A.9 Transparent deterministic contrarian_modifier formula (`contrarian-agg/1.0.0`)

Maps **one-to-one** to the four Sentiment/Contrarian signals in `tw-stock-agent`'s `scoring-rules.md`. Pure Python, seeded, no LLM; print the seed and you can hand-compute each term.
- **Step A population**: `stance = scenario_default_stance[archetype]` + seeded jitter; `influence_p = base_weight[a]*conviction_p` (normalised Σ=1).
- **Step B four sub-signals**: Crowding C = |Σ influence·sign(s)|; Hype H = pro-cyclical same-direction herding weighted; Panic/Euphoria P = signed tail emotion; Tone–Price Divergence D = crowd_tone − price_move (price_move is the **read-in** observed value).
- **Step C synthesis (frozen weights)**: `raw = -(0.30·C·dir + 0.25·(H_bull−H_panic) + 0.25·P − 0.20·D)`. The crowd over-leaning up = a negative contribution (lean cautious); crowd panic = a positive contribution (lean constructive).
- **Step D damping / clamp**: `completeness_factor = 1.0(full)/0.6(partial)`; `contrarian_modifier = clip(raw·factor, -1, +1)`; `no_tilt` band `[-0.15,+0.15]` (the engine's own NO_ACTION analogue).
- **worked example (00878 rate hike, seed=42, full) → −0.37, interpretation=fade_overbought**, hand-computable term by term, a regression fixture (the implementer must reproduce −0.37 from seed 42).

> **Stress-test VALUE important disclosure**: the Step A stance is a **table lookup of fixed archetype priors** + jitter; it does **not read** live crowding/hype/divergence. Under v3.1's pure-narrative side-rail, **this modifier enters no decision at all**, so "whether it is better than the existing contrarian score" no longer affects allocation correctness — it is only a **scenario-reference annotation** in the Pro report, its value pinned to the reaction_chain narrative. **We explicitly do not claim the modifier improves decisions, nor do we give it any chance to influence one.** If it were ever to carry a decision margin, one would have to (a) change the persona stances to react to `provenance.inputs_read` (margin_balance, turnover_vs_avg, headline_repetition, price_5d_return) rather than a lookup, and (b) **separately re-assess whether to lift the wiring firewall** — out of scope for this version.

## A.10 Demo 110-second runbook (the single authority, one cumulative clock, ≤110s / hard cap 120s)

Design law: the scenario engine gets the **opening visual + emotional peak**, but earn + spend + refused-spend get the **first and last lines** and most of the seconds. Every on-screen number is computed by deterministic Python.

| Segment | beat | Content (live / replayed marked) |
|---|---|---|
| 0:00–0:10 | Firewall opening line | "The crowd engine produces only narrative and one non-authoritative scalar; it touches no amount/weight/order, and StackFund places no securities order at any point." |
| 0:10–0:24 | **EARN (live Stripe)** | test-mode subscription collection, the P&L revenue ticks + a real Stripe object id. **LIVE** |
| 0:24–0:38 | SPEND (pre-staged) | the agent provisions a tool, the receipt lands the P&L cost. **All but one held-back are pre-provisioned** |
| 0:38–0:50 | **REFUSED SPEND (live error path)** | the second upgrade hits the monthly cap, the Stripe API hard-refuses → NO_ACTION + a one-line deterministic reason. Badge: SPEND REFUSED. |
| 0:50–0:78 | ★ Scenario engine WOW (pure replay, capped at 28s) | press ENTER → `--replay` loads `scenario_0056_cut.json`, <3s, zero LLM zero network, animate the three-stage reaction chain. At the bottom, a boxed `contrarian_modifier=+0.42` + a red `is_authoritative=FALSE`. Voiceover: "A fixed, **auditable** scenario rehearsal, **not a forecast and not backtested**." |
| 0:78–0:96 | HARD CUT back to the engine: the firewall appears | the PM view lists **only** the deterministic signals; the 0056 action prints **two independent hard reasons**; the crowd modifier is shown beside it only as a non-authoritative label. **Show the import graph on the spot: L4 never received the crowd layer — not "deleted and still holds", but "was never wired in at all"**. |
| 0:96–0:110 | CLOSE: viability | before/after P&L: revenue−cost is positive (or near break-even, the refused spend protecting the margin); the disclaimer is visible; "earn money, spend money, and refuse to spend when it isn't worth it." |

The engine takes ~82s (~75%) and gets the last line; the front's 28s is the peak. **Anti-cannibalisation**: a timing cue card per beat; the scenario beat is capped at 28s; on overrun **cut the narration, not the content**.

**Five demo must-fixes (folded in)**: ① the three live Stripe calls are the real blowup risk — mark live/replayed + ">5s alt-tab to the recording"; ② **forbid a live re-bake during the demo** (`--verify` only shows a pre-computed verify log or an offline assertion that the modifier scalar matches the checked-in expected value; the LLM text isn't byte-stable even at temp 0); ③ the static-card cut-line is a **first-class** fallback; ④ all reproducible artifacts are baked and checked in before live (Day-8 bake / Day-11 recording are on the critical path); ⑤ both the screen and the voiceover must say "reproducible ≠ validated".

## A.11 Build plan (6/19→6/30, firewall + Stripe earn/spend FIRST)

| Day | Task | pd |
|---|---|---|
| Day 1 (6/19) | **GO/NO-GO GATE [BLOCKING]**: verify Stripe TW dual-flow + TWSE/Yahoo reachability; fork tw-stock-agent, confirm SKILL.md loads | 1.0 |
| Day 2 (6/20) | lock the four schemas; freeze 0050/0056/00878 fixtures (incl. discount-premium/yield) | 1.0 |
| Day 3 (6/21) | deterministic scorecard (transparent formulas, R5) + cost optimizer (hard cap/reserve); unit-test the numbers | 1.0 |
| Day 4 (6/22) | **Stripe SPEND + REFUSED SPEND** (cap-breach → structured error → NO_ACTION, the hardest beat done early) | 1.0 |
| Day 5 (6/23) | Stripe EARN (subscription + test-mode collection into the P&L). The engine is end-to-end demoable (beats 1–4, 7) | 0.75 |
| Day 6 (6/24) | **firewall contract + hard-only PM + P&L**; five-layer enforcement + the **wiring CI invariant** (L4 import graph has no L3 / ContrarianSignal); firewall_test.py. **CORE FROZEN** | 1.0 |
| Day 7 (6/25) | scenario engine scaffold: personas.md (30 personas + prior citations), scenario_engine.py (RNG/tally/clamped formula). Numbers-only first | 1.0 |
| Day 8 (6/26) | **BAKE + LLM persona text**: one Nemotron call per sampled persona; bake `scenario_0056_cut.json`; add `--replay`/`--verify`; confirm byte-identical replay | 1.0 |
| Day 9 (6/27) | replay three-stage animation, non-authoritative chapter, scenario-rehearsal wording, hard-cut to the PM view; **the static-card cut-line is rehearsed and ready** | 1.0 |
| Day 10 (6/28) | NemoClaw wrap + end-to-end rehearsal (the final sandbox wrap); timing ≤110s; dry_run safety net | 1.0 |
| Day 11 (6/29) | record a silent 110s fallback; drill Stripe pop-ups / TWSE rate-limit / projector failure → alt-tab; confirm the disclaimer + scenario-rehearsal wording has no gaps | 0.75 |
| Day 12 (6/30) | buffer / submit; if the buffer is used up, the Day-9 static-card cut-line keeps the demo complete | 0.5 |

**Ordering rationale**: Days 1–6 deliver the entire scored engine + firewall before the front-of-house is even started; the most dangerous external dependency (Stripe TW) is resolved on Day 1, the most dangerous core beat (refused spend) on Day 4; the front (7–9) is a bolt-on and degradable.

## A.12 Regulatory and positioning guardrails (details)

- **Threat model (headlining exposure)**: ① SITA §4 advisory; ② Securities and Exchange Act §155 market integrity / appearance of manipulation; ③ R5/R6 credibility.
- **Defences assigned by "limb"**: the PRIMARY defence for SITA §4 is "no real consideration + a non-individualised publication framing + removal of absolute buy/sell instructions"; **the firewall is a correctness/credibility control, not the primary advisory defence** (corrects the old version's mis-assignment).
- **RebalancePlan reconciliation**: the post-paywall "reduce 0056 ±2pp" is rendered as **a non-individualised research illustration** ("an illustrative allocation under a research scenario", not "you should reduce"); generally available / not bespoke; on-screen note that it is not a recommendation to a specific person; test-mode / no fee removes the "consideration" trigger.
- **§155 breakdown**: the trading limb (wash / continuous trading) is **fully defused by zero orders**; the information limb §155(1)6 (disseminating information sufficient to affect price) is **only partly defused** — the published narrative must be a hypothetical stress scenario, never state how a named ETF will move, and forbid asserting a price direction for a named ticker.
- **Wording lexicon**: USE scenario rehearsal / stress test / synthetic persona samples / non-authoritative auxiliary signal; FORBID predict / forecast / accurately rehearse the future / real public opinion / sentiment forecast / sentiment engineering / buy-sell instruction / target-price guarantee. **The linter is a backstop** (token-matching can be bypassed); the PRIMARY control is **a prompt-level conditional-tone rule + human review of the single baked narrative**.
- **Four-tier disclaimer enforcement (placement is the control)**: Tier A (a SKILL.md load banner) / Tier B (every report, the schema's **required** `disclaimer` field, fail-closed) / Tier C (a micro-label on every persona card: "synthetic persona sample · scenario rehearsal · not real public opinion · not a forecast") / Tier D (the demo voiceover + a screen footer: "scenario rehearsal · synthetic personas · not a forecast · not real public opinion · not backtested; all amounts and weights are program-computed; StackFund places no securities order at any point").
- **Forward hard boundary**: if productisation simultaneously adds "real paying subscribers paying real consideration" + "directional advice on a named ticker", it likely crosses into a regulated securities investment advisory; **before going live one must** obtain the opinion of a qualified Taiwan securities-law adviser. This document is positioning / compliance framing, **not Taiwan legal advice**.

## A.13 Adversarial stress-test summary (all 5 hold_with_changes)

| Stress test | Finding (summary) | Neutralisation | Residual risk |
|---|---|---|---|
| **FW Firewall** | (v3.0 finding) the gate may be too loose (false independence); the tilt magnitude could move the P&L; spend could be triggered by the modifier; lacks a literal "zero-modifier re-run" check | **v3.1 structural resolution**: FACE becomes a pure-narrative side-rail, the modifier no longer enters L4 — the two-key gate / bounded clamp / threshold-flip / tilt are **all removed**; replaced by the **wiring firewall** (L4 does not import / does not receive ContrarianSignal, CI asserts the import graph) + spend gated solely by the VoI gate | **Low (lower than v3.0)**. The risk surface shrinks from "safely contain a write-back" to "ensure zero wiring", machine-checkable by import-graph CI; the residue is only the position-size corroboration of the L1 / L2 trunk itself |
| **DEMO feasibility** | the two choreographies conflict; the real blowup is the three Stripe calls; `--verify` live re-bake reintroduces non-determinism; the artifact doesn't exist | a unified runbook (single clock ≤110s); mark live/replayed + alt-tab; forbid live re-bake; static-card first-class fallback; Day-8/11 gated | **Medium**. The 110s slack is near zero; anti-cannibalisation relies on **rehearsal discipline**; Day-8 bake / Day-11 recording are on the critical path |
| **CREDIBILITY R5/R6** | the headline is LLM narrative, reproducible ≠ correct; priors are authored not observed; no backtest | disclose the modifier is weak, value pinned to narrative; attach citable priors per archetype; give the firewall / NO_ACTION equal weight in the demo, the action still holds after deleting the crowd; voiceover "not backtested" | **Medium (the most honest residue)**. The narrative is still unvalidated prose; synthetic priors are inherently non-backtestable. The line is held by is_authoritative=false + "scenario rehearsal not a forecast" + admitting "this is risk-scenario coverage, not forecasting accuracy" |
| **REGULATORY** | "firewall = primary advisory defence" mis-assignment; "zero orders → manipulation almost fully defused" overclaim; headlining makes "just research" harder to maintain | reassign defences by limb; render the RebalancePlan as a non-individualised illustration; split §155 into trading (full) / information (partial); add R2c; the forward hard boundary | **Medium**. The information limb is only partly defused; the demo (test-mode / no consideration / zero orders) is still within a research safe harbour, but this is positioning framing, not legal advice; going live needs counsel |
| **CLEAN-ROOM/VALUE** | the clean-room provenance can be proven false (cited a private class name that exists only in the source); the architecture borrows MiroFish's expression; the modifier's margin over the existing score is near zero | honestly restate the boundary, remove module/class references, (ideally) have someone who hasn't read the source re-implement; pin value to the reaction-chain narrative, downgrade the modifier | **Medium–Low**. Legal risk is low (never distributed, no code, MIT, no §13); the real risk is that, uncorrected, credibility collapses when a judge diffs the two repos → correcting the provenance is a non-negotiable must-fix |

**Summary**: the whole Core-B design passes the adversarial stress tests, **but only after folding in every required_fix**. The three most honest residual red lines (§1) should be stated proactively up front: reproducible ≠ validated, the modifier is no better than the existing score, and the real regulatory exposure is in the priced, directional RebalancePlan. Treating these three as a **proactively-disclosed sign of design maturity** is exactly the best proof that the face is eye-catching while the steering wheel is still clearly locked to the engine.
