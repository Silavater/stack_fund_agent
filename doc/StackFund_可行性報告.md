# StackFund 可行性報告（台股 ETF 研究台版）

| 項目 | 內容 |
|---|---|
| **專案名稱** | StackFund — Autonomous Taiwan ETF Research Desk |
| **產品定位** | 自主經營的台股 ETF 研究／顧問微型事業（Agentic Research-as-a-Service） |
| **文件版本** | v2.0（由 SaaS 投組版改為台股 ETF 版） |
| **日期** | 2026-06-19 |
| **比賽** | Hermes Agent Accelerated Business Hackathon（NVIDIA × Stripe × Nous Research） |
| **主題對齊** | 代理能 **earn／spend／run real operations**；評分:usefulness／viability／presentation；截止 2026-06-30 |

---

## 1. 執行摘要

StackFund 是一個由 **Hermes** 代理自主經營的**台股 ETF 研究台**。它在 **NVIDIA NemoClaw／OpenShell** 沙盒中執行,做三件真實的事:

1. **Run real operations** — 用一個自訂的 Hermes Skill(設計參考開源的 `AZNitro/tw-stock-agent`),拉取 TWSE OpenAPI、TPEX／MOPS、Yahoo Finance、新聞與反指標情緒,對熱門台股 ETF(0050、0056、00878 等)產出結構化研究與再平衡建議。
2. **Spend** — 用 **Stripe Skills for Hermes** 自行 provision 並付費它營運所需的資料／運算／SaaS 堆疊(資料 API、LLM 推論、資料庫、observability、報告遞送),並以 deterministic optimizer 在固定預算內再平衡這個「工具投組」。
3. **Earn** — 用 **Stripe** 向訂閱者收費販售研究與訊號,產生真實營收;並以 before／after 的 **Operational P&L** 證明這個代理事業能自負盈虧。

**結論:技術可行,建議執行(Go),附四項前置條件。**

最關鍵的設計判斷:**Stripe 負責「事業的金流」(花錢買工具、向客戶收費),而不是「證券下單」**。台股 ETF 是代理研究與服務的**標的**,不是用 Stripe 買賣的資產。如此一來,三個贊助平台(Hermes 編排、Stripe earn＋spend、NemoClaw 安全)各司其職、真實咬合,且同時命中比賽最看重的「earn＋spend＋real operations」三件事——這也是本版相對 v1(只有 spend)的最大升級。主要風險集中在**台灣金融顧問法規、資料來源穩定度與 demo 可信度**,而非「技術是否存在」。四項前置條件詳見第 8 節。

---

## 2. 產品定義與定位

StackFund 把自己定位成一個**會自己賺錢、自己付營運成本、自己做研究**的微型事業,而非單純的選股機器人。對外敘事用「自動化的台股 ETF 研究台」,產品類別寫成 **Agentic Research-as-a-Service**。

系統裡其實有**兩個投組**,這正是設計亮點:

| 投組 | 內容 | 誰受益 |
|---|---|---|
| **ETF 研究投組** | 0050／0056／00878 等台股 ETF 的配置與再平衡建議 | 訂閱客戶 |
| **營運成本投組** | 資料 API、LLM 推論、資料庫、observability、遞送等 SaaS | 代理自己(FinOps) |

代理同時對「客戶該怎麼配置 ETF」與「自己這門生意該怎麼花錢」做最佳化決策。概念對應:

| 用語 | 系統內真正代表的東西 |
|---|---|
| 資本 | 每月營運預算(由訂閱營收支應) |
| 資產 | (對外)台股 ETF;(對內)資料／運算／SaaS 服務 |
| 報酬 | (對外)研究品質與命中率;(對內)營收 − 成本的營運毛利 |
| 再平衡 | (對外)調整 ETF 配置建議;(對內)Upgrade／Downgrade／Add／Remove 工具 |
| 風險限制 | 支出上限、保留金、關鍵服務保護、**不做未授權投資顧問** |

**重要法規定位**:StackFund 提供的是**研究與決策支援(research / educational decision-support)**,**不是受託代客操作、也不是收費的證券投資顧問**。所有輸出附免責聲明,語氣採決策支援用語(見第 6 節 R2、與參考 skill 一致的「research, not autonomous trading」原則)。

---

## 3. 技術可行性

### 3.0 查證總表

| 元件 | 假設的能力 | 查證結果 |
|---|---|---|
| Stripe(Skills／billing) | 代理可 provision／付費 SaaS(spend),並向客戶收訂閱費(earn) | **成立**。Stripe Skills for Hermes 支援代理自助 provision 與付費;Stripe billing 支援訂閱收款 |
| Hermes | 開源代理、可載入 Agent Skills、跨 session 持續 | **成立**。Nous Research 開源 self-improving 代理,已整合 Stripe skill |
| NemoClaw／OpenShell | 代理沙盒,控管檔案／網路／憑證／推論 | **成立**。NVIDIA 官方沙盒,四個 policy domain,官方支援 Hermes |
| 台股資料層 | TWSE／TPEX／MOPS／Yahoo 可取得 ETF 價量、淨值、配息、籌碼、新聞 | **成立**。TWSE OpenAPI 為官方公開資料;`tw-stock-agent` 已示範整合路徑 |
| 自訂 ETF 分析 Skill | 以 SKILL.md + scripts/ + references/ 格式供 Hermes 載入 | **成立**。`tw-stock-agent` 已採此格式(即 Hermes／Stripe 官方 skill 同格式),可直接 fork 降低風險 |

### 3.1 Stripe（earn ＋ spend 的金流層）

- **Spend(provision／付費營運堆疊)**:透過 Stripe Skills for Hermes,代理可對資料庫、auth、hosting、analytics、AI、observability 等服務做 provision 與升降級,並在 **API 層強制硬性支出上限**(非 prompt 層),另有 merchant 白名單、完整交易紀錄與「高額需人工核可」門檻。憑證以 Shared Payment Token 交付,不以明文金鑰落地。
- **Earn(向訂閱者收費)**:用 Stripe billing 建立訂閱方案(如基礎版／專業版)、開立發票、收款,形成真實營收流。**這是命中比賽「earn」的核心,也是 v1 缺的一塊**。
- **代理友善**:指令支援非互動旗標與結構化輸出,適合在 Hermes skill 中以 script 呼叫。

### 3.2 Hermes（代理與編排層）

Hermes 是 Nous Research 的開源、self-improving 代理,跨 session 攜帶脈絡,適合「每天／每週反覆研究同一組 ETF 並服務同一批訂閱者」的工作流。Stripe 已將其 skill 整合進 Hermes;自訂的 StackFund Skill 與 ETF 分析 Skill 只要沿用 Agent Skills 格式即可載入。

### 3.3 NVIDIA NemoClaw／OpenShell（執行邊界與風控層）

- **四個 policy domain**:filesystem、network、process、inference,宣告式 YAML;network／inference 可熱更新。
- **憑證隔離**:金鑰不落沙盒檔案系統,由 L7 proxy 在 egress 時注入;預設 default-deny 網路。
- **kernel 級機制**:seccomp、Landlock、network namespaces。
- **模型**:預設以 Nemotron 為推論模型,可做衝擊解讀與決策說明;Privacy Router 可在本地／雲端間路由。
- **代理支援**:官方明確支援 Hermes。

對一個**同時處理真實金流(收款／付費)與金融研究輸出**的代理,沙盒提供的硬性支出上限與網路 policy,是最有說服力的安全 demo 賣點。

### 3.4 台股 ETF 資料層（本版新增，核心 operation）

設計參考開源專案 **`AZNitro/tw-stock-agent`**,自建一個 Hermes 相容的 ETF 分析 Skill。資料來源與優先序(沿用其 `references/data-sources.md` 精神):

1. **TWSE OpenAPI**(官方真實來源):ETF 價量、指數、融資融券、本益比／淨值比/殖利率、重大公告。
2. **TPEX／MOPS**:上櫃與財報／配息揭露。
3. **Yahoo Finance**:報價快照、分析師目標、同類比較、新聞敘事。
4. **Web／News**:催化事件與重複敘事偵測。
5. **反指標情緒**:過熱／恐慌／擁擠交易的風險修正層(輔助,不可凌駕硬數據)。

**ETF 特有欄位**需額外處理:淨值 vs 市價的**折溢價**、**追蹤誤差**、**成分股重疊**、**除息／配息日**。這些都用 deterministic Python 計算,LLM 只負責解讀與說明。

> **待確認項(低風險)**:`tw-stock-agent` 的 `scripts/` 目前是 placeholder(官方 README 已聲明),真正的 fetcher 需自行補上;但其 `SKILL.md`／`references/`(data-sources、scoring-rules、output-schema、value-analysis)已是可直接採用的設計骨架。

### 3.5 整合可行性小結

OpenShell 管「代理能不能繞過正常執行路徑」、Stripe 管「金額硬上限＋真實 earn／spend」、Hermes 管「跨 session 編排」、ETF Skill 管「真實研究 operation」。職責邊界清楚、無重疊或缺口。**技術可行性成立。**

---

## 4. 架構可行性

五層架構(ETF Data Book → Scenario Engine → Research & Portfolio Manager → FinOps & Execution → Audit & Operational P&L),其中幾項判斷尤其正確:

1. **LLM／deterministic 分工正確**。價格、淨值、折溢價、殖利率、配置權重、支出總額與約束檢查由 deterministic Python 計算;LLM(Nemotron／Hermes)只負責解讀市場衝擊、撰寫研究說明。讓 LLM 心算淨值或殖利率是經典失敗模式,架構明確避開——這是整份設計最重要的正確決策。
2. **雙投組、單一 P&L**。對外的 ETF 配置建議與對內的工具成本最佳化共用一套 Operational P&L,demo 能同時展示「給客戶的價值」與「代理自己的生意是否賺錢」。
3. **防禦縱深的支出控管**。三層獨立把關:StackFund 業務規則(軟)→ Stripe API 層支出上限(硬)→ OpenShell 執行邊界(硬)。即使 Hermes 失控想把預算花光,Stripe 的 API 級上限與 OpenShell 的網路 policy 仍能阻擋。
4. **Schema-first**。先鎖定 ETFResearchReport／RebalancePlan／OperationalReceipt 三份 JSON schema(ETF 報告直接採 `tw-stock-agent` 的 `output-schema.md` 改寫),再開發。敏感 token／金鑰不進 JSON。
5. **NO_ACTION 是設計亮點**。代理能證明「這週 ETF 配置不需要調整」或「這筆工具花費現在不值得」,是「真在推理」而非「看到就動作」的最強訊號。

**需強化的架構點**:信任邊界要明講。deterministic 計算的「不會幻想數字」保證,仍依賴沙盒未被攻陷;真正的硬保證是 Stripe API 級上限與 OpenShell policy,業務規則只是建議層。此外,**所有對外研究輸出須掛免責聲明**(研究／教育用途,非受託操作或收費投顧)。

---

## 5. 營運與執行可行性

| 面向 | 評估 |
|---|---|
| 團隊能力 | 具 CS／系統整合背景,能處理 CLI、Python、JSON 介面、沙盒設定與台股資料抓取,能力相符 |
| 開發範圍 | MVP 收斂得當(3–4 檔 ETF、1 個固定市場情境、deterministic scorecard、1 個真實 Stripe 付費、1 個真實 Stripe 收款、1 個被拒動作) |
| Demo 形式 | 90–120 秒 live demo;流程清楚,但真實執行存在出包風險(見第 6 節 R3) |
| 對外依賴 | 依賴 Stripe 帳號資格、TWSE／Yahoo 資料可用性,需 Day 1 驗證 |

**開發順序建議**:先驗證 Stripe 帳號(earn＋spend 都要)與 TWSE OpenAPI 可達 → 鎖三份 schema → fork `tw-stock-agent` 補 ETF fetcher → 固定 fixture → deterministic scorecard／optimizer → read-only Hermes 流程 → policy checker → 接 Stripe 真實付費＋收款 → dashboard → 最後包 NemoClaw 並錄 demo。「先把真實執行打通、最後才包沙盒」的順序正確。

---

## 6. 風險評估與緩解

| 編號 | 風險 | 等級 | 說明 | 緩解措施 |
|---|---|---|---|---|
| R1 | 台灣 Stripe earn／spend 資格 | 高 | Stripe Skills 付費層、訂閱收款的國別清單可能未含台灣或受限 | 設三模式 `dry_run／free_only／live_limited`;Day 1 直接驗證帳號可否「付費 provision」與「對測試卡收款」;退路是 free-tier provision＋測試模式收款,付費動作明確標記 blocked |
| R2 | 台灣投顧法規 | 高 | 在台灣,**收費**提供證券投資建議涉及《證券投資信託及顧問法》;自動化「買賣 ETF 建議」若收費恐觸法 | 產品定位為**研究／教育決策支援**,非受託操作、非個別化收費投顧;所有輸出掛免責聲明;用「偏多但估值偏高」式決策支援用語,避免絕對買賣指令;與參考 skill「research, not autonomous trading」原則一致 |
| R3 | Live demo 執行出包 | 高 | provision／收款會跳授權彈窗;TWSE／Yahoo 可能延遲或 rate limit | 服務事先 provision、demo 重播;演練授權彈窗／延遲／rate limit;`dry_run` 當安全網;備錄影 fallback |
| R4 | 資料來源穩定度與時效 | 中 | TWSE OpenAPI 有 rate limit;Yahoo 頁面可能改版;盤中即時資料有限 | 採參考 skill 的「官方日資料代理盤中」fallback(fmtqik／mi-stock20);所有數字標 freshness;部分資料缺失時明確標記 partial,不臆測 |
| R5 | scorecard 可信度 | 中 | 「聰明」其實是評分權重怎麼設的函數,結論可能被輸入餵出來 | 用**透明公式從可觀測訊號推導分數**(趨勢／基本面／估值／催化／情緒/風險,沿用 `scoring-rules.md`),折溢價與追蹤誤差等用真實數據,讓決策看起來是推理出來的 |
| R6 | Agency 認知 | 中 | 決策全是 deterministic Python 時,會被質疑「這是代理還是計算機加字幕」 | 把 agency 放在**執行／適應迴圈**:讓 Hermes 真的跑 Stripe provision、撞到上限失敗、讀懂錯誤改成 downgrade;真的對訂閱者收款;Demo 須演到「應對一個真實失敗」 |
| R7 | 次要技術點 | 低 | ① 自訂 skill 格式需對齊 Hermes;② `tw-stock-agent` scripts 為 placeholder | ① 直接 fork 同格式 repo,Day 1 驗證載入;② Day 1 補最小可用 fetcher(TWSE 價量＋Yahoo 報價即可起步) |

---

## 7. 資源需求與時程（MVP 範圍）

**必須完成**
3–4 檔台股 ETF(每檔取價量／淨值／折溢價／殖利率/配息)、1 個固定市場情境(如升息或電子權值回檔)、ETFResearchReport schema、deterministic scorecard＋成本 optimizer、自訂 Hermes ETF 分析 Skill(fork 自 `tw-stock-agent`)、至少 1 個真實 Stripe **付費**(spend)、至少 1 個真實 Stripe **收款／訂閱**(earn)、1 個被拒絕的支出動作、before／after Operational P&L、在 NemoClaw／OpenShell 中執行、輸出附免責聲明。

**有時間再做**
多期歷史回測、Hermes 記憶使用者偏好、自動排程每日盤後再平衡、多情境模擬、ETF 成分股重疊與追蹤誤差深度分析、客戶分級訂閱方案、`value-analysis.md` 的 A–E 護城河式 ETF 評級。

**明確不做**
真實證券下單／接券商 API、受託代客操作、收費個別化投顧、即時逐筆 tick 資料、槓桿／期貨型 ETF、上百檔 ETF、複雜 ML 預測。

此範圍與「don't do」清單顯示已從過度設計收斂,**範圍紀律良好**;且刻意避開「真實下單」與「收費投顧」兩個法規地雷。

---

## 8. 結論與建議

**建議:執行(Go)**,附以下四項前置條件,並設一個 Phase 1 go／no-go 檢查點。

**前置條件(須在開發初期完成)**
1. **Day 1 驗證 Stripe 雙向金流**:確認台灣帳號可「付費 provision 至少一個 SaaS」(spend)與「對測試卡建立訂閱並收款」(earn),決定 demo 走 `free_only` 還是 `live_limited`。
2. **Day 1 驗證台股資料層**:跑通 TWSE OpenAPI 取一檔 ETF 價量＋Yahoo 報價,確認 rate limit 與時效,補上 `tw-stock-agent` 的最小 fetcher。
3. **scorecard 改為公式推導**:在 optimizer 骨架就把分數從 telemetry／市場訊號算出來,杜絕「結論被輸入餵出來」(R5)。
4. **法規定位與免責聲明落地**:明確定位為研究／教育決策支援,輸出掛免責,語氣去除絕對買賣指令(R2);Demo 腳本去矛盾並備錄影(R3)。

**Go／No-Go 檢查點(Phase 1)**:若 Day 1 無法在台灣帳號上同時完成「至少一個真實付費 provision」與「至少一筆真實/測試模式收款」,則切換為 `free_only`＋測試模式為主的 demo,並向主辦確認 sandbox。**不要讓整個架構綁死在「台灣帳號一定能跑完整 earn＋spend」這個假設上。**

整體而言,本專案最強的地方不是「代理能選 ETF」,而是「代理能**自己經營一門台股 ETF 研究生意**——做真實研究、付自己的營運成本、向客戶收費、並在不值得時主動拒絕消費」,完整命中比賽 earn／spend／run real operations 三軸,也比單純的選股 bot 更接近可落地的事業,更貼合 usefulness 與 viability 的評分。

---

## 9. 參考來源

- Hermes Agent Accelerated Business Hackathon(NVIDIA × Stripe × Nous Research)— 主題與評分
- 台股 ETF 分析 skill 設計參考:`AZNitro/tw-stock-agent` — https://github.com/AZNitro/tw-stock-agent (SKILL.md／references/data-sources・scoring-rules・output-schema・value-analysis)
- TWSE 臺灣證券交易所 OpenAPI — https://openapi.twse.com.tw/
- 公開資訊觀測站 MOPS — https://mops.twse.com.tw/
- Stripe（Skills for Hermes／billing）官方文件 — https://docs.stripe.com/
- Hermes(Nous Research)— https://nousresearch.com/
- NVIDIA NemoClaw（GitHub） — https://github.com/NVIDIA/NemoClaw
- NVIDIA OpenShell（GitHub） — https://github.com/NVIDIA/OpenShell
- NVIDIA Technical Blog:Run Autonomous, Self-Evolving Agents More Safely with OpenShell — https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/

> 註:① 外部平台能力以摘要呈現,實際指令旗標與供應商清單請以各平台最新官方文件為準。② 本文件為比賽可行性評估,非投資建議;StackFund 產品定位為研究／教育決策支援,非受託操作或收費證券投資顧問。
