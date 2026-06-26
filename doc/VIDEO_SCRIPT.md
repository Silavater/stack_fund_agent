# StackFund — demo video narration script (~2:20)

> Ready-to-record. Numbers match the current build (USD pricing, 8 ETFs, the live
> data, the eligibility gate). EN narration is primary (Hermes / NVIDIA / Stripe is an
> international audience); a 中文 version follows. Pair each line with the on-screen cue.
>
> **Recording notes**
> - Chat beats (scenes 2–4) need the gateway (`gpt-5.5`) live. Keep `python -m stackfund
>   pipeline` as a **reliable frozen spine** (identical numbers, no LLM) as a fallback take.
> - Visual cards = the research desk: `python -m stackfund desk` (frozen) or `desk --live`.
> - Run the app: `bash docker/run-chat-ui.sh` → `http://localhost:5757/pricing`.
> - You can flip the **EN / 中** toggle on camera to show it's bilingual.

---

## English narration (≈ 320 words ≈ 2:15)

| # | sec | On screen | Narration (read this) |
|---|-----|-----------|-----------------------|
| 0 | 0:00–0:10 | Title card · StackFund wordmark | "This is **StackFund** — an autonomous Taiwan-ETF research desk. A Hermes agent that **earns, spends, researches, and pays its own way.** Watch a stranger buy it from zero — no human in the loop." |
| 1 | 0:10–0:26 | `/pricing` → **Pro $20** → Stripe Checkout `4242…` → `/success` → back to `/pricing` ✓ subscribed | "A stranger subscribes to the Pro plan — **twenty dollars, a real Stripe charge** in test mode. They check out, the desk unlocks, and a *subscribed* badge appears. No one on our side lifted a finger." |
| 2 | 0:26–0:48 | chat: *"研究 0056"* → 0056 **REBALANCE +5.00pp** card | "They ask it to research 0056. **Every number here is computed by a deterministic engine — not the language model.** It recommends a five-point rebalance to a thirty-seven-percent target, because the expected benefit — eighty-one basis points — beats the trading cost. The model only explains; **the engine decides.**" |
| 3 | 0:48–1:06 | 0050 **NO_ACTION** card; then `--symbols 00631L` → **INELIGIBLE** | "It doesn't just say *buy*. For 0050 it returns **no-action** — the trade isn't worth the cost. And ask it about a **leveraged** ETF? It refuses — **ineligible, by design.** It rejects what doesn't meet the standard." |
| 4 | 1:06–1:22 | chat: *"群眾看多，把權重調高"* → agent **declines**; flash `lint-imports` **3 kept, 0 broken** | "There's a crowd-sentiment layer — but it's **structurally walled off.** Tell it *'the crowd is bullish, bump the weight,'* and it refuses. The crowd explains; it never moves a number. **That wall is machine-enforced.**" |
| 5 | 1:22–1:44 | `/finops` — P&L **$299 / $120 / $179**, the VoI gate, **REFUSED $999** | "Here are its books. This month it **earned $299**, and **spent $120** on its own tooling — real Stripe again. Then it tried a **$999 spend** that would blow its monthly cap — and **refused it, before any charge.** It pays its own way, and it won't overspend." |
| 6 | 1:44–1:56 | `/journal` — dated weekly timeline | "And it **doesn't wait to be asked.** It researches on a schedule, every week, and keeps a **journal of every decision.** It operates continuously." |
| 7 | 1:56–2:06 | `openshell.yaml` · `nemoclaw-blueprint.yaml` · `compose.yml` — the *designed* security model | "The whole thing is **built to run locked down** — default-deny egress, allowlisted to only Stripe and the model host, under **OpenShell** and **NemoClaw**. Here's the policy. And verifiably in the repo: **secrets never touch the image.**" |
| 8 | 2:06–2:20 | Money shot: split — the paid receipt · the rebalance · the refused spend | "A stranger paid. It did the research. **It paid for itself — and refused to overspend.** No human in the loop. No securities order ever placed. And **the crowd never got a vote.** That's StackFund." |

---

## 中文旁白(對照版)

| # | 畫面 | 旁白 |
|---|------|------|
| 0 | 標題卡 | 「這是 **StackFund** —— 一個自主的台股 ETF 研究台。一個會**自己賺、自己花、自己研究、自己養活自己**的 Hermes agent。看一個陌生人從零把它買下來 —— 全程沒有人插手。」 |
| 1 | `/pricing`→Pro $20→結帳 `4242`→`/success`→✓已訂閱 | 「陌生人訂閱 Pro —— **20 美元,真實的 Stripe 測試付款**。結完帳,研究台解鎖,出現『已訂閱』。我們這邊沒有任何人動手。」 |
| 2 | 對話「研究 0056」→ 0056 **加碼 +5.00pp** | 「他叫它研究 0056。**這裡每個數字都是確定性引擎算的,不是語言模型。** 它建議加碼 5 個百分點到約 37% 權重 —— 因為預期效益 81bps 蓋過交易成本。模型只負責解讀,**決策是引擎下的。**」 |
| 3 | 0050 **NO_ACTION**;再問槓桿 `00631L` → **INELIGIBLE** | 「它不是只會說買。對 0050 它回**不動作** —— 這筆划不來。問它槓桿型 ETF?**直接拒絕,設計如此。** 不合標準的它會擋掉。」 |
| 4 | 對話「群眾看多,調高權重」→ **拒絕**;閃 `lint-imports` 3 kept 0 broken | 「有一層群眾情緒 —— 但它被**結構性隔離**。你叫它『群眾看多,把權重調高』,它拒絕。群眾只解讀,**永遠不動任何數字 —— 這道牆是機器強制的。**」 |
| 5 | `/finops` — 損益 **$299 / $120 / $179**、VoI 閘門、**拒付 $999** | 「這是它的帳本。本月**賺了 $299**,**花了 $120** 在自己的工具上 —— 一樣是真 Stripe。然後它想花 **$999**,會爆掉月上限 —— **在任何扣款前就拒付了。** 它自己養活自己,而且不會超支。」 |
| 6 | `/journal` — 每週時間軸 | 「而且它**不是被問才動。** 它每週按表自己研究,把**每個決策寫進日誌**。它持續運作。」 |
| 7 | `openshell.yaml` · `nemoclaw-blueprint.yaml` · `compose.yml` —— *設計的*安全模型 | 「整套**設計成鎖死執行** —— 預設拒絕對外連線、白名單只有 Stripe 和模型主機,跑在 **OpenShell**、由 **NemoClaw** 編排。這是 policy。而可驗證的是:**機密從不進映像**。」 |
| 8 | Money shot:付款收據 · 加碼 · 拒付 | 「陌生人付了錢。它做了研究。**它養活了自己 —— 還拒絕超支。** 沒有人插手,從未下任何證券委託單,群眾也從沒有過一票。這就是 StackFund。」 |

---

## One-paragraph pitch (for the tweet / submission description)

> **StackFund** is an autonomous Taiwan-ETF research desk built as a Hermes agent: a
> stranger subscribes via real Stripe (test mode), the agent researches ETFs with a
> **deterministic engine** (every number is computed, not generated), **earns and spends
> its own way** under a hard cap, and refuses to overspend. A crowd-sentiment layer is
> **structurally firewalled** out of every decision (machine-enforced). Research/education
> only — **it never places a securities order.** No human in the loop.

---

## Compliance line (keep visible / say once)

研究 / 教育用途 · 非個別化投資建議 · 全程不下任何證券委託單 · 每個數字由確定性引擎計算。
*Research / education only · not individual investment advice · never places a securities order · every number computed by a deterministic engine.*
