# StackFund 架構分析（Mermaid，Core-B 排版優化版）

> 來源文件：`doc/StackFund_可行性報告.md` · English: [StackFund_Architecture_Mermaid.md](StackFund_Architecture_Mermaid.md)
>
> 本文件對齊可行性報告 v3.1「Core-B 架構定案版（FACE 純敘事側軌）」。本次更新落實 v3.1 架構變更：FACE 改為純敘事側軌，群眾層不回寫 L4——移除 two-key gate／bounded clamp／threshold-flip／TiltProvenance／zero-modifier CI，改以「L4 不接線」結構防火牆取代。

## 0. 撰寫假設與驗收標準

### 撰寫假設

- StackFund 的主體是自主經營的台股 ETF 研究微型事業；產品門面是「群眾情境推演引擎」。
- Stripe 只負責事業金流：訂閱、營運支出、SaaS provision、支出拒絕；不負責證券下單。
- Core-B 的核心契約是 FACE / ENGINE 分離：群眾情境引擎是 FACE，deterministic Python 主幹是 ENGINE。
- 群眾情境引擎只輸出敘事、人格樣本、反應鏈與一個非權威 `contrarian_modifier`；不得決定 price／NAV／yield／weight／spend-cap 等權威數字，也不回寫任何決策層。
- RebalancePlan 由 ScoreCard 單獨決定；群眾 modifier 不進入決策路徑，故每個非零動作按建構即由硬數據獨立辯護。

### 驗收標準

- 能看出 v3 從舊五層架構升級為 Core-B 六層架構。
- 能看出 L3 群眾情境引擎是純敘事側軌葉節點，不回寫 L1／L2／L4／L5（對決策路徑零連線）。
- 能看出 Portfolio Manager 只吃 ScoreCard 產出 hard-only plan／NO_ACTION，完全不消費 modifier。
- Mermaid 圖只做排版優化，保持原版樣式，不加顏色或 theme。

---

## 1. 更新後可行性報告的架構判讀

| 分析面向 | v3 判讀 | 架構影響 |
|---|---|---|
| 產品門面 | Pro 方案賣二階反應鏈敘事，不是更強的數字 | 新增 Crowd Scenario FACE |
| 主幹可信度 | 所有市場數字、權重、支出由 deterministic Python 算 | L1／L2／L4／L5 保持權威 |
| 防火牆 | L3 只 emit typed object，不 import 計算或 Stripe 模組，且不連決策路徑 | 需要 type、import、input、flag、**接線** 五層控制 |
| PM 消費方式 | **L4 完全不消費 modifier，只吃 ScoreCard** | L4 不 import／不接收 ContrarianSignal（接線 CI） |
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
        Firewall["Core-B 防火牆<br/>narrative only / no authoritative numbers / no write-back to engine"]

        Boundary --> Engine
        Engine -->|"frozen projection"| Face
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
- 群眾情境引擎是純敘事葉節點：讀 `ScenarioSeed`，輸出 `ContrarianSignal` 只流向 Pro 報告與稽核，不能回寫 L1／L2／L4／L5。
- L4 是方向盤：只吃 ScoreCard 產生 hard-only plan 或 NO_ACTION，不接收任何 tilt。

---

## 3. Core-B 六層架構

```mermaid
flowchart LR
    subgraph EngineMain["ENGINE 主幹"]
        direction LR
        L1["L1 ETF Data Book<br/>deterministic ingest<br/>price / NAV / 折溢價 / 追蹤誤差 / 殖利率 / freshness"]
        L2["L2 Deterministic Scorecard<br/>trend / fundamental / valuation / catalyst / risk"]
        HardPlan["Hard-only RebalancePlan"]
        L4["L4 Portfolio Manager<br/>ScoreCard only<br/>hard-only plan / NO_ACTION"]
        L5["L5 FinOps & Execution<br/>Stripe earn / spend<br/>Value-of-Information gate"]
        L6["L6 Audit & Operational P&L<br/>Full provenance / replay / P&L"]
        L1 --> L2 --> HardPlan --> L4 --> L5 --> L6
    end

    subgraph FaceLane["FACE 側軌（純敘事）"]
        direction LR
        Seed["ScenarioSeed<br/>read-only, frozen, ordinal buckets"]
        L3["L3 Crowd Scenario Engine<br/>N=20-50 synthetic personas<br/>LLM 只寫文字"]
        Signal["ContrarianSignal<br/>narrative annotation [-1,+1]<br/>non-authoritative"]
        Seed -.-> L3 -.-> Signal
    end

    ProReport["Pro 報告<br/>敘事＝產品"]

    L1 -.->|"projection only"| Seed
    Signal -.->|"narrative only, NO write-back"| ProReport
    Signal -.->|"record only"| L6
```

### 六層責任

| 層級 | 權威性 | 責任 | 不可做 |
|---|---|---|---|
| L1 ETF Data Book | 權威 | 擷取、正規化、標記 freshness、產生 DataBook / ScenarioSeed | 做投資結論 |
| L2 Deterministic Scorecard | 權威 | 以透明公式產生 scorecard 與 hard signals | 讓 LLM 心算 |
| L3 Crowd Scenario Engine | 非權威 | 產出二階反應鏈敘事、人格樣本、非權威 modifier 標註 | 決定價格、權重、支出、下單，或回寫任何決策層 |
| L4 Portfolio Manager | 權威 | 只吃 ScoreCard 產 hard-only plan、NO_ACTION、decision provenance | import 或接收 ContrarianSignal |
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
        L3-->>L6: CrowdScenarioReport + ContrarianSignal (record only, non-authoritative)
    else 低價值事件或 demo fallback
        L3->>L3: replay / skipped (no LLM)
    end

    Note over L3,L4: L4 不 import、不接收 ContrarianSignal（接線防火牆）
    L4->>L4: build plan from ScoreCard only (no modifier)

    alt hard-only plan 跨過門檻
        L4-->>L6: RebalancePlan + DecisionProvenance
    else 在容差內
        L4-->>L6: NO_ACTION + hard-only reason
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
        WireGuard["Wiring guard<br/>L4 import graph 無 L3/Signal"]
        Signal["ContrarianSignal<br/>modifier in [-1,+1]<br/>is_authoritative=false"]
        TypeGuard --> FlagGuard --> WireGuard --> Signal
    end

    ProReport["Pro 報告<br/>敘事＝產品"]
    L4Decision["L4 決策路徑<br/>ScoreCard only（不接 Signal）"]
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

### 防火牆不變式

| 不變式 | 檢查方式 |
|---|---|
| L3 不輸出權威市場或動作欄位 | `CrowdScenarioReport` / `ContrarianSignal` schema fail-closed |
| L3 不 import 計算、Portfolio、Stripe 模組 | `test_firewall_no_imports` / import graph grep |
| L3 只讀 frozen `ScenarioSeed` | 無 setter，輸入已分桶 |
| `is_authoritative` 永遠為 false | schema const + runtime assert |
| 人格文字不得帶入數字決策 | forbidden-output scan / numeric-token strip |
| L4 決策路徑不接收 `ContrarianSignal` | L4 import graph grep；`build_rebalance_plan` 簽章只吃 `ScoreCard` |

---

## 6. Portfolio Manager 決策規則（純硬數據，無 modifier 消費）

```mermaid
flowchart TD
    Start["收到 ScoreCard<br/>（無 ContrarianSignal 參數）"]
    HardOnly["build_plan_from_scorecard<br/>唯一輸入 ScoreCard"]
    HardEmpty{"hard_plan 為空<br/>或在容差內？"}
    NoAction["NO_ACTION<br/>附 hard-only 理由"]
    Final["RebalancePlan<br/>final_delta = hard_delta<br/>附兩個獨立硬理由"]
    Provenance["DecisionProvenance<br/>scorecard_id / hard_delta / hard_signals"]

    Start --> HardOnly --> HardEmpty
    HardEmpty -->|"是"| NoAction
    HardEmpty -->|"否"| Final --> Provenance
```

### PM 設計解讀

- 群眾 modifier 完全不進入 L4；RebalancePlan 只由 ScoreCard 決定，按建構即可獨立辯護。
- L4 根本不接收 modifier，故不存在「L3 暗中成為決策主因」的可能；NO_ACTION 與動作皆純硬數據。
- 接線 CI 是可機器檢測的核心：斷言 L4 import graph 中無 L3／ContrarianSignal、`build_rebalance_plan` 簽章只吃 ScoreCard。

---

## 7. 資料契約與核心物件

v3 schema 從三份擴成四份：`ETFResearchReport`、`RebalancePlan`、`OperationalReceipt`、`CrowdScenarioReport`。同時新增 `ScenarioSeed`、`ContrarianSignal`、`DecisionProvenance` 作為防火牆與可稽核性的關鍵物件。**群眾層輸出（`ContrarianSignal`）只連報告與稽核，不連 `RebalancePlan`。**

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

### Schema-first 更新點

- `CrowdScenarioReport` 根層 `is_authoritative` 必須是 `false`，且 `additionalProperties:false`。
- `ContrarianSignal` 的 `contrarian_modifier ∈ [-1,+1]` 是**非權威報告標註**，不進入任何決策路徑。
- `RebalancePlan` 由 ScoreCard 單獨產生，保存 hard-only 理由與 `NO_ACTION` 理由（無 tilt provenance）。
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

- `contrarian_modifier` 完全不參與支出決策（連 tie-breaker 都不是）；spend 純由 deterministic VoI gate 把關。
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
        D6["Day 6<br/>firewall + hard-only PM + 接線 CI<br/>CORE FROZEN"]
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
| 0:78-0:96 | Hard cut 回引擎 | 秀 import graph：L4 從未接收群眾層（根本沒接進來） |
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
| 防火牆回寫風險 | FACE 純敘事側軌，modifier 不進 L4；接線 CI（L4 import graph 無 L3／Signal） |
| modifier 影響支出 | spend 純由 VoI gate；modifier 不參與（連 tie-breaker 都不是） |
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
| `ContrarianSignal` typed output | 讓 L3 只能輸出有界、可稽核、非權威物件，且只連報告與稽核、不進 L4 |
| hard-only only | L4 只吃 ScoreCard，群眾敘事永不進決策 |
| 接線防火牆 | L4 不 import／不接收 ContrarianSignal，結構上零連線 |
| 接線 CI | 把「L4 根本沒接群眾層」變成可測不變式（import graph） |
| VoI gate 控制付費報告 | 讓 spend 決策仍由硬資料與預算控制 |

---

## 13. 文件結論

更新後的 StackFund 架構不再只是「台股 ETF 研究台 + Stripe 金流」。v3 把產品門面改成「群眾情境推演引擎」，但最重要的架構價值在於它被嚴格隔離：群眾層負責可展示、可銷售、可重播的二階敘事；deterministic 主幹負責所有數字、權重、支出與 P&L。

Core-B 成立的條件是三個可檢查承諾：

- 群眾層只輸出 `ContrarianSignal`，且 `is_authoritative=false`。
- L4 的每個 RebalancePlan 只由 ScoreCard 決定；群眾層從未進入決策路徑（接線 CI 可證）。
- L5 的 spend 由 deterministic VoI gate 與 Stripe 硬上限控制，群眾層不能主觸發支出。

因此，這份架構分析的結論是：v3 的可行性比舊版更有 presentation 優勢，但也更依賴防火牆、用語、demo 紀律與主動揭露。只要 Day 6 前凍結 Core（防火牆、hard-only PM、P&L、接線 CI），即使最後砍掉情境動畫，StackFund 仍保有 earn／spend／run real operations 的核心說服力。
