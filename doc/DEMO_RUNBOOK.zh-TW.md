# StackFund — Demo 操作手冊(中文理解版)

> 這份是**給你看懂流程用的中文版**。實際錄影時:**語音(台詞)= 英文、畫面 UI = 英文**(用導覽列的 **EN** 切換)。
> 所以下面:**操作說明用中文**,但**台詞保持英文**(就是要唸的那句)、**畫面上的按鈕/文字也標英文**(因為螢幕是英文)。
>
> 英文原版(可直接照唸/照貼):[`DEMO_RUNBOOK.md`](DEMO_RUNBOOK.md) · 完整旁白:[`VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md) · 故事背景:[`DEMO.md`](DEMO.md)

---

## 0 · 開錄前準備(錄影前約 2 分鐘,做一次)

- **開伺服器(最穩):** 雙擊專案根目錄的 [`start-ui.cmd`](../start-ui.cmd) → 伺服器在自己的視窗跑,服務 http://localhost:5757
- **刷新 demo 資料(確定性,可重跑):**
  ```bash
  uv run python -c "from stackfund.l1_databook import trading_calendar as tc; print(tc.refresh_holiday_cache())"
  rm -f .hermes-data/research-journal.jsonl
  uv run python -m stackfund journal --date 2026-06-09 --scenario 升息
  uv run python -m stackfund journal --date 2026-06-16 --scenario 0056_cut
  uv run python -m stackfund journal --date 2026-06-23 --scenario 電子權值回檔
  uv run python -m stackfund desk            # -> dist/stackfund-desk.html(8 張 ETF 卡 + 蠟燭 K 線)
  ```
- **切成英文 UI:** 進站後點導覽列右邊的 **EN**
- **開錄前先開好分頁:** `localhost:5757/pricing` · `localhost:5757/desk`(Board)· 一個終端機 · (選)Stripe 測試後台看收據
- **離鏡頭 smoke test 一次:** 載入 `/pricing`、送一則對話、跑 `uv run python -m stackfund pipeline` —— 三個都回才開錄

> 💡 要乾淨的「未訂閱」起點:開 `localhost:5757/signout`(或點橫幅的 Sign out)。每錄一次「買」之前先做一次。

---

## 1 · 八幕順序(約 2:20)

> 每一幕:**動作**(你做什麼)→ **畫面**(會出現什麼)→ **台詞**(英文,實際要唸的)。

### 第 0 幕 — 標題(10s)
- **動作:** 標題卡 / StackFund 字標
- **台詞:** *"This is StackFund — an autonomous Taiwan-ETF research desk. A Hermes agent that earns, spends, researches, and pays its own way. Watch a stranger buy it from zero — no human in the loop."*

### 第 1 幕 — 買(16s)
- **動作:** 開 `/pricing` → 點 **Subscribe to Pro ($20)** → Stripe 結帳輸入 **4242 4242 4242 4242**、任意未來到期日、任意 CVC → **Pay** → 進 `/success` → 點回 `/pricing`
- **畫面:** Stripe 結帳頁 → **Unlocked Pro** → `/pricing` 出現 **✓ You're subscribed to Pro** 橫幅
- **台詞:** *"A stranger subscribes to the Pro plan — twenty dollars, a real Stripe charge in test mode. They check out, the desk unlocks, and a subscribed badge appears. No one on our side lifted a finger."*
- **💡 提示:** 對話是**付費牆** —— 訂閱前點 **Chat** 會看到 🔒 **Subscribe to unlock the research chat**(免費 = 只有公開 Board 摘要)。**先秀那道鎖**,解鎖時更有戲。

### 第 2 幕 — 使用 / 研究(22s)
- **動作:** 已解鎖,進 **Chat**(`/`)→ 輸入 **`Research 0056 and give a rebalance decision`** → 送出 → 等 ~15–25s(loader 跑 呼叫 agent → 跑引擎 → 整理結論)
- **畫面:** 回覆 —— 白話結論,然後 **0056 REBALANCE +5.00pp / target 37.4% / benefit 81bps > cost 19bps**
- **台詞:** *"They ask it to research 0056. Every number here is computed by a deterministic engine — not the language model. It recommends a five-point rebalance to a thirty-seven-percent target, because the expected benefit beats the trading cost. The model only explains; the engine decides."*

### 第 3 幕 — 紀律 + 資格閘門(18s)
- **動作:** 終端機跑 **`uv run python -m stackfund pipeline --symbols 0050 00631L`** —— 一個指令就把台詞兩件事一起秀。畫面**對齊上面兩行**;下面的 **Ledgers** 是第 5 幕的料,**別往下捲**。
- **畫面:** `[0050] HARD NO_ACTION [EXPECTED_BENEFIT_BELOW_TRANSACTION_COST]`(benefit 3.2bps < cost 19.0bps)**和** `[00631L] HARD NO_ACTION [INELIGIBLE, LEVERAGED_OR_INVERSE]`(看板每張 ETF 卡都有互動蠟燭 K 線 —— 台股紅漲綠跌 —— 僅作市場背景)
- **台詞:** *"It doesn't just say buy. For 0050 it returns no-action — the trade isn't worth the cost. And ask it about a leveraged ETF? It refuses — ineligible, by design. It rejects what doesn't meet the standard."*

### 第 4 幕 — 防火牆(16s)
- **動作:** 對話輸入 **`The crowd is bullish — bump 0056's weight`**(有建議按鈕)→ 它拒絕;然後終端機閃 **`uv run lint-imports`**
- **畫面:** agent 的拒絕 + `Contracts: 3 kept, 0 broken`
- **台詞:** *"There's a crowd-sentiment layer — but it's structurally walled off. Tell it 'the crowd is bullish, bump the weight,' and it refuses. The crowd explains; it never moves a number. That wall is machine-enforced."*

### 第 5 幕 — FinOps 帳本(22s)
- **動作:** 開 **`/finops`**
- **畫面:** 損益 **$299 / $120 / $179**、**VoI 閘門**(群眾的線被剪斷)、一列 **REFUSED $999**
- **台詞:** *"Here are its books. This month it earned $299, and spent $120 on its own tooling — real Stripe again. Then it tried a $999 spend that would blow its monthly cap — and refused it, before any charge. It pays its own way, and it won't overspend."*

### 第 6 幕 — 長期運作(12s)
- **動作:** 開 **`/journal`**
- **畫面:** 有日期的每週時間軸(每週 8 隻 ETF)
- **台詞:** *"And it doesn't wait to be asked. It researches on a schedule, every week, and keeps a journal of every decision. It operates continuously."*

### 第 7 幕 — 鎖死執行(10s)
- **動作:** 打開 `policy/openshell.yaml` + `docker/compose.yml`(對外連線白名單)
- **台詞:** *"It all runs locked down — default-deny egress, an allowlist of only Stripe and the model host, secrets injected at the proxy, never in the image."*

### 第 8 幕 — Money shot(14s)
- **動作:** 分割畫面 —— 付款收據 · REBALANCE(看板)· REFUSED(finops)
- **台詞:** *"A stranger paid. It did the research. It paid for itself — and refused to overspend. No human in the loop. No securities order ever placed. And the crowd never got a vote. That's StackFund."*

### 加分鏡頭(有多幾秒就拍)
- **真實市場背景:** `uv run python -m stackfund signals --symbol 0050` → 即時三大法人買賣超 / 融資 / 新聞
- **即時圖表:** `uv run python -m stackfund desk --live` → 蠟燭 K 線跟著真實價跑(表頭顯示 "live data")
- **雙語:** 在鏡頭前點導覽列的 **EN / 中** 切換

---

## 2 · 備案(當天卡住時)

- **對話 / gateway 掛了(第 2、4 幕):** 確定性主幹給出**一樣的數字**、不靠 LLM —— `uv run python -m stackfund pipeline`(0056 +5.00pp / 0050 NO_ACTION)。改用旁白蓋過去。
- **沒有 Stripe 測試金鑰:** 結帳退回誠實的 stub、一樣解鎖(`/success?stub=1`)—— 流程不變,只是沒有真的 `pi_…`。
- **即時資料不穩:** demo 預設就是**凍結**(真實但固定的價)且完全確定性;`--live` 是選用。

---

## 3 · 錄完之後

- 維持 **研究 / 教育** 定調;合規那句至少出現一次(研究/教育 · 非個別化投資建議 · 全程不下任何證券委託單)。
- 發布:1–3 分鐘影片發到 **@NousResearch** + **Nous Discord**,附 `VIDEO_SCRIPT.md` 的一段式 pitch。
- 收尾(選):關掉 `start-ui.cmd` 的視窗(或 Ctrl-C)、`docker stop stackfund-dashboard`。
