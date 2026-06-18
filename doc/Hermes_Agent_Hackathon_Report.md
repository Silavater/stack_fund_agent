# Hermes Agent Accelerated Business Hackathon 專案報告
## 專案名稱：Autonomous AI Hedge Fund (自動化微型量化基金代理)

**開發負責人**：羅德銘 (阿呆)
**單位**：國立臺中科技大學 資訊管理系 (NUTC IM)
**比賽截止日**：6/30 EOD

---

## 1. 專案概述 (Project Overview)

本專案旨在打造一個具備企業級安全與自主財務管理能力的「微型量化基金代理 (Autonomous AI Hedge Fund)」。
系統不僅能透過 `tw-stock-agent` 與 `mirofish` 技能執行台股與大盤型 ETF (如 0050) 的市場分析與自主交易，更能利用 **Stripe Skills** 根據市場波動度自動訂閱或降級付費的金融數據源。本專案完美符合主辦方 (NVIDIA × Stripe × Nous Research) 對於 **Earn, Spend, Run real operations** 的核心硬指標要求。

## 2. 系統架構 (System Architecture)

系統採用嚴謹的多層解耦設計，確保 AI 決策與資金執行的安全隔離：

*   **Layer 0 基礎設施**：以 Python 作為核心後端開發語言，確保與資料科學套件的完美相容。
*   **Layer 1 決策大腦 (Hermes Agent)**：作為核心大腦，負責接收市場訊號並進行推理計算。
*   **Layer 2 市場觀測與交易層 (tw-stock-agent + mirofish)**：負責抓取台股報價、ETF 的走勢，並封裝下單動作為可被 Agent 呼叫的技能。
*   **Layer 3 自主消費層 (Stripe Skills)**：當 Hermes 判斷大盤波動劇烈，免費報價的延遲可能導致交易風險時，Agent 會透過 Stripe API 自主刷卡訂閱高頻即時 API，並在行情平淡時自動降級以節省預算 (Spend to Earn)。
*   **Layer 4 安全護欄 (NemoClaw)**：導入沙盒攔截機制。設定嚴格的白名單防護網，避免 Agent 因幻覺 (Hallucination) 購買高風險微型股。

## 3. 核心決策演算法 (Attributed Value Logic)

為了向評審證明 Agent 具備真實的財商推理能力，決策邏輯採用動態權重計算：

```text
Trade Signal = Alpha Score (0-1) * Market Sentiment * Risk Weight
Net Profitability = (Expected Trade Value) - (API Subscription Cost)
```

**自體優化機制**：當 `Net Profitability` 連續下降，Agent 會自主觸發 `Stripe Skill` 退訂非必要的進階資料源，實踐 SaaS FinOps 的成本控管。

## 4. 展演與護城河策略 (Demo Strategy)

針對 1-3 分鐘的官方 Demo 影片，將採用 **雙拼畫面 (Split-Screen)** 結合 **誘捕展示法 (Trap Strategy)** 進行火力展示：

1.  **動態升級 (Spend)**：展示 Agent 發現現有免費 API 延遲過高，自主呼叫 Stripe 付費訂閱進階資料，右側即時顯示 Stripe Dashboard 的扣款成功與訂閱狀態改變。
2.  **安全攔截 (Security)**：刻意在 Prompt 或市場訊號中混入惡意雜訊，誘使 Agent 嘗試重倉買入非白名單的高風險標的。此時底層 NemoClaw 即時觸發 `[Transaction Blocked]` 的紅色警告，展示企業級的 Rogue AI 防禦能力。
3.  **穩健獲利 (Earn)**：Agent 修正策略後，轉向購買預設白名單內的大盤型 ETF (如 0050)，順利完成合規交易。

## 5. 待辦事項清單 (Action Items)

- [ ] 確認主辦方 Discord：台灣 Stripe 測試帳號的權限範圍。
- [ ] 整合 Python 後端與 Stripe API，封裝成 Hermes 可調用的 Skill。
- [ ] 設定 NemoClaw 環境與台股白名單 (0050 等權值股) 的防護規則。
- [ ] 錄製 3 分鐘 Demo 影片，並確保所有環境預先暖機，避免展示時冷啟動的延遲。
