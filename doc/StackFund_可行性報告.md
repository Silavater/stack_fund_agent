# StackFund 可行性報告

| 項目 | 內容 |
|---|---|
| **專案名稱** | StackFund — Autonomous AI Stack Portfolio Manager |
| **產品定位** | Autonomous FinOps Agent／Agentic SaaS Treasury |
| **文件版本** | v1.0 |
| **日期** | 2026-06-19 |
| **適用情境** | Hackathon（主題:能花錢並執行真實操作的代理；評分:usefulness／viability／presentation） |

---

## 1. 執行摘要

StackFund 是一個在固定月預算下，自動管理「API／模型／SaaS 訂閱組合」的自主代理。它由 **Hermes** 代理在 **NVIDIA OpenShell** 沙盒中執行，透過 **Stripe Projects** 對真實 SaaS 服務進行 provision、升級、降級與移除，並以 deterministic 最佳化決定資金配置。核心賣點是：**能把有限預算重新配置到最有價值的工具上，並在不值得時主動拒絕消費**。

**結論：技術可行，建議執行（Go），但附三項前置條件。**

本報告查證後確認，專案所依賴的三個外部平台——Stripe Projects、Hermes、NVIDIA NemoClaw／OpenShell——均為真實、且在 2026 年第一至第二季陸續釋出的產品，彼此的整合關係也與架構假設一致。換言之，這不是把不存在的功能拼在一起，而是把三個本來就為「會花錢、長時間執行的代理」設計的平台正確組合。主要風險集中在**執行面與 demo 可信度**，而非「技術是否存在」。三項前置條件詳見第 8 節。

---

## 2. 產品定義與定位

StackFund 把 API、模型與 SaaS 方案視為一個「工具投資組合」，由代理在固定預算內自動再平衡。對外可用「hedge-fund-style portfolio management」作為比喻，但產品類別應寫成 **Autonomous FinOps Agent**，避免「炒股／對沖基金」敘事——後者既不符合比賽「執行真實營運」的精神，也會逼團隊去假造一個股票市場。

概念對應如下：

| 投組用語 | 系統內真正代表的東西 |
|---|---|
| 資本 | 每月 SaaS／API 預算 |
| 資產 | OpenRouter、Sentry、Supabase、PostHog 等服務 |
| 報酬 | 完成任務、成功請求、產生的業務價值 |
| 波動 | 用量、價格、延遲、錯誤率、需求變化 |
| 再平衡 | Upgrade／Downgrade／Add／Remove |
| 風險限制 | 支出上限、保留金、關鍵服務保護 |

最關鍵的設計判斷是：**Stripe Projects 本身就是代理能操作的 SaaS 資產市場，不需要自己模擬一個**。這讓 demo 落在真實操作上，而非空轉。

---

## 3. 技術可行性

### 3.0 查證總表

| 元件 | 架構假設的能力 | 查證結果 |
|---|---|---|
| Stripe Projects | CLI 可 provision／升降級服務、查支出、設支出上限 | **成立**。功能與假設一致，上限在 API 層強制 |
| Hermes | 開源代理、支援 skill、跨 session 持續 | **成立**。Nous Research 開源 self-improving 代理，已整合 Stripe skill |
| NemoClaw／OpenShell | 代理沙盒，控管檔案／網路／憑證／推論 | **成立**。NVIDIA 官方沙盒，四個 policy domain，官方支援 Hermes |
| Nemotron | 用於衝擊解讀與決策說明 | **成立**。NVIDIA 開源模型，為 NemoClaw 預設推論模型 |

### 3.1 Stripe Projects（資產市場與執行層）

Stripe Projects 是一個「用 CLI／coding agent 來 provision 與管理軟體堆疊」的產品。經查證，它提供的能力與本架構假設一致：

- **服務生命週期操作**：`init`、`add`、`status`、`catalog`、`upgrade`、`downgrade`、`env --pull`、`link`、`billing add` 等指令，可對資料庫、auth、hosting、analytics、AI、observability 等服務進行 provision 與升降級。
- **支出控管**：支援全域與單一 provider 的硬性支出上限，且**在 API 層強制**（非 prompt 層）；另有 merchant 白名單、完整交易紀錄、可選的「高額需人工核可」門檻。這正好對應架構中 Layer 3 的外部硬限制。
- **代理友善**：每個指令都支援非互動旗標（CI／script／agent 適用）與結構化輸出；憑證以 Shared Payment Token 形式交付給 provider，不以明文金鑰落地。
- **供應商規模**：目前已接 **49 家 provider**（近期一次新增 16 家，含 Metronome 做 usage billing、ClickHouse 做 LLM observability）。架構原估「30 多家」屬保守，實際更充足。
- **整合形式**：以 skill 形式提供，已可在 Hermes、Factory Droids、Warp 等代理中使用，並相容 MCP。

### 3.2 Hermes（代理與決策編排層）

Hermes 是 Nous Research 的**開源、self-improving 代理**。經查證，Stripe 已於近期（約一週前）將 Stripe Projects 以 skill 形式整合進 Hermes；其定位是「跨 session 攜帶脈絡的持續協作者」，適合需要在數天／數週內反覆操作同一專案的工作流。這支持架構中「Hermes＋自訂 StackFund Skill」的設計。

> **待確認項**：自訂的 StackFund Skill 需對齊 Hermes 實際載入的 skill 規格。Stripe 官方 skill 採用 Agent Skills 格式（`SKILL.md` + `scripts/` + `references/`），Hermes 可載入；自訂 skill 應沿用同一格式以確保相容（屬低風險，但須在 Day 1 驗證）。

### 3.3 NVIDIA NemoClaw／OpenShell（執行邊界與風控層）

NemoClaw 是 NVIDIA 的開源參考堆疊，把代理包進 OpenShell 沙盒以強化安全；OpenShell 是 NVIDIA Agent Toolkit 的一部分（Apache 2.0），於 GTC 2026 釋出。經查證，其能力與架構假設一致：

- **四個 policy domain**：filesystem、network、process、inference。policy 為宣告式 YAML；filesystem／process 在沙盒建立時鎖定，network／inference 可**熱更新**。
- **憑證隔離**：金鑰不落在沙盒檔案系統，由 L7 proxy 在 egress 時注入；預設 default-deny 網路（「全關→只開必要孔」）。
- **kernel 級機制**：seccomp（syscall 過濾）、Landlock（檔案存取）、network namespaces（流量隔離）。
- **模型**：以 Nemotron 為預設推論模型，Privacy Router 可在本地 Nemotron 與雲端之間路由。
- **代理支援**：預設跑 OpenClaw，但**官方明確支援 Hermes**（有對應 Quickstart 與 model-specific setup）。

這證明架構把 NemoClaw／OpenShell 當作「會動用預算的長時間代理」的執行邊界，是合理選型，而非硬塞 NVIDIA logo。

### 3.4 整合可行性小結

三個平台彼此咬合：OpenShell 負責「代理能不能繞過正常執行路徑」，Stripe Projects 負責「金額硬上限與真實服務操作」，Hermes 負責「跨 session 編排與執行」。三者的職責邊界清楚，沒有功能重疊或缺口。**技術可行性成立。**

---

## 4. 架構可行性

五層架構（Portfolio Book → Shock Simulator → Portfolio Manager → Risk & Execution → Audit & Operational P&L）在工程上站得住，其中幾項判斷尤其正確：

1. **LLM／deterministic 分工正確**。價格、ROI、支出總額與約束檢查由 deterministic Python 計算，LLM（Nemotron／Hermes）只負責解讀衝擊與產生說明。讓 LLM 心算價格是經典失敗模式，架構明確避開，這是整份設計最重要的正確決策。
2. **防禦縱深的支出控管**。三層獨立把關：StackFund 業務規則（軟）→ Stripe API 層支出上限（硬）→ OpenShell 執行邊界（硬）。即使 Hermes 失控想把預算花光，Stripe 的 API 級上限與 OpenShell 的網路 policy 仍能阻擋——這是最有說服力的安全 demo 賣點。
3. **Schema-first**。先鎖定 PortfolioSnapshot／RebalancePlan／ExecutionReceipt 三份 JSON schema，再開發，既正確也讓 demo 對評審易讀。敏感 token／金鑰不進 JSON 的原則正確。
4. **NO_ACTION 是設計亮點**。代理能證明「現在不值得花這筆錢」，是「真在推理」而非「看到工具就買」的最強訊號。

**需強化的架構點**：信任邊界要明講。deterministic optimizer 若以 Hermes skill script 形式在沙盒內執行，其「不會幻想價格」的保證仍依賴沙盒未被攻陷；因此真正的硬保證是 Stripe API 級上限與 OpenShell policy，業務規則只是建議層。Demo 與文件都應把這點講清楚。

---

## 5. 營運與執行可行性

| 面向 | 評估 |
|---|---|
| 團隊能力 | 具 CS／系統整合背景，能處理 CLI、Python 最佳化、JSON 介面與沙盒設定，能力相符 |
| 開發範圍 | MVP 收斂得當（3 服務、1 固定衝擊、deterministic optimizer、1 個真實 Stripe 操作、1 個被拒操作） |
| Demo 形式 | 90–120 秒 live demo；流程設計清楚，但**真實執行存在出包風險**（見第 6 節 R2） |
| 對外依賴 | 依賴 Stripe 帳號資格與 provider 目錄狀態，需 Day 1 驗證 |

開發順序建議維持原案：先驗證 Stripe 帳號與 provider catalog → 鎖三份 schema → 固定 fixture → deterministic optimizer → read-only Hermes 流程 → policy checker → 接 Projects 真實操作 → dashboard → 最後包 NemoClaw 並錄 demo。**「先把真實執行打通、最後才包沙盒」的順序正確**，能避免太早被環境問題卡住。

---

## 6. 風險評估與緩解

| 編號 | 風險 | 等級 | 說明 | 緩解措施 |
|---|---|---|---|---|
| R1 | 台灣 Stripe 付費資格 | 高 | Stripe Projects 付費層的國別清單可能未含台灣；Link CLI 可能仍 US-only | 設三模式 `dry_run／free_only／live_limited`；Day 1 直接驗證帳號；向主辦詢問是否提供 sandbox。即使無法付費升級，仍可演真實 free-tier add／remove + 讀 catalog／status，付費 upgrade 明確標記為 blocked |
| R2 | Live demo 執行出包 | 高 | 官方文件警告 provisioning／憑證交換會跳瀏覽器授權彈窗；另有延遲與 rate limit | 所有服務**事先 provision**，demo 跑在已連線服務上重播；演練授權彈窗／延遲／rate limit 三種失敗；`dry_run` 當安全網；備一份錄影 fallback |
| R3 | optimizer 可信度（attributed_value 手填） | 高 | 代理的「聰明」其實是 value 數字怎麼設的函數，結論可能被輸入餵出來 | 用**透明公式從可觀測訊號推導 value**（如 requests × success_rate × criticality 或 value-per-successful-request），讓決策看起來是推理出來、而非預先寫好 |
| R4 | Demo 決策的直覺矛盾 | 中 | 需求暴增 2.5× 卻砍 observability，pattern-match 成錯誤；真正逼出取捨的是 `reserve_floor` | 把「撞到預算上限＋保留金、被迫取捨」講在最前面；或**換一個不跟直覺打架的犧牲品**（如把使用率偏低、tier 過高的服務降級） |
| R5 | Agency 認知 | 中 | 決策全是 deterministic Python 時，會被質疑「這是代理還是計算機加字幕」 | 把 agency 放在**執行／適應迴圈**：讓 Hermes 真的跑 `stripe projects upgrade`、撞到 provider cap 失敗、讀懂錯誤、改成 downgrade。Demo 須演到「應對一個真實失敗」 |
| R6 | 次要技術點 | 低 | ① 自訂 skill 格式需對齊 Hermes；② vendor concentration 只在 dashboard、未進 objective | ① Day 1 驗證 skill 載入；② 若要「risk-adjusted」成立，集中度風險應進目標函數 |

---

## 7. 資源需求與時程（MVP 範圍）

**必須完成**
3 個服務（每個 2 個候選方案）、1 個固定 demand shock、PortfolioSnapshot、deterministic ROI optimizer、自訂 Hermes StackFund Skill、至少 1 個真實 Stripe Projects 操作、1 個被拒絕的支出動作、before／after Operational P&L、在 NemoClaw／OpenShell 中執行。

**有時間再做**
單次付費 API、多期歷史資料、Hermes 記憶使用者偏好、自動排程每小時再平衡、多個 shock scenario、真正 provider telemetry。

**明確不做**
真實股票交易、台股 API、上千個代理、知識圖譜、完整財務會計系統、複雜 ML 預測、Coupon／Promotion、超過 4–5 個供應商。

此範圍與「don't do」清單顯示團隊已從過度設計收斂，**範圍紀律良好**。

---

## 8. 結論與建議

**建議：執行（Go）**，附以下三項前置條件，並設一個 Phase 1 go／no-go 檢查點。

**前置條件（須在開發初期完成）**
1. **Day 1 驗證 Stripe 帳號**：跑 `projects init／catalog／add <free-tier>／status／billing add／billing update --limit`，確認台灣帳號可達到的操作邊界，並決定 demo 走 `free_only` 還是 `live_limited`。
2. **attributed_value 改為公式推導**：在 optimizer 骨架就把 value 從 telemetry 訊號算出來，杜絕「結論被輸入餵出來」的可信度漏洞（R3）。
3. **Demo 腳本去矛盾並備 fallback**：重新檢視核心再平衡決策（R4），並把授權彈窗／延遲的失敗模式演練過、備好錄影（R2）。

**Go／No-Go 檢查點（Phase 1）**：若 Day 1 無法在台灣帳號上完成「至少一個真實 free-tier add／remove + 讀取 catalog／status」，則立即切換為 `free_only`＋`dry_run` 為主的 demo，並向主辦確認 sandbox。**不要讓整個架構綁死在「台灣帳號一定能付費升級」這個假設上。**

整體而言，本專案最強的地方不是「代理能花錢」，而是「代理能把有限的錢重新配置到最有價值的工具上，並在不值得時主動拒絕消費」——這比單純的自動付款代理更接近可落地的企業產品，也更貼合比賽對 usefulness 與 viability 的評分。

---

## 9. 參考來源

- Stripe Projects 官方文件 — https://docs.stripe.com/projects
- Stripe Projects 產品頁 — https://projects.dev/
- Stripe Blog：Projects 新增代理整合、供應商與開發者控制（含 Hermes 整合、49 providers） — https://stripe.com/blog/stripe-projects-adds-new-agents-providers-developer-controls
- NVIDIA NemoClaw（GitHub） — https://github.com/NVIDIA/NemoClaw
- NVIDIA OpenShell（GitHub） — https://github.com/NVIDIA/OpenShell
- NVIDIA NemoClaw 官方文件 / 架構 — https://docs.nvidia.com/nemoclaw/latest/reference/architecture
- NVIDIA Technical Blog：Run Autonomous, Self-Evolving Agents More Safely with OpenShell — https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/
- NVIDIA Newsroom：NVIDIA Announces NemoClaw — https://nvidianews.nvidia.com/news/nvidia-announces-nemoclaw

> 註：本報告中所有外部平台能力均經上述來源查證後以摘要方式呈現；實際指令旗標與供應商清單請以各平台最新官方文件為準。
