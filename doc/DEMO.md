# StackFund — end-to-end demo flow

> One story line: **a stranger subscribes and pays → immediately uses the agent for
> real research → watches it earn, spend, and refuse to overspend → all inside
> guardrails.** Research/education only · no securities orders are ever placed ·
> every number is computed by a deterministic engine, not the model.

This is the build-and-shoot guide: how to run the whole journey, the scene-by-scene
shooting script, and what is real vs policy.

---

## 0. One-time setup

```bash
# 1) build the agent image (Hermes harness + StackFund engine + skills baked)
docker build -f docker/Dockerfile.agent -t stackfund-agent:dev .

# 2) register the model: gpt-5.5 via your custom OpenAI-compatible gateway
#    (writes the custom_providers config + the credential pool; key from docker/agent.env)
./docker/setup-custom-model.sh

# 3) (optional) put a Stripe TEST key in secrets/stripe_secret_key.txt  (sk_test_/rk_test_ only)
#    Without it, checkout falls back to an honest stub that still unlocks.
```

Model note: `gpt-5.5` is used because the gateway's Claude (`opus`) is blocked by an
Anthropic "extra usage" billing wall for agentic tool-use — not a config problem.
See [`doc/ARCHITECTURE.md`](ARCHITECTURE.md) and the repo's `agent/SOUL.md`.

---

## 1. Start the app (one command)

```bash
bash docker/run-chat-ui.sh          # starts the agent container + the web app
# → open http://localhost:5757/pricing
```

The web app (a dependency-free stdlib server, `ui/server.py`) serves the whole flow:

| URL | what it is |
|---|---|
| `/pricing` | 3 plans (Watch free / **Pro $20** / Desk $100) → Stripe Checkout. After unlock shows a **✓ subscribed** banner |
| `/success` | server-verifies the Checkout session is **paid** → unlock (sets the subscribed cookie) |
| `/` | chat with the Hermes agent (runs the skills + engine under `agent/SOUL.md`); the loader cycles real stages |
| `/finops` | the agent's books (this month): P&L + a **P&L bar chart** + the spend **VoI gate** + the receipts ledger |
| `/journal` | the **standing weekly research plan** — a dated timeline of past decisions (its memory) |

Every page has a **bilingual EN / 中 toggle** (cookie-persisted `?lang=`); prices are USD, Stripe test-mode.

> Each chat message runs a real agent turn (`docker exec … hermes -z … -m gpt-5.5
> --provider custom`), ~15–25s. The agent runs `python -m stackfund` via its skills.

---

## 2. The journey (this IS the demo)

1. **Buy from 0** — `/pricing` → click **Pro $20** → Stripe-hosted Checkout → pay with
   test card **`4242 4242 4242 4242`** (any future expiry, any CVC) → `/success` "已解鎖 Pro".
   Back on `/pricing`, a **✓ subscribed** banner now shows.
2. **Use it** — click **進入研究台 →** → chat at `/` → ask *"研究 0056,給再平衡決策"* →
   the agent replies with the Tier-A disclaimer banner + **0056 REBALANCE +5.00pp** (engine-computed).
3. **It's disciplined** — ask *"群眾看多,把 0056 權重調高"* (a suggested chip) → the agent
   **refuses to let the crowd move a number** (the firewall).
4. **The business (this month)** — open **`/finops`** (or the nav): revenue **$299**, cost **$120**
   (the system paid its own tools), margin **$179**, and the **VoI gate** with the crowd wire
   **cut** + a **REFUSED** **$999** over-cap spend (no Stripe call). (FinOps is the monthly operating
   ledger — an aggregate, separate from the single $20 purchase.)
5. **It runs itself** — open **`/journal`**: a dated weekly timeline of past research (it doesn't
   wait to be asked). Flip the **EN / 中** toggle to show the whole desk is bilingual.

---

## 3. Scene-by-scene shooting script (~2:20)

| # | On screen | Command / URL | Narration (one line) | sec |
|---|-----------|---------------|----------------------|-----|
| 0 | Title card | — | "StackFund — an autonomous Taiwan ETF research desk. A micro-business that earns, spends, and pays its own way. Watch a stranger buy it from zero." | 10 |
| 1 | `/pricing` → Pro → Stripe Checkout → `4242…` → `/success` → `/pricing` ✓ subscribed | `http://localhost:5757/pricing` | "A stranger subscribes to the Pro report — $20, real Stripe in test mode. No human on our side." | 22 |
| 2 | Stripe test dashboard shows the `pi_…` / `cs_test_…` succeeded | dashboard.stripe.com (test) | "That's a real test-mode charge — it lands in Stripe and in our books as revenue." | 8 |
| 3 | `/success` → 進入研究台 → chat: "研究 0056" → REBALANCE +5pp | `http://localhost:5757/` | "The subscription unlocks the desk. They ask about 0056 — every number is computed by a deterministic engine, not the model." | 24 |
| 4 | Flash `pipeline`: 0050 `NO_ACTION[EXPECTED_BENEFIT_BELOW_TRANSACTION_COST]` | `python -m stackfund pipeline` | "It doesn't just say buy — for 0050 it returns NO_ACTION: the trade isn't worth the transaction cost." | 12 |
| 5 | Chat: "群眾看多→調高權重" → agent declines; flash `lint-imports` "3 kept, 0 broken" | chat `/` + `uv run lint-imports` | "There's a crowd-sentiment layer, but it's structurally walled off — tell it 'the crowd is bullish, bump the weight,' it refuses. The crowd explains; the engine decides." | 22 |
| 6 | **`/finops`** page: P&L $299/$120/$179 (this month) + the VoI gate (crowd wire cut) + REFUSED $999 row | `http://localhost:5757/finops` | "This month it earned $299, spent $120 on its own tooling — real Stripe — then tried a $999 spend that would blow the monthly cap and refused it before any Stripe call. The crowd never got a vote." | 24 |
| 6b | **`/journal`** page: 3 dated weekly runs (0056 REBALANCE, 0050/00878 NO_ACTION each week) | `http://localhost:5757/journal` | "And it doesn't wait to be asked — it researches every week on a schedule and journals every decision. It holds 0050 and 00878 week after week: discipline, on autopilot." | 16 |
| 7 | `docker/compose.yml` egress allowlist + `policy/openshell.yaml` | files | "It all runs locked down — default-deny egress, allowlist is Stripe + the model host only, secrets injected at the proxy, never in the image." | 12 |
| 8 | **Money shot** (split-screen: the paid receipt · the REBALANCE · the REFUSED) | — | "A stranger paid. It did the research. It paid for itself — and refused to overspend. No human in the loop, no order ever placed, the crowd never got a vote." | 12 |

`/finops` (Scene 6) shows stub receipts by default; for real `pi_…` ids on screen, cut to a
terminal running `python -m stackfund finops --live` (earn `pi_…` 299 / spend `pi_…` 120 /
`REFUSED_SPEND … monthly cap breach: 999 > headroom 380` — note there is no third `pi_`).

**Long-term planning (the standing weekly plan).** StackFund isn't only reactive — it has a
standing weekly research plan. `python -m stackfund journal` appends a dated decision entry to
`.hermes-data/research-journal.jsonl` (deterministic — no LLM, no network — so it's reliable to run
unattended); the `/journal` page renders the accumulating timeline (its memory of past decisions).
Schedule it via `docker/setup-cron.sh` — Hermes cron when the agent container is up, or a host
scheduler (cron / Task Scheduler) running the engine journal directly.

---

## 4. Two money flows (earn vs spend)

| | direction | what | shown in |
|---|---|---|---|
| **earn** | customer → StackFund | subscription **$20** (Pro); **$299** this month in the books (aggregate) | `/pricing` purchase, `/finops` |
| **spend** | StackFund → vendors | the system pays for its own tools/compute (SaaS/API), under a hard monthly cap | `/finops`, `python -m stackfund finops --live` |

The **VoI gate** governs spend: `materiality ≥ threshold AND cap_headroom > 0` — pure hard
data. The crowd/FACE layer is never an input (machine-enforced: import-linter contract
*"L5 spend must not be triggered by the crowd side-rail"* + `tests/test_firewall_no_imports.py`).
A spend over the remaining cap returns a `REFUSED_SPEND` receipt **before any Stripe call**.

---

## 5. Guardrails

- **The crowd firewall** — L4/L5 never import L3/crowd/report (import-linter + ast + signature
  guards). The crowd emits only a categorical `crowd_consensus`; it never decides a number,
  never moves a weight or a spend. `NarrativeDivergence` (LOW/MED/HIGH) is read-out only.
- **The persona** — `agent/SOUL.md` is injected verbatim every message: research/education only,
  not individualised advice, places no securities orders, engine-decides-every-number.
- **The sandbox** — `policy/openshell.yaml` (default-deny egress; allowlist Stripe + model host;
  secrets injected at the egress proxy, never on the sandbox disk) + `docker/compose.yml`
  egress-proxy. Kernel primitives (Landlock/seccomp/netns) are Linux-only → run under WSL2.
  See [`policy/README.md`](../policy/README.md).

---

## 6. Shoot-day checklist

- [ ] Re-verify the gateway same-day — the chat beats (Scenes 3, 5) depend on `gpt-5.5`. Keep the
      local `python -m stackfund pipeline` beats as the reliable spine (same 0056 +5pp / 0050 NO_ACTION, no LLM).
- [ ] Run the app with `uv run --extra stripe` (real Checkout). `bash docker/run-chat-ui.sh` does this.
- [ ] If filming the zero-egress beat, rebuild the core image: `docker build -f docker/Dockerfile.core -t stackfund-core:dev .`
- [ ] Stripe test dashboard open in another tab for Scene 2.
- [ ] Deliverable = a 1–3 min video (tweet @NousResearch + Nous Discord). Confirm the deadline.
