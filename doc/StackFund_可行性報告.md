# StackFund 可行性報告（台股 ETF 研究台 — Core-B 架構定案版）

| 項目 | 內容 |
|---|---|
| **專案名稱** | StackFund — Autonomous Taiwan ETF Research Desk |
| **產品定位** | 自主經營的台股 ETF 研究／顧問微型事業;門面為「群眾情境推演引擎」（Agentic Crowd-Scenario Research） |
| **文件版本** | v3.0（採用 Core-B 架構:群眾情境引擎升為產品門面,並以防火牆與 deterministic 主幹隔離） |
| **日期** | 2026-06-19｜截止 2026-06-30 |
| **比賽** | Hermes Agent Accelerated Business Hackathon（NVIDIA × Stripe × Nous Research） |
| **主題對齊** | 代理能 **earn／spend／run real operations**;評分:usefulness／viability／presentation |
| **設計準則** | deterministic Python 算所有數字;LLM 只解讀衝擊與寫敘事;NO_ACTION 為設計亮點;群眾情境層**非權威**、碰不到任何數字 |

> 本版整併了「Core-B 設計」。主體（§1–§9）為 exec 高度的可行性論證;群眾情境引擎的工程契約、schema、人格庫、demo runbook、逐日建置計畫等深度細節收於**附錄 A**。Core-B 設計已通過五項對抗性壓測（結論皆 holds_with_changes），其 required_fix 已折入本文。

---

## 1. 執行摘要

StackFund 是一個由 **Hermes** 代理自主經營的**台股 ETF 研究台**,在 **NVIDIA NemoClaw／OpenShell** 沙盒中執行,做三件真實的事:

1. **Run real operations** — 用自訂的 Hermes Skill（ETF 分析層設計參考開源 `AZNitro/tw-stock-agent`），拉取 TWSE OpenAPI、TPEX／MOPS、Yahoo、新聞與反指標情緒,對熱門台股 ETF（0050／0056／00878 等）產出結構化研究與再平衡建議。
2. **Spend** — 用 **Stripe Skills for Hermes** 自行 provision 並付費營運所需的資料／運算／SaaS 堆疊,並以 deterministic optimizer 在固定預算內再平衡這個「工具投組」。
3. **Earn** — 用 **Stripe billing** 向訂閱者收費販售研究,產生真實營收;以 before／after 的 **Operational P&L** 證明這門代理生意能自負盈虧。

**產品門面（headline）是「群眾情境推演引擎」**:對一則已算好的市場事件,用 20–50 個台灣散戶**合成人格**演練二階反應鏈（「若升息 → 存股族照扣不動 → 當沖客先停損電子權值 → 賣壓集中 0050 → 0056 抗跌敘事 → 資金二次輪動」），這是相對「又一個 TWSE 儀表板」的差異化。但它被**防火牆**嚴格隔離:**門面（FACE）可以改變我們講什麼故事、並在硬數據已允許的方向內把某檔 ETF 權重微調至多 ±2pp;它永遠不能決定任何數字、不能成為任何動作的唯一理由、碰不到任何算數字的函式。方向盤永遠鎖在引擎（Stripe earn／spend 的 deterministic 主幹）上,不鎖在門面上。**

**結論:技術可行,建議執行（Go），附五項前置條件。** 最關鍵的設計判斷:**Stripe 負責「事業金流」（花錢買工具、向客戶收費），不負責「證券下單」**;台股 ETF 是研究與服務的**標的**,StackFund 全程不下任何證券委託單。三個贊助平台（Hermes 編排、Stripe earn＋spend、NemoClaw 安全）各司其職,完整命中「earn＋spend＋real operations」。

**主動揭露的三條誠實紅線（設計成熟度,先講不閃）：**（1）**可重現 ≠ 已驗證**——情境引擎是合成排練,價值在 risk-scenario 覆蓋,非預測準確度;（2）**群眾 modifier 並不優於既有 contrarian 分數**——產品價值釘在「二階反應鏈**敘事**」,不在那個純量;（3）**真正的法規曝險在「收費＋指名＋方向性」的 RebalancePlan**（在主幹上）,靠 test-mode／無費／零下單守 safe harbor。主要風險集中在台灣金融法規、資料來源穩定度與 demo 可信度,而非「技術是否存在」。五項前置條件詳見 §8。

---

## 2. 產品定義與定位

StackFund 是一個**會自己賺錢、自己付營運成本、自己做研究**的微型事業,而非選股機器人。產品類別:**Agentic Crowd-Scenario Research for Taiwan ETFs**——一個 deterministic 研究台,門面是一個群眾反應的**壓力測試**引擎。

### 2.1 兩個投組（設計亮點）

| 投組 | 內容 | 誰受益 |
|---|---|---|
| **ETF 研究投組** | 0050／0056／00878 等台股 ETF 的配置與再平衡建議 | 訂閱客戶 |
| **營運成本投組** | 資料 API、LLM 推論、資料庫、observability、遞送等 SaaS | 代理自己（FinOps） |

代理同時對「客戶該怎麼配置 ETF」與「自己這門生意該怎麼花錢」做最佳化決策,共用一套 Operational P&L。

### 2.2 護城河 — 釘在敘事,不釘在數字

儀表板與 `tw-stock-agent` 回答**一階問題**（00878 的價格、NAV、折溢價、殖利率是多少）——零防禦性的商品事實。StackFund 的 moat 是**二階反應鏈敘事**:「誰因為別人做什麼而做什麼」,一個資料源賣不出來、`tw-stock-agent` 也產不出來的 artifact。

> moat 一句話:「儀表板賣**資料**;`tw-stock-agent` 已有情緒分數;StackFund 多賣的是一個**資料之後、群眾互相牽動的二階故事**——一個敘事 artifact,而非更強的數字。」

### 2.3 訂閱者買什麼（三層 Stripe 方案,強化 EARN）

免費數字是鉤子,情境**敘事報告**是付費商品;付費牆切在防火牆同一條線（免費＝權威數字／引擎,付費＝加值敘事層／門面）。

| 方案 | Stripe 價（demo） | 內容 |
|---|---|---|
| **Watch（免費）** | NT$0 | 每日數字卡:price／NAV／折溢價／殖利率／freshness。純 deterministic 事實,刻意商品化。 |
| **Pro（headline SKU）** | ~NT$299/月 | 單事件群眾情境報告:二階反應鏈敘事＋5–8 個人格樣本＋`contrarian_modifier`（標「情境參考訊號,非投資建議」）＋其下 deterministic 研究結論。**這就是產品。** |
| **Desk（roadmap,非 MVP）** | ~NT$999/月 | Pro＋事件觸發排程＋跨 ETF 輪動鏈＋原始擁擠時間序列。 |

情境引擎消耗的 LLM 推論是一筆**真實、變動、每報告**的算力成本,由 agent 經 Stripe Skills 付費 ⇒ 乾淨單位經濟學;低價值事件時 agent 可判定「不值得花這次推演成本」⇒ **被拒絕的支出**（最難忘的 demo beat）。

### 2.4 定位用語與法規邊界

- 動詞一律用**推演／壓力測試（simulate／rehearse／stress-test）**,**永不用預測／預報（predict／forecast）**。門面 tagline:「ETF 衝擊情境的**群眾反應壓力測試**」,刻意與 MiroFish「預測萬物」用語拉開距離。
- StackFund 提供**研究／教育決策支援**,**非受託代客操作、非收費個別化證券投資顧問,且不下任何證券委託單**。所有輸出掛四層免責（見 §7 與 附錄 A.12）。
- **誠實邊界**:6/30 前不存在真實付費訂閱者;EARN 故事建立在「差異化帶來的付費意願可信度」＋「已展示一筆真實 Stripe 收款」,**非**「已驗證市場」。

---

## 3. 技術可行性

### 3.0 查證總表

| 元件 | 假設的能力 | 查證結果 |
|---|---|---|
| Stripe（Skills／billing） | 代理可 provision／付費 SaaS（spend），並向客戶收訂閱費（earn） | **成立**。Stripe Skills for Hermes 支援代理自助 provision 與付費;billing 支援訂閱收款 |
| Hermes | 開源代理、可載入 Agent Skills、跨 session 持續 | **成立**。Nous Research 開源 self-improving 代理,已整合 Stripe skill |
| NemoClaw／OpenShell | 代理沙盒,控管檔案／網路／憑證／推論 | **成立**。NVIDIA 官方沙盒,四個 policy domain,官方支援 Hermes |
| 台股資料層 | TWSE／TPEX／MOPS／Yahoo 取得 ETF 價量、淨值、配息、籌碼、新聞 | **成立**。TWSE OpenAPI 為官方公開資料;`tw-stock-agent` 已示範整合路徑 |
| ETF 分析 Skill | 以 SKILL.md＋scripts/＋references/ 格式供 Hermes 載入 | **成立**。`tw-stock-agent` 已採此格式（即 Hermes／Stripe 官方 skill 同格式），可 fork |
| **群眾情境引擎 Skill** | **clean-room 蒸餾的輕量原生 skill,N=20–50 人格,無 OASIS／Zep,deterministic 聚合** | **成立**。同 Agent Skills 格式;不含任何 MiroFish 程式碼;見 §3.5 |

### 3.1 Stripe（earn ＋ spend 的金流層）

- **Spend**:透過 Stripe Skills for Hermes,代理可 provision／升降級資料庫、AI、observability 等服務,並在 **API 層強制硬性支出上限**（非 prompt 層），另有 merchant 白名單、完整交易紀錄、「高額需人工核可」門檻;憑證以 Shared Payment Token 交付。
- **Earn**:用 Stripe billing 建立 Watch／Pro／Desk 訂閱、開立發票、收款,形成真實營收流（命中比賽「earn」核心）。
- **代理友善**:指令支援非互動旗標與結構化輸出,適合在 Hermes skill 中以 script 呼叫。

### 3.2 Hermes（代理與編排層）

Nous Research 的開源、self-improving 代理,跨 session 攜帶脈絡,適合「反覆研究同一組 ETF 並服務同一批訂閱者」的工作流。Stripe 已整合 skill;自訂的 StackFund Skill、ETF 分析 Skill、群眾情境 Skill 只要沿用 Agent Skills 格式即可載入。

### 3.3 NVIDIA NemoClaw／OpenShell（執行邊界與風控層）

- **四個 policy domain**:filesystem、network、process、inference,宣告式 YAML;network／inference 可熱更新。
- **憑證隔離**:金鑰不落沙盒檔案系統,由 L7 proxy 在 egress 時注入;預設 default-deny 網路。
- **kernel 級機制**:seccomp、Landlock、network namespaces。
- **模型**:預設以 **Nemotron** 為推論模型（群眾情境引擎亦用同一棧寫人格文字）;Privacy Router 可在本地／雲端間路由。
- **代理支援**:官方明確支援 Hermes。

對一個同時處理真實金流與金融研究輸出的代理,沙盒的硬性支出上限與網路 policy 是最有說服力的安全 demo 賣點。

### 3.4 台股 ETF 資料層（核心 operation）

設計參考 `AZNitro/tw-stock-agent`,自建 Hermes 相容的 ETF 分析 Skill。來源優先序:① TWSE OpenAPI（官方:價量、融資融券、本益比／淨值比／殖利率、公告）② TPEX／MOPS（上櫃與財報／配息）③ Yahoo（報價、分析師目標、同類比較、新聞）④ Web／News（催化事件）⑤ 反指標情緒（過熱／恐慌／擁擠,輔助層）。**ETF 特有欄位**（折溢價、追蹤誤差、成分股重疊、除息日）一律 deterministic Python 計算。

> **待確認項（低風險）**:`tw-stock-agent` 的 `scripts/` 為 placeholder（官方 README 已聲明），fetcher 須自補;但其 `SKILL.md`／`references/` 已是可採用的設計骨架。

### 3.5 群眾情境引擎（為何不直接整合 MiroFish，改採 clean-room 蒸餾）

門面的概念靈感來自開源的群體智能模擬引擎 **`666ghj/MiroFish`**。經評估,**直接整合 MiroFish 為 blocker 級**,理由有三:

1. **授權**:MiroFish 為 **AGPL-3.0**（強 copyleft）。其 §13 網路條款會讓「以 Stripe 收費的網路服務」反而需對**每位付費用戶**揭露原始碼——與本專案的商業／品牌前提衝突。
2. **執行型態**:它是常駐 Flask＋Vue（~19.5k 行）、OASIS 引擎＋付費 Zep Cloud GraphRAG＋高耗 LLM 的有狀態雙平台模擬,塞不進 90–120 秒 live demo,且與 deterministic 原則正面衝突。
3. **成本**:LLM 量＝agents × rounds × 2 平台,官方自承「消耗較大」。

**故採 Path B — clean-room 蒸餾「想法」成輕量原生 skill**:只取「異質人格對事件反應 → 產生二階反應鏈與反指標訊號」這個**概念**,以 N=20–50 人格、固定 RNG 種子、deterministic Python 聚合實作,**無 OASIS／無 Zep／無常駐伺服器**,LLM 只寫人格反應文字、不算數字。**clean-room 紀律（誠實版）**:為理解架構曾檢視 MiroFish source,但**未複製任何 code／prompt／schema 文字**,所有欄位名、schema、公式均為原創,設計上以「`tw-stock-agent` contrarian 層的延伸」重新論證,而非縮小版 MiroFish（細節見 附錄 A.6）。

### 3.6 整合可行性小結

OpenShell 管「代理能否繞過正常執行路徑」、Stripe 管「金額硬上限＋真實 earn／spend」、Hermes 管「跨 session 編排」、ETF Skill 管「真實研究 operation」、群眾情境 Skill 管「差異化敘事門面（受防火牆隔離）」。職責邊界清楚、無重疊或缺口。**技術可行性成立。**

---

## 4. 架構可行性（Core-B 六層 + 防火牆契約）

### 4.1 一句話契約

> 群眾情境引擎可以改變**我們講什麼故事**,可以在硬數據**已允許的方向與帶寬內**把某檔 ETF 權重微調至多 **±2 個百分點**;它**永不能決定一個數字、永不能成為動作的唯一理由、永不能觸及任何計算數字的函式**。它是 FACE;deterministic 主幹是 ENGINE。

### 4.2 六層骨架（│＝deterministic 主幹;┊＝advisory 單一純量）

```
                    STACKFUND — Core-B 6-LAYER ARCHITECTURE
  ┌────────────────────────────────────────────────────────────────────────┐
  │  L1  ETF DATA BOOK（deterministic ingest）                              │
  │  TWSE / TPEX / MOPS / Yahoo / news。算所有數字:price, NAV, 折溢價,      │
  │  追蹤誤差, 殖利率, 配息日。Output ▶ DataBook（immutable, book_hash）     │
  └──────────┬──────────────────────────────────┬──────────────────────────┘
             │ DataBook(full)                    │ ScenarioSeed(projection,
             │                                   │   read-only, frozen, 已分桶)
             ▼                                   ▼
  ┌───────────────────────────┐    ╔════════════════════════════════════════╗
  │ L2 DETERMINISTIC SCORECARD│    ║ L3  CROWD SCENARIO ENGINE   ★CORE-B★    ║
  │   （主幹）                │    ║     群眾情境推演引擎（FACE / headline）  ║
  │ 透明公式 → trend /        │    ║ 蒸餾自 idea（非 swarm）:               ║
  │ fundamental / valuation / │    ║  seed → N=20–50 deterministic-RNG      ║
  │ catalyst / risk 子分數     │    ║  personas → LLM 只寫反應文字＋立場      ║
  │ Output ▶ ScoreCard        │    ║  → deterministic Python AGGREGATION    ║
  └──────────┬────────────────┘    ║  → ONE bounded scalar                  ║
             │ ScoreCard            ║ NO OASIS / NO Zep / NO server / 不算數字 ║
             │ (authoritative)      ║ Output ▶ ContrarianSignal              ║
             │   ┌──────────────────╢  { narrative, persona_samples,          ║
             │   │ ContrarianSignal ║    contrarian_modifier ∈ [-1,+1],       ║
             │   │ is_authoritative ║    is_authoritative = FALSE }           ║
             │   │  = FALSE  ┊┊┊┊┊▶ ╚════════════════════════════════════════╝
             ▼   ▼ (advisory, 單一純量, 只經 ONE gate+clamp)
  ┌────────────────────────────────────────────────────────────────────────┐
  │  L4  PORTFOLIO MANAGER（主幹 — 方向盤）                                 │
  │  先用 ScoreCard ALONE 建 hard_plan。再 IFF 兩把鑰匙 gate 通過才施加     │
  │  bounded tilt。Clamp: |Δ_tilt| ≤ min(2.00pp, 1×Δ_hard) per ETF。       │
  │  modifier 永不能創造動作、翻轉方向、突破 hard band。NO_ACTION 為一級輸出。│
  │  Output ▶ RebalancePlan(+ tilt_provenance)                             │
  └──────────┬─────────────────────────────────────────────────────────────┘
             │ RebalancePlan
             ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  L5  FINOPS & EXECUTION（主幹）                                         │
  │  Stripe SPEND(provision, 硬上限)＋EARN(訂閱收款)。Value-of-Information   │
  │  gate 決定是否值得跑付費報告。情境引擎對此層 ZERO 觸及。                 │
  └──────────┬─────────────────────────────────────────────────────────────┘
             ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │  L6  AUDIT & OPERATIONAL P&L                                           │
  │  記錄每個決策＋每次 modifier 使用的 FULL PROVENANCE。可重播。P&L。       │
  └────────────────────────────────────────────────────────────────────────┘
```

**關鍵結構事實**:L3 是側軌上的**葉節點**——資料流入（ScenarioSeed）、恰一個 typed 物件流出（ContrarianSignal），對 L1／L2／L5／L6 無任何外向邊（除 L6 記錄它輸出了什麼）。deterministic 市場情境（升息／電子權值回檔——合法地驅動數字）留在 L1／L2 主幹;只把**群眾／人格反應**切成 L3。

### 4.3 防火牆 — 四層強制（細節見 附錄 A.1–A.3）

1. **型別層**:`ContrarianSignal` 上**不存在** price／nav／折溢價／yield／weight／cap 欄位 → 合約上回不了數字。
2. **import 層**:L3 不 import 任何計算模組;CI guard `test_firewall_no_imports` grep import graph,違者 build fail。
3. **輸入層**:L3 只拿 frozen `ScenarioSeed`（已分桶的 ordinal context,**人格永遠看不到原始數字**），無 setter 可呼叫。
4. **flag 層**:`is_authoritative` 硬寫 False 並 assert。

即使 L3 內遭 prompt-injection,最多產出生動但錯的故事＋一個已被 clamp 到 [-1,+1] 的純量,對任何**已計算數字**造成**零**損害。

### 4.4 Portfolio Manager 如何消費（壓測修正版,細節見 附錄 A.3）

L4 嚴格依序:**①硬數據計畫先行**（modifier 不可見;若 hard_plan 空／在容差內 → **NO_ACTION 在讀 modifier 前發出**）→ **②兩把鑰匙 gate**（須 ≥2 個來自 ≥2 個不同 factor family〔valuation／yield／trend／flows〕的獨立硬訊號同向,且 modifier 符號與硬方向相同,只放大不翻轉）→ **③bounded clamp**（`tilt ≤ min(2pp, 1×hard_delta)`，硬數據永遠主導）→ **④threshold-flip 防護**（把 tilt 歸零重跑,若只有加 tilt 才會觸發動作就**回退 NO_ACTION**）。

**獨立可辯護性不變式（headline 可信度保證,可機器檢測）**:對 RebalancePlan 中每一個非零權重變動,存在一個**移除群眾後仍成立**的純硬數據解釋。**端到端 CI 不變式:把 modifier 歸零重跑,動作必須仍以同方向發生且跨過所有門檻,否則 reject。** 這就是「independently-justifiable-from-hard-data-alone」的字面可測形式。

### 4.5 仍然正確的幾項判斷

1. **LLM／deterministic 分工**:價格、淨值、折溢價、殖利率、權重、支出由 deterministic Python 算;LLM 只解讀衝擊、寫敘事。群眾引擎**不算任何數字**,反而**強化**了這條原則。
2. **雙投組、單一 P&L**:demo 能同時展示「給客戶的價值」與「代理自己賺不賺錢」。
3. **防禦縱深的支出控管**:StackFund 業務規則（軟）→ Stripe API 層上限（硬）→ OpenShell 執行邊界（硬）。
4. **Schema-first**:先鎖 ETFResearchReport／RebalancePlan／OperationalReceipt／CrowdScenarioReport 四份 JSON schema。敏感 token 不進 JSON。
5. **NO_ACTION 是設計亮點**:能證明「這週不需要調整」或「這筆花費不值得」,是「真在推理」的最強訊號。

**需強化的架構點**:真正的硬保證是 Stripe API 級上限與 OpenShell policy,業務規則只是建議層;且所有對外研究輸出須掛免責（§7）。

---

## 5. 營運與執行可行性

| 面向 | 評估 |
|---|---|
| 團隊能力 | 具 CS／系統整合背景,能處理 CLI、Python、JSON、沙盒設定與台股資料抓取,能力相符 |
| 開發範圍 | MVP 收斂得當（3 檔 ETF、1 個固定情境、deterministic scorecard＋optimizer、1 真實 Stripe 付費＋1 收款＋1 被拒、防火牆 code、1 個 pre-baked 群眾情境） |
| Demo 形式 | 90–110 秒 live demo（硬上限 120 秒）;群眾引擎為情緒高峰,但 earn／spend／refused-spend 拿頭尾句與多數秒數 |
| 對外依賴 | 依賴 Stripe 帳號資格、TWSE／Yahoo 資料可用性,需 Day 1 驗證 |

**開發順序（防火牆＋Stripe FIRST）**:Day 1 驗 Stripe TW 雙流＋TWSE 可達 → 鎖四份 schema＋凍結 fixtures → deterministic scorecard＋optimizer → **Stripe SPEND＋REFUSED SPEND** → Stripe EARN → **防火牆契約＋PM tilt＋P&L（Day 6 結束 CORE FROZEN——之後即使砍門面 demo 仍可贏）** → 群眾情境引擎 scaffold＋bake → replay／非權威章／hard-cut → 最後包 NemoClaw 並錄 demo。逐日計畫見 附錄 A.11。

---

## 6. 風險評估與緩解

| 編號 | 風險 | 等級 | 說明 | 緩解措施 |
|---|---|---|---|---|
| R1 | 台灣 Stripe earn／spend 資格 | 高 | Stripe Skills 付費層／訂閱收款的國別清單可能未含台灣或受限 | 三模式 `dry_run／free_only／live_limited`;Day 1 驗帳號可否「付費 provision」與「對測試卡收款」;退路 free-tier＋測試模式收款,付費動作標 blocked |
| R2 | 台灣投顧法規（SITA §4） | 高 | 收費、個別化證券建議涉《證券投資信託及顧問法》 | **PRIMARY 防線**:demo 無真實報酬（test-mode、無委任人）＋**非個別化**研究／出版品 framing＋去絕對買賣指令;RebalancePlan 渲染為「研究情境下之示意配置」非「您應減碼」。**防火牆是 correctness／credibility 控制,不是主要投顧防線**（更正自舊版誤指） |
| R2b | 市場誠信／操縱觀感（證交法 §155） | 中–高 | §155 分**交易型 limb**（沖洗／連續買賣——**零下單即完全 defuse**）與**資訊型 limb §155(1)6**（散布足以影響價格之資訊——**僅部分 defuse**） | 不可宣稱「幾乎完全 defuse」;published 敘事須 framed 為**假設性壓力情境**、**永不**陳述某指名 ETF 將如何變動;禁對指名 ticker 主張價格方向的對外語;demo 敘事明確 counterfactual（「**若**…**這類**人格**可能**…」） |
| R2c | headline 化降級研究 carve-out | 中 | 行銷從「數字」轉向「群眾會**做**什麼」,更 action-oriented、離中性出版品更遠 | tagline／Pro 文案保持**情境／教育**（壓力測試／情境推演），絕不 outcome-promising |
| R3 | Live demo 執行出包 | 高 | 三筆 live Stripe（收款／provision／refused）才是真正 blowup 風險;授權彈窗／延遲／rate limit | 服務事先 provision、群眾 sim 純 replay;標明 live／replayed;**禁 demo 中 live re-bake**;`>5s → alt-tab 到錄影`;static-card 為**一級** fallback;dry_run 安全網 |
| R4 | 資料來源穩定度與時效 | 中 | TWSE rate limit;Yahoo 改版;盤中即時有限 | 採「官方日資料代理盤中」fallback（fmtqik／mi-stock20）;標 freshness;缺失標 partial,不臆測 |
| R5 | 可信度:可重現 ≠ 已驗證（R5／R6） | 中 | headline 是 **LLM 敘事**;deterministic 聚合只買「可重現」非「正確」;人格立場是 authored 先驗、非 observed;無回測 | 揭露 **modifier 偏弱、價值釘敘事**;每 archetype 附**可引用先驗**;demo 給防火牆／NO_ACTION 同等或更高權重、當場「刪群眾面板動作仍成立」;口播明說「**未經回測**」;敘事一律條件式 |
| R6 | Agency 認知 | 中 | 決策全 deterministic 時會被質疑「代理還是計算機加字幕」 | agency 放在**執行／適應迴圈**:真跑 Stripe provision、撞上限失敗、讀錯誤改 downgrade;真對訂閱者收款;demo 演到「應對一個真實失敗」 |
| R7 | clean-room／授權 credibility | 中–低 | 法律風險低（從未散布、repo 內無 MiroFish code、欄位名原創、MIT、stateless 無 §13 surface）;**但**若 provenance 聲明不誠實,評審 diff 兩 repo 時 credibility pillar 會崩 | `clean-room.md` 採誠實版（檢視過 source 但未複製 code／prompt／schema）;從設計移除 MiroFish module／class 名稱引用;NOTICE 僅致謝 idea（附錄 A.6） |
| R8 | 次要技術點 | 低 | ① 自訂 skill 格式需對齊 Hermes;② `tw-stock-agent` scripts 為 placeholder | ① 直接 fork 同格式,Day 1 驗載入;② Day 1 補最小 fetcher（TWSE 價量＋Yahoo 報價起步） |

**五項對抗性壓測**（防火牆／demo／credibility／regulatory／clean-room）結論皆 **holds_with_changes**,required_fix 已折入本文與附錄;殘餘風險最誠實的三條即 §1 的三條紅線（完整壓測總表見 附錄 A.13）。

---

## 7. 資源需求與時程（Core-B MVP 範圍）

**IN — 不可移動 CORE（引擎,即使門面被砍也須 ship）**
3 檔 ETF（0050／0056／00878,frozen fixtures,皆 Python 算）;ETFResearchReport／RebalancePlan／OperationalReceipt／CrowdScenarioReport schema;deterministic scorecard＋cost optimizer（硬上限／保留金）;**1 筆真實 Stripe EARN＋1 筆 SPEND＋1 筆 REFUSED SPEND**;**防火牆 code 強制**（`firewall_test.py` 斷言引擎絕不寫任何數字欄位）;PM 在護欄內讀 modifier、每動作附獨立硬數據理由;before／after P&L;NemoClaw 內執行;輸出附四層免責。

**IN — 門面（signature beat,bolt-on,可降級）**
**僅一個** pre-baked scenario `0056_cut`,N=30,seed=42,replay animation,非權威章。

**OUT（明確不做）**
live 多輪／多情境 swarm;任何 OASIS／Zep／Flask runtime;>1 scenario;N>50;真實下單／券商 API;收費個別化投顧;盤中 tick;槓桿／期貨 ETF;上百檔 ETF;ML 預測;歷史回測;per-user 記憶;A–E 護城河評級。

**CUT-LINE（6/29 落後時）**:砍 replay animation,beat 5 改 static card;防火牆、PM tilt、其餘 beats 不動。**門面永不在關鍵路徑上。**

此範圍與「don't do」清單顯示已從過度設計收斂,範圍紀律良好,且刻意避開「真實下單」與「收費個別化投顧」兩個法規地雷。

---

## 8. 結論與建議

**建議:執行（Go）**,附以下五項前置條件,並設一個 Phase 1 go／no-go 檢查點。

**前置條件（須在開發初期完成）**
1. **Day 1 驗證 Stripe 雙向金流**:台灣帳號可「付費 provision 至少一個 SaaS」＋「對測試卡建立訂閱並收款」,決定 demo 走 `free_only` 或 `live_limited`。
2. **Day 1 驗證台股資料層**:跑通 TWSE OpenAPI 取一檔 ETF 價量＋Yahoo 報價,確認 rate limit 與時效,補 `tw-stock-agent` 最小 fetcher。
3. **scorecard 改公式推導**:在 optimizer 骨架就把分數從可觀測訊號算出來,杜絕「結論被輸入餵出來」（R5）。
4. **防火牆契約落地**:`ContrarianSignal`（is_authoritative=false）＋四層強制＋PM 的 gate／clamp／threshold-flip＋**零-modifier CI 不變式**＋`firewall_test.py`,於 Phase 1 即就位（Day 6 凍結 CORE）。
5. **法規定位、用語 lexicon 與四層免責落地**:定位為研究／教育、不下任何證券委託單;敘事條件式語氣;demo runbook 含 Tier D 口播檢查項;`clean-room.md` 採誠實版。

**Go／No-Go 檢查點（Phase 1）**:若 Day 1 無法在台灣帳號同時完成「至少一個真實付費 provision」與「至少一筆真實／測試模式收款」,即切換 `free_only`＋測試模式 demo,並向主辦確認 sandbox。**不要讓架構綁死在「台灣帳號一定能跑完整 earn＋spend」這個假設上。**

整體而言,StackFund 最強的地方不是「代理能選 ETF」,而是「代理能**自己經營一門台股 ETF 研究生意**——做真實研究、付自己的營運成本、向客戶收費、在不值得時主動拒絕消費」,並以一個**搶眼但被嚴格隔離**的群眾情境門面做差異化。完整命中 earn／spend／run real operations,且把「face 搶眼、方向盤仍明顯鎖在 engine 上」當作主動揭露的設計成熟度——這正是 viability 與 presentation 的最佳證明。

---

## 9. 參考來源

- Hermes Agent Accelerated Business Hackathon（NVIDIA × Stripe × Nous Research）— 主題與評分
- 台股 ETF 分析 skill 設計參考:`AZNitro/tw-stock-agent` — https://github.com/AZNitro/tw-stock-agent
- 群眾情境引擎**概念**靈感（**未整合其程式碼**;AGPL-3.0,直接整合經評估為 blocker,改採 clean-room 蒸餾,見 §3.5／附錄 A.6）:`666ghj/MiroFish` — https://github.com/666ghj/MiroFish
- TWSE 臺灣證券交易所 OpenAPI — https://openapi.twse.com.tw/
- 公開資訊觀測站 MOPS — https://mops.twse.com.tw/
- Stripe（Skills for Hermes／billing）官方文件 — https://docs.stripe.com/
- Hermes（Nous Research）— https://nousresearch.com/
- NVIDIA NemoClaw — https://github.com/NVIDIA/NemoClaw ｜ NVIDIA OpenShell — https://github.com/NVIDIA/OpenShell
- NVIDIA Technical Blog:Run Autonomous, Self-Evolving Agents More Safely with OpenShell — https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/

> 註:① 外部平台能力以摘要呈現,實際指令旗標與供應商清單以各平台最新官方文件為準。② 本文件為比賽可行性評估,**非投資建議**;StackFund 產品定位為研究／教育決策支援,非受託操作或收費證券投資顧問,且不下任何證券委託單。③ 群眾情境為合成人格之**情境推演**,非真實民意或市場預測。

---
---

# 附錄 A — 群眾情境引擎詳細設計（Core-B）

> 本附錄為 §4 的工程展開,已折入五項對抗性壓測的 required_fix。

## A.1 資料契約（防火牆即型別）

**讀側 `ScenarioSeed`（L3 唯一能讀的東西,frozen 投影）**:由純函式 `make_seed(book)->ScenarioSeed` 產生,只帶**已分桶的 ordinal context**（折溢價→{deep_discount…rich}、殖利率→{low,normal,high}）＋`rng_seed`＋`market_scenario_label`。**人格永遠看不到原始數字**——結構性阻止 LLM 回吐或重算數字。無 live handle、無 setter、無 optimizer／Stripe／weight／cap reference。

**寫側 `ContrarianSignal`（L3 唯一能 emit 的東西）**:
```python
@dataclass(frozen=True)
class ContrarianSignal:
    seed_id: str                # 必須等於它反應的 ScenarioSeed.seed_id
    rng_seed: int
    n_personas: int             # 20..50
    contrarian_modifier: float  # ∈ [-1,+1];正=群眾過熱→偏防禦,負=群眾恐慌→偏進取
    is_authoritative: bool      # HARD-WIRED False（__post_init__ assert）
    narrative_md: str           # 二階反應鏈故事（LLM 寫）
    persona_samples: tuple[PersonaReaction, ...]
    # 此型別上「不存在」price/nav/折溢價/yield/weight/cap 欄位
    def __post_init__(self):
        assert -1.0 <= self.contrarian_modifier <= 1.0
        assert self.is_authoritative is False
```
從 N 個人格立場到單一純量的聚合是 **deterministic Python**,非 LLM:`modifier = clamp(mean(stance_i) * crowding_factor, -1, +1)`,其中 `stance_i ∈ {-1,0,+1}` 由 rule-based、version-pinned 分類器解析 LLM 文字。**LLM 寫文字;Python 把文字變數字。**

## A.2 硬禁止（四層強制）

① **型別層**:`ContrarianSignal` 無任何數字欄位。② **import 層**:L3 不 import `l1_databook.compute`／`l2_scorecard`／`l4_portfolio.optimizer`／`l5_finops.stripe`;CI guard `test_firewall_no_imports` 違者 build fail。③ **輸入層**:L3 只拿 frozen `ScenarioSeed`,無 setter。④ **flag 層**:`is_authoritative` 硬寫 False 並 assert。

## A.3 Portfolio Manager 消費四步驟

**Step 1 — 硬數據計畫先行（modifier 不可見）**:`hard_plan = build_plan_from_scorecard(scorecard)`。若空／在容差內 → **NO_ACTION 在讀 modifier 前發出**。

**Step 2 — 兩把鑰匙 gate（正交性）**:tilt 只在以下皆成立才開:(a) hard 方向非零;(b) ≥2 個來自 **≥2 個不同、不重疊 factor family（valuation／yield／trend／flows）** 的獨立硬訊號同向（**不是兩個訊號名**,杜絕 trend 與 catalyst 共動的假獨立）;(c) modifier 符號與 hard 方向相同（只放大,不翻轉）。

**Step 3 — bounded clamp（量級永遠由硬數據主導）**:
```python
GUARDRAIL_PP = 2.00
tilt_pp = signal.contrarian_modifier * min(GUARDRAIL_PP, 1.0*abs(hard_delta[t])) if gate(...) else 0.0
delta_final = clamp_to_hard_band(hard_delta[t] + tilt_pp, scorecard.band[t])
assert abs(delta_final - hard_delta[t]) <= GUARDRAIL_PP
assert not signal.is_authoritative
```

**Step 4 — threshold-flip 防護（最關鍵）**:把 tilt 歸零、用同一條 min-trade floor 重跑 hard-only 計畫:**若只有加了 tilt 的計畫會觸發執行、hard-only 不會,則回退 NO_ACTION**。

**獨立可辯護性不變式**:對每一個**被執行**的非零 `delta_final`,其 hard-only 版本也會被執行且跨過所有門檻。**端到端 CI:把 modifier 歸零重跑,動作必須仍同方向發生且跨門檻,否則 reject。**

## A.4 SPEND 防火牆與 provenance（L6）

付費報告／provisioning 由 **deterministic value-of-information 規則**（materiality＋spend-cap headroom,皆從硬輸入算）把關;`contrarian_modifier` **只能當 tie-breaker**,不能當主觸發。**CI 斷言:spend 決策不以 ContrarianSignal 為 primary trigger。**

每次 L4 決策寫一筆 `TiltProvenance`:`{decision_id, seed_id, rng_seed, ticker, hard_delta_pp, hard_signals[(名稱,值)], contrarian_modifier, gate_passed, tilt_pp_applied(≤2pp), final_delta_pp, is_authoritative(恆 False), narrative_digest(sha256)}`——**有界、可歸因、可重播**。demo dashboard line:「硬數據動作:+3.0pp 0056（valuation+yield+trend）│ 群眾微調:+1.4pp（群眾過熱、反向防禦）│ 在護欄內 ✓」。

## A.5 crowd-scenario-skill 設計（clean-room）

```
crowd-scenario-skill/
  SKILL.md
  scripts/
    seed_builder.py     # deterministic: DataBook -> EventSeed（無 LLM）
    persona_sim.py      # 固定 RNG 選 roster/order/edges;LLM 只寫文字＋立場
    aggregate.py        # deterministic: 立場 -> contrarian_modifier ＋ 反應鏈（無 LLM）
  references/
    personas.md         # 固定 N=20..50 人格庫（每 archetype 附行為先驗依據＋引用）
    seed.lock.json      # rng_seed / roster hash / model_id / temperature=0.0
    firewall.md         # 防火牆契約（可執行規則）
    output-schema.md    # EventSeed / ScenarioReport / ContrarianSignal JSON schema
    clean-room.md       # AGPL 邊界與 provenance（誠實版,見 A.6）
```

| 步驟 | 誰做 | 內容 |
|---|---|---|
| `seed_builder.py` | **Python** | 讀 databook.json,選固定 market_event,把連續指標分桶成 ordinal,emit EventSeed＋seed_hash。無 LLM。 |
| `persona_sim.py` | **Python＋LLM** | Python（RNG seeded）選 N 個人格、反應順序、who-reads-whom 稀疏邊。Round 1 各人格獨立反應;Round 2 各人格讀 K 個鄰居 round-1 文字後可改立場（二階／contagion,in-memory,無 Zep）。LLM **只**回 `{reaction_text, stance-token}`。 |
| `aggregate.py` | **Python（＋1 次 LLM）** | 立場 token→clamped `contrarian_modifier`;走邊列舉二階反應鏈;算 stance_histogram／flip_count;跑 forbidden-output 掃描;最後 **1 次** LLM 只吃已算好的值寫敘事（numeric-token diff 驗證,違者 strip）。 |

**Round 模型（N=20–50,無 OASIS/Zep）**:2 rounds × N personas = 40–100 個小 LLM 呼叫,可平行,在 demo budget 內。**deterministic seeding**:`seed.lock.json` 為唯一真相源（rng_seed、roster_hash、pinned model_id、temperature=0.0）;modifier 只依賴 closed-vocab `stance` token,對 LLM 用字漂移 robust;另有 **stance 重導交叉檢查**（以 deterministic 規則重導立場,與 LLM 立場比對,超容差 fallback 至 deterministic 立場）。`--dry-run` 以 stub 換掉 LLM,零呼叫零 spend,供 CI 與 R3 安全網。

**SKILL.md front-matter ＋ Guardrails**:
```yaml
---
name: crowd-scenario-engine
description: 對「已算好的」市場事件,推演台股 ETF 投資人各型態的反應,產出二階反應鏈
  敘事與一個有界、非權威的 contrarian_modifier。情境推演,非情緒預報。
version: 1.0.0
license: MIT
metadata:
  hermes:
    tags: [scenario, crowd, contrarian, ETF, Taiwan, narrative, non-authoritative]
    firewall: non-authoritative
---
```
G1 輸出白名單（只 narrative／樣本／立場計數／鏈／一個純量,任何 price/NAV/NTD pattern 即 schema violation abort）;G2 `is_authoritative:false` 硬寫;G3 PM 只當一個訊號、雙重理由必要;G4 LLM 不算數字,人格文字含數字則 aggregate strip;G5 determinism。

## A.6 clean-room AGPL 紀律（誠實版）

**法律風險本身低**:從未散布、repo 內無 MiroFish code、欄位名與公式原創,ship MIT、stateless CLI 無 §13 surface;NOTICE 僅致謝 idea 啟發。**但專案自訂的 clean-room 標準必須誠實達成**:
1. `clean-room.md` 寫明——「為**理解**架構曾檢視 MiroFish source;**未複製**任何 code／prompt／schema 文字;所有欄位名、schema、stance／contrarian 公式均為原創。」（**不**聲稱 README-only。）
2. 從架構**移除 MiroFish 的 expression**:不複刻其 module 分解與私有 class 名;從第一原理（或 `tw-stock-agent` 自身 scorecard 結構）重新論證 seed→personas→rounds→aggregate pipeline,使設計讀起來是 `tw-stock-agent` contrarian 層的延伸。
3. 若要求真正的 README-only clean-room:由一位**未讀過 source** 的人依概念 spec 重作實作。

## A.7 CrowdScenarioReport JSON Schema（Draft 2020-12,關鍵防禦）

根層 `is_authoritative` 為 `const:false`;每個 object `additionalProperties:false`;**全 schema 不存在 price/NAV/折溢價/yield/weight/spend-cap 型別欄位**;唯一輸出的決策純量是 `contrarian_modifier ∈ [-1,+1]`（亦 `is_authoritative:false`,`formula_id` pinned）。
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
`engine.seed`＋`signals`＋`provenance.inputs_read` 使 R5 主張（結論可由可觀測訊號重現）**機器可檢**。

## A.8 台灣散戶人格 archetype taxonomy（10 類,閉集）

每個 archetype 帶 stance／conviction／time_horizon／leverage_appetite／yield_sensitivity／herding／polarity／register／**base_weight（群眾影響權重,非投資權重,Σ=1）**,並**附一行可引用行為先驗依據**。

| archetype | 中文 | herding | polarity | base_weight | 行為先驗依據（ship 前須補 3–5 條真實引用） |
|---|---|---|---|---|---|
| long_term_holder | 存股族 | 0.15 | contra | 0.16 | 0050/0056 長期持有結構、配息再投入 |
| day_trader | 當沖客 | 0.85 | pro | 0.12 | 台股當沖佔比、停損 cascade |
| yield_seeker | 殖利率派 | 0.40 | pro | 0.14 | 除息日輪動、配息調整敏感度 |
| leveraged_etf_player | 槓桿 ETF 玩家 | 0.70 | pro | 0.08 | 00631L 類波動下強制 unwind |
| foreign_institutional_lens | 外資視角 | 0.10 | contra | 0.12 | 外資淨流向、指數調整 |
| panic_retail | 恐慌散戶 | 0.90 | pro | 0.10 | 反指標、追高殺低 |
| ptt_dcard_trendwatch | PTT/Dcard 風向 | 0.95 | pro | 0.08 | 敘事放大、迷因速度 |
| mom_savings_group | 媽媽存股社團 | 0.35 | contra | 0.08 | 定期定額成長、抗跌黏著 |
| main_force_lens | 主力/中實戶 | 0.20 | contra | 0.06 | 融資融券、大戶持股 fade |
| dca_newbie | 定期定額新手 | 0.75 | pro | 0.06 | 2023 後新開戶、近因偏誤 |

刻意平衡:**pro-cyclical 放大器 0.56** vs **contra-cyclical 穩定器 0.44**。`is_synthetic:true` 強制標示;`base_weight` 與投資權重隔離。
> **壓測 CREDIBILITY 修正**:「依據」欄目前為**佔位描述**,ship 前 `personas.md` 每個 archetype **必須**附 3–5 條可引用真實依據（TWSE 散戶結構統計、定期定額帳戶成長等），否則此無法回測層作為 headline 無法辯護。

## A.9 透明 deterministic contrarian_modifier 公式（`contrarian-agg/1.0.0`）

與 `tw-stock-agent` `scoring-rules.md` 的四個 Sentiment/Contrarian 訊號**一對一**對映。純 Python、seeded、無 LLM、印出 seed 即可逐項手算。
- **Step A 種群**:`stance = scenario_default_stance[archetype]`＋seeded jitter;`influence_p = base_weight[a]*conviction_p`（正規化 Σ=1）。
- **Step B 四子訊號**:Crowding C＝|Σ influence·sign(s)|;Hype H＝pro-cyclical 同向 herding 加權;Panic/Euphoria P＝有號 tail 情緒;Tone–Price Divergence D＝crowd_tone − price_move（price_move 為**讀來**的觀測值）。
- **Step C 合成（frozen 權重）**:`raw = -(0.30·C·dir + 0.25·(H_bull−H_panic) + 0.25·P − 0.20·D)`。群眾過度向上＝負貢獻（偏謹慎）;群眾恐慌＝正貢獻（偏建設）。
- **Step D damping／clamp**:`completeness_factor = 1.0(full)/0.6(partial)`;`contrarian_modifier = clip(raw·factor, -1, +1)`;`no_tilt` band `[-0.15,+0.15]`（引擎自身的 NO_ACTION analogue）。
- **worked example（00878 升息,seed=42,full）→ −0.37,interpretation=fade_overbought**,逐項可手算,為 regression fixture（實作者須能由 seed 42 重現 −0.37）。

> **壓測 VALUE 重要揭露**:Step A 立場是**固定 archetype 先驗的 table lookup**＋jitter,**不讀** live crowding/hype/divergence;故此 modifier 作為決策訊號**未優於、甚至偏弱於**既有 contrarian 分數。**我們不宣稱 modifier 改善了決策**;它被防火牆刻意 neuter,價值釘在 reaction_chain 敘事。**改善方向（time-permitting）**:若要 modifier 帶決策邊際,人格立場須改為對 `provenance.inputs_read`（margin_balance、turnover_vs_avg、headline_repetition、price_5d_return）反應,而非 lookup。

## A.10 Demo 110 秒 runbook（唯一權威,單一累積時鐘,≤110s／硬上限 120s）

設計律:情境引擎拿**開場視覺＋情緒高峰**,但 earn＋spend＋refused-spend 拿**第一句與最後一句**及多數秒數。每個畫面數字皆 deterministic Python 算。

| 時段 | beat | 內容（live／replayed 標明） |
|---|---|---|
| 0:00–0:10 | 防火牆開場句 | 「群眾引擎只產出敘事與一個非權威純量;不碰金額/權重/下單,StackFund 全程不下任何證券單。」 |
| 0:10–0:24 | **EARN（live Stripe）** | test-mode 訂閱收款,P&L revenue 跳動＋真實 Stripe object id。**LIVE** |
| 0:24–0:38 | SPEND（pre-staged） | agent provision 工具,receipt 上 P&L cost。**除一筆 held-back 外皆 pre-provisioned** |
| 0:38–0:50 | **REFUSED SPEND（live error path）** | 第二次升級撞月度上限,Stripe API 硬拒 → NO_ACTION＋一行 deterministic 理由。徽章 SPEND REFUSED。 |
| 0:50–0:78 | ★ 情境引擎 WOW（純 replay,封頂 28s） | 按 ENTER → `--replay` 載 `scenario_0056_cut.json`,<3s,零 LLM 零網路,animate 三階反應鏈。底部 boxed `contrarian_modifier=+0.42`＋紅章 `is_authoritative=FALSE`。口播:「固定、**可稽核**的情境推演,**不是預測,也未經回測**。」 |
| 0:78–0:96 | HARD CUT 回引擎:防火牆現形 | PM view 列 deterministic 訊號＋群眾 modifier（標非權威）。0056 小幅 tilt,印**兩個獨立硬理由**。**當場把群眾面板刪掉,同一動作仍成立**。 |
| 0:96–0:110 | CLOSE:viability | before/after P&L:revenue−cost 為正（或近損益兩平,refused spend 護毛利）;免責可見;「賺錢、花錢、在不值得時拒絕花錢。」 |

引擎佔 ~82s（~75%）並拿最後一句;門面 28s 為高峰。**反 cannibalization**:每 beat 計時 cue card;情境 beat 上限 28s,超時**剪 narration 不剪 content**。

**五項 demo 必改（已折入）**:① 三筆 live Stripe 才是真正 blowup 風險,標 live/replayed＋「>5s alt-tab 到錄影」;② **禁 demo 中 live re-bake**（`--verify` 只展示預先算好的 verify log 或離線斷言 modifier 純量對 checked-in 期望值;LLM 文字即使 temp 0 也非 byte-stable）;③ static-card cut-line 為**一級** fallback;④ 所有可重現 artifact 在 live 前 bake 並 check-in（Day-8 bake／Day-11 錄影在關鍵路徑）;⑤ 螢幕與口播都要講「可重現 ≠ 已驗證」。

## A.11 建置計畫（6/19→6/30,防火牆＋Stripe earn/spend FIRST）

| 日 | 任務 | pd |
|---|---|---|
| Day 1 (6/19) | **GO/NO-GO GATE [BLOCKING]**:驗 Stripe TW 雙流＋TWSE/Yahoo 可達;fork tw-stock-agent,確認 SKILL.md 載入 | 1.0 |
| Day 2 (6/20) | 鎖四份 schema;freeze 0050/0056/00878 fixtures（含折溢價/殖利率） | 1.0 |
| Day 3 (6/21) | deterministic scorecard（透明公式 R5）＋cost optimizer（硬上限/保留）;數字 unit test | 1.0 |
| Day 4 (6/22) | **Stripe SPEND＋REFUSED SPEND**（cap-breach→結構化錯誤→NO_ACTION,最難 beat 早做） | 1.0 |
| Day 5 (6/23) | Stripe EARN（訂閱＋test-mode 收款接 P&L）。引擎端到端可 demo（beats 1–4,7） | 0.75 |
| Day 6 (6/24) | **防火牆契約＋PM tilt＋P&L**;gate/clamp/threshold-flip＋零-modifier CI 不變式;firewall_test.py。**CORE FROZEN** | 1.0 |
| Day 7 (6/25) | scenario engine scaffold:personas.md（30 人格＋先驗引用）、scenario_engine.py（RNG/tally/clamped 公式）。先 numbers-only | 1.0 |
| Day 8 (6/26) | **BAKE＋LLM 人格文字**:每抽樣人格呼叫 Nemotron 一次;bake `scenario_0056_cut.json`;加 `--replay`/`--verify`;確認 byte-identical replay | 1.0 |
| Day 9 (6/27) | replay 三階 animation、非權威章、情境推演 wording、hard-cut 轉 PM view;**static-card cut-line 演練就緒** | 1.0 |
| Day 10 (6/28) | NemoClaw wrap＋端到端 rehearsal（沙盒最後包）;計時 ≤110s;dry_run 安全網 | 1.0 |
| Day 11 (6/29) | 錄靜音 110s fallback;演練 Stripe 彈窗/TWSE rate-limit/投影機失敗→alt-tab drill;確認免責＋情境推演 wording 無遺漏 | 0.75 |
| Day 12 (6/30) | buffer / submit;buffer 用盡則 Day-9 static-card cut-line 保 demo 完整 | 0.5 |

**排序理由**:Days 1–6 在門面尚未開工前即交付整個受評引擎＋防火牆;最危險外部依賴（Stripe TW）Day 1 解決,最危險 core beat（refused spend）Day 4 解決;門面（7–9）為附加且可降級。

## A.12 法規與定位護欄（細節）

- **威脅模型（headline 化曝露）**:① SITA §4 投顧;② 證交法 §155 市場誠信/操縱觀感;③ R5/R6 credibility。
- **防線依「限」指派**:SITA §4 的 PRIMARY 防線是「無真實報酬＋非個別化出版品 framing＋去絕對買賣指令」;**防火牆是 correctness/credibility 控制,非主要投顧防線**（更正舊版誤指）。
- **RebalancePlan 調和**:付費牆後的「減碼 0056 ±2pp」渲染為**非個別化研究示意**（「研究情境下之示意配置」，非「您應減碼」）;一般可得/非客製;螢幕註明非對特定人之推介;test-mode/無費移除「報酬」trigger。
- **§155 拆解**:交易型 limb（沖洗/連續買賣）**零下單即完全 defuse**;資訊型 limb §155(1)6（散布足以影響價格資訊）**僅部分 defuse**——published 敘事須假設性壓力情境、永不陳述指名 ETF 將如何變動、禁對指名 ticker 主張價格方向。
- **用語 lexicon**:USE 情境推演/壓力測試/合成人格樣本/非權威輔助訊號;FORBID 預測/預報/精準推演未來/真實民意/情緒預報/情緒工程/買賣指令/目標價保證。**linter 為 backstop**（token-matching 可被繞過）,PRIMARY 控制是 **prompt-level 條件語氣規則＋對唯一 baked 敘事的人工審查**。
- **四層強制免責（placement 即控制）**:Tier A（SKILL.md 載入 banner）／Tier B（每份報告,schema **必填** `disclaimer` 欄,fail-closed）／Tier C（每張人格卡微標「合成人格樣本·情境推演·非真實民意·非預測」）／Tier D（demo 口播＋螢幕下緣:「情境推演·合成人格·不是預測·不是真實民意·未經回測;所有金額權重由程式計算;StackFund 全程不下任何證券單」）。
- **前瞻硬界線**:產品化若同時加入「真實付費訂閱者付真實報酬」＋「指名 ticker 方向性建議」,很可能跨入受規範之證券投資顧問,**上線前必須**取得合格台灣證券法律顧問意見。本文件為定位/合規 framing,**非台灣法律意見**。

## A.13 對抗性壓測總表（5 項皆 holds_with_changes）

| 壓測 | 發現（摘要） | 中和方式 | 殘餘風險 |
|---|---|---|---|
| **FW 防火牆** | gate 可能太鬆（假獨立）;tilt 量級可能動 P&L;spend 可能被 modifier 觸發;缺「零-modifier 重跑」字面檢查 | ≥2 個不同 factor family 訊號;tilt≤min(2pp,1×hard);threshold-flip 回退;spend 由 VoI gate、modifier 僅 tie-breaker;零-modifier CI 不變式 | **低**。需明確定義 factor family 正交性;GUARDRAIL_PP=2.00／N 仍須對部位規模佐證 |
| **DEMO 可行性** | 兩版 choreography 衝突;真正 blowup 是三筆 Stripe;`--verify` live re-bake 重引非決定性;artifact 未存在 | 合一 runbook（單一時鐘 ≤110s）;標 live/replayed＋alt-tab;禁 live re-bake;static-card 一級 fallback;Day-8/11 gated | **中**。110s slack 近零,防 cannibalization 靠**排練紀律**;Day-8 bake／Day-11 錄影在關鍵路徑 |
| **CREDIBILITY R5/R6** | headline 是 LLM 敘事,可重現≠正確;先驗 authored 非 observed;無回測 | 揭露 modifier 偏弱、價值釘敘事;每 archetype 附引用先驗;demo 給防火牆/NO_ACTION 同等權重、刪群眾後動作仍成立;口播「未經回測」 | **中（最誠實殘餘）**。敘事仍是未驗證 prose;合成先驗本質無法回測。守線靠 is_authoritative=false＋「情境推演非預測」＋坦承「這是 risk-scenario 覆蓋,非預測準確度」 |
| **REGULATORY** | 「防火牆＝主要投顧防線」誤指;「零下單→操縱幾乎完全 defuse」過度宣稱;headline 化使「只是研究」更難維持 | 防線依 limb 重新指派;RebalancePlan 改非個別化示意;§155 拆交易型(完全)/資訊型(部分);新增 R2c;前瞻硬界線 | **中**。資訊型 limb 僅部分 defuse;demo（test-mode/無報酬/零下單）尚屬研究 safe harbor,但係定位 framing 非法律意見,上線需 counsel |
| **CLEAN-ROOM/VALUE** | clean-room provenance 可證為假（曾引用只在 source 的私有 class 名）;架構借 MiroFish expression;modifier 對既有分數邊際近零 | 誠實重述邊界、移除 module/class 引用、（理想）由未讀 source 者重作;價值釘 reaction-chain 敘事、modifier 降級 | **中–低**。法律風險低（從未散布、無 code、MIT、無 §13）;真正風險是若不更正,評審 diff 兩 repo 時 credibility 崩 → provenance 更正為非協商必改 |

**總結**:整套 Core-B 設計通過對抗性壓測,但**只在折入每一項 required_fix 後成立**。三條最誠實的殘餘紅線（§1）應主動先講:可重現≠已驗證、modifier 不優於既有分數、真正法規曝險在收費方向性 RebalancePlan。把這三點當作**主動揭露的設計成熟度**,正是 face 搶眼、方向盤仍明顯鎖在 engine 上的最佳證明。
