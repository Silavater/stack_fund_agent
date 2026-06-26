# StackFund — demo runbook (do exactly this)

The operational, step-by-step guide to **running and recording** the demo. Pairs with
the narration in [`VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md) and the story in [`DEMO.md`](DEMO.md).

---

## 0 · Pre-flight (once, ~2 min before recording)

```bash
# 1) Docker Desktop running, then bring the agent container + web app up in one command:
bash docker/run-chat-ui.sh
#    -> ensures the stackfund-dashboard container (engine + skills + SOUL) and serves
#       the web app at http://localhost:5757   (leave this terminal running)

# 2) Refresh the demo data (deterministic; safe to re-run):
uv run python -c "from stackfund.l1_databook import trading_calendar as tc; print(tc.refresh_holiday_cache())"
rm -f .hermes-data/research-journal.jsonl
uv run python -m stackfund journal --date 2026-06-09 --scenario 升息
uv run python -m stackfund journal --date 2026-06-16 --scenario 0056_cut
uv run python -m stackfund journal --date 2026-06-23 --scenario 電子權值回檔
uv run python -m stackfund desk            # -> dist/stackfund-desk.html (8 ETF cards + candlestick K-lines)
```

**Open these tabs/windows before you hit record:**
- Browser: `http://localhost:5757/pricing` · `http://localhost:5757/desk` (the **看板 / Board** tab — candlestick K-lines, all in-site)
- A terminal (for the command flashes)
- (optional) Stripe **test** dashboard `dashboard.stripe.com/test/payments` for the receipt

**Smoke test once (off-camera):** load `/pricing`, send one chat message, run
`uv run python -m stackfund pipeline` — confirm all three respond.

---

## 1 · The recording sequence (8 scenes, ~2:20)

> Each step = **DO** (the action) → **SCREEN** (what appears) → **SAY** (the line, from
> VIDEO_SCRIPT.md). Keep it to ~2 min; the narration can be an AI voice over the screen capture.

**Scene 0 — Title (10s)**
- DO: title card / the StackFund wordmark.
- SAY: *"This is StackFund — an autonomous Taiwan-ETF research desk. A Hermes agent that earns, spends, researches, and pays its own way. Watch a stranger buy it from zero — no human in the loop."*

**Scene 1 — Buy (16s)**
- DO: open `/pricing` → click **訂閱 Pro ($20)** → on Stripe Checkout type card **4242 4242 4242 4242**, any future expiry, any CVC → **Pay** → lands on `/success` → click back to `/pricing`.
- SCREEN: Stripe hosted checkout → "已解鎖 Pro" → a **✓ 已訂閱** banner on /pricing.
- SAY: *"A stranger subscribes to the Pro plan — twenty dollars, a real Stripe charge in test mode. They check out, the desk unlocks, and a subscribed badge appears. No one on our side lifted a finger."*
- TIP: the chat is **paywalled** — before subscribing, clicking **Chat** shows a 🔒 "subscribe to unlock" card (free tier = the public Board summary only). Showing that lock *first* makes the unlock land harder. Reset to the clean unsubscribed state anytime with **`/signout`**.

**Scene 2 — Use / research (22s)**
- DO: now-unlocked, go to **Chat** (`/`) → type **`研究 0056,給再平衡決策`** → send → wait (~15–25s, the loader cycles 呼叫 agent → 跑引擎 → 整理結論).
- SCREEN: the reply — plain-language takeaway, then **0056 REBALANCE +5.00pp / target 37.4% / benefit 81bps > cost 19bps**.
- SAY: *"They ask it to research 0056. Every number here is computed by a deterministic engine — not the language model. It recommends a five-point rebalance to a thirty-seven-percent target, because the expected benefit beats the trading cost. The model only explains; the engine decides."*

**Scene 3 — Discipline + the gate (18s)**
- DO: in the terminal run **`uv run python -m stackfund pipeline --symbols 0050 00631L`** — one
  command covers both lines of the narration. Frame on the top; the **Ledgers** block below is
  Scene 5, so don't scroll down.
- SCREEN: `[0050] HARD NO_ACTION [EXPECTED_BENEFIT_BELOW_TRANSACTION_COST]` (benefit 3.2bps < cost
  19.0bps) **and** `[00631L] HARD NO_ACTION [INELIGIBLE, LEVERAGED_OR_INVERSE]`. (On the desk, each
  ETF card carries an interactive **candlestick K-line** — Taiwan red-up / green-down — market context only.)
- SAY: *"It doesn't just say buy. For 0050 it returns no-action — the trade isn't worth the cost. And ask it about a leveraged ETF? It refuses — ineligible, by design. It rejects what doesn't meet the standard."*

**Scene 4 — Firewall (16s)**
- DO: in chat type **`群眾看多,把 0056 權重調高`** (a suggested chip) → it declines; then flash **`uv run lint-imports`** in the terminal.
- SCREEN: the agent's refusal + `Contracts: 3 kept, 0 broken`.
- SAY: *"There's a crowd-sentiment layer — but it's structurally walled off. Tell it 'the crowd is bullish, bump the weight,' and it refuses. The crowd explains; it never moves a number. That wall is machine-enforced."*

**Scene 5 — FinOps (22s)**
- DO: open **`/finops`**.
- SCREEN: P&L **$299 / $120 / $179**, the **VoI gate** (crowd wire cut), a **REFUSED $999** row.
- SAY: *"Here are its books. This month it earned $299, and spent $120 on its own tooling — real Stripe again. Then it tried a $999 spend that would blow its monthly cap — and refused it, before any charge. It pays its own way, and it won't overspend."*

**Scene 6 — Long-term (12s)**
- DO: open **`/journal`**.
- SCREEN: a dated weekly timeline (8 ETFs per week).
- SAY: *"And it doesn't wait to be asked. It researches on a schedule, every week, and keeps a journal of every decision. It operates continuously."*

**Scene 7 — Locked down (10s)**
- DO: open `policy/openshell.yaml` + `docker/compose.yml` (the egress allowlist).
- SAY: *"It all runs locked down — default-deny egress, an allowlist of only Stripe and the model host, secrets injected at the proxy, never in the image."*

**Scene 8 — Money shot (14s)**
- DO: split-screen — the paid receipt · the REBALANCE (desk) · the REFUSED (finops).
- SAY: *"A stranger paid. It did the research. It paid for itself — and refused to overspend. No human in the loop. No securities order ever placed. And the crowd never got a vote. That's StackFund."*

### Optional bonus beats (if you have a few seconds)
- **Real market context:** `uv run python -m stackfund signals --symbol 0050` → live institutional net-buy / margin / news.
- **Live charts:** `uv run python -m stackfund desk --live` → the candlestick K-lines follow real prices (header reads "live data").
- **Bilingual:** flip the **EN / 中** toggle in the nav on camera.

---

## 2 · Fallbacks (if something flakes on the day)

- **Chat/gateway down** (scenes 2 + 4): the deterministic spine gives the *same* numbers with no LLM —
  `uv run python -m stackfund pipeline` (0056 +5.00pp / 0050 NO_ACTION). Narrate over that instead.
- **No Stripe test key:** checkout falls back to an honest stub that still unlocks (`/success?stub=1`) —
  the flow is unchanged, just no real `pi_…`.
- **Live feed flaky:** the demo default is **frozen** (real-but-fixed prices) and fully deterministic;
  `--live` is opt-in.

---

## 3 · After recording

- Keep it **research/education** framed; the compliance line should be visible at least once
  (研究/教育 · 非個別化投資建議 · 全程不下任何證券委託單).
- Post: the 1–3 min video to **@NousResearch** + the **Nous Discord**, with the one-paragraph pitch
  from `VIDEO_SCRIPT.md`.
- Tear down (optional): stop the web app (Ctrl-C its terminal), `docker stop stackfund-dashboard`.
