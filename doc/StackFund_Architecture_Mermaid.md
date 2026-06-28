# StackFund Architecture Analysis (Mermaid, Core-B layout-optimised edition)

> Source document: `doc/StackFund_Feasibility_Report.md` · 中文版 / Chinese: [StackFund_架構分析_Mermaid.md](StackFund_架構分析_Mermaid.md)
>
> This document is aligned with feasibility report v3.1, "Core-B finalised architecture (FACE as a pure-narrative side-rail)". This update realises the v3.1 architecture change: FACE becomes a pure-narrative side-rail, the crowd layer never writes back to L4 — the two-key gate / bounded clamp / threshold-flip / TiltProvenance / zero-modifier CI are removed and replaced by an "L4 is not wired" structural firewall.

## 0. Authoring assumptions and acceptance criteria

### Authoring assumptions

- StackFund's core is an autonomously-run Taiwan-ETF research micro-business; the product front-of-house is the "crowd-scenario rehearsal engine".
- Stripe handles only the business cash flow: subscriptions, operating spend, SaaS provisioning, spend refusal; it never places securities orders.
- Core-B's central contract is the FACE / ENGINE separation: the crowd-scenario engine is FACE; the deterministic Python trunk is ENGINE.
- The crowd-scenario engine emits only narrative, persona samples, a reaction chain and one non-authoritative `contrarian_modifier`; it must not decide authoritative numbers like price / NAV / yield / weight / spend-cap, and never writes back to any decision layer.
- The RebalancePlan is decided by the ScoreCard alone; the crowd modifier never enters the decision path, so every non-zero action is, by construction, independently justified by hard data.

### Acceptance criteria

- You can see v3 upgrade from the old five-layer architecture to the Core-B six-layer architecture.
- You can see that the L3 crowd-scenario engine is a pure-narrative side-rail leaf node that does not write back to L1 / L2 / L4 / L5 (zero wiring to the decision path).
- You can see that the Portfolio Manager consumes only the ScoreCard's output (hard-only plan / NO_ACTION) and never consumes the modifier.
- The Mermaid diagrams are layout-optimised only, keeping the original style — no colours or themes added.

---

## 1. Reading of the updated feasibility report's architecture

| Analysis dimension | v3 reading | Architecture impact |
|---|---|---|
| Product front | The Pro plan sells a second-order reaction-chain narrative, not stronger numbers | Adds the Crowd Scenario FACE |
| Trunk credibility | All market numbers, weights and spend are computed by deterministic Python | L1 / L2 / L4 / L5 stay authoritative |
| Firewall | L3 only emits typed objects, imports no compute or Stripe modules, and is not wired to the decision path | Needs five layers of control: type, import, input, flag, **wiring** |
| How the PM consumes | **L4 consumes no modifier at all — only the ScoreCard** | L4 does not import / does not receive ContrarianSignal (wiring CI) |
| Regulatory risk | The firewall is a correctness control, not the primary advisory defence | The compliance line is still: non-individualised, test-mode, zero orders, disclaimer |
| Demo strategy | The crowd engine takes the WOW beat, but earn / spend / refused-spend stay the spine | The runbook marks live / replayed; live re-bake is forbidden |

---

## 2. System overview: FACE catches the eye, ENGINE steers

This diagram keeps only the high-level system boundaries; detailed object relationships are left to the later diagrams, so the overview doesn't become a circuit diagram.

```mermaid
flowchart TB
    subgraph Inputs["Inputs & governance"]
        direction LR
        Subscriber["Subscriber"]
        MarketSources["Market data sources<br/>TWSE / TPEX / MOPS / Yahoo / News"]
        StripeLayer["Stripe<br/>Billing / Skills / spend cap"]
        Sandbox["NemoClaw / OpenShell<br/>sandbox policy"]
    end

    subgraph Runtime["StackFund Runtime"]
        direction TB
        Boundary["Controlled-agent execution boundary<br/>Hermes / Crowd / FinOps"]
        Engine["ENGINE: deterministic trunk<br/>ETF Data Book -> Scorecard -> Portfolio -> FinOps -> Audit/P&L"]
        Face["FACE: non-authoritative front<br/>ScenarioSeed -> Crowd Scenario -> ContrarianSignal"]
        Firewall["Core-B firewall<br/>narrative only / no authoritative numbers / no write-back to engine"]

        Boundary --> Engine
        Engine -->|"frozen projection"| Face
        Face --> Firewall
    end

    subgraph Outputs["Product & evidence"]
        direction LR
        Watch["Watch free number card"]
        Pro["Pro crowd-scenario report"]
        Desk["Desk roadmap"]
        PNL["Operational P&L<br/>before / after evidence"]
        Watch --> Pro -.-> Desk
        Pro --> PNL
    end

    Subscriber --> StripeLayer
    MarketSources --> Boundary
    StripeLayer --> Boundary
    Sandbox --> Boundary
    Engine --> Watch
    Engine --> Pro
    Engine --> PNL
```

### Architecture highlights

- `Watch` sells deterministic facts; `Pro` sells the crowd-scenario narrative plus the underlying research conclusion.
- The crowd-scenario engine is a pure-narrative leaf node: it reads `ScenarioSeed` and emits a `ContrarianSignal` that flows only to the Pro report and the audit — it cannot write back to L1 / L2 / L4 / L5.
- L4 is the steering wheel: it consumes only the ScoreCard to produce a hard-only plan or NO_ACTION, and accepts no tilt.

---

## 3. The Core-B six-layer architecture

```mermaid
flowchart LR
    subgraph EngineMain["ENGINE trunk"]
        direction LR
        L1["L1 ETF Data Book<br/>deterministic ingest<br/>price / NAV / discount-premium / tracking error / yield / freshness"]
        L2["L2 Deterministic Scorecard<br/>trend / fundamental / valuation / catalyst / risk"]
        HardPlan["Hard-only RebalancePlan"]
        L4["L4 Portfolio Manager<br/>ScoreCard only<br/>hard-only plan / NO_ACTION"]
        L5["L5 FinOps & Execution<br/>Stripe earn / spend<br/>Value-of-Information gate"]
        L6["L6 Audit & Operational P&L<br/>Full provenance / replay / P&L"]
        L1 --> L2 --> HardPlan --> L4 --> L5 --> L6
    end

    subgraph FaceLane["FACE side-rail (pure narrative)"]
        direction LR
        Seed["ScenarioSeed<br/>read-only, frozen, ordinal buckets"]
        L3["L3 Crowd Scenario Engine<br/>N=20-50 synthetic personas<br/>LLM writes text only"]
        Signal["ContrarianSignal<br/>narrative annotation [-1,+1]<br/>non-authoritative"]
        Seed -.-> L3 -.-> Signal
    end

    ProReport["Pro report<br/>narrative = product"]

    L1 -.->|"projection only"| Seed
    Signal -.->|"narrative only, NO write-back"| ProReport
    Signal -.->|"record only"| L6
```

### Six-layer responsibilities

| Layer | Authority | Responsibility | Must not |
|---|---|---|---|
| L1 ETF Data Book | Authoritative | Fetch, normalise, mark freshness, produce DataBook / ScenarioSeed | Draw investment conclusions |
| L2 Deterministic Scorecard | Authoritative | Produce the scorecard and hard signals via transparent formulas | Let the LLM do mental arithmetic |
| L3 Crowd Scenario Engine | Non-authoritative | Produce the second-order reaction-chain narrative, persona samples, and a non-authoritative modifier annotation | Decide price, weight, spend or orders, or write back to any decision layer |
| L4 Portfolio Manager | Authoritative | Consume only the ScoreCard to produce a hard-only plan, NO_ACTION, decision provenance | Import or receive ContrarianSignal |
| L5 FinOps & Execution | Authoritative | Stripe earn/spend, refused spend, VoI gate | Be primarily triggered by a crowd signal |
| L6 Audit & Operational P&L | Authoritative | Provenance, replay, Operational P&L, disclaimer | Store sensitive tokens |

---

## 4. Main operational flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Subscriber
    participant Billing as Stripe Billing
    participant Hermes as Hermes Agent
    participant Shell as OpenShell
    participant L1 as ETF Data Book
    participant L2 as Scorecard
    participant L3 as Crowd Scenario FACE
    participant L4 as Portfolio Manager
    participant L5 as FinOps
    participant Stripe as Stripe Skills
    participant L6 as Audit & P&L

    User->>Billing: Watch / Pro subscription or test-mode payment
    Billing-->>L6: revenue receipt

    Hermes->>Shell: start controlled workflow
    Shell->>L1: allow data fetch
    L1->>L2: DataBook + hard metrics
    L1-->>L3: frozen ScenarioSeed only
    L2-->>L4: hard signals + hard-only plan

    alt Pro report and VoI allows running the scenario
        L3->>L3: seeded personas + LLM reaction text
        L3-->>L6: CrowdScenarioReport + ContrarianSignal (record only, non-authoritative)
    else low-value event or demo fallback
        L3->>L3: replay / skipped (no LLM)
    end

    Note over L3,L4: L4 does not import / does not receive ContrarianSignal (wiring firewall)
    L4->>L4: build plan from ScoreCard only (no modifier)

    alt hard-only plan crosses the threshold
        L4-->>L6: RebalancePlan + DecisionProvenance
    else within tolerance
        L4-->>L6: NO_ACTION + hard-only reason
    end

    L5->>L5: deterministic Value-of-Information gate
    L5->>Stripe: provision / upgrade / downgrade
    alt within cap and allowlist
        Stripe-->>L5: spend receipt
    else over budget or needs manual approval
        Stripe-->>L5: refused spend
    end
    L5-->>L6: OperationalReceipt
```

---

## 5. The crowd-scenario firewall

```mermaid
flowchart LR
    Seed["ScenarioSeed<br/>frozen ordinal context<br/>no raw price setters"]

    subgraph InputChecks["Input / import checks"]
        direction TB
        InputGuard["Input guard<br/>ScenarioSeed read-only"]
        ImportGuard["Import guard<br/>no L1/L2/L4/L5 compute imports"]
    end

    subgraph CrowdLayer["L3 Crowd Scenario Engine"]
        direction LR
        Personas["Synthetic personas<br/>N=20-50"]
        Reaction["LLM reaction text<br/>stance token only"]
        Aggregate["Deterministic aggregate<br/>closed-vocab stance"]
        Personas --> Reaction --> Aggregate
    end

    subgraph OutputChecks["Output checks"]
        direction TB
        TypeGuard["Type guard<br/>no price / NAV / yield / weight / cap fields"]
        FlagGuard["Flag guard<br/>assert is_authoritative=false"]
        WireGuard["Wiring guard<br/>L4 import graph has no L3/Signal"]
        Signal["ContrarianSignal<br/>modifier in [-1,+1]<br/>is_authoritative=false"]
        TypeGuard --> FlagGuard --> WireGuard --> Signal
    end

    ProReport["Pro report<br/>narrative = product"]
    L4Decision["L4 decision path<br/>ScoreCard only (no Signal)"]
    Audit["L6 Audit<br/>record only"]
    Reject["Schema violation<br/>abort / strip / fail closed"]

    Seed --> InputGuard --> Personas
    ImportGuard -.-> Personas
    Aggregate --> TypeGuard
    TypeGuard -->|"forbidden numeric/action field"| Reject
    FlagGuard -->|"flag not false"| Reject
    Signal -.->|"narrative only, NO write-back"| ProReport
    Signal -->|"record only"| Audit
    WireGuard --x L4Decision
```

### Firewall invariants

| Invariant | How it is checked |
|---|---|
| L3 emits no authoritative market or action fields | `CrowdScenarioReport` / `ContrarianSignal` schema, fail-closed |
| L3 imports no compute, Portfolio or Stripe modules | `test_firewall_no_imports` / import-graph grep |
| L3 reads only the frozen `ScenarioSeed` | No setters; inputs are already bucketed |
| `is_authoritative` is always false | Schema const + runtime assert |
| Persona text must not carry into a numeric decision | Forbidden-output scan / numeric-token strip |
| The L4 decision path does not receive `ContrarianSignal` | L4 import-graph grep; `build_rebalance_plan` signature takes only `ScoreCard` |

---

## 6. Portfolio Manager decision rule (pure hard data, no modifier consumption)

```mermaid
flowchart TD
    Start["Receive ScoreCard<br/>(no ContrarianSignal parameter)"]
    HardOnly["build_plan_from_scorecard<br/>sole input: ScoreCard"]
    HardEmpty{"hard_plan empty<br/>or within tolerance?"}
    NoAction["NO_ACTION<br/>with hard-only reason"]
    Final["RebalancePlan<br/>final_delta = hard_delta<br/>with two independent hard reasons"]
    Provenance["DecisionProvenance<br/>scorecard_id / hard_delta / hard_signals"]

    Start --> HardOnly --> HardEmpty
    HardEmpty -->|"yes"| NoAction
    HardEmpty -->|"no"| Final --> Provenance
```

### PM design reading

- The crowd modifier never enters L4; the RebalancePlan is decided by the ScoreCard alone and is independently justifiable by construction.
- L4 simply never receives the modifier, so there is no possibility of "L3 quietly becoming the deciding factor"; both NO_ACTION and actions are pure hard data.
- The wiring CI is the machine-checkable core: it asserts that the L4 import graph contains no L3 / ContrarianSignal, and that the `build_rebalance_plan` signature takes only the ScoreCard.

---

## 7. Data contracts and core objects

The v3 schema set grows from three to four: `ETFResearchReport`, `RebalancePlan`, `OperationalReceipt`, `CrowdScenarioReport`. It also adds `ScenarioSeed`, `ContrarianSignal`, `DecisionProvenance` as the key objects for the firewall and auditability. **The crowd-layer output (`ContrarianSignal`) is wired only to the report and the audit, never to the `RebalancePlan`.**

```mermaid
erDiagram
    ETF ||--o{ DATA_BOOK : has
    DATA_BOOK ||--|| SCORECARD : produces
    DATA_BOOK ||--o| SCENARIO_SEED : projects
    SCENARIO_SEED ||--o| CROWD_SCENARIO_REPORT : rehearses
    CROWD_SCENARIO_REPORT ||--|| CONTRARIAN_SIGNAL : emits
    SCORECARD ||--o| REBALANCE_PLAN : justifies
    REBALANCE_PLAN ||--o| DECISION_PROVENANCE : records
    SUBSCRIPTION ||--o{ OPERATIONAL_RECEIPT : revenue
    TOOL_SERVICE ||--o{ OPERATIONAL_RECEIPT : cost
    OPERATIONAL_RECEIPT }o--|| OPERATIONAL_PNL : rolls_up
    REBALANCE_PLAN }o--|| OPERATIONAL_PNL : evidence

    ETF {
        string symbol PK
        string name
        string market
    }

    DATA_BOOK {
        string id PK
        string etf_symbol FK
        datetime observed_at
        string freshness
        string book_hash
    }

    SCORECARD {
        string id PK
        string databook_id FK
        float trend_score
        float valuation_score
        float yield_score
        float risk_score
    }

    SCENARIO_SEED {
        string id PK
        string databook_id FK
        string event_label
        string seed_hash
        string ordinal_context
    }

    CROWD_SCENARIO_REPORT {
        string id PK
        string scenario_seed_id FK
        boolean is_authoritative
        string reaction_chain
        string persona_samples
        string disclaimer
    }

    CONTRARIAN_SIGNAL {
        string id PK
        string report_id FK
        float contrarian_modifier
        boolean is_authoritative
        string formula_id
    }

    REBALANCE_PLAN {
        string id PK
        string scorecard_id FK
        string action
        float hard_delta_pp
        string no_action_reason
    }

    DECISION_PROVENANCE {
        string id PK
        string decision_id FK
        string scorecard_id
        float hard_delta_pp
        string hard_signals
        string action
    }

    SUBSCRIPTION {
        string id PK
        string stripe_customer_id
        string plan
        string status
    }

    TOOL_SERVICE {
        string id PK
        string vendor
        string category
        string tier
    }

    OPERATIONAL_RECEIPT {
        string id PK
        string type
        string status
        float amount
        string reason
    }

    OPERATIONAL_PNL {
        string id PK
        float revenue
        float cost
        float gross_margin
        datetime period
    }
```

### Schema-first update points

- `CrowdScenarioReport`'s root-level `is_authoritative` must be `false`, with `additionalProperties:false`.
- `ContrarianSignal`'s `contrarian_modifier ∈ [-1,+1]` is a **non-authoritative report annotation**; it enters no decision path.
- `RebalancePlan` is produced by the ScoreCard alone, preserving hard-only reasons and the `NO_ACTION` reason (no tilt provenance).
- `OperationalReceipt` must be able to represent `spend`, `earn`, `refused_spend`, `blocked`, `manual_review`.
- No schema may store sensitive tokens, plaintext keys or payment credentials.

---

## 8. Crowd Scenario skill pipeline

```mermaid
flowchart TB
    DataBook["databook.json"]
    SeedBuilder["seed_builder.py<br/>Python only<br/>DataBook -> EventSeed"]
    SeedLock["seed.lock.json<br/>rng_seed / roster_hash / model_id / temp=0"]
    PersonaSim["persona_sim.py<br/>seeded roster + sparse edges"]
    Round1["Round 1<br/>persona independent reaction"]
    Round2["Round 2<br/>persona reads K neighbors"]
    Stance["closed-vocab stance token"]
    CrossCheck["stance re-derive check<br/>fallback if drift"]
    Aggregate["aggregate.py<br/>deterministic modifier + reaction_chain"]
    Narrative["final LLM narrative<br/>only from computed values"]
    Report["CrowdScenarioReport<br/>schema + disclaimer"]
    DryRun["--dry-run stub<br/>zero LLM / zero spend"]

    DataBook --> SeedBuilder --> SeedLock --> PersonaSim
    PersonaSim --> Round1 --> Round2 --> Stance --> CrossCheck --> Aggregate
    Aggregate --> Narrative --> Report
    DryRun -.-> PersonaSim
```

### Clean-room and value reading

| Reading | Architecture handling |
|---|---|
| Do not integrate MiroFish directly | AGPL, a long-running service, OASIS/Zep, high LLM cost — all unsuitable for an MVP |
| Use clean-room distillation | Take only the "heterogeneous personas form a second-order chain" idea; copy no code / prompt / schema |
| The modifier claims no greater accuracy | The value is pinned to the reaction_chain narrative, not to a scalar |
| Reproducible ≠ validated | `seed.lock.json` makes the replay reproducible, but the demo must state it is not backtested |
| The front is degradable | If behind schedule by 6/29, cut the replay animation for a static card; the core is untouched |

---

## 9. FinOps, subscriptions and a single P&L

```mermaid
flowchart LR
    subgraph Plans["Stripe subscription plans"]
        direction TB
        WatchPlan["Watch NT$0<br/>deterministic number card"]
        ProPlan["Pro ~NT$299/mo<br/>crowd scenario narrative"]
        DeskPlan["Desk ~NT$999/mo<br/>roadmap"]
    end

    subgraph Earn["EARN"]
        direction TB
        Billing["Stripe Billing"]
        Revenue["Revenue Receipt"]
        Billing --> Revenue
    end

    subgraph Spend["SPEND"]
        direction TB
        VoI["Value-of-Information gate<br/>materiality + cap headroom"]
        Provision["SaaS provision / upgrade / downgrade"]
        Refused["Refused Spend<br/>cap breach / not worth it"]
        VoI -->|"worth it"| Provision
        VoI -->|"not worth it"| Refused
    end

    subgraph PNL["Operational P&L"]
        direction TB
        Cost["Cost Receipt"]
        Margin["Revenue - Cost"]
        Evidence["before / after evidence"]
        Margin --> Evidence
    end

    WatchPlan --> Billing
    ProPlan --> Billing
    DeskPlan -.-> Billing
    Revenue --> Margin
    Provision --> Cost --> Margin
    Refused --> Evidence
```

### The FinOps firewall

- `contrarian_modifier` plays no part whatsoever in a spend decision (not even as a tie-breaker); spend is gated purely by the deterministic VoI gate.
- Whether a paid report is worth running is judged by the deterministic VoI gate.
- Refused spend is a core demo beat: the agent doesn't just spend money — it can also refuse to spend when it isn't worth it.

---

## 10. Demo and build roadmap

```mermaid
flowchart TD
    subgraph Core["Days 1-6: freeze the core first"]
        direction TB
        D1["Day 1<br/>Stripe TW dual-flow + TWSE/Yahoo reachable"]
        D2["Day 2<br/>lock the four schemas + freeze fixtures"]
        D3["Day 3<br/>scorecard + cost optimizer + unit tests"]
        D4["Day 4<br/>Stripe SPEND + REFUSED SPEND"]
        D5["Day 5<br/>Stripe EARN + P&L"]
        D6["Day 6<br/>firewall + hard-only PM + wiring CI<br/>CORE FROZEN"]
        D1 --> D2 --> D3 --> D4 --> D5 --> D6
    end

    subgraph FaceBuild["Days 7-9: the front is degradable"]
        direction TB
        D7["Day 7<br/>crowd scenario scaffold"]
        D8["Day 8<br/>bake LLM persona text + replay artifact"]
        D9["Day 9<br/>animation + non-authoritative badge + hard cut"]
        D7 --> D8 --> D9
    end

    subgraph Delivery["Days 10-12: delivery"]
        direction TB
        D10["Day 10<br/>NemoClaw wrap + rehearsal"]
        D11["Day 11<br/>110s fallback recording + drills"]
        D12["Day 12<br/>buffer / submit"]
        D10 --> D11 --> D12
    end

    Core --> FaceBuild --> Delivery
```

### The 110-second demo rhythm

| Segment | Purpose | Architecture signal |
|---|---|---|
| 0:00-0:10 | Firewall cold open | The crowd engine is non-authoritative, touches no amount/weight/order |
| 0:10-0:24 | EARN live | Stripe Billing revenue flows into the P&L |
| 0:24-0:38 | SPEND pre-staged | The agent provisions a tool; the cost flows into the P&L |
| 0:38-0:50 | REFUSED SPEND live error path | Stripe cap hard-refuses; the agent does NO_ACTION |
| 0:50-0:78 | Scenario engine WOW replay | `is_authoritative=false`; auditable but not validated |
| 0:78-0:96 | Hard cut back to the engine | Show the import graph: L4 never received the crowd layer (it was never wired in) |
| 0:96-0:110 | Viability close | Before/after P&L and the disclaimer |

---

## 11. Risk-mapping diagram

```mermaid
flowchart LR
    subgraph Risks["Risks"]
        direction TB
        R1["R1 Stripe TW earn / spend eligibility"]
        R2["R2 SITA investment-advisory regulation"]
        R2B["R2b Market integrity / appearance of information-based manipulation"]
        R2C["R2c Headlining weakens the research carve-out"]
        R3["R3 Live demo execution failure"]
        R4["R4 Data-source stability"]
        R5["R5 Reproducible is not validated"]
        R6["R6 Agency perception"]
        R7["R7 Clean-room / licensing credibility"]
    end

    subgraph Mitigations["Mitigations"]
        direction TB
        M1["dry_run / free_only / live_limited"]
        M2["Non-individualised publication framing<br/>test-mode / zero orders / no buy-sell instructions"]
        M2B["Hypothetical stress scenario<br/>no directional claim about a named ETF's price"]
        M2C["Scenario-rehearsal / stress-test wording"]
        M3["pre-stage + replay + fallback recording"]
        M4["official sources first + freshness + fixture fallback"]
        M5["proactively disclose not-backtested<br/>modifier value pinned to narrative"]
        M6["show provision / cap breach / downgrade"]
        M7["honest clean-room.md<br/>copy no code/prompt/schema"]
    end

    R1 --> M1
    R2 --> M2
    R2B --> M2B
    R2C --> M2C
    R3 --> M3
    R4 --> M4
    R5 --> M5
    R6 --> M6
    R7 --> M7
```

### Updated risk reading

| Risk | Updated architecture response |
|---|---|
| Firewall write-back risk | FACE is a pure-narrative side-rail; the modifier never enters L4; wiring CI (L4 import graph has no L3 / Signal) |
| Modifier influencing spend | Spend is gated purely by the VoI gate; the modifier plays no part (not even as a tie-breaker) |
| The three demo Stripe calls failing | live/replayed marking, pre-staged spend, fallback recording |
| Headline narrative misread as a forecast | Use "scenario rehearsal / stress test"; forbid "forecast / prediction" |
| Regulatory exposure | The primary defence is non-individualised, test-mode, zero orders, disclaimer — not the firewall |
| Clean-room credibility | Honestly acknowledge having understood the source, but copied no code / prompt / schema |

---

## 12. Summary of key design decisions

| Decision | Why it matters |
|---|---|
| Promote the crowd engine to the product front, but keep it non-authoritative | Adds differentiation while avoiding polluting the core decision |
| The Core-B six-layer architecture | Makes the FACE / ENGINE boundary explicit |
| `ContrarianSignal` typed output | Lets L3 emit only a bounded, auditable, non-authoritative object, wired only to the report and audit — never into L4 |
| Hard-only only | L4 consumes only the ScoreCard; the crowd narrative never enters a decision |
| The wiring firewall | L4 does not import / does not receive ContrarianSignal — structurally zero-wired |
| The wiring CI | Turns "L4 never wired in the crowd layer" into a testable invariant (import graph) |
| The VoI gate controlling paid reports | Keeps the spend decision governed by hard data and budget |

---

## 13. Document conclusion

The updated StackFund architecture is no longer just "a Taiwan-ETF research desk + Stripe cash flow". v3 makes the product front-of-house a "crowd-scenario rehearsal engine", but the most important architectural value is that it is strictly isolated: the crowd layer owns the demonstrable, sellable, replayable second-order narrative; the deterministic trunk owns all numbers, weights, spend and P&L.

Core-B holds on three checkable commitments:

- The crowd layer emits only a `ContrarianSignal`, with `is_authoritative=false`.
- Every RebalancePlan in L4 is decided by the ScoreCard alone; the crowd layer never enters the decision path (provable by the wiring CI).
- L5's spend is governed by the deterministic VoI gate and a hard Stripe cap; the crowd layer cannot primarily trigger a spend.

So the conclusion of this architecture analysis is: v3 is more presentation-advantaged than the old version, but also more dependent on the firewall, the wording, demo discipline and proactive disclosure. As long as the Core is frozen before Day 6 (firewall, hard-only PM, P&L, wiring CI), even if the scenario animation is cut at the end, StackFund still retains the core persuasiveness of earn / spend / run real operations.
