# StackFund 架構分析（Mermaid，Core-B 排版優化版）

> 來源文件：`doc/StackFund_可行性報告.md`
>
> 本文件對齊可行性報告 v3.0「Core-B 架構定案版」。本次更新只整理 Mermaid 排版與可讀性，不加顏色、不改架構語意。

## 0. 撰寫假設與驗收標準

### 撰寫假設

- StackFund 的主體是自主經營的台股 ETF 研究微型事業；產品門面是「群眾情境推演引擎」。
- Stripe 只負責事業金流：訂閱、營運支出、SaaS provision、支出拒絕；不負責證券下單。
- Core-B 的核心契約是 FACE / ENGINE 分離：群眾情境引擎是 FACE，deterministic Python 主幹是 ENGINE。
- 群眾情境引擎只輸出敘事、人格樣本、反應鏈與一個非權威 `contrarian_modifier`；不得決定 price／NAV／yield／weight／spend-cap 等權威數字。
- RebalancePlan 的每個非零動作，都必須在移除群眾 modifier 後仍能由硬數據獨立辯護。

### 驗收標準

- 能看出 v3 從舊五層架構升級為 Core-B 六層架構。
- 能看出 L3 群眾情境引擎是側軌葉節點，不回寫 L1／L2／L5。
- 能看出 Portfolio Manager 的四步消費：hard-only first、two-key gate、bounded clamp、threshold-flip。
- Mermaid 圖只做排版優化，保持原版樣式，不加顏色或 theme。

---

## 1. 更新後可行性報告的架構判讀

| 分析面向 | v3 判讀 | 架構影響 |
|---|---|---|
| 產品門面 | Pro 方案賣二階反應鏈敘事，不是更強的數字 | 新增 Crowd Scenario FACE |
| 主幹可信度 | 所有市場數字、權重、支出由 deterministic Python 算 | L1／L2／L4／L5 保持權威 |
| 防火牆 | L3 只 emit typed object，不 import 計算或 Stripe 模組 | 需要 type、import、input、flag 四層控制 |
| PM 消費方式 | modifier 只能在硬數據同方向、雙理由成立時微調 | L4 必須有 gate／clamp／zero-modifier CI |
| 法規風險 | 防火牆是 correctness 控制，不是主要投顧防線 | 合規主線仍是非個別化、test-mode、零下單、免責 |
| Demo 策略 | 群眾引擎拿 WOW beat，但 earn／spend／refused-spend 保持主軸 | runbook 標 live／replayed，禁 live re-bake |

---

## 2. 系統總覽：FACE 搶眼，ENGINE 掌舵

這張圖只保留高階系統邊界，細部物件關係交給後續圖表，避免總覽圖變成電路圖。

```mermaid
flowchart TB
    subgraph Inputs["輸入與治理"]
        direction LR
        Subscriber["訂閱者"]
        MarketSources["市場資料來源<br/>TWSE / TPEX / MOPS / Yahoo / News"]
        StripeLayer["Stripe<br/>Billing / Skills / spend cap"]
        Sandbox["NemoClaw / OpenShell<br/>sandbox policy"]
    end

    subgraph Runtime["StackFund Runtime"]
        direction TB
        Boundary["受控代理執行邊界<br/>Hermes / Crowd / FinOps"]
        Engine["ENGINE：deterministic 主幹<br/>ETF Data Book -> Scorecard -> Portfolio -> FinOps -> Audit/P&L"]
        Face["FACE：非權威門面<br/>ScenarioSeed -> Crowd Scenario -> ContrarianSignal"]
        Firewall["Core-B 防火牆<br/>advisory only / no authoritative numbers / no primary spend trigger"]

        Boundary --> Engine
        Engine -->|"frozen projection"| Face
        Face -.->|"bounded modifier only"| Engine
        Face --> Firewall
    end

    subgraph Outputs["產品與證據"]
        direction LR
        Watch["Watch 免費數字卡"]
        Pro["Pro 群眾情境報告"]
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

### 架構重點

- `Watch` 賣 deterministic 事實；`Pro` 賣群眾情境敘事加底層研究結論。
- 群眾情境引擎是葉節點：讀 `ScenarioSeed`，輸出 `ContrarianSignal`，不能回寫 L1／L2／L5。
- L4 是方向盤：先產生 hard-only plan，再決定是否接受 bounded tilt。

---

## 3. Core-B 六層架構

```mermaid
flowchart LR
    subgraph EngineMain["ENGINE 主幹"]
        direction LR
        L1["L1 ETF Data Book<br/>deterministic ingest<br/>price / NAV / 折溢價 / 追蹤誤差 / 殖利率 / freshness"]
        L2["L2 Deterministic Scorecard<br/>trend / fundamental / valuation / catalyst / risk"]
        HardPlan["Hard-only RebalancePlan"]
        L4["L4 Portfolio Manager<br/>hard_plan first<br/>gate / clamp / threshold-flip"]
        L5["L5 FinOps & Execution<br/>Stripe earn / spend<br/>Value-of-Information gate"]
        L6["L6 Audit & Operational P&L<br/>Full provenance / replay / P&L"]
        L1 --> L2 --> HardPlan --> L4 --> L5 --> L6
    end

    subgraph FaceLane["FACE 側軌"]
        direction LR
        Seed["ScenarioSeed<br/>read-only, frozen, ordinal buckets"]
        L3["L3 Crowd Scenario Engine<br/>N=20-50 synthetic personas<br/>LLM 只寫文字"]
        Signal["ContrarianSignal<br/>bounded scalar [-1,+1]<br/>non-authoritative"]
        Seed -.-> L3 -.-> Signal
    end

    Tilt["TiltProvenance<br/>guardrail <= 2pp"]

    L1 -.->|"projection only"| Seed
    Signal -.->|"one gate + clamp only"| L4
    L4 --> Tilt --> L6
```

### 六層責任

| 層級 | 權威性 | 責任 | 不可做 |
|---|---|---|---|
| L1 ETF Data Book | 權威 | 擷取、正規化、標記 freshness、產生 DataBook / ScenarioSeed | 做投資結論 |
| L2 Deterministic Scorecard | 權威 | 以透明公式產生 scorecard 與 hard signals | 讓 LLM 心算 |
| L3 Crowd Scenario Engine | 非權威 | 產出二階反應鏈敘事、人格樣本、bounded modifier | 決定價格、權重、支出、下單 |
| L4 Portfolio Manager | 權威 | hard-only plan、gate、clamp、NO_ACTION、tilt provenance | 讓 modifier 創造或翻轉動作 |
| L5 FinOps & Execution | 權威 | Stripe earn/spend、refused spend、VoI gate | 被 crowd signal 主觸發 |
| L6 Audit & Operational P&L | 權威 | provenance、replay、Operational P&L、免責聲明 | 儲存敏感 token |

---

## 4. 主要營運流程

```mermaid
sequenceDiagram
    autonumber
    actor User as 訂閱者
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

    User->>Billing: Watch / Pro 訂閱或 test-mode 付款
    Billing-->>L6: revenue receipt

    Hermes->>Shell: 啟動受控 workflow
    Shell->>L1: 允許資料擷取
    L1->>L2: DataBook + hard metrics
    L1-->>L3: frozen ScenarioSeed only
    L2-->>L4: hard signals + hard-only plan

    alt Pro 報告且 VoI 允許跑情境
        L3->>L3: seeded personas + LLM reaction text
        L3-->>L4: ContrarianSignal(is_authoritative=false)
    else 低價值事件或 demo fallback
        L3-->>L4: no_tilt / replay / skipped
    end

    L4->>L4: hard-only first
    L4->>L4: two-key gate + bounded clamp
    L4->>L4: zero-modifier rerun

    alt hard-only 也支持同方向動作
        L4-->>L6: RebalancePlan + TiltProvenance
    else 只有 crowd tilt 才觸發
        L4-->>L6: NO_ACTION + threshold-flip reason
    end

    L5->>L5: deterministic Value-of-Information gate
    L5->>Stripe: provision / upgrade / downgrade
    alt 在 cap 與白名單內
        Stripe-->>L5: spend receipt
    else 超額或需人工核可
        Stripe-->>L5: refused spend
    end
    L5-->>L6: OperationalReceipt
```

---

## 5. 群眾情境防火牆

```mermaid
flowchart LR
    Seed["ScenarioSeed<br/>frozen ordinal context<br/>no raw price setters"]

    subgraph InputChecks["輸入 / import 檢查"]
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

    subgraph OutputChecks["輸出檢查"]
        direction TB
        TypeGuard["Type guard<br/>no price / NAV / yield / weight / cap fields"]
        FlagGuard["Flag guard<br/>assert is_authoritative=false"]
        Signal["ContrarianSignal<br/>modifier in [-1,+1]<br/>is_authoritative=false"]
        TypeGuard --> FlagGuard --> Signal
    end

    PM["L4 Portfolio Manager"]
    Audit["L6 Audit<br/>record only"]
    Reject["Schema violation<br/>abort / strip / fail closed"]

    Seed --> InputGuard --> Personas
    ImportGuard -.-> Personas
    Aggregate --> TypeGuard
    TypeGuard -->|"forbidden numeric/action field"| Reject
    FlagGuard -->|"flag not false"| Reject
    Signal -.->|"advisory only"| PM
    Signal -->|"provenance"| Audit
```

### 防火牆不變式

| 不變式 | 檢查方式 |
|---|---|
| L3 不輸出權威市場或動作欄位 | `CrowdScenarioReport` / `ContrarianSignal` schema fail-closed |
| L3 不 import 計算、Portfolio、Stripe 模組 | `test_firewall_no_imports` / import graph grep |
| L3 只讀 frozen `ScenarioSeed` | 無 setter，輸入已分桶 |
| `is_authoritative` 永遠為 false | schema const + runtime assert |
| 人格文字不得帶入數字決策 | forbidden-output scan / numeric-token strip |

---

## 6. Portfolio Manager 消費規則

```mermaid
flowchart TD
    Start["收到 ScoreCard 與可選 ContrarianSignal"]
    HardOnly["Step 1: hard-only plan<br/>modifier invisible"]
    HardEmpty{"hard_plan 為空<br/>或在容差內？"}
    NoActionEarly["NO_ACTION<br/>讀 modifier 前結束"]
    Gate["Step 2: two-key gate<br/>至少 2 個不同 factor family 同向<br/>modifier 同符號"]
    GatePass{"gate 通過？"}
    NoTilt["不套用 tilt<br/>保留 hard-only plan"]
    Clamp["Step 3: bounded clamp<br/>tilt <= min(2pp, 1x hard_delta)"]
    Rerun["Step 4: zero-modifier rerun<br/>同一 min-trade floor"]
    Flip{"只有加 tilt<br/>才會觸發動作？"}
    Rollback["回退 NO_ACTION<br/>threshold-flip 防護"]
    Final["RebalancePlan<br/>附獨立硬數據理由"]
    Provenance["TiltProvenance<br/>hard_delta / hard_signals / modifier / applied_tilt"]

    Start --> HardOnly --> HardEmpty
    HardEmpty -->|"是"| NoActionEarly
    HardEmpty -->|"否"| Gate --> GatePass
    GatePass -->|"否"| NoTilt
    GatePass -->|"是"| Clamp
    NoTilt --> Rerun
    Clamp --> Rerun
    Rerun --> Flip
    Flip -->|"是"| Rollback
    Flip -->|"否"| Final --> Provenance
```

### PM 設計解讀

- 群眾 modifier 只能放大硬數據已允許的方向，不能創造動作、翻轉方向或突破 hard band。
- `NO_ACTION` 必須能在讀取 modifier 前產生，否則 L3 會暗中成為決策主因。
- zero-modifier CI 是可機器檢測的核心：把 modifier 歸零後，動作仍需同方向成立並跨過門檻。

---

## 7. 資料契約與核心物件

v3 schema 從三份擴成四份：`ETFResearchReport`、`RebalancePlan`、`OperationalReceipt`、`CrowdScenarioReport`。同時新增 `ScenarioSeed`、`ContrarianSignal`、`TiltProvenance` 作為防火牆與可稽核性的關鍵物件。

```mermaid
erDiagram
    ETF ||--o{ DATA_BOOK : has
    DATA_BOOK ||--|| SCORECARD : produces
    DATA_BOOK ||--o| SCENARIO_SEED : projects
    SCENARIO_SEED ||--o| CROWD_SCENARIO_REPORT : rehearses
    CROWD_SCENARIO_REPORT ||--|| CONTRARIAN_SIGNAL : emits
    SCORECARD ||--o| REBALANCE_PLAN : justifies
    CONTRARIAN_SIGNAL }o--o| REBALANCE_PLAN : bounded_tilt
    REBALANCE_PLAN ||--o| TILT_PROVENANCE : records
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
        float final_delta_pp
        string no_action_reason
    }

    TILT_PROVENANCE {
        string id PK
        string decision_id FK
        string seed_id
        float hard_delta_pp
        float tilt_pp_applied
        string narrative_digest
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

### Schema-first 更新點

- `CrowdScenarioReport` 根層 `is_authoritative` 必須是 `false`，且 `additionalProperties:false`。
- `ContrarianSignal` 的唯一決策純量是 `contrarian_modifier ∈ [-1,+1]`，且也必須是非權威。
- `RebalancePlan` 必須保存 hard-only 理由、`NO_ACTION` 理由與 tilt provenance。
- `OperationalReceipt` 必須能表示 `spend`、`earn`、`refused_spend`、`blocked`、`manual_review`。
- 所有 schema 不得儲存敏感 token、明文金鑰或 payment credential。

---

## 8. Crowd Scenario Skill 管線

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

### Clean-room 與價值判讀

| 判讀 | 架構處理 |
|---|---|
| 不直接整合 MiroFish | AGPL、常駐服務、OASIS/Zep、高 LLM 成本皆不適合 MVP |
| 採 clean-room 蒸餾 | 只取「異質人格反應形成二階鏈」概念，不複製 code／prompt／schema |
| modifier 不宣稱更準 | 價值釘在 reaction_chain 敘事，不釘在純量 |
| 可重現不等於已驗證 | `seed.lock.json` 讓 replay 可重現，但 demo 必須說明未經回測 |
| 門面可降級 | 6/29 落後時砍 replay animation，改 static card，核心不動 |

---

## 9. FinOps、訂閱與單一 P&L

```mermaid
flowchart LR
    subgraph Plans["Stripe 訂閱方案"]
        direction TB
        WatchPlan["Watch NT$0<br/>deterministic number card"]
        ProPlan["Pro ~NT$299/月<br/>crowd scenario narrative"]
        DeskPlan["Desk ~NT$999/月<br/>roadmap"]
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

### FinOps 防火牆

- `contrarian_modifier` 不能成為支出主觸發，只能作 tie-breaker。
- 付費報告是否值得跑，由 deterministic VoI gate 判斷。
- Refused spend 是 demo 的核心 beat：代理不只會花錢，也能在不值得時拒絕花錢。

---

## 10. Demo 與建置路線

```mermaid
flowchart TD
    subgraph Core["Days 1-6：先凍結核心"]
        direction TB
        D1["Day 1<br/>Stripe TW 雙流 + TWSE/Yahoo 可達"]
        D2["Day 2<br/>鎖四份 schema + freeze fixtures"]
        D3["Day 3<br/>scorecard + cost optimizer + unit tests"]
        D4["Day 4<br/>Stripe SPEND + REFUSED SPEND"]
        D5["Day 5<br/>Stripe EARN + P&L"]
        D6["Day 6<br/>firewall + PM tilt + zero-modifier CI<br/>CORE FROZEN"]
        D1 --> D2 --> D3 --> D4 --> D5 --> D6
    end

    subgraph FaceBuild["Days 7-9：門面可降級"]
        direction TB
        D7["Day 7<br/>crowd scenario scaffold"]
        D8["Day 8<br/>bake LLM persona text + replay artifact"]
        D9["Day 9<br/>animation + non-authoritative badge + hard cut"]
        D7 --> D8 --> D9
    end

    subgraph Delivery["Days 10-12：交付"]
        direction TB
        D10["Day 10<br/>NemoClaw wrap + rehearsal"]
        D11["Day 11<br/>110s fallback recording + drills"]
        D12["Day 12<br/>buffer / submit"]
        D10 --> D11 --> D12
    end

    Core --> FaceBuild --> Delivery
```

### 110 秒 demo 節奏

| 時段 | 作用 | 架構訊號 |
|---|---|---|
| 0:00-0:10 | 防火牆開場 | 群眾引擎非權威、不碰金額/權重/下單 |
| 0:10-0:24 | EARN live | Stripe Billing 收款進 P&L |
| 0:24-0:38 | SPEND pre-staged | agent provision 工具，成本進 P&L |
| 0:38-0:50 | REFUSED SPEND live error path | Stripe cap 硬拒，代理 NO_ACTION |
| 0:50-0:78 | 情境引擎 WOW replay | `is_authoritative=false`，可稽核但未驗證 |
| 0:78-0:96 | Hard cut 回引擎 | 刪掉群眾面板後，同一動作仍成立 |
| 0:96-0:110 | viability close | before/after P&L 與免責聲明 |

---

## 11. 風險對應圖

```mermaid
flowchart LR
    subgraph Risks["風險"]
        direction TB
        R1["R1 Stripe TW earn / spend 資格"]
        R2["R2 SITA 投顧法規"]
        R2B["R2b 市場誠信 / 資訊型操縱觀感"]
        R2C["R2c headline 化削弱研究 carve-out"]
        R3["R3 live demo 執行出包"]
        R4["R4 資料來源穩定度"]
        R5["R5 可重現不等於已驗證"]
        R6["R6 agency 認知"]
        R7["R7 clean-room / 授權 credibility"]
    end

    subgraph Mitigations["緩解"]
        direction TB
        M1["dry_run / free_only / live_limited"]
        M2["非個別化出版品 framing<br/>test-mode / 零下單 / 去買賣指令"]
        M2B["假設性壓力情境<br/>不主張指名 ETF 價格方向"]
        M2C["情境推演 / 壓力測試 wording"]
        M3["pre-stage + replay + fallback recording"]
        M4["官方來源優先 + freshness + fixture fallback"]
        M5["主動揭露未回測<br/>modifier 價值釘敘事"]
        M6["展示 provision / cap breach / downgrade"]
        M7["誠實 clean-room.md<br/>不複製 code/prompt/schema"]
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

### 風險判讀更新

| 風險 | 更新後架構回應 |
|---|---|
| 防火牆 gate 太鬆 | 兩個不同 factor family、bounded clamp、zero-modifier CI |
| modifier 影響支出 | FinOps 由 VoI gate 主導，modifier 最多 tie-breaker |
| demo 三筆 Stripe 失敗 | live/replayed 標示、pre-staged spend、fallback recording |
| headline 敘事被誤讀成預測 | 用「情境推演／壓力測試」，禁「預測／預報」 |
| 法規曝險 | 主要防線是非個別化、test-mode、零下單、免責，不是防火牆 |
| clean-room credibility | 誠實承認曾理解 source，但未複製 code／prompt／schema |

---

## 12. 關鍵設計決策摘要

| 決策 | 為什麼重要 |
|---|---|
| 群眾引擎升為產品門面，但非權威 | 增加差異化，同時避免污染核心決策 |
| Core-B 六層架構 | 把 FACE 與 ENGINE 的邊界顯性化 |
| `ContrarianSignal` typed output | 讓 L3 只能以有界、可稽核、非權威物件進入 L4 |
| hard-only first | 防止群眾敘事成為動作唯一原因 |
| threshold-flip 防護 | 若只有 crowd tilt 才讓動作跨門檻，回退 NO_ACTION |
| zero-modifier CI | 把「移除群眾仍成立」變成可測不變式 |
| VoI gate 控制付費報告 | 讓 spend 決策仍由硬資料與預算控制 |

---

## 13. 文件結論

更新後的 StackFund 架構不再只是「台股 ETF 研究台 + Stripe 金流」。v3 把產品門面改成「群眾情境推演引擎」，但最重要的架構價值在於它被嚴格隔離：群眾層負責可展示、可銷售、可重播的二階敘事；deterministic 主幹負責所有數字、權重、支出與 P&L。

Core-B 成立的條件是三個可檢查承諾：

- 群眾層只輸出 `ContrarianSignal`，且 `is_authoritative=false`。
- L4 的每個非零 RebalancePlan 都能在 modifier 歸零後由硬數據同方向成立。
- L5 的 spend 由 deterministic VoI gate 與 Stripe 硬上限控制，群眾層不能主觸發支出。

因此，這份架構分析的結論是：v3 的可行性比舊版更有 presentation 優勢，但也更依賴防火牆、用語、demo 紀律與主動揭露。只要 Day 6 前凍結 Core（防火牆、PM tilt、P&L、zero-modifier CI），即使最後砍掉情境動畫，StackFund 仍保有 earn／spend／run real operations 的核心說服力。
